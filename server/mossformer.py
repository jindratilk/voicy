"""Pinned MossFormer2 inference, preserving input gain and sample alignment."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import os
import urllib.request
import numpy as np
import torch
import torchaudio

REVISION = 'eff8c97925c8bec812af707814b3e5d777fd4503'
SHA256 = '03692b9f773bbd6bb43b9c5a41f96b1e28affd66e13796b7bec66ad3d8b227c6'
URL = f'https://huggingface.co/alibabasglab/MossFormer2_SE_48K/resolve/{REVISION}/last_best_checkpoint.pt'

def checkpoint(root):
    path = Path(root) / 'mossformer2' / 'model.pt'
    def valid(p):
        if not p.is_file(): return False
        with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest() == SHA256
    if not valid(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix('.partial')
        try:
            with urllib.request.urlopen(URL, timeout=60) as source, partial.open('wb') as out:
                while data := source.read(1024 * 1024): out.write(data)
            if not valid(partial): raise ValueError('MossFormer model checksum mismatch. Retry the download.')
            os.replace(partial, path)
        finally:
            partial.unlink(missing_ok=True)
    return path

class MossFormer:
    def __init__(self, root):
        from mossformer2_se.mossformer2_se_wrapper import MossFormer2_SE_48K
        self.args = SimpleNamespace(sampling_rate=48000, win_type='hamming', win_len=1920, win_inc=384, fft_len=1920, num_mels=60)
        self.model = MossFormer2_SE_48K(self.args).model
        weights = torch.load(checkpoint(root), map_location='cpu', weights_only=True)
        weights = {k.removeprefix('module.'):v for k,v in weights.items()}
        self.model.load_state_dict(weights, strict=True)
        self.model.eval()

    @torch.inference_mode()
    def piece(self, x):
        from mossformer2_se.features import compute_fbank, stft, istft
        if np.max(np.abs(x)) < 1e-7: return np.zeros_like(x)
        length = len(x)
        # Pad to complete STFT frames; the upstream no-center transform otherwise
        # zero-pads the final partial frame during inverse reconstruction.
        padded_length = max(1920, 1920 + ((max(0,length-1920)+383)//384)*384)
        audio = torch.from_numpy(np.pad(x,(0,padded_length-length))).float()*32768
        with torch.random.fork_rng():
            torch.manual_seed(2026)
            f = compute_fbank(audio[None],self.args)
        delta = torchaudio.functional.compute_deltas(f.T)
        delta2 = torchaudio.functional.compute_deltas(delta)
        features = torch.cat([f,delta.T,delta2.T],dim=1)[None]
        mask = self.model(features)[-1].permute(2,1,0)
        spec = stft(audio,self.args)*mask
        result = istft(torch.complex(spec[:,:,0],spec[:,:,1]),self.args,len(audio))
        return result.numpy()[:length]/32768

    def enhance(self, audio, progress, cancel, cancelled):
        output = np.empty_like(audio)
        # Full context for short voice memos; bounded chunks with surrounding
        # context for longer files. All starts stay on the 384-sample STFT grid.
        chunk, context = 48000*16, 48000*2
        if len(audio)<=48000*20:
            if cancel.is_set(): raise cancelled()
            result=self.piece(audio)
            if cancel.is_set(): raise cancelled()
            progress(.85,'Full-band speech enhancement complete.')
            return result
        for start in range(0,len(audio),chunk):
            if cancel.is_set(): raise cancelled()
            end=min(start+chunk,len(audio))
            lo=max(0,start-context); hi=min(len(audio),end+context)
            y=self.piece(audio[lo:hi])
            output[start:end]=y[start-lo:end-lo]
            progress(.08+.77*end/len(audio),'Enhancing full-band speech…')
        if cancel.is_set(): raise cancelled()
        return output
