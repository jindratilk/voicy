"""Single-user localhost application with bounded jobs and persistent results."""
import asyncio
import json
import logging
import os
import shutil
import threading
import time
import uuid
import secrets
import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import numpy as np
import soundfile as sf
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .audio import decode, describe, master
from .engines import engines, Cancelled
from .auk import available as auk_available

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.getenv('CLEARVOICE_DATA', ROOT / '.data'))
DATA.mkdir(parents=True, exist_ok=True)
ACTIVE = {'queued', 'analyzing', 'enhancing'}
logger = logging.getLogger('clearvoice')
SESSION_TOKEN = os.getenv('VOICY_SESSION_TOKEN', '')
VERSION = '0.3.1'
app = FastAPI(title='Voicy', docs_url=None, redoc_url=None, openapi_url=None)
subscribers = set()

def broadcast():
    for loop, event in tuple(subscribers):
        try:
            loop.call_soon_threadsafe(event.set)
        except RuntimeError:
            pass
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1','localhost','[::1]','testserver'])
executor = ThreadPoolExecutor(max_workers=1)
lock = threading.RLock()
jobs = {}
cancels = {}

class Settings(BaseModel):
    engine: Literal['denoise','restore','mossformer','studio','auk'] = 'denoise'
    mode: Literal['natural','strong'] = 'natural'
    amount: int = Field(default=80, ge=0, le=100)
    level: bool = True


def save(job):
    with lock:
        path = DATA / job['id'] / 'job.json'
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(job))
        tmp.replace(path)
        broadcast()

for path in DATA.glob('*/job.json'):
    try:
        job = json.loads(path.read_text())
        if job['status'] in ACTIVE:
            job.update(status='error', message='Processing was interrupted. Try again.')
        jobs[job['id']] = job
        cancels[job['id']] = threading.Event()
        save(job)
    except (ValueError, KeyError, OSError):
        logger.warning('Skipped unreadable job metadata: %s', path.name)

@app.middleware('http')
async def local_requests_only(request: Request, call_next):
    if SESSION_TOKEN and request.url.path != '/session':
        supplied = request.cookies.get('voicy-session', '') or request.headers.get('X-Voicy-Token', '')
        if not secrets.compare_digest(supplied, SESSION_TOKEN):
            return JSONResponse({'detail': 'This session is not authorized.'}, status_code=401)
    origin = request.headers.get('origin')
    if origin and urlparse(origin).netloc != request.headers.get('host'):
        # Vite development is the only other allowed local origin.
        if origin not in ('http://localhost:5173', 'http://127.0.0.1:5173'):
            return JSONResponse({'detail':'Only same-origin local requests are allowed.'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.get('/session')
def session(token: str = ''):
    if not SESSION_TOKEN or not secrets.compare_digest(token, SESSION_TOKEN):
        raise HTTPException(403, 'Invalid session.')
    response = RedirectResponse('/', status_code=303)
    response.set_cookie('voicy-session', SESSION_TOKEN, httponly=True, samesite='lax')
    return response

@app.get('/api/events')
async def events(request: Request):
    async def stream():
        event = asyncio.Event()
        subscriber = (asyncio.get_running_loop(), event)
        subscribers.add(subscriber)
        try:
            yield 'data: refresh\n\n'
            while not await request.is_disconnected():
                try:
                    await asyncio.wait_for(event.wait(), timeout=25)
                    event.clear()
                    yield 'data: refresh\n\n'
                except asyncio.TimeoutError:
                    yield ': keepalive\n\n'
        finally:
            subscribers.discard(subscriber)
    return StreamingResponse(stream(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache'})


def get_job(job_id):
    with lock:
        if job_id not in jobs:
            raise HTTPException(404, 'Recording not found.')
        return jobs[job_id]


def change(job, **kwargs):
    with lock:
        job.update(kwargs)
        save(job)


def analyze(job):
    path = DATA / job['id']
    try:
        change(job, status='analyzing', message='Reading your recording…', progress=.1)
        audio, sr = decode(path/'upload', path/'original.wav')
        if cancels[job['id']].is_set():
            raise Cancelled()
        meta = describe(audio, sr)
        warnings = []
        if meta['peak_db'] < -65:
            warnings.append('This recording is nearly silent. Enhancement cannot recover speech that was not captured.')
        if meta['clipped_samples'] > len(audio)*.001:
            warnings.append('The recording appears clipped. Some distortion may remain.')
        change(job, status='ready', message='Ready to enhance.', progress=0, original=meta, warnings=warnings)
    except Cancelled:
        change(job, status='cancelled', message='Processing cancelled.', progress=0)
    except Exception as e:
        logger.exception('Decode failed')
        change(job, status='error', message=str(e) if isinstance(e,ValueError) else 'Could not read this recording.', progress=0)


def process(job, settings):
    path = DATA / job['id']
    began = time.monotonic()
    try:
        if cancels[job['id']].is_set():
            raise Cancelled()
        change(job, status='enhancing', progress=.01, message='Preparing your recording…')
        audio, sr = sf.read(path/'original.wav', dtype='float32')
        def progress(value, message):
            if cancels[job['id']].is_set():
                raise Cancelled()
            change(job, progress=value, message=message)
        if np.max(np.abs(audio)) < 1e-6:
            enhanced = audio.copy()
        else:
            enhanced, sr = engines.run(audio, settings.engine, settings.amount, settings.mode, progress, cancels[job['id']])
        progress(.9, 'Finishing and preparing your download…')
        if len(enhanced) != len(audio) or not np.isfinite(enhanced).all():
            raise ValueError('The model returned invalid audio. Try the noise-removal engine.')
        next_file = path/'next.wav'
        master(enhanced, sr, next_file, settings.level)
        progress(.97, 'Preparing the comparison…')
        final, sr = sf.read(next_file, dtype='float32')
        next_file.replace(path/'enhanced.wav')
        # Gain-match the original for a fair A/B listen, without affecting download.
        original_rms = np.sqrt(np.mean(audio.astype(np.float64)**2))
        result_rms = np.sqrt(np.mean(final.astype(np.float64)**2))
        compare_gain = min(4., float(result_rms / max(original_rms, 1e-9)))
        change(job, status='done', message='Your voice, in the clear.', progress=1,
               enhanced=describe(final,sr), elapsed=round(time.monotonic()-began,2),
               compare_gain=compare_gain, result_settings=settings.model_dump(), revision=job.get('revision',0)+1)
    except Cancelled:
        change(job, status='cancelled', message='Processing cancelled. Your original is safe.', progress=0)
    except Exception:
        logger.exception('Enhancement failed')
        change(job, status='error', message='Enhancement failed. Try again or open Diagnostics from the Help menu.', progress=0)
    finally:
        (path/'next.wav').unlink(missing_ok=True)
        (path/'premaster.wav').unlink(missing_ok=True)

@app.get('/api/health')
def health():
    return {'status':'ok', 'app':'voicy', 'version':VERSION, 'local':True, 'ffmpeg': bool(shutil.which('ffmpeg')),
            'engines':['denoise','restore','mossformer','studio'] + (['auk'] if auk_available() else []),
            'auk_available': auk_available()}

@app.get('/api/jobs')
def list_jobs():
    with lock:
        return sorted(copy.deepcopy(list(jobs.values())), key=lambda j:j['created'], reverse=True)

@app.post('/api/jobs', status_code=201)
async def upload(file: UploadFile = File(...)):
    with lock:
        if len(jobs) >= 100:
            raise HTTPException(409, 'Your library is full. Remove some recordings first.')
        if sum(j['status'] in ACTIVE for j in jobs.values()) >= 4:
            raise HTTPException(429, 'Please wait for current recordings to finish.')
    job_id = uuid.uuid4().hex
    path = DATA/job_id
    path.mkdir()
    try:
        total = 0
        with (path/'upload').open('wb') as out:
            while chunk := await file.read(1024*1024):
                total += len(chunk)
                out.write(chunk)
        if total == 0:
            raise HTTPException(400, 'The selected file is empty.')
    except Exception:
        shutil.rmtree(path)
        raise
    finally:
        await file.close()
    job = dict(id=job_id, name=Path(file.filename or 'Recording').name[:160], created=time.time(),
               status='queued', message='Waiting to read your recording…', progress=0, bytes=total)
    with lock:
        jobs[job_id] = job
        cancels[job_id] = threading.Event()
        save(job)
    executor.submit(analyze, job)
    return job

@app.get('/api/jobs/{job_id}')
def status(job_id: str):
    with lock:
        return dict(get_job(job_id))

@app.post('/api/jobs/{job_id}/enhance', status_code=202)
def enhance_job(job_id: str, settings: Settings):
    with lock:
        job = get_job(job_id)
        if job['status'] in ACTIVE:
            raise HTTPException(409, 'This recording is already processing.')
        if not (DATA/job_id/'original.wav').exists() or 'original' not in job:
            raise HTTPException(409, 'Please choose a valid audio recording first.')
        if settings.engine == 'auk' and not auk_available():
            raise HTTPException(503, 'AuK requires the optional local runtime and model installation. See the AuK setup notes.')
        cancels[job_id].clear()
        change(job, status='queued', progress=0, message='Waiting for the local audio engine…', settings=settings.model_dump())
        executor.submit(process, job, settings)
        return job

@app.post('/api/jobs/{job_id}/cancel')
def cancel_job(job_id: str):
    job = get_job(job_id)
    cancels[job_id].set()
    return {'message':'Cancellation requested. AuK stops its worker; other engines finish the current chunk.'}

@app.delete('/api/jobs/{job_id}', status_code=204)
def delete_job(job_id: str):
    with lock:
        job = get_job(job_id)
        if job['status'] in ACTIVE:
            raise HTTPException(409, 'Cancel processing before removing this recording.')
        trash = DATA/'.trash'
        trash.mkdir(exist_ok=True)
        (DATA/job_id).replace(trash/job_id)
        del jobs[job_id]
        del cancels[job_id]
        broadcast()

@app.get('/api/jobs/{job_id}/audio/{kind}')
def audio_file(job_id: str, kind: Literal['original','enhanced'], download: bool = False):
    job = get_job(job_id)
    path = DATA/job_id/f'{kind}.wav'
    if not path.exists():
        raise HTTPException(404, 'Audio is not ready yet.')
    filename = f"{Path(job['name']).stem}-{kind}.wav" if download else None
    return FileResponse(path, media_type='audio/wav', filename=filename,
                        headers={'Cache-Control':'no-store'})

WEB_ROOT = Path(os.getenv('VOICY_WEB_ROOT', ROOT/'web/dist'))
if WEB_ROOT.exists():
    app.mount('/', StaticFiles(directory=WEB_ROOT, html=True), name='web')
