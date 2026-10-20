# E16 result: timeout surfaced while evaluating Thinker conditioning

Observed 20 October 2026 under the separately frozen [single-case diagnostic protocol](E03-GPU-DIAGNOSIS.md). The one attempt **failed**. It narrowed the observed exception boundary, but did not identify a GPU kernel, establish a root cause or fix the application. The [failed five-case E15 ledger](E03-033-CURRENT-RESULTS.md) remains unchanged.

## Identity and retrieval

[Run39475551692, attempt1](https://github.com/jindratilk/voicy/actions/runs/39475551692), job`118810438715`, source`c682517ed300b9aa1a0cff2ce85472708dfdaa86`; terminal failure at18:42UTC. SYSTEM records selection`[2]`, protocol SHA`6a9b3ea4e5bbcc5847bbb2017b72d223211ed8d0b1059c7a814904398b1284f0` and observer SHA`e6a0ae32205ddba1cb8afd1422789bde582f5d5d932fcd79f972ab1f6599447d`. The workflow's copied job key is named`fixed-five`; it is not evidence that five cases ran.

The standard host was macOS15.7.9, Apple M1 (Virtual), 7GiB RAM, below the recommended16GB. All ten canonical input/reference hashes and original source/parameter records matched. The generated variant remained intact. Exact signed/notarized0.3.3 image`459f8699304ec2efa923001b0691a9fd3231067716a66b18f676f88f4c4f6e7b` and the original runner/model settings were verified.

Artifact`12289089004`: 24,644,083-byte ZIP, SHA`6a24b8d6b59b2be956366484c5466dc2ec30ab0d84c171ba1865372edfccd515`. Ciphertext SHA`b257cc02393cba099776932d3d1a11862e969d2c60fac2dc3de8e0ad440c19dd`; decrypted archive SHA`a3d8ffa40ff4479094a6786f4596c710c4e4359cebde9057ce0f9c92d5422a0b`. After retrieval/decryption, every one of65 inventory entries and the exact file set were independently verified. Raw logs/configs/trace and the local-only key remain outside public Git; remote retention is seven days.

## What the trace actually shows

The trace contains12 monotonically ordered records, SHA`c13474336429a7731d1c19cc511adc847fced57818a1bfa944ca44f50628fca5`. It was not capped. No C-call events were exposed in this run, so the Python boundaries and actual traceback are the evidence; absence of C events does not mean no GPU work occurred.

| Observer-relative seconds | Recorded event |
| --- | --- |
| 5.731 | Enter `generate_chunks` |
| 5.754–6.585 | `_build_vae` call/return events |
| 6.585–6.588 | `encode_audio` call/return events; return alone is not GPU completion |
| 9.762–9.840 | Enter/return `_release`, after the source's reference-evaluation boundary |
| 9.840–10.026 | `_build_thinker` call/return events |
| 49.020–49.022 | `generate_chunks` return event while unwinding, then `runner_raised: RuntimeError` |

The preserved traceback identifies `server/auk_exact/scheduling.py:44`, `mx.eval(text)`, as the boundary where this error was raised:

```text
[METAL] Command buffer execution failed: Caused GPU Timeout Error
(00000002:kIOGPUCommandBufferCallbackErrorTimeout).
```

The model child exited1 after54.69seconds of parent-observed wall time. E15 instead terminated with-6; retain this different exception surface. No output WAV/result was produced, and there is no new ASR or listening result. Recorded samples retained at least37,868,904,448 free bytes and pressure values1 or2. Disk/critical-pressure/case deadline guards did not trigger. Normal image detachment had no recorded error in this attempt.

The error surfaced while evaluating the conditioning tensor after Thinker construction. This is not proof that the preceding Python method completed all GPU work, or that a particular Thinker operation caused the timeout. The replacement `encode_text` method has a different module/name from the observer's selected Python events; its missing call event is not evidence it was skipped. The actual traceback and signed source establish the evaluation location. Observer overhead, a different host and running case2 first rather than after case1 also prevent attributing any difference to profiling alone.

## Static source checks and next hypothesis

Actual E15 configs show both cases planned one288,000-frame block at24kHz (12seconds), with identical model/precision/seed/memory settings. Valid source lengths differed:117,720 versus212,640 frames. It is therefore unsupported to explain this simply as a larger computational chunk or present input shortening as a fix.

Static inspection of the exact qualified image, mounted read-only and then detached without running a model locally, confirmed the conditioning boundary and builder. Source identities: `.auk/source/auk_mlx/infer.py` SHA`c60f4d5159f337db8eb9c594965f25d7e210aac60063a65fcf0a4556a82edd3c`; `server/auk_exact/scheduling.py` SHA`fa8c4b12d386145162ab48ffd4f7f82985bb4e78be72bd8a4ac02ed860512188`.

The builder loads Thinker weights and calls `m.eval()`. In [pinned MLX0.32.2 source](https://github.com/ml-explore/mlx/blob/v0.32.2/python/mlx/nn/layers/base.py), that method selects inference mode; it is distinct from materializing arrays with `mx.eval(model.parameters())`. This distinction suggests a separately controlled weight-loading/conditioning-boundary investigation; it does not establish that lazy loading caused either timeout or that eager evaluation is a fix. Do not add it to this already-run protocol or alter the public runtime on that inference alone. Preserve exact weights/settings and resource guards in any separately frozen follow-up.

No watchdog override, driver flag, shorter input, model upgrade, numerical change, paid runner or further attempt was used. Current public-release qualification remains separate; this is not a successful five-case benchmark, human quality judgment, general reliability result or search-ranking outcome.

LibriSpeech ©2014 Vassil Panayotov · [OpenSLR SLR12](https://www.openslr.org/12) · [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). Case2 original resampling/normalization/simulated reflections remain as frozen; no completed new enhancement or reader endorsement is implied.
