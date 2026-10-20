# E03 current-release extension, version 1

Frozen 20 October 2026 before current-release model output generation. This is a separate run of the original five-case demonstration with the qualified public 0.3.3 runtime. It does not amend or overwrite the historical 0.3.2 protocol/results, establish superiority or create human judgments.

## Fixed execution

Use the exact complete offline image: 6510981427 bytes, SHA-256 `459f8699304ec2efa923001b0691a9fd3231067716a66b18f676f88f4c4f6e7b`. Its four public release parts and hashes are fixed in the harness. Assemble once, verify full identity, mount read-only, verify the complete app signature/Gatekeeper and version 0.3.3. No signing, release creation, secrets, app modification or new model weights.

Use one standard public-repository `macos-15` arm64 GitHub runner, with no paid/larger runner. Record actual OS, architecture, physical RAM and guards. A hosted VM below the recommended 16 GB RAM is a methodological limitation; retain the automatic memory policy and critical-pressure stop. This is direct packaged-runner evidence, excluding desktop UI/import/export, not a consumer speed benchmark. Existing separate native/public-download qualification remains distinct.

Reconstruct all five original selections and degradation recipes from the pinned LibriSpeech test-clean archive and unchanged preparation script. Use NumPy 2.4.6 and SciPy 1.17.1 in a new preparation-only environment. Build minimal FFmpeg/FFprobe 9.0.1 from the [official source archive](https://ffmpeg.org/releases/ffmpeg-9.0.1.tar.xz), SHA-256 `cf38e0e28c7e5605942c4a77755349b0145804a397af37eb1fb4c77cb237f635`. Preparation tools do not replace the signed runtime's bundled FFmpeg/model code.

Before any inference, require all five utterance IDs, transcripts, source hashes and input/reference paths, frame counts, rates and SHA-256 values to match the existing E03 manifest exactly. A platform/tool mismatch is a recorded preparation failure, not permission to retune, substitute inputs or select a more favorable case. Retain failed preparation evidence; revise a protocol only with an explicit reason before a later run.

Run sequentially with AuK32, q8/group64, seed 2026, CFG2, original chunk/context/overlap and automatic memory policy. Pin the packaged runner to SHA-256 `82970522e890207d1a7c112a8437f213fba1555af6677017fcc14a1d6e8ab193`. The child gets an allowlist of normal process essentials and offline model flags; CI credentials do not enter it. No new model download or per-case tuning.

Require 26 GiB initial headroom for installer/source/build overhead, then preserve the original minimum 12 GiB guard throughout preparation/model execution. Monitor pressure/storage every two seconds during each model process, with a 1200-second case timeout. Stop on failed execution, critical pressure or insufficient storage and keep partial outputs/logs; do not skip ahead or discard a failure. Do not lower the local Mac's guard or delete its recordings/models/other projects.

The 120-minute job reserves its last 30 minutes for finalization/upload. A 90-minute work budget starts at source retrieval, then uses a monotonic deadline to bound preparation commands and model monitoring; expiry is a failed attempt with partial evidence, not permission to shorten or skip a case. Source requests are time-bounded; detachment/encryption have separate five-minute command limits. Save platform/source/protocol facts and structured initial resource observations before enforcing the headroom gate, so a rejected host remains inspectable. External runner cancellation or provider/upload failure can still prevent retrieval and must be reported honestly.

For each completed output retain raw WAV, model report, wall time, input identity, pressure/storage samples, output SHA-256, exact mono24kHz float32 frame count, finite-sample check, peak and clipping count. Structural validity is not transcript fidelity or audio quality. ASR, mastering, accessible listening copies and actual review are separate later stages; no public audio or quality claim follows from this run alone.

## Evidence transport and preservation

All raw inputs/outputs, reports, compiler logs, failures and an inventory are archived on the ephemeral runner. Before artifact upload, encrypt the archive using OpenSSL CMS AES-256 to the project-specific public recipient certificate. Its SHA-256 is `e950ddd13c15263027ccf8a12dab61e86e1f520bb56304977147c51f0cea0bbf`. The matching private key stays outside Git on the owner's Mac; it is never an action input or secret. The certificate is an evidence recipient, not a TLS/login identity.

Only ciphertext and a non-audio hash/status receipt enter the seven-day GitHub artifact. There is no plaintext/audio upload fallback. Retrieve and decrypt promptly into a new private directory, verify the archive and each inventory hash, then preserve source/run/head/attempt provenance outside public Git. If encryption or retrieval fails, report the missing evidence; do not call the run validated. CMS encryption alone does not authenticate a run: bind the ciphertext/receipt to the actual reviewed GitHub workflow and artifact identity.

The four public image-part requests are project QA traffic, with possible network retries. Record them in the download measurement ledger; they cannot be counted as customer acquisitions. No new primary-assistant download is needed for this direct-runtime experiment.

LibriSpeech © 2014 Vassil Panayotov · [OpenSLR SLR12](https://www.openslr.org/12) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Preserve exact utterance attribution and the original resampling/degradation/enhancement notices. Training overlap is unknown. All five fixed English audiobook cases, including the clean control, stay in the ledger; no independent listener panel, real-world population claim or Adobe comparison is established.
