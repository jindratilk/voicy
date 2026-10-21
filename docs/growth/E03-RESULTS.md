# E03 technical execution — 15 October 2026

All five frozen inputs ran successfully through the signed Voicy 0.3.2 packaged runtime. This establishes execution and file integrity for these short examples. **Subjective listening and perceptual quality remain unverified; the new audio is not published.** It is not an Adobe comparison or a quality benchmark.

The [protocol](E03-PROTOCOL.md) and [input manifest](E03-MANIFEST.json) predate model output inspection. The [complete technical results](E03-RESULTS.json) retain all five cases, output hashes, exact runtime/model settings, hardware, memory observations, achieved listening-copy loudness and unedited ASR transcripts. Large inputs, outputs, model files and logs remain outside Git.

| Fixed condition | Output duration | Direct runner wall time | Technical result |
| --- | ---: | ---: | --- |
| Simulated fan | 4.905 s | 102.56 s | Passed |
| Simulated reflections, including tail | 8.860 s | 98.49 s | Passed |
| Intermittent synthetic noise | 8.920 s | 100.41 s | Passed |
| Quiet speech with noise | 7.040 s | 100.46 s | Passed |
| Already-clean control | 4.070 s | 98.50 s | Passed |

“Passed” means process return code 0, expected mono 24 kHz float32 frame count, finite samples and no clipped samples. It does not mean the sound improved or every word/voice characteristic was preserved. These are direct packaged-runner observations on one occupied Apple M4 with 24 GiB RAM, excluding desktop UI/import/export. They are not a controlled speed comparison or a throughput promise.

## Runtime and output checks

- Complete installer size and SHA-256 matched the released artifact; code signature integrity passed and Gatekeeper accepted the notarized Developer ID application.
- The disk image was mounted read-only; all 18 model/config/license files in the existing model manifest matched their expected hashes.
- AuK32, q8/group64, seed 2026, CFG 2 and automatic memory policy were unchanged. All five used the packaged exact-execution path. No critical pressure was observed in the sampled checks and no storage/memory abort occurred.
- Fifteen separate listening copies (reference, input, enhanced for each case) were generated through the packaged mastering function. All are mono 48 kHz PCM24, independently checked with FFprobe and hashes. Resampling does not create new source bandwidth.
- Mastering targets -16 LUFS and -1.5 dBTP. Achieved integrated loudness ranged from -17.26 to -16.05 LUFS; do not claim exact target matching. All versions and measured values are retained.

## Transcript observations

Local Whisper small.en decoded each enhanced output once, using the same fixed settings as the reference/input checks. In the intermittent-noise case, enhanced ASR read “Mrs. Whitney,” matching the source/reference text; noisy-input ASR read “Mrs. Kitten.” This is a recognizer observation, not proof of audible word restoration or human intelligibility.

Compounding, hyphenation and date-number wording vary in some transcripts. The full unedited strings are in the JSON; no WER score or zero-word-error claim is made. ASR agreement cannot validate voice texture, artifacts, listening preference or overall perceptual quality. The clean control also needs listening review.

## Reproduction scope

Prepare the five inputs using `scripts/growth/prepare_audio_cases.py`, the licensed official archive and the frozen protocol. Verify the released installer/signature and model manifest before executing its bundled runner. Use a new output directory for every case and preserve failures. For example, after mounting the verified release:

```sh
voicy_runtime="/Volumes/Voicy/Voicy.app/Contents/Resources/runtime"
voicy_inputs="/path/to/prepared-corrected"
voicy_results="/path/to/new-output-root"
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONHOME="$voicy_runtime/python" \
PYTHONPATH="$voicy_runtime/.auk/source:$voicy_runtime" \
NUMBA_CACHE_DIR="$voicy_results/numba-cache" \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
"$voicy_runtime/python/bin/python3" -u \
  "$voicy_runtime/experiments/enhance_auk_local.py" \
  "$voicy_inputs/01-simulated-fan/input.wav" \
  --models "$voicy_runtime/.auk/models" \
  --output "$voicy_results/01-simulated-fan" --nfe 32 --memory-mode auto
```

Repeat sequentially for every input listed in the manifest, including the clean control; this single command is an invocation example, not the whole experiment. Monitor pressure and storage as required by the protocol. The desktop application itself was not exercised by this runner test.

LibriSpeech © 2014 Vassil Panayotov, [OpenSLR SLR12](https://www.openslr.org/12), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Full utterances were resampled/normalized, controlled degradations added, then enhanced and separately mastered. No reader endorsement is implied. Training overlap is unknown. No human listening panel, Adobe processing or comparative quality metric was performed.

## Later current-runtime research — 21 October 2026

The separate [E34 full-batch protocol and outcome](E34-FULL-BATCH.md#recorded-outcome--21-october-2026) records five completed cases in each of two external-bootstrap arms, identical paired decoded samples and ten fixed ASR inspections. Both arms completed; the experiment does not demonstrate a need for the extra parameter evaluation or resolve earlier E15/E17 timeouts. It is not unmodified 0.3.3 app qualification, human listening or published quality evidence. The historical 0.3.2 results above and all later negative ledgers remain distinct.
