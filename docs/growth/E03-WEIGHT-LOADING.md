# E17: one controlled pair for Thinker weight materialization

Frozen 20 October 2026 before this pair's outputs. [E15](E03-033-CURRENT-RESULTS.md) and [E16](E03-GPU-TRACE-RESULTS.md) failures, inputs and first-case output are already known. This is a bounded execution-boundary hypothesis test, not a blind trial, a fix, a replacement five-case ledger or audio-quality comparison.

## Hypothesis and two arms

The E16 traceback surfaced a Metal timeout at conditioning evaluation after Thinker construction. Exact signed source loads weights and calls Module.eval; [pinned MLX0.32.2](https://github.com/ml-explore/mlx/blob/v0.32.2/python/mlx/nn/layers/base.py) distinguishes inference mode from explicit array materialization. Test whether evaluating already-loaded Thinker parameters before conditioning changes the observed outcome. Do not assume lazy loading is the cause.

Run exactly one `control` and one `materialize` job under the exact owner branch `codex/e03-weight-loading`, using standard public macos15 arm64 runners. GitHub documents [fresh hosted VMs for these jobs](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners). Use matrix max-parallel1, fail-fastfalse and the existing shared research concurrency group. List control first, but record actual start/completion order rather than assume scheduling order. Each arm starts case2 first in its own guest; do not share a GPU context after an abort. Failure of one arm does not cancel the other predefined arm. Provider/upload/capacity failures are missing or failed evidence, never permission to replace a job or add repeats.

Both arms share the same external bootstrap, import order, original runner argv/script-directory path, CPU profile observer, builder wrapper and metadata traversal. The wrapper calls the original Thinker builder and obtains its parameter tree. Control adds no tensor evaluation. Materialize adds exactly one `mx.eval(parameters)` before returning that same model to the original caller. Record begin/end boundaries and arm name. Compare parameter-name/shape/dtype/byte fingerprints, object identities and training mode before/after, without reading/logging numeric values. Fail on an unexpected change or second Thinker build. This metadata check is not a numeric checksum or proof of output equivalence.

The signed bundle stays read-only and unchanged, but treatment deliberately changes an execution boundary. Its output is candidate execution evidence, not proof of the unmodified public app. The unchanged E16 observer helper remains separate; neither prior experiment is rerun or retroactively modified.

## Fixed inputs, limits and evidence

Retain the [qualified image/runner/settings and guards](E03-033-ADDENDUM.md). Require all ten original input/reference hashes after canonical restoration before either model starts. Select only original case2, utterance121-121726-0000, input SHA`dc00a36cf0fe0dee058954e7c5969c72f24b3e3e5ef532663a7fe613f673ddcf`. Its original12-second padded computational block, valid length, AuK32, q8/group64, seed2026, CFG2, precision, context and automatic memory policy remain fixed. No shorter input, weight change, re-quantization, new model, GPU/driver/watchdog flag or paid/larger runner.

Keep26GiB entry/12GiB ongoing headroom, critical-pressure and original RSS guards, 1200-second case timeout, 90-minute work budget and30-minute finalization reserve in each120-minute job. No parallel model arms or outcome-based retry. Record physical RAM, runtime versions, initial/ongoing observations, exact arm, protocol/bootstrap/observer/source identities, all bindings, configs, traces, errors, partial/output WAV and original return code. Use distinct arm-labelled encrypted artifact names and the existing local-only recipient key. Preserve failures and detachment/encryption/upload errors; no plaintext audio fallback. The eight planned image-part requests are own QA, not acquisitions.

The [standard-runner table](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) advertises14GB SSD; do not treat it as measured free capacity or a guaranteed hard ceiling. Actual E15/E16 SYSTEM observations recorded45,785,968,640 and45,790,347,264 bytes initially free, and their retrieved results retained over37GB during execution. This supports trying the same standard class with the unchanged gate, not assuming every future allocation will fit. A smaller host must fail and preserve its resource observation; do not weaken the gate or select a paid runner to obtain data.

Retrieve both into fresh private arm directories. Verify GitHub ZIP digest, cipher/archive hashes, every inventory entry/exact file set and the arm/protocol/source/input/image bindings. Local retrieval reserves1.5GiB with240MB initially budgeted for the pair; recheck actual sizes and free space rather than deleting evidence or other projects. A larger receipt remains pending if it cannot safely fit. Independently inspect every successful raw WAV's mono24kHz float32 encoding, frames, finiteness, peak/clipping and SHA; retain adverse outputs rather than selecting a better one.

After the entire pair is terminal and successful raw files are validated, decode each valid arm output once with the original small.en SHA`f953ad0fd29cacd07d5a9eda5624af0f6bcf2258be67c92b79389873d91e0872`, CPU/four threads, English/transcribe, temperature0, no temperature fallback/previous context, fp16false. Verify the unchanged installed toolchain and1.5GiB/critical-pressure auxiliary guards first. Keep full unedited transcripts/errors and failed-arm rows; no alternate recognizer or outcome-based rerun. ASR is only an inspection proxy, not human intelligibility, WER/MOS or quality proof.

## Interpretation fixed before outputs

- Control fails/materialize completes: supports further investigation of this boundary in this context; not a proven cause/fix, replicated result or release qualification.
- Control completes/materialize fails: retain the adverse treatment outcome; do not ship it as a fix.
- Both fail: this pair does not resolve the observed problem; preserve both failure boundaries.
- Both complete: no demonstrated need for the change in this pair; compare actual raw identities without claiming general equivalence.
- Missing/invalid arm: report the comparison as incomplete, without replacement attempts.

One pair cannot control all host/time/resource variation or establish causality. Common observer/bootstrap/metadata overhead also differs from a direct public run; CPU events do not identify GPU kernels. Further replication, a full original five-case run/control and actual native/release checks need their own justified steps before any product change or public quality claim. Human listening remains unverified. No new audio publication, ranking result or external outreach follows.

LibriSpeech ©2014 Vassil Panayotov · [OpenSLR SLR12](https://www.openslr.org/12) · [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). Preserve frozen resampling/normalization/simulated-reflection attribution and failures; no reader endorsement.
