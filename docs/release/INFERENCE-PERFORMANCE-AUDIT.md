# Inference performance audit — 21 September 2026

## Decision

Enhancement latency is the highest-priority product limitation raised by the user. Keep the approved AuK Base / 32-step configuration as the reference checkpoint. Investigate a 10× end-to-end acceleration target, but do not present it as achieved or guaranteed. This audit changes documentation only; it does not replace the released model or start a training run.

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

Therefore the practical route is: identify the bottleneck, remove repeated model work, test the already-distilled Flash model, and measure complete latency and quality together. A SwiftUI rewrite, packaging Python differently, additional UI work or removing export overhead cannot plausibly be credited with 10× model acceleration without evidence.

## Acceptance protocol

1. Keep the approved checkpoint, parameters and reference files immutable. Record model hashes, versions, chip, memory, power mode and thermal conditions.
2. Use at least three matched runs per configuration; report median and range, cold startup and warm reuse separately. Retain failed runs in the report.
3. Use the existing 18.965-second reference plus short and several-minute recordings covering Czech/English, different voices, reverberation, stationary/transient noise, quiet syllables and multiple speakers. Use only recordings authorized for testing.
4. Report end-to-end wall time, per-stage synchronized timings, real-time factor, peak process/Metal memory, memory pressure and cancellation latency. Test under realistic simultaneous app use.
5. For runtime-only changes, compare PCM exactly first. Compilation-related differences need a stated numerical tolerance and listening checks. For model changes, use randomized, loudness-matched blind A/B, content/timing checks and explicit failure examples; automated quality/ASR scores are supporting evidence only.
6. Promote a fast model only with user approval of its sound. A later UI could offer Quality (approved AuK 32) and Fast (validated alternative), but do not add a mode before it earns that distinction.
7. First bounded investigation: profiling + resident-model comparison + one Flash candidate. Stop and report speed/quality/memory results before committing to custom training. Do not delay the beta indefinitely in pursuit of an unverified 10× claim.

## Primary references

- [Tencent AuK repository](https://github.com/Tencent-Hunyuan/AuK): upstream architecture and supported inference paths; local inspection used the pinned source shipped with Voicy.
- [Official AuK-Flash model card](https://huggingface.co/tencent/AuK-Flash): distilled four-step checkpoint. This establishes availability, not quality equivalence to the user's approved result.
- [MLX compilation documentation](https://ml-explore.github.io/mlx/build/html/usage/compile.html): compilation, tracing and optimization behavior. No source benchmark is assumed to transfer directly to Voicy.

See also [release validation](VALIDATION.md) and [macOS audit](MACOS-AUDIT.md).
