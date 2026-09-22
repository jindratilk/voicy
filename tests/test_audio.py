from pathlib import Path
import numpy as np
import soundfile as sf
import pytest
from server.audio import decode,master,describe
from server.engines import Engines,Cancelled
import threading

def test_m4a_decoding_preserves_duration_and_rate(tmp_path):
    import subprocess
    sr=44100;x=.2*np.sin(np.arange(sr)*2*np.pi*440/sr)
    source=tmp_path/'source.wav';sf.write(source,x,sr)
    encoded=tmp_path/'encoded.m4a'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),str(encoded)],check=True)
    y,rate=decode(encoded,tmp_path/'decoded.wav')
    assert rate==48000 and abs(len(y)/rate-1)<.05
    assert np.isfinite(y).all()

def test_silence_stays_silent(tmp_path):
    target=tmp_path/'out.wav';master(np.zeros(48000,dtype=np.float32),48000,target,True)
    y,sr=sf.read(target)
    assert not np.any(y) and sr==48000

def test_peak_protection_and_24bit_export(tmp_path):
    target=tmp_path/'out.wav'
    x=np.tile(np.array([1.8,-1.8,.2,-.2],dtype=np.float32),12000)
    master(x,48000,target,False)
    y,sr=sf.read(target)
    assert len(y)==len(x) and max(abs(y))<.892
    assert sf.info(target).subtype=='PCM_24'

def test_corrupt_and_too_short_input(tmp_path):
    bad=tmp_path/'bad';bad.write_text('not audio')
    with pytest.raises(ValueError):decode(bad,tmp_path/'out.wav')
    sf.write(tmp_path/'short.wav',np.zeros(1000),48000)
    with pytest.raises(ValueError,match='quarter'):decode(tmp_path/'short.wav',tmp_path/'out.wav')

def test_cancel_before_model_load():
    e=threading.Event();e.set()
    with pytest.raises(Cancelled):Engines().run(np.zeros(48000,dtype=np.float32),'denoise',80,'natural',lambda *_:None,e)

def test_decode_preserves_recording_beyond_twenty_minutes(tmp_path):
    source=tmp_path/'long.wav'
    sr=8000
    block=np.zeros(sr,dtype=np.float32)
    with sf.SoundFile(source,'w',samplerate=sr,channels=1,subtype='PCM_16') as f:
        for _ in range(20*60+1):f.write(block)
        f.write(.2*np.sin(np.arange(sr)*2*np.pi*440/sr))
    x,rate=decode(source,tmp_path/'decoded.wav')
    assert rate==48000 and len(x)==(20*60+2)*rate
    assert np.max(np.abs(x[-rate:]))>.1


def test_large_wav_selects_rf64_without_changing_pcm(monkeypatch,tmp_path):
    from server.audio import write_wav
    calls=[]
    monkeypatch.setattr(sf,'write',lambda *a,**kw:calls.append((a,kw)))
    class LargeAudio:
        size=2**30
    audio=LargeAudio()
    write_wav(tmp_path/'large.wav',audio,48000)
    assert calls[0][0][1] is audio
    assert calls[0][1]=={'subtype':'FLOAT','format':'RF64'}

def test_rf64_recording_decodes_with_bundled_ffmpeg(tmp_path):
    x=.2*np.sin(np.arange(48000)*2*np.pi*440/48000)
    source=tmp_path/'rf64.wav'
    sf.write(source,x,48000,subtype='FLOAT',format='RF64')
    y,sr=decode(source,tmp_path/'decoded.wav')
    assert sr==48000 and np.array_equal(y,x.astype(np.float32))
