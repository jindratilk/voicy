# E16: bounded observation of the case-2 GPU abort

Frozen 20 October 2026 before this diagnostic attempt. [E15](E03-033-CURRENT-RESULTS.md) already exposed the inputs, first output/ASR and case-2 Metal timeout. This is fault isolation, not a blind experiment or a replacement for its failed five-case ledger and unrun clean control.

## One selected attempt

Use one standard public-repository macOS15 arm64 CI job on the exact owner branch `codex/e03-gpu-diagnosis`. Reuse the qualified signed 0.3.3 image, original preparation and lossless canonical transport. Verify all ten original input/reference hashes before image/model execution. Then select only original case2 (`121-121726-0000`, input SHA `dc00a36cf0fe0dee058954e7c5969c72f24b3e3e5ef532663a7fe613f673ddcf`) for diagnosis. Do not shorten or replace it. Record selection `[2]` and this protocol/observer SHA in SYSTEM.json. Default E14/E15 branches still execute their full original five-case loop without observation.

Preserve the exact public image/runner hashes, AuK32, q8/group64, seed2026, CFG2, context and automatic memory policy from the [current-release addendum](E03-033-ADDENDUM.md). Keep the 26GiB entry/12GiB ongoing disk guards, critical-pressure stop, 1200-second case timeout, 90-minute work budget, 30-minute finalization reserve and encrypted-only artifact transport. No paid/larger runner, signature modification, driver/system setting change, model upgrade, GPU timeout override or parallel model job. One attempt only; any later numerical/execution change needs a separate reason and contract.

## Observer and interpretation

An external standard-library Python bootstrap invokes the original pinned packaged runner with its original arguments via runpy. It reproduces the original script-directory import path and restores the bootstrap state afterward. The signed bundle is unchanged. A main-thread sys.setprofile callback records selected Python stage call/return events and MLX eval/async_eval/synchronize C-call events when exposed by the binding. It logs monotonically timed JSON lines, function/module and runtime-relative file/line only. It never inspects arguments, arrays, locals, audio, tokens or credentials; never invokes an extra model/tensor operation, evaluation or synchronization; and never changes inference flags/parameters or catches an abort as success.

Stages cover model construction/release, audio/text encoding, sampling and decoding. Flush each recorded boundary so a process abort leaves its preceding events. A maximum of50,000 matching events is explicit: write `trace_capped`, stop profiling and retain the original model's exit behavior. Preserve pre-existing trace files rather than overwriting. Native SIGABRT may prevent a terminal Python event; preserve logs/configs/partial files and the actual return code. Normal detachment/encryption failures remain separate failed evidence.

Profiling/flush overhead can change timing and may affect reproducibility. A Python return event can also occur while unwinding an exception; it is not by itself proof of a completed computation. A C call may only enqueue GPU work, and some bindings may expose no C events. The last observed CPU boundary does not identify a GPU kernel or establish the underlying cause. If this instrumented run succeeds, retain that observation without erasing E15 or claiming a fix, five-case pass or general reliability. Do not repeat until a preferred outcome occurs.

## Retrieval and follow-up

Retain the actual run/head/attempt, signed-image/input bindings, resource samples, raw trace, complete configs/stdout/stderr/output or errors, and encrypted inventory/receipt. Retrieve/decrypt into a fresh private directory; verify artifact ZIP/cipher/archive and every inventory entry/exact file set. Inspect the chronology and state its limits before proposing a narrowly targeted next experiment. Reuse the existing local-only recipient key; no new credentials/accounts or plaintext audio upload fallback.

No new audio, human listening result, ASR rerun, public quality claim or search ranking outcome follows. The public release's separate qualification remains distinct. The four image-part requests are own QA, not acquisitions. LibriSpeech ©2014 Vassil Panayotov · [OpenSLR SLR12](https://www.openslr.org/12) · [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). Preserve original source/transformation attribution; no reader endorsement.

API semantics: Python3.13 [sys.setprofile](https://docs.python.org/3.13/library/sys.html#sys.setprofile) and [runpy.run_path](https://docs.python.org/3.13/library/runpy.html#runpy.run_path). The observer is not a sandbox or proof of GPU completion.
