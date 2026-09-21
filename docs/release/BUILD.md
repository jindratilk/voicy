# Building Voicy

Use an Apple Silicon Mac with Xcode Command Line Tools, Rust, Node.js 20+ and [uv](https://docs.astral.sh/uv/). Run commands from the repository root.

## First build

```sh
npm --prefix web ci
python3 scripts/bootstrap-auk.py
python3 scripts/stage-python.py
./scripts/build-ffmpeg.sh
./scripts/build-voicy.sh
```

The bootstrap downloads pinned AuK/Qwen assets and converts them to MLX q8/group64. It needs substantial free disk space for original and converted checkpoints (allow 30 GB during preparation), internet access, and several GB of memory. Every retained model file is checked against the manifest from the approved runtime. It does not use private recordings or any adjacent research workspace.

`stage-python.py` copies the relocatable python-build-standalone runtime, not a virtualenv with references to the developer's interpreter. The app bundles this Python, its dependencies, the audio-only FFmpeg, model source, licenses and weights. The output is `../Voicy.app`.

Subsequent code builds use `./scripts/build-voicy.sh`. During development `./script/build_and_run.sh` builds and opens the app. Quit the old app before rebuilding a running bundle.

## Tests

```sh
npm --prefix web test
npm --prefix web run build
uv venv --python 3.13 .test-venv
uv pip install --python .test-venv/bin/python fastapi uvicorn python-multipart numpy scipy soundfile librosa pytest httpx
PATH="$PWD/build/runtime/bin:$PATH" .test-venv/bin/python -m pytest tests/test_api.py tests/test_audio.py tests/test_auk.py tests/test_chunking.py tests/test_startup.py tests/test_processor_audio.py tests/test_memory_policy.py -q
cargo check --manifest-path src-tauri/Cargo.toml
```

Tests for optional older research engines require their additional dependencies. The full development environment supports those tests; the production app uses AuK.

## Runtime data

Preferences, logs and recordings live under `~/Library/Application Support/Voicy`. The existing recording library is preserved at `runtime/.data`. Removed recordings move into `.trash` inside the library. The app bundle itself contains no user recordings. On startup Voicy creates its own authenticated loopback session rather than reusing a development server.

## Validation scope

A relocated bundle and bundled-runtime inference are exercised on the development Mac. The reproducible bootstrap pins upstream revisions and verifies converted weights; a full clean-machine install should still be part of release qualification. Do not call a build notarized until Apple's submission and stapling checks pass.

## Exact-output inference benchmark

The small real-MLX regression test needs the pinned model source and portable Python:

```sh
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONHOME="$PWD/build/runtime/python" \
PYTHONPATH="$PWD/build/runtime/.auk/source:$PWD" \
build/runtime/python/bin/python3 tests/test_auk_runtime.py
```

Save the approved pre-change runner outside the checkout, then compare it with the candidate using the same decoded WAV:

```sh
.test-venv/bin/python scripts/benchmark-auk-runtime.py /path/to/input.wav \
  --reference-runner /path/to/reference-runner.py \
  --output ../voicy-benchmark --repeats 3
```

The output directory must not already exist. This performs eight sequential full-file runs: one warmup per variant, followed by three measured runs per variant in alternating order. It retains private audio and logs locally, checks exact float-audio equality, records memory pressure and reports medians. Do not commit this output or compare a cold original run with a warm candidate run. Close other compute-intensive workloads; record the machine and power conditions. No input is uploaded. See the [performance audit](INFERENCE-PERFORMANCE-AUDIT.md) for the measured scope and limitations.
