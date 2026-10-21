# E34: full original batch with a controlled materialization boundary

Frozen 21 October 2026 before this pair's outputs. E15 failed after case1 completed; E17 control failed and materialize completed only case2. Those outcomes are already known. This follow-up asks whether the same single boundary intervention permits the entire original batch, with retained negative outcomes. It is not a blind trial, exact single-case replication, shipping fix, public-app qualification or listening-quality experiment.

## Declared comparison

Run one control and one materialize job, in fresh standard public `macos-15` arm64 guests, max-parallel1 and fail-fastfalse. Both jobs attempt original cases1,2,3,4,5 in that order, with a fresh packaged-runner child for each case and stop at the first failed execution/guard. Do not skip ahead, replace a guest or rerun a case. Record all five outcomes, including not-run cases after a failure. Actual provider scheduling order must be recorded rather than assumed.

Both arms use the unchanged E17 bootstrap and CPU observer, original import order/runner arguments and metadata checks. Control adds zero tensor evaluations. Materialize adds exactly one `mx.eval(parameters)` after each child's original Thinker builder, before returning the same model. Preserve name/shape/dtype/byte metadata, parameter identities and training mode checks. Do not modify the signed image, weights, quantization, generation settings, watchdog, GPU policy or public application. This is an external override of the execution boundary, not the unmodified app. E17's protocol remains the parent method; this document explicitly supersedes its single-case selection only for E34.

The pinned [MLX module source](https://github.com/ml-explore/mlx/blob/v0.32.2/python/mlx/nn/layers/base.py) distinguishes inference mode from array evaluation. This motivates the hypothesis without establishing lazy loading as the cause. A prior case1 in the same guest differs from E17's case2-first design; it is common to both E34 arms and must remain an interpretation limit.

## Freeze, guards and one execution

- Use exactly the [qualified033 image, runner and original limits](E03-033-ADDENDUM.md), [canonical transport](E03-CANONICAL-INPUTS.md) and frozen E03 manifest. Require all ten original input/reference hashes before either job starts inference. Preserve generated as well as restored inputs.
- Keep AuK32, seed2026, q8/group64, CFG2, original12-second computational blocks, context/overlap, precision and automatic memory policy. All original utterances/transcripts/degradation recipes remain fixed, including clean control. No new model or per-case tuning.
- Keep26GiB measured initial free capacity,12GiB ongoing reserve, critical-pressure/RSS guards,1200seconds per case,90minutes work plus30minutes finalization in each120-minute job. Source retrieval counts toward work time. A resource failure is evidence, not grounds to lower a gate or buy a runner.
- Standard public [GitHub runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) remain free; their7GiB RAM is below the16GB consumer recommendation. Actual E15–17 guests had over45GB initially free despite the nominal14GB storage table. Measure the new allocations and reject insufficient capacity; do not assume it.
- Trigger only the initial creation of `voicy-e34-full-batch-20261021`, after reviewed source is merged and remote tag absence is checked. Never move/delete/recreate the tag or use attempt2. Guard creation/forced updates/run-attempt before any source retrieval. Branch/PR pushes only run ordinary checks, not this experiment. Preserve shared research concurrency, sequential arms and distinct arm-labelled artifacts.

Each job records exact source/protocol/bootstrap/observer/image/runtime identities, physical RAM, selected cases, input binding, configs, pressure/storage, arm, per-case trace, return code, wall time, raw/partial WAV and errors. Use distinct CASE1 through CASE5 traces. Stop on failure and preserve logs and not-run status. No public release, audio publication, website/date/sitemap change, IndexNow or message follows merely from starting this experiment. The eight planned image-part requests are own QA, not acquisitions.

## Retrieval and fixed inspection

Keep the existing CMS recipient certificate and local-only private key. Upload only ciphertext and its non-audio receipt, with seven-day retention. Preserve failed jobs, detachment/encryption/upload errors, exact artifact/ZIP/cipher/archive identities, inventory hashes and complete file set. No plaintext fallback. Inspect actual artifact sizes before retrieval; initially budget512MiB total auxiliary transport/storage and preserve at least1.5GiB locally. If evidence cannot safely fit, retain the concrete dependency rather than deleting other work.

Independently check every completed raw WAV: SHA, mono24kHz float32, original frame count, finite samples, peak and clipped-sample count. This is structural validity, not quality. Only after both jobs are terminal and this binding audit passes, decode each valid output once with the existing fixed small.en model SHA `f953ad0fd29cacd07d5a9eda5624af0f6bcf2258be67c92b79389873d91e0872`, CPU/four threads, English/transcribe, temperature0, no fallback/previous context, fp16false. Recheck installed toolchain, model identity and auxiliary storage/pressure guard first. An exact raw hash with an existing receipt under that identical policy may reuse that dated transcript; identify reuse, never claim a new decode. Keep full raw transcripts/errors and all failed/not-run rows, no alternate recognizer or outcome-based repeats. ASR is an inspection proxy; human listening remains separate and unverified.

## Decisions fixed before outputs

- Control stops/materialize completes all five: evidence for a full-batch candidate in this context, not a release fix or causal proof. Next product step still needs source review and actual signed/native/minimum-OS qualification.
- Materialize fails any case: retain the failed boundary and unrun cases; do not claim a five-case solution or select only successful materialize examples for publication.
- Both complete: record both without assuming the extra boundary was needed or outputs equivalent.
- Missing/invalid job or artifact: incomplete pair, no replacement. No success from a workflow badge without independently verified outputs.

Separate guests/time/resources, observer/metadata overhead, small fixed English audiobook sample and unknown training overlap limit interpretation. No MOS/WER/PESQ, independent listener claim, Adobe superiority, consumer speed benchmark or ranking result. Preserve original E15/E17 failure ledgers. Any public audible evidence or product change is a separate reviewed decision.

LibriSpeech ©2014 Vassil Panayotov · [OpenSLR12](https://www.openslr.org/12) · [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). Retain resampling/normalization/simulated-degradation attribution; no reader endorsement.
