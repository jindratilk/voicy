# Inference performance audit — 22 September 2026

## Binding quality requirement — updated 21 September 2026

The user clarified that speedups must preserve the approved quality. This overrides the broader candidate list below: keep the same AuK Base weights, q8 precision, 32 steps, seed, chunk duration and overlap. Flash, fewer steps, stronger quantization and altered joins are outside the current implementation task. Demand sample-for-sample equality against the reference first; do not silently accept numerical changes from compiled kernels. Memory residency must adapt to both total RAM and current headroom/pressure, with a conservative fallback. The 16/32/128 GiB policy cases need tests; an M5/32 GiB measurement is not a claim of validation on all those machines.

## Final measured result — 22 September 2026

**No substantial acceleration was established.** The candidate median was **95.282 seconds**, versus **96.022 seconds** for the original worker: **1.00776×**, or **0.7703% less time** (0.740 seconds saved). The individual ranges overlap; this is a small observed difference on one recording and machine, not evidence for a universal improvement. **10× was not achieved.** Do not compare against the old 162.87-second native-app run and claim a larger gain; those conditions and measurement boundaries differ.

| Same 18.965-second reference recording | Median, three measured runs | Range | Peak process RSS |
| --- | ---: | ---: | ---: |
| Original approved worker | 96.022 s | 95.403–96.305 s | 4.891 GiB |
| Exact reuse + automatic memory policy | 95.282 s | 95.107–95.558 s | 4.894 GiB |

Apple M5, 32 GiB, macOS 26.6.2, AC power, MLX 0.32.2. Runs used separate worker processes in alternating order after one excluded warmup per variant; all eight completed successfully. System memory pressure was normal before and after each run, and macOS reported no thermal/performance warning. This was a development machine, not an otherwise isolated laboratory system. Timings include worker imports, preprocessing, inference, joining and WAV writing; they exclude native-app import and final export. The baseline runner SHA-256 matches commit `18a9a0e`. See [machine-readable measurements](INFERENCE-BENCHMARK.json) and the [reproduction commands](BUILD.md#exact-output-inference-benchmark).

**Quality:** all eight outputs have the same decoded float32 PCM SHA-256. Each contains 455,168 samples at 24 kHz; there are zero changed samples. The approved weights, q8/group64, 32 steps, CFG 2, seed 2026, 12-second chunks, 4-second overlaps and joins are unchanged. Four additional real-MLX small-model equality tests cover reference changes, cache reset, no reference, disabled caching and guidance transitions. This is exact-output validation for these tests, not proof that a generative model cannot damage arbitrary speech.

The signed native app also completed a fresh import/enhancement run in 114.68 seconds. A comparison against the saved original app runtime using that **same newly decoded input** produced identical final 48 kHz PCM24 output (910,336 samples, maximum difference 0). This additionally checks the app's resampling and mastering path. A historical M4A decode was slightly different and was not used to claim a regression or speedup.

**Implemented:** reuse the identical target projection across CFG branches and immutable reference projections inside one sampling call. Cache identity is scoped to the current reference and cleared between chunks. Do not cache input-dependent Thinker output between recordings. No compilation, lower precision, changed model, reduced step count, altered overlap or asynchronous scheduling was promoted.

**Memory policy:** calculate residency eligibility from physical memory, current reclaimable memory and pressure. Leave a system reserve of at least 3 GiB or one eighth of RAM, limit the budget to 60% of physical RAM, and allow additional activation headroom above weight size. Retain models only when the budget qualifies; on warning/critical/unknown pressure or insufficient reserve, fall back between complete chunks to sequential execution. Unknown initial system information preserves the conservative sequential defaults. Allocator limits are caps, not preallocations. Final measurements selected sequential mode on the 32 GiB test Mac because current headroom did not qualify for residency. Residency-only speedup is not claimed. The 16/32/128 GiB cases and pressure transitions are unit-tested policies; only the M5/32 GiB hardware was physically tested.

The production app still exits the model worker after each recording, so weights are released rather than held indefinitely. A reusable worker and different GPU kernels remain possible future investigations, with their own cancellation, idle-memory and exact-output gates. They are not presented as delivered improvements.

## Completed investigation: interpretation of pilot runs

The controlled repeated comparison is recorded separately from these exploratory runs. All pilots used the same 18.965333-second decoded input, AuK Base q8/group64, 32 steps, seed 2026, CFG 2, 12-second chunks and 4-second overlaps. Pilot times are **not** a defensible speedup ratio: memory pressure, OS caches and machine load varied. The first reference run (117.624 s) was a warmup under memory pressure and is excluded from final speedup claims. One 2.518-second harness failure was caused by a local `profile.py` shadowing Python's standard-library module; it produced no audio and is excluded, not treated as a fast success.

| Experiment | Pilot worker time | Finding |
| --- | ---: | --- |
| Original sequential worker, later runs | 85.293 / 96.982 s | Substantial timing variation on the development Mac. |
| All three models resident | 98.466 / 95.297 s | No independently established residency-only gain. More memory is not inherently faster. |
| Exact embedding reuse, sequential | 80.902 / 95.523 s | Removes duplicated target embedding and immutable reference embedding work; exact output on the reference clip. Repeated comparison required. |
| Residency plus embedding reuse | 80.204 s | 6.725 GiB process high-water RSS; one pilot cannot establish a general multiplier. |
| Bounded asynchronous two-step dispatch plus reuse | 94.892 s | Exact output, but no compelling speed evidence; not selected for production. |
| 2 GiB allocator cache plus reuse | 96.467 s | No compelling improvement over the adjacent 96.982-second reference; extra cache is not selected. |
| Automatic memory policy plus reuse | 82.099 s | Correctly selected sequential execution when this 32 GiB Mac lacked the requested residency headroom. |

A synchronized phase profile took 93.797 seconds, of which the two 32-step sampling calls took 36.589 + 35.668 = **72.257 seconds (77.0%)**. Thinker conditioning took 2.211 seconds and reference VAE encoding 0.284 seconds; the remaining time includes VAE decoding, startup, model construction/materialization, memory release and file I/O. Builder timing alone does not represent all lazy checkpoint loading. Even removing every operation outside sampling would cap this particular run at approximately **1.30×** acceleration. Model computation itself must improve substantially to approach 10×.

Whole-DiT `mx.compile` was rejected at the small-model numerical gate: 110 output values changed, with maximum absolute difference 0.000190854. This is not proof of audible degradation; it fails the chosen exact-output acceptance rule. No changed-precision or fused numerical path is enabled. See [MLX compilation](https://ml-explore.github.io/mlx/build/html/usage/compile.html) for the graph optimization mechanism.

Fresh-worker startup and non-chunk overhead in representative later runs was approximately 3–4 seconds. A reusable worker could reduce subsequent-file startup, but that alone is only a few percent of this workload; no persistent-worker gain is claimed or shipped without lifecycle/cancellation validation.

## Original audit and experiment plan (before implementation)

The sections below record the initial investigation plan. The binding quality requirement above excludes Flash, reduced steps, altered chunking and any numerically different optimization from this implementation. They remain research alternatives, not changes to the approved app.

### Original decision

Enhancement latency is the highest-priority product limitation raised by the user. Keep the approved AuK Base / 32-step configuration as the reference checkpoint. Investigate a 10× end-to-end acceleration target, but do not present it as achieved or guaranteed. At the time of the original audit, only documentation changed. Implementation measurements will be recorded separately; no model replacement or training is authorized by this plan.

The measured final native run took **162.87 seconds for 18.965 seconds of audio** (real-time factor approximately 8.59). A 10× improvement means approximately **16.29 seconds for that same recording**, including import/preprocessing, inference, joining and export. The earlier 138.17-second run demonstrates timing variability; use repeated, controlled comparisons rather than choosing the slowest baseline. The developer Mac reports **Apple M5, 32 GiB physical memory**. A faster backend import is not faster neural inference.

## Findings in the actual implementation

- `experiments/enhance_auk_local.py` uses `sequential=True`: the upstream MLX engine constructs and releases the Thinker, DiT and VAE as phases advance. VAE construction occurs for both encoding and decoding. This repeats across chunks. It trades residency for repeated model setup/loading/evaluation. Lazy loading and the OS cache mean this is not necessarily physical disk I/O every time; profiling must distinguish construction, page faults, loading and GPU computation.
- The runner fixes the MLX allocation limit to 8 GiB and allocator cache to 512 MiB, and terminates above 14 GiB process high-water RSS. These are conservative budgets, not a measured optimum for every Mac. A 32 GiB machine is a candidate for greater model residency, subject to actual memory pressure and activation peaks. Do not simply allocate all RAM or remove safeguards.
- `server/auk.py` starts a fresh Python/model worker per recording. This reliably returns memory after completion but prevents warm model reuse across recordings.
- `server/chunking.py` uses 12-second chunks with 4-second overlap and zero-pads the last chunk to the full size. For long recordings, this represents approximately 1.5× processed audio duration. A 3-second recording still uses a 12-second chunk. Removing this overhead can affect context, timing and joins; it is not a quality-neutral switch or a guaranteed proportional speedup.
- Base sampling performs 32 Euler steps with classifier-free guidance (CFG). The implementation computes conditional/unconditional branches as a batch, not as two separate serial Python calls. It evaluates the updated latent each step. The DiT already enables its upstream cache; do not count adding the same cache again as an optimization.
- The pinned MLX implementation contains a distinct Flash path: 4 steps, its own time grid and no CFG. A compatible distilled Flash checkpoint is required. Setting Base to four steps does not reproduce that model.

## Ranked experiments

| Order | Experiment | Quality implications | Interpretation of potential gain |
| --- | --- | --- | --- |
| 1 | Profile phase times: startup, checkpoint preparation, Thinker, VAE encode, each DiT step, VAE decode, joins, export. Separate cold and warm runs. | No intended audio change. Synchronize MLX at measurement boundaries so lazy dispatch is not mistaken for completion. | Establish where time is actually spent before assigning speedup estimates. |
| 2 | Retain loaded models across chunks on memory-capable Macs; compare the existing sequential path with non-sequential or selectively resident execution. | Same checkpoint, seed, steps and chunks. Verify PCM equality; investigate numerical differences rather than assuming identity. | Removes repeated setup/loading, but total gain is unknown until measured. Keep a low-memory fallback. |
| 3 | Reuse a worker across files with an idle timeout, explicit release, cancellation and crash recovery. | Same inference algorithm. Extra idle RAM is the principal product tradeoff. | Benefits subsequent files; do not advertise warm-start gains as cold-start gains. |
| 4 | Profile MLX compilation/fusion on stable chunk shapes and the expensive DiT step; assess attention/matmul kernels and supported precision. | Compilation/precision can change floating-point results. Test caches, random state and numerical stability. | No blanket multiplier. Avoid compiling an unbounded number of shapes or capturing stale conditioning. |
| 5 | Benchmark official AuK-Flash with its correct checkpoint and scheduler against approved AuK 32. | Different distilled model; evaluate voice identity, consonants, words, noise and dereverberation blind. | Strongest ready-made algorithmic route toward a large speedup. Four versus 32 steps is 8× fewer iterations; removing CFG further reduces branch work. Neither number is an end-to-end speed claim. |
| 6 | Evaluate shorter padded tails, supported variable chunk lengths, less overlap or conservative silence handling. | Changes context and joins; may damage quiet speech, breaths and boundaries. Requires listening and timing checks. | Workload-dependent. Overlap alone cannot yield 10×; approximate long-file duration overhead is only 1.5×. |
| 7 | If Flash quality fails, investigate enhancement-specific distillation into a 4–8-step student or a smaller restoration model. | Retraining and quality regression risks; requires licensed/consented diverse data and held-out evaluation. | A research project with compute costs, not a same-day optimization. Teacher outputs are not perfect clean ground truth. |

Lower step counts on Base, q4 quantization, mixed precision and cached/approximated intermediate features are additional experiments, not guaranteed quality-preserving optimizations. The release is already q8. Reduced bit width does not automatically translate into proportional GPU speed, and input-dependent Thinker conditioning cannot simply be reused for different audio chunks.

## Is 10× plausible?

It is a reasonable **research target**, especially with a distilled checkpoint plus runtime improvements. There is no evidence yet for 10× faster, equally good enhancement on this M5, and even less evidence for bit-identical AuK 32 output at that speed.

Use Amdahl's law: if fraction `p` of total runtime is accelerated by `k`, end-to-end speedup is `1 / ((1 - p) + p/k)`. For illustration, if 90% of time were in a portion accelerated 16×, the complete app would improve only **6.4×**. Achieving 10× with that hypothetical 16× kernel improvement requires at least 96% of runtime to be in the accelerated portion. These are mathematical examples, not measurements of Voicy. CFG branch batching also prevents treating a branch-count reduction as an exact wall-clock multiplier.

Under the updated constraint, the practical route is to identify the bottleneck, remove repeated work and measure latency together with exact output equality. Flash is outside the current task. A SwiftUI rewrite, packaging Python differently, additional UI work or removing export overhead cannot plausibly be credited with 10× model acceleration without evidence.

## Acceptance protocol

1. Keep the approved checkpoint, parameters and reference files immutable. Record model hashes, versions, chip, memory, power mode and thermal conditions.
2. Use at least three matched runs per configuration; report median and range, cold startup and warm reuse separately. Retain failed runs in the report.
3. Use the existing 18.965-second reference plus short and several-minute recordings covering Czech/English, different voices, reverberation, stationary/transient noise, quiet syllables and multiple speakers. Use only recordings authorized for testing.
4. Report end-to-end wall time, per-stage synchronized timings, real-time factor, peak process/Metal memory, memory pressure and cancellation latency. Test under realistic simultaneous app use.
5. For runtime-only changes, compare PCM exactly first. Compilation-related differences need a stated numerical tolerance and listening checks. For model changes, use randomized, loudness-matched blind A/B, content/timing checks and explicit failure examples; automated quality/ASR scores are supporting evidence only.
6. Promote a fast model only with user approval of its sound. A later UI could offer Quality (approved AuK 32) and Fast (validated alternative), but do not add a mode before it earns that distinction.
7. Updated bounded investigation: synchronized profiling, resident-model comparison, embedding reuse, bounded asynchronous scheduling and allocator cache size. Report speed/quality/memory results; no custom training or Flash substitution. Do not delay the beta indefinitely in pursuit of an unverified 10× claim.

## Primary references

- [Tencent AuK repository](https://github.com/Tencent-Hunyuan/AuK): upstream architecture and supported inference paths; local inspection used the pinned source shipped with Voicy.
- [Official AuK-Flash model card](https://huggingface.co/tencent/AuK-Flash): distilled four-step checkpoint. This establishes availability, not quality equivalence to the user's approved result.
- [MLX compilation documentation](https://ml-explore.github.io/mlx/build/html/usage/compile.html): compilation, tracing and optimization behavior. No source benchmark is assumed to transfer directly to Voicy.

See also [release validation](VALIDATION.md) and [macOS audit](MACOS-AUDIT.md).

## 0.3.2 exact execution update

The approved Base32 optimization is integrated; see [qualification evidence](VALIDATION.md#exact-auk-execution--032)
and [packaged run measurements](EXACT-EXECUTION-0.3.2.json). The previous 10×
research target was not achieved without quality loss. This release uses only
Base32 execution changes and retains the original numerical settings.
