"""Real neural inference. No hosted API and no DSP masquerading as AI."""
import os
import sys
import threading
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))

class Cancelled(Exception):
    pass

class Engines:
    def __init__(self):
        self.df = None
        self.restore = None
        self.moss = None
        self.lock = threading.Lock()

    def run(self, audio, engine, amount, mode, progress, cancel):
        if cancel.is_set():
            raise Cancelled()
        if engine == 'auk':
            with self.lock:
                if cancel.is_set():
                    raise Cancelled()
                from .auk import enhance
                return enhance(audio, progress, cancel, Cancelled)
        import torch
        torch.set_num_threads(min(4, os.cpu_count() or 1))
        with self.lock, torch.inference_mode():
            if cancel.is_set():
                raise Cancelled()
            if engine in ('mossformer', 'studio'):
                from .mossformer import MossFormer
                if self.moss is None:
                    progress(.02, 'Loading the full-band speech model…')
                    self.moss = MossFormer(Path(os.getenv('CLEARVOICE_MODELS', ROOT / '.models')))
                stage_progress = (lambda p, text: progress(p*.35, text)) if engine == 'studio' else progress
                cleaned = self.moss.enhance(audio, stage_progress, cancel, Cancelled)
                if engine == 'studio':
                    if cancel.is_set():
                        raise Cancelled()
                    return self._restore(cleaned, 0, lambda p, text: progress(.32+p*.62, text), cancel, tau=.25)
                return cleaned, 48000
            if engine == 'restore':
                return self._restore(audio, amount, progress, cancel)
            return self._denoise(audio, amount, mode, progress, cancel)

    def _denoise(self, audio, amount, mode, progress, cancel):
        import torch
        from df.enhance import init_df, enhance
        if self.df is None:
            progress(.02, 'Loading the local noise-removal model…')
            self.df = init_df(model_base_dir='DeepFilterNet3', log_level='ERROR', log_file=None)[:2]
        model, state = self.df
        # Context on both sides; crop only after compensating model/STFT latency.
        # This bounds memory and avoids independent, zero-context chunk seams.
        chunk, context = 48000 * 12, 48000
        out = np.zeros_like(audio)
        limit = (18 if mode == 'natural' else 40) * amount / 100
        if amount == 0:
            return audio.copy(), 48000
        for start in range(0, len(audio), chunk):
            if cancel.is_set():
                raise Cancelled()
            end = min(start + chunk, len(audio))
            lo, hi = max(0, start-context), min(len(audio), end+context)
            x = torch.from_numpy(audio[lo:hi].copy()).unsqueeze(0)
            y = enhance(model, state, x, pad=True, atten_lim_db=limit).squeeze(0).cpu().numpy()
            out[start:end] = y[start-lo:end-lo]
            progress(.1 + .75 * end / len(audio), 'Removing background noise…')
        return out, 48000

    def _restore(self, audio, amount, progress, cancel, *, tau=.5):
        import torch
        from scipy.signal import resample_poly
        from resemble_enhance.enhancer.inference import load_enhancer
        from resemble_enhance.inference import inference_chunk, remove_weight_norm_recursively
        model_dir = Path(os.getenv('CLEARVOICE_MODELS', ROOT / '.models')) / 'resemble'
        if self.restore is None:
            progress(.02, 'Loading the restoration model (first use downloads weights)…')
            self.restore = load_enhancer(model_dir, 'cpu')
            remove_weight_norm_recursively(self.restore)
        model = self.restore
        model.configurate_(nfe=64, solver='midpoint', lambd=amount/100, tau=tau)
        x = resample_poly(audio, 147, 160).astype(np.float32)
        sr, chunk, overlap = 44100, 44100 * 30, 44100
        # Equal-gain overlap-add without moving speech in time; never wet/dry mix
        # regenerated speech, whose phase need not match the input.
        out, weight = np.zeros_like(x), np.zeros_like(x)
        hop = chunk - overlap
        torch.manual_seed(2026)
        for start in range(0, len(x), hop):
            if cancel.is_set():
                raise Cancelled()
            end = min(start + chunk, len(x))
            piece = x[start:end]
            if np.max(np.abs(piece)) < 1e-6:
                y = np.zeros_like(piece)
            else:
                # Minimum context supports STFT reflection padding for short tails.
                padded = np.pad(piece, (0, max(0, 2048-len(piece))))
                y = inference_chunk(model, torch.from_numpy(padded), sr, 'cpu').numpy()[:len(piece)]
            w = np.ones(len(piece), dtype=np.float32)
            n = min(overlap, len(piece))
            if start > 0:
                w[:n] *= np.linspace(0, 1, n)
            if end < len(x):
                w[-n:] *= np.linspace(1, 0, n)
            out[start:end] += y*w
            weight[start:end] += w
            progress(.08+.77*end/len(x), 'Restoring speech detail… This model takes longer.')
            if end == len(x):
                break
        result = resample_poly(out / np.maximum(weight, 1e-8), 160, 147).astype(np.float32)
        return np.pad(result, (0, max(0,len(audio)-len(result))))[:len(audio)], 48000

engines = Engines()
