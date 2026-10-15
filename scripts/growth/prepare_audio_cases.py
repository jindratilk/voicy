#!/usr/bin/env python3
"""Prepare the fixed E03 v1 demonstration set; never runs enhancement.

Requires Python 3.11+, NumPy, SciPy, FFmpeg and FFprobe. See E03-PROTOCOL.md.
Audio stays in an explicitly chosen directory outside the source repository.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

import numpy as np
import scipy
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
ARCHIVE_MD5 = "32fa31d27d2e1cad72775fee3f4849a9"
CONDITIONS = ["simulated-fan", "simulated-reflections", "intermittent-noise", "quiet-speech", "clean-control"]


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs).stdout


def frame_mask(audio):
    size = SR // 50
    padded = np.pad(audio, (0, (-len(audio)) % size)).reshape(-1, size)
    levels = np.sqrt(np.mean(padded.astype(np.float64) ** 2, axis=1))
    return np.repeat(levels > levels.max() * .1, size)[:len(audio)]


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


def add_noise(speech, noise, mask, target_snr, combined_mask=False):
    # Case 3's frozen definition uses the resulting mixture's active frames.
    # Resolve that mask without drawing new noise or tuning a model outcome.
    for _ in range(32):
        if rms(speech[mask]) <= 0 or rms(noise[mask]) <= 0:
            raise ValueError("Cannot define SNR for zero active signal")
        scaled = noise * (rms(speech[mask]) / (10 ** (target_snr / 20) * rms(noise[mask])))
        mixture = speech + scaled
        next_mask = frame_mask(mixture) if combined_mask else mask
        if np.array_equal(mask, next_mask):
            measured = 20 * math.log10(rms(speech[mask]) / rms(scaled[mask]))
            return mixture, measured
        mask = next_mask
    raise ValueError("Combined-signal SNR mask did not converge; preserve as a failed case")


def construct(reference, index):
    mask = frame_mask(reference)
    if not mask.any():
        raise ValueError("No active speech frames")
    normalized = reference * (10 ** (-23 / 20) / rms(reference[mask]))
    gain = min(1., 10 ** (-3 / 20) / np.max(np.abs(normalized)))
    reference = normalized * gain
    generator = np.random.Generator(np.random.PCG64(20261015 + index))
    n = len(reference)
    times = np.arange(n) / SR
    snr = None
    if index == 0:
        noise = sosfilt(butter(2, 900, fs=SR, output="sos"), generator.standard_normal(n))
        noise += .12 * np.sin(2 * np.pi * 120 * times) + .06 * np.sin(2 * np.pi * 240 * times)
        degraded, snr = add_noise(reference, noise, mask, 9)
    elif index == 1:
        response = np.zeros(int(.4 * SR) + 1)
        response[0] = 1.
        for delay, amplitude in [(0.035, .4), (.070, .25), (.110, .15)]:
            response[round(delay * SR)] += amplitude
        tail_times = np.arange(len(response)) / SR
        envelope = np.exp(-6.9 * tail_times / .4) * (tail_times >= .02)
        tail = generator.standard_normal(len(response)) * envelope
        tail *= .25 / np.linalg.norm(tail)
        response += tail
        degraded = fftconvolve(reference, response)
        reference = np.pad(reference, (0, len(degraded) - n))
    elif index == 2:
        envelope = np.zeros(n)
        for start, end in [(.15, .30), (.48, .60), (.78, .90)]:
            envelope[int(start * n):int(end * n)] = 1.
        noise = generator.standard_normal(n) * envelope
        degraded, snr = add_noise(reference, noise, mask, 6, combined_mask=True)
    elif index == 3:
        reference = reference * .1
        degraded, snr = add_noise(reference, generator.standard_normal(n), mask, 6)
    elif index == 4:
        degraded = reference.copy()
    else:
        raise ValueError(index)
    shared_gain = min(1., 10 ** (-3 / 20) / max(np.max(np.abs(reference)), np.max(np.abs(degraded))))
    return reference * shared_gain, degraded * shared_gain, {
        "seed": 20261015 + index,
        "active_frame_ms": 20,
        "active_frame_threshold_fraction_of_max_rms": .1,
        "normalized_reference_active_rms_target_dbfs": -23,
        "initial_peak_protection_gain": gain,
        "quiet_speech_gain": .1 if index == 3 else 1.,
        "shared_final_peak_protection_gain": shared_gain,
        "achieved_active_snr_db": snr,
        "reflection_tail_seconds": .4 if index == 1 else 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; preserving all prior results")
    repo = Path(__file__).resolve().parents[2]
    if args.output.resolve().is_relative_to(repo):
        parser.error("Audio output must be outside the source repository")
    if digest(args.archive, "md5") != ARCHIVE_MD5:
        parser.error("Archive does not match official test-clean MD5")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(args.output.parent).free < 12 * 1024 ** 3:
        parser.error("Less than 12 GiB storage headroom")
    ffmpeg = str(Path(shutil.which(args.ffmpeg) or args.ffmpeg).resolve())
    ffprobe = str(Path(shutil.which(args.ffprobe) or args.ffprobe).resolve())
    selected = []
    metadata_files = {}
    with tarfile.open(args.archive, "r:gz") as archive:
        members = archive.getmembers()
        transcripts = {}
        for member in members:
            if member.isfile() and member.name.endswith(".trans.txt"):
                for line in archive.extractfile(member).read().decode().splitlines():
                    name, text = line.split(" ", 1)
                    transcripts[name] = text
            if member.isfile() and Path(member.name).name in {"LICENSE.TXT", "README.TXT", "SPEAKERS.TXT", "CHAPTERS.TXT", "BOOKS.TXT"}:
                metadata_files[Path(member.name).name] = archive.extractfile(member).read()
        audio = [m for m in members if m.isfile() and re.fullmatch(r"\d+-\d+-\d+\.flac", Path(m.name).name)]
        audio.sort(key=lambda m: tuple(map(int, Path(m.name).stem.split("-"))))
        used = set()
        for member in audio:
            name = Path(member.name).stem
            speaker = int(name.split("-")[0])
            if speaker in used or name not in transcripts:
                continue
            data = archive.extractfile(member).read()
            details = json.loads(run([ffprobe, "-v", "error", "-show_entries", "stream=sample_rate,duration", "-of", "json", "-i", "pipe:0"], input=data))
            duration = float(details["streams"][0]["duration"])
            if not 4 <= duration <= 10:
                continue
            raw = run([ffmpeg, "-nostdin", "-v", "error", "-i", "pipe:0", "-map", "0:a:0", "-ac", "1", "-ar", str(SR), "-f", "f32le", "pipe:1"], input=data)
            reference = np.frombuffer(raw, dtype="<f4").astype(np.float64)
            if not np.isfinite(reference).all() or not len(reference):
                raise ValueError("Invalid selected source audio")
            selected.append((name, speaker, transcripts[name], member.name, data, reference, duration))
            used.add(speaker)
            if len(selected) == 5:
                break
    if len(selected) != 5:
        raise ValueError("Five eligible speakers not found")
    args.output.mkdir()
    source_meta = args.output / "source-metadata"
    source_meta.mkdir()
    for name, data in metadata_files.items():
        (source_meta / name).write_bytes(data)
    manifest = {
        "protocol": "E03 v1", "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_sha256": digest(args.protocol), "script_sha256": digest(Path(__file__)),
        "source": {"resource": "https://www.openslr.org/12", "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/", "archive_md5": ARCHIVE_MD5, "archive_sha256": digest(args.archive)},
        "tools": {"numpy": np.__version__, "scipy": scipy.__version__, "ffmpeg": run([ffmpeg, "-version"]).decode().splitlines()[0], "ffprobe": run([ffprobe, "-version"]).decode().splitlines()[0]},
        "selection_rule": "first eligible 4-10s full utterance per numerically sorted speaker/chapter/utterance; first five eligible speakers",
        "cases": [], "status": "inputs prepared; no model inference or quality review yet",
    }
    for index, (name, speaker, transcript, member, data, reference, duration) in enumerate(selected):
        directory = args.output / f"{index + 1:02}-{CONDITIONS[index]}"
        directory.mkdir()
        source = directory / f"{name}.flac"
        source.write_bytes(data)
        clean, degraded, parameters = construct(reference, index)
        outputs = {}
        for label, samples in [("reference", clean), ("input", degraded)]:
            path = directory / f"{label}.wav"
            wavfile.write(path, SR, samples.astype(np.float32))
            outputs[label] = {"path": path.relative_to(args.output).as_posix(), "sha256": digest(path), "frames": len(samples), "sample_rate": SR, "peak_dbfs": 20 * math.log10(max(float(np.max(np.abs(samples))), 1e-12)), "clipped_samples": int(np.count_nonzero(np.abs(samples) >= 1.))}
        case = {"case": index + 1, "condition": CONDITIONS[index], "utterance_id": name, "speaker_id": speaker, "transcript": transcript, "archive_member": member, "source_sha256": digest(source), "source_duration_seconds": duration, "parameters": parameters, "outputs": outputs}
        manifest["cases"].append(case)
        (directory / "case.json").write_text(json.dumps(case, indent=2) + "\n")
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "cases": [{"id": c["utterance_id"], "condition": c["condition"], "duration": c["source_duration_seconds"]} for c in manifest["cases"]], "status": manifest["status"]}, indent=2))


if __name__ == "__main__":
    main()
