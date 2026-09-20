import threading
import numpy as np
import pytest
from server.mossformer import MossFormer
from server.engines import Cancelled

def test_context_chunks_cover_tail_and_preserve_alignment():
    model=MossFormer.__new__(MossFormer)
    seen=[]
    def identity(x):
        seen.append(len(x)); return x.copy()
    model.piece=identity
    # Non-frame-aligned end exercises the last partial chunk.
    audio=np.arange(48000*45+137,dtype=np.float32)
    result=model.enhance(audio,lambda *_:None,threading.Event(),Cancelled)
    np.testing.assert_array_equal(result,audio)
    assert len(seen)==3 and max(seen)<=48000*20

def test_cancel_after_chunk_prevents_further_inference():
    model=MossFormer.__new__(MossFormer)
    cancel=threading.Event(); calls=[]
    def piece(x):
        calls.append(len(x));return x
    model.piece=piece
    with pytest.raises(Cancelled):
        model.enhance(np.ones(48000*42,dtype=np.float32),lambda *_:cancel.set(),cancel,Cancelled)
    assert len(calls)==1

def test_silence_stays_silent_without_model_forward():
    model=MossFormer.__new__(MossFormer)
    audio=np.zeros(12345,dtype=np.float32)
    np.testing.assert_array_equal(model.piece(audio),audio)
