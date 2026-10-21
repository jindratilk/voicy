# E03 v1 — Reproducible local speech-cleanup examples

Frozen before selection or model output inspection: 15 October 2026.
Purpose: help prospective users hear Voicy's behavior on human read speech with controlled degradations, including an already-clean control. This is a demonstration set, not a blinded trial, general quality benchmark, independent review, or Adobe comparison.

## Source and rights

Use only LibriSpeech `test-clean.tar.gz` from OpenSLR SLR12. OpenSLR identifies the corpus as CC BY 4.0 and attributes preparation to Vassil Panayotov with assistance from Daniel Povey. Citation: Vassil Panayotov, Guoguo Chen, Daniel Povey and Sanjeev Khudanpur, *LibriSpeech: an ASR corpus based on public domain audio books*, ICASSP 2015.

- Resource and license declaration: https://www.openslr.org/12
- License: https://creativecommons.org/licenses/by/4.0/
- Archive: https://openslr.trmal.net/resources/12/test-clean.tar.gz
- Official MD5: `32fa31d27d2e1cad72775fee3f4849a9` (integrity only; calculate SHA-256 as well).
- Preserve archive metadata/license files and exact utterance transcript. Published derivatives must carry attribution, source/utterance IDs, license link and an explicit notice of resampling, added degradations, enhancement and mastering.
- Do not imply the readers endorse Voicy. These are public audiobook speech excerpts, not customer recordings. No private audio is used.

## Selection rule, fixed in advance

Sort speaker IDs numerically, then chapters and utterance IDs numerically. For each speaker, choose the first utterance whose unmodified source duration is at least 4 and at most 10 seconds, with a supplied transcript. Stop at the first five eligible speakers. Do not select on sound quality, model outcome, words, accent, age or apparent identity. Do not crop an utterance to make it fit. Preserve all five outputs/failures; changing this rule requires a new protocol version with a reason.

This controls selection but is not a representative sample of speakers, languages, microphones or real noisy recordings. LibriSpeech is widely used in speech-model research; training-set overlap with AuK and its components is not established here. Do not call these held-out model-generalization tests.

## Input construction

Decode the full selected FLAC to mono 48 kHz float32 with the pinned available FFmpeg, preserving the source. Normalize reference active-speech RMS to -23 dBFS using 20 ms frames above 10% of the maximum frame RMS; then apply a common peak-protection gain if needed. Report the exact definition, measured gain and achieved active-region SNR. Use a dedicated NumPy PCG64 generator with seed `20261015 + case_index` (zero-based). No retries to find a more flattering random draw.

Assign the five selected speakers to the following conditions in order:

1. **Steady fan-like noise:** deterministic low-pass noise plus 120/240 Hz hum, +9 dB active-region speech-to-noise ratio. This is simulated fan-like noise, not a fan recording.
2. **Room reflections:** deterministic impulse response with direct sound and reflections at 35/70/110 ms (gains .40/.25/.15), plus decaying seeded noise from 20 ms to 400 ms; preserve full convolved tail. Label as simulated reflections, not a measured room.
3. **Intermittent noise:** seeded broadband noise with three fixed burst windows (15–30%, 48–60%, 78–90% of source duration), +6 dB active-region SNR during the combined signal's active frame mask. This is synthetic interference, not a street or restaurant recording.
4. **Quiet speech:** attenuate reference by 20 dB, then add seeded noise at +6 dB active-region SNR. Do not imply this reproduces a specific microphone noise floor.
5. **Already-clean control:** use the reference without added degradation. A clean control can expose unnecessary speech changes.

Use one shared gain for each degraded/reference pair if needed to keep both below -3 dBFS peak. Record gains, resulting SNR and clipping count. No dynamic processing is applied before model inference. Save pre-master float32 input and reference with SHA-256 hashes. Source 16 kHz bandwidth cannot be restored by resampling to 48 kHz.

## Product execution

Run the published signed Voicy 0.3.2 runtime, not an unqualified experimental model or altered solver settings. Verify the installer SHA-256 (`7e23011e3169adff45be0126d1af9bed2e25338e15b69beb5550ec31d8fa3081`), code signature and Gatekeeper acceptance before execution. Mount read-only and keep model downloads offline. Inspect the bundled runner and invoke its documented isolated-Python path; log the exact command and hashes without credentials.

Settings: AuK32, q8/group64, seed 2026, CFG 2, original context/overlap and automatic memory policy. No per-case tuning or output substitution. Run sequentially. Capture hardware/OS/runtime versions, memory pressure, wall time, result duration/frame count, finite samples, peak and clipping. Report failures and stop if memory pressure is critical or storage headroom falls below 12 GiB. Do not disturb existing applications, models or recordings.

## Listening deliverables and limits

Preserve original FLAC, reference, degraded input, raw enhanced output and processing report outside Git. Prepare separately loudness-normalized listening versions using the app's two-pass -16 LUFS mastering and -1.5 dBTP ceiling; keep raw versions downloadable if publication is approved within the project scope. Explain normalization and make reference/condition/processed versions distinguishable. Samples must not autoplay.

Before public publication, inspect every output for structural correctness and transcript/word fidelity using available local ASR plus listening review where possible. ASR agreement alone is not proof of perceptual quality. If a necessary check cannot be performed, mark it unverified and keep that case unpublished or clearly present a documented failure without a quality endorsement. Never state a subjective listening review occurred if only ASR was used.

Do not publish comparative MOS, PESQ, STOI or other quality claims without a separately specified valid measurement protocol. These five cases do not establish superiority over Adobe or a population-wide benefit. Keep failures and negative controls visible in the evidence ledger; no best-output cherry-picking.

## Provenance and storage

Working directory: `voicy-growth-evidence/e03-v1/`, stored outside the public checkout. The absolute location is retained only in private operational records.
Public repository: protocol, preparation script, sanitized manifest and summary only. Do not commit the large installer/archive, model weights, logs with private paths/credentials, or raw audio by accident. Public listening assets require an explicit Git allowlist and small, reviewed file set. Preserve source/protocol/script hashes and generated UTC timestamps. A completed preparation run is not a completed enhancement experiment.
