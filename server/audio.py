"""Local decoding, waveform analysis, and transparent mastering."""
from pathlib import Path
import json
import subprocess
import numpy as np
import soundfile as sf

SAMPLE_RATE = 48000
MAX_SECONDS = 20 * 60


def command(args, timeout=120):
    try:
        return subprocess.run(args, capture_output=True, check=True, timeout=timeout)
    except FileNotFoundError as e:
        raise ValueError('FFmpeg is missing. Install FFmpeg and restart Clearvoice.') from e
    except subprocess.TimeoutExpired as e:
        raise ValueError('Audio decoding took too long.') from e
    except subprocess.CalledProcessError as e:
        raise ValueError('This file could not be decoded as audio. Try WAV, MP3, M4A, or FLAC.') from e


def decode(source: Path, target: Path):
    # Decode with a hard duration bound even when container metadata is false.
    command(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-protocol_whitelist', 'file,pipe',
             '-i', str(source), '-map', '0:a:0', '-vn', '-t', str(MAX_SECONDS + 1),
             '-ac', '1', '-ar', str(SAMPLE_RATE), '-c:a', 'pcm_f32le', str(target)])
    x, sr = sf.read(target, dtype='float32')
    if len(x) < sr // 4:
        raise ValueError('Choose a recording at least a quarter of a second long.')
    if len(x) > sr * MAX_SECONDS:
        raise ValueError('This recording exceeds the 20-minute limit.')
    if not np.isfinite(x).all():
        raise ValueError('The recording contains invalid audio samples.')
    return x, sr


def describe(x, sr=SAMPLE_RATE):
    peak = float(np.max(np.abs(x))) if len(x) else 0
    rms = float(np.sqrt(np.mean(x.astype(np.float64) ** 2))) if len(x) else 0
    bins = np.array_split(x, min(240, len(x)))
    return dict(duration=len(x)/sr, sample_rate=sr, channels=1,
                peak_db=round(20*np.log10(max(peak, 1e-9)), 2),
                rms_db=round(20*np.log10(max(rms, 1e-9)), 2),
                clipped_samples=int(np.count_nonzero(np.abs(x) >= .9999)),
                peaks=[round(float(np.max(np.abs(b))), 5) for b in bins])


def master(x, sr, target: Path, level: bool):
    """Two-pass BS.1770 loudness normalization; avoid boosting digital silence."""
    raw = target.with_name('premaster.wav')
    sf.write(raw, x, sr, subtype='FLOAT')
    if not level or np.max(np.abs(x)) < 1e-6:
        # Constant peak protection avoids clipping without squeezing quiet passages.
        peak = max(float(np.max(np.abs(x))), 1e-9)
        sf.write(target, x * min(1., .89125 / peak), sr, subtype='PCM_24')
        raw.unlink(missing_ok=True)
        return
    result = command(['ffmpeg','-nostdin','-hide_banner','-i',str(raw),'-af',
                      'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'])
    log = result.stderr.decode(errors='replace')
    m = json.loads(log[log.rfind('{'):log.rfind('}')+1])
    if not all(np.isfinite(float(m[k])) for k in ('input_i','input_tp','input_lra','input_thresh','target_offset')):
        sf.write(target, x * min(1., .89125 / max(float(np.max(np.abs(x))), 1e-9)), sr, subtype='PCM_24')
    else:
        filt = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:"
                f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
                f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
        command(['ffmpeg','-nostdin','-v','error','-y','-i',str(raw),'-af',filt,
                 '-ar',str(sr),'-c:a','pcm_s24le',str(target)])
    raw.unlink(missing_ok=True)
