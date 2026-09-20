"""Pinned, integrity-checked local model cache. Modified for Clearvoice."""
import hashlib
from pathlib import Path
import urllib.request

REVISION = '4e3510ce4a8391159f665903544c5150bee7b2cb'
HASHES = {'hparams.yaml': '80c3f15bc5a5b2cacf2c698699a0f6599d62911c0d53e1d6dee895c0d7cbaeac', 'ds/G/latest': '37a8eec1ce19687d132fe29051dca629d164e2c4958ba141d5f4133a33f0688f', 'ds/G/default/mp_rank_00_model_states.pt': 'f9d035f318de3e6d919bc70cf7ad7d32b4fe92ec5cbe0b30029a27f5db07d9d6'}

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def download(run_dir=None):
    target = Path(run_dir) if run_dir else Path(__file__).parent.parent/'model_repo/enhancer_stage2'
    for relative, expected in HASHES.items():
        path = target/relative
        if path.exists() and digest(path) == expected:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix(path.suffix+'.partial')
        url = f'https://huggingface.co/ResembleAI/resemble-enhance/resolve/{REVISION}/enhancer_stage2/{relative}'
        try:
            with urllib.request.urlopen(url, timeout=60) as response, partial.open('wb') as out:
                while chunk := response.read(1024*1024):
                    out.write(chunk)
            if digest(partial) != expected:
                raise RuntimeError('Restoration model checksum mismatch. Please retry the download.')
            partial.replace(path)
        finally:
            partial.unlink(missing_ok=True)
    return target
