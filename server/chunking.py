"""Context-overlapped assembly for independently generated mono speech.

This preserves the sample timeline; it does not correct model timing drift.
Low-energy joins reduce seam risk but are not a voice-activity detector.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Chunk:
    start: int
    frames: int
    valid_frames: int


def plan_chunks(frames: int, sample_rate: int, seconds: float = 12,
                overlap_seconds: float = 4) -> list[Chunk]:
    if frames <= 0 or sample_rate <= 0:
        raise ValueError('Audio length and sample rate must be positive')
    size = round(seconds * sample_rate)
    overlap = round(overlap_seconds * sample_rate)
    if not 0 < overlap < size:
        raise ValueError('Overlap must be positive and shorter than a chunk')
    chunks = []
    start = 0
    while True:
        chunks.append(Chunk(start, size, min(size, frames - start)))
        if start + size >= frames:
            return chunks
        start += size - overlap


def assemble_chunks(source: np.ndarray, generated: list[np.ndarray],
                    plan: list[Chunk], sample_rate: int) -> tuple[np.ndarray, list[dict]]:
    """Join at automatically chosen low-energy positions with 20 ms fades.

    Source and generated chunks must already have the same sample rate. Each
    generated chunk includes any end padding; only real source duration is kept.
    """
    source = np.asarray(source)
    if source.ndim != 1 or not len(source) or not np.isfinite(source).all():
        raise ValueError('Expected finite, nonempty mono source')
    if sample_rate <= 0 or len(generated) != len(plan) or not plan or plan[0].start != 0:
        raise ValueError('Invalid sample rate or chunk plan')
    for i, (chunk, audio) in enumerate(zip(plan, generated)):
        if (np.ndim(audio) != 1 or len(audio) != chunk.frames or
                not np.isfinite(audio).all() or chunk.valid_frames != min(chunk.frames, len(source)-chunk.start)):
            raise ValueError('Generated audio does not match the chunk plan')
        if i and not plan[i-1].start < chunk.start < plan[i-1].start + plan[i-1].frames:
            raise ValueError('Chunks must be ordered with overlapping coverage')
    if plan[-1].start + plan[-1].frames < len(source):
        raise ValueError('Chunk plan does not cover the source')
    output = np.empty(len(source), dtype=np.float32)
    first = min(len(source), plan[0].frames)
    output[:first] = generated[0][:first]
    joins = []
    half = max(1, round(.01 * sample_rate))
    radius = max(half, round(.02 * sample_rate))
    previous_seam = 0
    for index in range(1, len(plan)):
        left, right = plan[index-1], plan[index]
        end = min(left.start + left.frames, len(source))
        overlap = end - right.start
        margin = max(radius, min(round(.5*sample_rate), overlap//4))
        low = max(right.start + margin, previous_seam + 2*half)
        high = end - margin
        if high < low:
            raise ValueError('Insufficient overlap for a safe fade')
        candidates = np.arange(low, high+1, max(1, round(.005*sample_rate)))
        tracks = [(source, 0), (generated[index-1], left.start), (generated[index], right.start)]
        score = np.zeros(len(candidates))
        for audio, offset in tracks:
            # Normalize each track so input loudness cannot dominate seam choice.
            region = np.asarray(audio[right.start-offset:end-offset], dtype=np.float64)
            scale = max(float(np.mean(region*region)), 1e-12)
            for j, center in enumerate(candidates):
                window = audio[center-offset-radius:center-offset+radius]
                score[j] += float(np.mean(np.square(window, dtype=np.float64))) / scale
        # Stable tie-break favors the middle of overlap for silent recordings.
        best = np.flatnonzero(score <= score.min() + 1e-12)
        pick = best[np.argmin(abs(candidates[best] - (low+high)/2))]
        seam = int(candidates[pick]);lo, hi = seam-half, seam+half
        weight = np.linspace(0, 1, hi-lo, dtype=np.float32)
        incoming = generated[index]
        output[lo:hi] = output[lo:hi]*(1-weight) + incoming[lo-right.start:hi-right.start]*weight
        stop = min(right.start+right.frames, len(source))
        output[hi:stop] = incoming[hi-right.start:stop-right.start]
        joins.append({'sample': seam, 'seconds': seam/sample_rate,
                      'fade_seconds': 2*half/sample_rate, 'normalized_energy': float(score[pick])})
        previous_seam = seam
    return output, joins
