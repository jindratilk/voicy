import numpy as np
import pytest
from server.chunking import plan_chunks, assemble_chunks

@pytest.mark.parametrize('seconds', [.001, 11.999, 12, 12.001, 20, 20.001, 43, 120])
def test_identity_and_coverage(seconds):
    sr=1000;n=round(seconds*sr)
    x=np.random.default_rng(12).normal(0,.1,n).astype(np.float32)
    plan=plan_chunks(n,sr)
    chunks=[np.pad(x[c.start:c.start+c.valid_frames],(0,c.frames-c.valid_frames)) for c in plan]
    y,joins=assemble_chunks(x,chunks,plan,sr)
    assert len(y)==n
    np.testing.assert_allclose(y,x,atol=3e-8,rtol=0)
    assert len(joins)==len(plan)-1

def test_finds_pause_without_a_timestamp_hint():
    sr=1000;x=np.ones(19000,dtype=np.float32)*.2;x[9600:10400]=0
    plan=plan_chunks(len(x),sr)
    chunks=[np.pad(x[c.start:c.start+c.valid_frames],(0,c.frames-c.valid_frames)) for c in plan]
    y,joins=assemble_chunks(x,chunks,plan,sr)
    assert 9.62<=joins[0]['seconds']<=10.38
    assert np.isfinite(y).all()

def test_rejects_missing_or_invalid_output():
    x=np.zeros(19000,dtype=np.float32);plan=plan_chunks(len(x),1000)
    with pytest.raises(ValueError):assemble_chunks(x,[np.zeros(12000)],plan,1000)
    with pytest.raises(ValueError):assemble_chunks(x,[np.zeros(12000),np.full(12000,np.nan)],plan,1000)
