import os,sys,threading,time
from pathlib import Path
import numpy as np
import pytest
from server import auk
from server.engines import Cancelled


def fake_worker(monkeypatch,tmp_path,body):
    root=tmp_path/'app';(root/'experiments').mkdir(parents=True)
    script=root/'experiments/enhance_auk_local.py'
    script.write_text('import argparse,time,os\nfrom pathlib import Path\nimport numpy as np,soundfile as sf\np=argparse.ArgumentParser();p.add_argument("input");p.add_argument("--output");p.add_argument("--models");a=p.parse_args()\n'+body)
    monkeypatch.setattr(auk,'ROOT',root)
    monkeypatch.setattr(auk,'available',lambda:True)
    monkeypatch.setattr(auk,'configuration',lambda:(Path(sys.executable),tmp_path,tmp_path))


def test_real_subprocess_output_and_progress(monkeypatch,tmp_path):
    fake_worker(monkeypatch,tmp_path,'x,sr=sf.read(a.input);out=Path(a.output);out.mkdir();print("Completed chunk 1/1",flush=True);time.sleep(.4);sf.write(out/"output.wav",x[::2],24000,subtype="FLOAT")\n')
    updates=[];x=np.ones(48001,dtype=np.float32)*.1
    y,sr=auk.enhance(x,lambda p,m:updates.append(p),threading.Event(),Cancelled)
    assert sr==48000 and y.shape==x.shape and np.isfinite(y).all()
    assert updates==sorted(updates) and .84==pytest.approx(updates[-2])


def test_cancellation_terminates_worker(monkeypatch,tmp_path):
    pid=tmp_path/'pid'
    fake_worker(monkeypatch,tmp_path,f'Path({str(pid)!r}).write_text(str(os.getpid()));time.sleep(30)\n')
    event=threading.Event()
    def cancel():
        deadline=time.monotonic()+5
        while not pid.exists() and time.monotonic()<deadline:time.sleep(.02)
        event.set()
    thread=threading.Thread(target=cancel);thread.start();t=time.monotonic()
    with pytest.raises(Cancelled):auk.enhance(np.ones(4800,dtype=np.float32),lambda *_:None,event,Cancelled)
    thread.join();assert time.monotonic()-t<6
    assert pid.exists()
    with pytest.raises(ProcessLookupError):os.kill(int(pid.read_text()),0)


def test_wrong_duration_rejected(monkeypatch,tmp_path):
    fake_worker(monkeypatch,tmp_path,'out=Path(a.output);out.mkdir();sf.write(out/"output.wav",np.zeros(10),24000)\n')
    with pytest.raises(ValueError,match='duration'):auk.enhance(np.ones(4800,dtype=np.float32),lambda *_:None,threading.Event(),Cancelled)

def test_prefers_ready_app_installation(monkeypatch,tmp_path):
    monkeypatch.setattr(auk,'ROOT',tmp_path)
    for key in ['CLEARVOICE_AUK_HOME','CLEARVOICE_AUK_PYTHON','CLEARVOICE_AUK_SOURCE','CLEARVOICE_AUK_MODELS']:
        monkeypatch.delenv(key,raising=False)
    install=tmp_path/'.auk';install.mkdir();(install/'READY.json').write_text('{}')
    assert auk.configuration()==(install/'venv/bin/python',install/'source',install/'models')
    monkeypatch.setenv('CLEARVOICE_AUK_MODELS',str(tmp_path/'override'))
    assert auk.configuration()[2]==tmp_path/'override'
