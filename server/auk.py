"""Run the experimental Apple Silicon engine in an isolated, cancellable process."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]


def configuration():
    installed = Path(os.getenv('CLEARVOICE_AUK_HOME', ROOT/'.auk'))
    if (installed/'READY.json').is_file():
        defaults = (installed/'venv/bin/python', installed/'source', installed/'models')
    else:
        defaults = (WORKSPACE/'work/mlx-lab/bin/python', WORKSPACE/'work/AuK/src', WORKSPACE/'work/auk-lab')
    return tuple(Path(os.getenv(name, default)) for name, default in zip(
        ('CLEARVOICE_AUK_PYTHON','CLEARVOICE_AUK_SOURCE','CLEARVOICE_AUK_MODELS'), defaults))


def available():
    python, source, models = configuration()
    return python.is_file() and (source/'auk_mlx/infer.py').is_file() and all(
        (models/p).is_file() for p in ['mlx/vae.safetensors','mlx/dit_base.q8.safetensors',
        'mlx/fusion_base.safetensors','mlx/thinker/thinker.q8.safetensors',
        'mlx/thinker/thinker_config.json','original/config.yaml','qwen/config.json'])


def enhance(audio, progress, cancel, cancelled):
    from scipy.signal import resample_poly
    if cancel.is_set():raise cancelled()
    if not available():raise ValueError('AuK local runtime and weights are not installed. See the AuK setup notes.')
    python, source, models = configuration()
    with tempfile.TemporaryDirectory(prefix='clearvoice-auk-') as directory:
        temp=Path(directory);inp=temp/'input.wav';out=temp/'result'
        sf.write(inp,audio,48000,subtype='FLOAT')
        env={**os.environ,'PYTHONPATH':str(source),'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'}
        command=[str(python),'-u',str(ROOT/'experiments/enhance_auk_local.py'),str(inp),'--output',str(out),'--models',str(models)]
        progress(.03,'Loading AuK locally…')
        with (temp/'worker.log').open('w') as writer, (temp/'worker.log').open('r') as log:
            process=subprocess.Popen(command,stdout=writer,stderr=subprocess.STDOUT,env=env)
            try:
                position=0
                while process.poll() is None:
                    if cancel.is_set():raise cancelled()
                    log.seek(position);lines=log.readlines();position=log.tell()
                    for line in lines:
                        started=re.search(r'Starting chunk (\d+)/(\d+)',line)
                        if started:
                            current,total=map(int,started.groups())
                            progress(.08+.76*(current-1)/total,f'AuK: restoring section {current} of {total}…')
                        match=re.search(r'Completed chunk (\d+)/(\d+)',line)
                        if match:
                            done,total=map(int,match.groups())
                            progress(.08+.76*done/total,f'AuK: processed section {done} of {total}…')
                    time.sleep(.2)
                if cancel.is_set():raise cancelled()
                if process.returncode:
                    log.seek(0);detail=log.read()[-4000:]
                    raise RuntimeError(f'AuK worker exited with code {process.returncode}: {detail}')
                y,sr=sf.read(out/'output.wav',dtype='float32')
                if sr!=24000 or y.ndim!=1 or not np.isfinite(y).all():raise ValueError('Invalid AuK output')
                # App exports use its fixed 48k timeline. Resampling does not add bandwidth.
                expected=(len(audio)+1)//2
                if len(y)!=expected:raise ValueError('AuK output duration mismatch')
                y=resample_poly(y,2,1).astype(np.float32)[:len(audio)]
                progress(.86,'AuK enhancement complete.')
                return y,48000
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill();process.wait(timeout=3)
