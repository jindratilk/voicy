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
- Standard public [GitHub runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) remain free; their7GiB RAM is below the 16 GB consumer recommendation. Actual E15–17 guests had over45GB initially free despite the nominal14GB storage table. Measure the new allocations and reject insufficient capacity; do not assume it.
- Trigger only the initial creation of `voicy-e34-full-batch-20261021`, after reviewed source is merged and remote tag absence is checked. Never move/delete/recreate the tag or use attempt2. Guard creation/forced updates/run-attempt before any source retrieval. Branch/PR pushes only run ordinary checks, not this experiment. Preserve shared research concurrency, sequential arms and distinct arm-labelled artifacts.

Each job records exact source/protocol/bootstrap/observer/image/runtime identities, physical RAM, selected cases, input binding, configs, pressure/storage, arm, per-case trace, return code, wall time, raw/partial WAV and errors. Use distinct CASE1 through CASE5 traces. Stop on failure and preserve logs and not-run status. No public release, audio publication, website/date/sitemap change, IndexNow or message follows merely from starting this experiment. The eight planned image-part requests are own QA, not acquisitions.

## Retrieval and fixed inspection

Keep the existing CMS recipient certificate and local-only private key. Upload only ciphertext and its non-audio receipt, with seven-day retention. Preserve failed jobs, detachment/encryption/upload errors, exact artifact/ZIP/cipher/archive identities, inventory hashes and complete file set. No plaintext fallback. Inspect actual artifact sizes before retrieval; initially budget512MiB total auxiliary transport/storage and preserve at least1.5GiB locally. If evidence cannot safely fit, retain the concrete dependency rather than deleting other work.

Independently check every completed raw WAV: SHA, mono 24 kHz float32, original frame count, finite samples, peak and clipped-sample count. This is structural validity, not quality. Only after both jobs are terminal and this binding audit passes, decode each valid output once with the existing fixed small.en model SHA `f953ad0fd29cacd07d5a9eda5624af0f6bcf2258be67c92b79389873d91e0872`, CPU/four threads, English/transcribe, temperature0, no fallback/previous context, fp16false. Recheck installed toolchain, model identity and auxiliary storage/pressure guard first. An exact raw hash with an existing receipt under that identical policy may reuse that dated transcript; identify reuse, never claim a new decode. Keep full raw transcripts/errors and all failed/not-run rows, no alternate recognizer or outcome-based repeats. ASR is an inspection proxy; human listening remains separate and unverified.

## Decisions fixed before outputs

- Control stops/materialize completes all five: evidence for a full-batch candidate in this context, not a release fix or causal proof. Next product step still needs source review and actual signed/native/minimum-OS qualification.
- Materialize fails any case: retain the failed boundary and unrun cases; do not claim a five-case solution or select only successful materialize examples for publication.
- Both complete: record both without assuming the extra boundary was needed or outputs equivalent.
- Missing/invalid job or artifact: incomplete pair, no replacement. No success from a workflow badge without independently verified outputs.

Separate guests/time/resources, observer/metadata overhead, small fixed English audiobook sample and unknown training overlap limit interpretation. No MOS/WER/PESQ, independent listener claim, Adobe superiority, consumer speed benchmark or ranking result. Preserve original E15/E17 failure ledgers. Any public audible evidence or product change is a separate reviewed decision.

LibriSpeech ©2014 Vassil Panayotov · [OpenSLR12](https://www.openslr.org/12) · [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). Retain resampling/normalization/simulated-degradation attribution; no reader endorsement.

## Recorded outcome — 21 October 2026

[Run 39583894992, attempt 1](https://github.com/jindratilk/voicy/actions/runs/39583894992) executed source `9209749845818a32a94e181b4a5b2fcf963e8139` with the [frozen protocol at that source](https://github.com/jindratilk/voicy/blob/9209749845818a32a94e181b4a5b2fcf963e8139/docs/growth/E34-FULL-BATCH.md). Both arms completed all original five cases. Control ran first (10:20:42–10:46:01 UTC); materialize followed in a different fresh guest (10:46:05–11:14:11 UTC). These are job/setup bounds, not consumer inference benchmarks. Each guest reported macOS 15.7.9 arm64 and 7 GiB physical RAM, below the 16 GB consumer recommendation.

The two encrypted artifacts were retrieved after their respective jobs finished. ZIP digests, ciphertext/archive hashes, recipient certificate, complete inventories (95 entries per arm), reviewed source/protocol/bootstrap/observer identities, signed 0.3.3 image and all ten canonical input/reference hashes were checked independently. All ten raw outputs have the expected mono 24 kHz float32 frame count, finite samples and zero clipped samples. Every case’s 0/1 extra-evaluation trace preserves parameter identities/metadata; paired saved configs are identical. Initial/ongoing resource guards passed. No job, case, tag or output was replaced.

| Original case | Control | Materialize | Frames per output |
| --- | --- | --- | ---: |
| 1 | Completed | Completed | 117720 |
| 2 | Completed | Completed | 212640 |
| 3 | Completed | Completed | 214080 |
| 4 | Completed | Completed | 168960 |
| 5 | Completed | Completed | 97680 |

Raw WAV identities remain distinct:

| Case | Control WAV SHA-256 | Materialize WAV SHA-256 |
| --- | --- | --- |
| 1 | `58788a464cad3de43e8919e193a320f70318240e3c2347ad9d60bd8dfcd0e317` | `65fdf4520192819ce24cb6f4f66316deaf15f1017461aacac535ce91b5b1f57a` |
| 2 | `9091df3a7990fb85a3e1fc7194c4058c264babcae84d8307d20dddb978667c6f` | `b231f8363057154c1daf4c2b2e698fb67f953b5b27ee81f86eefcdd730cf2682` |
| 3 | `b882e801d1580f93d9efd12aac1565baf0e70b673a2c9f06f9c3b5d17bffb800` | `e34986984265ce03aa672a65ab9c470d94ba61a93e20d7d0c379eafacf0b0117` |
| 4 | `2d613fcb07afbc56ac90b5f8657326425c5be54627f9e79e7c9112b095f388e4` | `9b88344d760357324bf48bd8f7f404292b5e6856ee565390ee9538254da0fb0e` |
| 5 | `9b4087e774132087a3239d4713ebac5d45dc5d2243104a12eee0d87e4d96f03d` | `02fbd861eb940612eb7e4cf7c274e84045cfff575f80055b5c24585b915930b6` |

A post hoc RIFF-chunk and decoded-sample inspection explains those differing container hashes: within each pair, only the `PEAK` chunk timestamp differs. The audio `data` chunks and independently decoded little-endian float32 samples are byte-identical. This additional inspection was not the primary predefined execution endpoint and is not a perceptual-quality result. The decoded-sample hashes below apply to both arms, produced with `ffmpeg -nostdin -v error -i output.wav -map 0:a:0 -f f32le pipe:1` and SHA-256 over its stdout.

| Case | Decoded float32 sample SHA-256, both arms |
| --- | --- |
| 1 | `342f084493c2f4c044405ade5e8b8cbe20767e8b59a6304c9b71318a1d2a66f0` |
| 2 | `cd40748090c0f8b82e17197e298e750c25a18de06c7d37fb8b7a2ff831c4a06f` |
| 3 | `f4224e7c48ee1d2f0b54f230f96c42d472f0a0a36c45b621a0c91afdcc64479c` |
| 4 | `c5a72dd55b660a10fd7da9d3a0960f8efa2c1416d6733b211bf7f42898e663e8` |
| 5 | `b84e4e051925aea2848265ac91746b6c045306591448afe50222a9c5397721ad` |

After both jobs were terminal and the paired raw audit passed, the unchanged Python 3.14.3 / openai-whisper 20250625 / torch 2.10.0 / numpy 2.3.5 toolchain decoded each of the ten raw files once, using the fixed small.en hash and CPU/four-thread/English/transcribe/temperature0/no-fallback/no-previous-context/fp16false policy above. No alternate decoder or outcome-based repeat was used. Each pair returned the same full string (leading whitespace retained):

1. ` He began a confused complaint against the wizard, who had vanished behind the curtain on the left.`
2. ` Also, a popular contrivance whereby lovemaking may be suspended but not stopped during the picnic season.`
3. ` Then, dear, said Mrs. Whitney, you must be kinder to her than ever. Think what it would be for one of you to be away from home, even among friends.`
4. ` Saturday August 15. The sea unbroken all-round. No land in sight.`
5. ` Out in the woods stood a nice little fir tree.`

These are unedited recognizer outputs, not human word-fidelity or listening judgments. For example, source `LOVE MAKING` becomes `lovemaking`; date/compound/punctuation formatting also differs. No WER, MOS, perceived quality, Adobe comparison or consumer speed conclusion is inferred. All ten full decoder JSON outputs/logs, per-case traces, failures/not-run ledgers (none in this pair), configs and raw files remain in dated private evidence.

**Decision:** both arms completed, so E34 does not demonstrate that the added evaluation boundary was necessary. It does not establish the cause or resolution of E15/E17 GPU timeouts. Preserve those negative records and do not ship this experimental intervention as a fix. Both arms use an external bootstrap/import/observer boundary; control adds zero explicit evaluations but is not an unmodified public-app run. Separate guests, a preceding case 1, timing/resources, known prior outcomes and five short English audiobook examples limit generalization. No new public audio or subjective review occurred; the existing publication gate remains. Website/title/canonical/sitemap and signed app stay unchanged, with no IndexNow notification or ranking/citation claim.
