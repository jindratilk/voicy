"""Pinned fixed-task ATen frontend without importing the Torch Python package."""
import ctypes
import hashlib
import json
from pathlib import Path
import numpy as np
from . import lean_frontend
BASE=Path(__file__).resolve().parent

class Extractor:
    def __init__(self,qwen_dir):
        meta=json.loads((BASE/'frontend/constants.json').read_text())
        if [meta[k] for k in ['audio_samples_16k','n_fft','hop_length','n_samples','dither']] != [192000,400,160,4800000,0]:
            raise ValueError('Unsupported native frontend configuration')
        for name,expected in meta['source_hashes'].items():
            if hashlib.sha256((Path(qwen_dir)/name).read_bytes()).hexdigest()!=expected:
                raise ValueError(f'Frontend constants do not match: {name}')
        with np.load(BASE/'frontend/constants.npz') as z:self.filters=np.ascontiguousarray(z['mel_filters'],dtype=np.float32)
        if self.filters.shape!=(201,128):raise ValueError('Unexpected mel matrix')
        self.library=ctypes.CDLL(str(BASE/'native_frontend.dylib'))
        self.compute=self.library.voicy_logmel
        pointer=ctypes.POINTER(ctypes.c_float)
        self.compute.argtypes=[pointer,pointer,pointer,ctypes.c_char_p,ctypes.c_int]
        self.compute.restype=ctypes.c_int
    def __call__(self,audio,*,sampling_rate,padding,return_attention_mask,return_tensors):
        if len(audio)!=1 or sampling_rate!=16000 or padding!='max_length' or return_tensors!='np' or not return_attention_mask:
            raise ValueError('Unsupported frontend call')
        samples=np.ascontiguousarray(audio[0],dtype=np.float32)
        if samples.shape!=(192000,):raise ValueError('Unsupported audio length')
        output=np.empty((1,128,30000),dtype=np.float32)
        pointer=ctypes.POINTER(ctypes.c_float);error=ctypes.create_string_buffer(2048)
        status=self.compute(samples.ctypes.data_as(pointer),self.filters.ctypes.data_as(pointer),
                            output.ctypes.data_as(pointer),error,len(error))
        if status:raise RuntimeError(error.value.decode('utf-8',errors='replace'))
        mask=np.zeros((1,30000),dtype=np.int32);mask[:,:1200]=1
        return {'input_features':output,'attention_mask':mask}

def install():
    lean_frontend.load_extractor=Extractor
    lean_frontend.install()
