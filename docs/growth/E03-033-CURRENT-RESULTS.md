# E15 current-release attempt: canonical inputs pass, model batch fails

Observed 20 October 2026. This is a failed five-case run of the fixed [current-release extension](E03-033-ADDENDUM.md) with the separately frozen [canonical transport](E03-CANONICAL-INPUTS.md). It is not a successful benchmark, human listening result or Adobe comparison. Historical 0.3.2 results remain separate.

## Run and retrieved evidence

- [Run 39470226394, attempt 1](https://github.com/jindratilk/voicy/actions/runs/39470226394), job `118792020645`, source `3340674568dd61e0697d84523fd161c8c9b3a4dd`; terminal **failure**, 18:10 UTC.
- Standard macOS 15.7.9 arm64 host: Apple M1 (Virtual), 7 GiB RAM. This is below the app's recommended 16 GB; it does not establish behavior on the recommended hardware.
- All ten canonical input/reference hashes, source selections and parameters matched the original 15 October manifest. Case 2 was losslessly restored from the recorded CI variant to `dc00a36cf0fe0dee058954e7c5969c72f24b3e3e5ef532663a7fe613f673ddcf`. The complete generated directory and its own manifest remain preserved and hash-consistent.
- Exact public image `459f8699304ec2efa923001b0691a9fd3231067716a66b18f676f88f4c4f6e7b`; deep/strict signature verification, notarized Gatekeeper acceptance and version 0.3.3 passed. Original AuK32, seed, quantization, context and automatic memory policy were retained.
- Artifact `12288306190`: 26,504,174-byte ZIP, SHA-256 `ee27e03d4d7ded5f50ad6fa05ff28c33de33b1cc66db977a76fdedd9528ddecd`. Its two entries are the receipt and encrypted evidence. Ciphertext SHA-256 `3ea5208b20787715d15dd5ebc0b792ba9d191b444489bb560cbaafe94c05fbc3`; decrypted archive SHA-256 `fec9f129161984a9bd0a55b3a0fb17649378b9c53b0c3755d36a567ae42f2371`. All 71 inventory entries and the exact file set were independently checked after local decryption. Private keys, raw audio and full logs remain outside public Git; remote artifact retention is seven days.

## All five cases

| Fixed case | Actual outcome |
| --- | --- |
| 1, simulated fan | Completed; one structurally valid output, independently decoded and inspected locally |
| 2, simulated reflections | Process aborted with return code -6 after 18.62 seconds; no output WAV |
| 3, intermittent noise | Not run after case 2 failed |
| 4, quiet speech | Not run after case 2 failed |
| 5, clean control | Not run after case 2 failed; no current-release negative-control result |

Case 1 output is mono float32 at 24 kHz, 117,720 frames (4.905 seconds), finite throughout, peak `0.6304582953453064`, zero samples at or above absolute amplitude 0.9999. SHA-256: `8c3ec40b970d3f90429c81107250838d860865abaaa11ed94260f9fc021423b3`. Direct hosted-runner elapsed time was 223.76 seconds, including its startup/inspection; this is not a consumer speed benchmark. It is not identical to the historical 0.3.2 output, and no waveform/perceptual equivalence is asserted.

After the batch was terminal and its archive/raw files were validated, the same fixed small.en/CPU/four-thread/temperature-0/no-fallback/no-previous-context decoder checked this one valid output once. The exact original model SHA and installed toolchain versions were verified. Its unedited text was: “He began a confused complaint against the wizard, who had vanished behind the curtain on the left.” It agrees with the supplied wording after punctuation/case differences, but ASR agreement is not proof of sound quality or human intelligibility. Cases 2–5 have no current-release enhanced ASR result. No alternative model, parameters or outcome-based decode retry was used.

## Failure and limits

Case 2 logged the automatic nonresident plan, a 4 GiB Metal limit and `Starting chunk 1/1`, then:

```text
[METAL] Command buffer execution failed: Caused GPU Timeout Error
(00000002:kIOGPUCommandBufferCallbackErrorTimeout).
```

The recorded resource samples retained at least 37,046,722,560 free bytes and memory-pressure values 1 or 2. Neither the 12 GiB disk guard nor critical-pressure guard caused the stop. This does not rule out an unobserved transient or diagnose the underlying GPU/driver/model interaction. Final normal image detachment also failed with `Resource busy`; that secondary failure is preserved separately, and the overall run remains failed.

An MLX maintainer [describes the same error class in a different CPU/GPU synchronization workload](https://github.com/ml-explore/mlx/issues/3583). This is diagnostic context, not evidence that Voicy has that issue or that a reported workaround fixes this run. Do not alter runtime flags, shorten an input, skip the failed/control cases, disable guards, use a paid runner or silently rerun until a batch passes.

The canonical transport's actual CI behavior is verified. The five-case current-release model/ASR/listening evidence is **incomplete**. Preserve this failure before defining a separate, bounded diagnosis of the exact case-2 abort. No new model-output/listening audio is published, no human review is claimed, and no ranking or conversion outcome follows. The separately qualified public 0.3.3 installer and earlier native checks are not a substitute for this failed batch.

LibriSpeech © 2014 Vassil Panayotov · [OpenSLR SLR12](https://www.openslr.org/12) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Original fixed resampling, normalization and simulated degradations are described in E03; case 1 was additionally enhanced. No reader endorsement is implied. Training overlap is unknown.
