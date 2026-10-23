# Building Voicy

Use an Apple Silicon Mac with Xcode Command Line Tools, Rust, Node.js 20+ and [uv](https://docs.astral.sh/uv/) 0.13.4 or newer. Run commands from the repository root.

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

Bootstrap and staging reject uv versions older than 0.13.4 before dependency downloads ([uv trust-store advisory](https://github.com/advisories/GHSA-hq85-5cpj-mr62)). Bootstrap replaces certifi immediately after syncing the historical freeze and verifies it before model downloads; the derived runtime lock records that override while the historical experiment file stays unchanged. Packaging refreshes the derived runtime lock even when reusing an older staging tree. Staging pins certifi 2026.10.19 to address [the compromised emSign CA trust advisory](https://github.com/advisories/GHSA-6q48-6c7w-9gw2). Before packaging, `runtime_trust.py` checks the staged interpreter's certifi metadata, approved version and CA bundle against its installed RECORD hash. Missing, stale or inconsistent data stops the build before resource copying. Run `python3 scripts/stage-python.py` to refresh an older staging runtime; this does not modify an already signed app or previously published installer. This narrow gate is not a complete dependency audit.

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

## AuK native frontend (0.3.2)

`prepare-portable-runtime.py` builds `server/auk_exact/native_frontend.dylib`
against the bundled Torch 2.14.0 headers and libraries. Xcode Command Line Tools
are required. Library lookup is relative to the dylib inside the bundle, never
an absolute development path. The source and fixed input-independent token/mel
constants are included; no recording features or research audio are shipped.

For development, build it with `.auk/venv/bin/python scripts/build-native-frontend.py`.
Without this library the worker keeps the original Python feature extractor.
Exact GPU optimizations require MLX 0.32.2; other versions keep the original
execution path. `VOICY_DISABLE_EXACT=1` is a diagnostic fallback for comparison.
Sampling remains Base32, q8/group64, CFG 2 and seed 2026. Two independent chunks
share model loading when memory allows; low headroom selects one chunk and
releases the VAE between stages. There is no tensor batching or reduced step count.

The macOS baseline CI also bootstraps uv 0.13.4 from its exact official arm64 wheel with a reviewed SHA-256, then invokes the same downloader gate before creating Python. The MLX helper installs its checksum-verified local wheels with networking disabled. CI still performs actual Metal computation on macOS 14 and 15; this small compatibility check does not qualify the full model runtime or replace the published installer. Historical research tags and their dependency freezes are unchanged.

Pillow is also pinned to 13.0.0 in bootstrap and staging, addressing the security fixes in its [official release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html). The offline pre-package gate rejects missing, duplicate or older Pillow metadata. Both certifi and Pillow overrides are recorded in the derived runtime lock; an absent or duplicate lock entry stops preparation. The historical experiment freeze is preserved. An isolated overlay on the original read-only 0.3.3 Python passed local audio adapter, lean feature extraction and PCM24 decode/export compatibility with exact array equality; this is not a full model run or a new signed release qualification.
