import threading
from types import SimpleNamespace
import numpy as np
import pytest
from server.engines import Engines, Cancelled

def test_studio_orders_models_and_disables_duplicate_predenoising(monkeypatch):
    engine=Engines();seen=[];progress=[]
    source=np.ones(100,dtype=np.float32)
    def clean(audio,report,cancel,exc):
        seen.append('clean');report(.85,'clean');return audio*.5
    def restore(audio,amount,report,cancel,*,tau):
        seen.append('restore');assert amount==0;assert tau==.25
        np.testing.assert_array_equal(audio,source*.5)
        report(.85,'restore');return audio*.8,48000
    engine.moss=SimpleNamespace(enhance=clean)
    monkeypatch.setattr(engine,'_restore',restore)
    result,sr=engine.run(source,'studio',99,'strong',lambda p,_:progress.append(p),threading.Event())
    assert seen==['clean','restore'] and sr==48000
    assert progress==sorted(progress)
    np.testing.assert_allclose(result,source*.4)

def test_studio_cancellation_between_models(monkeypatch):
    engine=Engines();cancel=threading.Event()
    def clean(audio,*_): cancel.set();return audio
    engine.moss=SimpleNamespace(enhance=clean)
    def forbidden(*_): raise AssertionError('Restoration ran after cancellation')
    monkeypatch.setattr(engine,'_restore',forbidden)
    with pytest.raises(Cancelled):
        engine.run(np.ones(100,dtype=np.float32),'studio',80,'natural',lambda *_:None,cancel)
