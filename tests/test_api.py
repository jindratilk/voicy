import importlib,io,time
import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

@pytest.fixture
def api(tmp_path,monkeypatch):
    monkeypatch.setenv('CLEARVOICE_DATA',str(tmp_path/'jobs'))
    import server.app as module
    # Runtime state is isolated from the user's actual local recordings.
    module=importlib.reload(module)
    with TestClient(module.app) as client:
        yield client,module
    module.executor.shutdown(wait=True)

def wait(client,jobid):
    for _ in range(200):
        j=client.get('/api/jobs/'+jobid).json()
        if j['status'] not in ('queued','analyzing','enhancing'):return j
        time.sleep(.02)
    raise AssertionError('Job timed out')

def wav():
    b=io.BytesIO();sf.write(b,np.zeros(48000),48000,format='WAV');return b.getvalue()

def test_upload_process_range_export_delete(api):
    c,m=api
    response=c.post('/api/jobs',files={'file':('silence.wav',wav(),'audio/wav')})
    assert response.status_code==201
    id=response.json()['id'];assert wait(c,id)['status']=='ready'
    assert c.post(f'/api/jobs/{id}/enhance',json={'amount':101}).status_code==422
    assert c.post(f'/api/jobs/{id}/enhance',json={'engine':'denoise'}).status_code==202
    done=wait(c,id);assert done['status']=='done' and done['enhanced']['duration']==1
    result=c.get(f'/api/jobs/{id}/audio/enhanced?download=true')
    assert result.status_code==200 and 'attachment' in result.headers['content-disposition']
    assert sf.info(io.BytesIO(result.content)).subtype=='PCM_24'
    assert c.get(f'/api/jobs/{id}/audio/original',headers={'Range':'bytes=0-99'}).status_code==206
    assert c.delete(f'/api/jobs/{id}').status_code==204
    assert c.get(f'/api/jobs/{id}').status_code==404

def test_invalid_audio_and_empty_upload(api):
    c,_=api
    assert c.post('/api/jobs',files={'file':('empty.wav',b'')}).status_code==400
    result=c.post('/api/jobs',files={'file':('bad.wav',b'not audio')}).json()
    assert wait(c,result['id'])['status']=='error'
    assert c.post(f"/api/jobs/{result['id']}/enhance",json={}).status_code==409

def test_cross_origin_and_unknown_host_rejected(api):
    c,_=api
    assert c.post('/api/jobs',headers={'Origin':'https://evil.example'},files={'file':('a.wav',wav())}).status_code==403
    assert c.get('/api/health',headers={'Host':'evil.example'}).status_code==400
    assert c.get('/api/health').json()['local'] is True

def test_delete_and_duplicate_enhance_rejected_while_busy(api,monkeypatch):
    c,m=api
    monkeypatch.setattr(m.executor,'submit',lambda *args:None)
    j=c.post('/api/jobs',files={'file':('queued.wav',wav())}).json()
    assert c.delete('/api/jobs/'+j['id']).status_code==409
    assert c.post('/api/jobs/'+j['id']+'/enhance',json={}).status_code==409
    assert c.post('/api/jobs/'+j['id']+'/cancel').status_code==200

def test_auk_missing_runtime_returns_setup_error(api,monkeypatch):
    c,m=api;monkeypatch.setattr(m,'auk_available',lambda:False)
    response=c.post('/api/jobs',files={'file':('silence.wav',wav(),'audio/wav')})
    id=response.json()['id'];assert wait(c,id)['status']=='ready'
    r=c.post(f'/api/jobs/{id}/enhance',json={'engine':'auk'})
    assert r.status_code==503 and 'optional local runtime' in r.json()['detail']
    assert c.get(f'/api/jobs/{id}').json()['status']=='ready'


def test_session_cookie_required_when_native_token_enabled(tmp_path, monkeypatch):
    monkeypatch.setenv('CLEARVOICE_DATA', str(tmp_path/'private-jobs'))
    monkeypatch.setenv('VOICY_SESSION_TOKEN', 'test-only-session-token')
    import server.app as module
    module = importlib.reload(module)
    with TestClient(module.app) as client:
        assert client.get('/api/jobs').status_code == 401
        assert client.get('/session?token=wrong').status_code == 403
        response = client.get('/session?token=test-only-session-token', follow_redirects=False)
        assert response.status_code == 303
        assert 'HttpOnly' in response.headers['set-cookie']
        assert client.get('/api/jobs').status_code == 200
        assert client.post('/api/jobs', headers={'Origin':'https://evil.example'}, files={'file':('a.wav',wav())}).status_code == 403
    module.executor.shutdown(wait=True)
    monkeypatch.delenv('VOICY_SESSION_TOKEN')
    importlib.reload(module)


def test_cancel_queued_enhancement_never_calls_engine(api, monkeypatch):
    c,m=api
    j=c.post('/api/jobs',files={'file':('silence.wav',wav())}).json()
    assert wait(c,j['id'])['status']=='ready'
    monkeypatch.setattr(m.executor,'submit',lambda *args:None)
    assert c.post(f"/api/jobs/{j['id']}/enhance",json={'engine':'denoise'}).status_code==202
    c.post(f"/api/jobs/{j['id']}/cancel")
    monkeypatch.setattr(m.engines,'run',lambda *args:pytest.fail('Cancelled job reached inference'))
    m.process(m.jobs[j['id']],m.Settings(engine='denoise'))
    assert m.jobs[j['id']]['status']=='cancelled'
    assert not (m.DATA/j['id']/'enhanced.wav').exists()


def test_library_removal_preserves_recoverable_audio(api):
    c,m=api
    j=c.post('/api/jobs',files={'file':('silence.wav',wav())}).json()
    assert wait(c,j['id'])['status']=='ready'
    assert c.delete('/api/jobs/'+j['id']).status_code==204
    assert (m.DATA/'.trash'/j['id']/'original.wav').exists()
    assert c.get('/api/jobs/'+j['id']).status_code==404

def test_upload_accepts_more_than_250_mb(api,monkeypatch):
    import asyncio
    client,module=api
    monkeypatch.setattr(module.executor,'submit',lambda *args:None)
    class LargeUpload:
        filename='long.wav'
        remaining=251
        async def read(self,size):
            if not self.remaining:return b''
            self.remaining-=1
            return b'\0'*(1024*1024)
        async def close(self):pass
    job=asyncio.run(module.upload(LargeUpload()))
    assert job['bytes']==251*1024*1024
    assert (module.DATA/job['id']/'upload').stat().st_size==job['bytes']
