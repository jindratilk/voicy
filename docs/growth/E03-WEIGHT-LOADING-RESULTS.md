# E17 result: control timed out; parameter materialization completed case 2

Observed 20 October 2026 under the separately frozen [one-pair protocol](E03-WEIGHT-LOADING.md). The control failed and the materialization arm completed. This supports further investigation of the execution boundary in this context; it does **not** establish a cause, replicated fix, public-app qualification or audio quality. The workflow correctly concludes **failure** because one matrix arm failed. The earlier [E15 five-case failure](E03-033-CURRENT-RESULTS.md) and [E16 diagnostic failure](E03-GPU-TRACE-RESULTS.md) remain intact.

## Actual execution and bindings

[Run 39480972284, attempt 1](https://github.com/jindratilk/voicy/actions/runs/39480972284), source `e3d92a3b5a5ea83ec259ee1cb490ea74a39814f7`:

| Arm | Job | Actual UTC execution | Outcome | Parent-observed case seconds |
| --- | --- | --- | --- | --- |
| Control | `118829126870` | 19:09:16–19:19:08 | Failed, child exit 1 | 82.763 |
| Materialize | `118829127711` | 19:19:15–19:30:34 | Completed, child exit 0 | 244.847 |

Both used fresh standard macOS 15.7.9 Apple M1 (Virtual) hosts with 7GiB RAM, below the recommended 16GB. No parallel model arms, replacement jobs or outcome-based retries occurred. All ten original canonical input/reference hashes, signed image `459f8699304ec2efa923001b0691a9fd3231067716a66b18f676f88f4c4f6e7b`, original case-2 settings and source bindings passed. The two resulting configuration records are exactly equal, including the same one 288,000-frame computational block, 212,640 valid frames, AuK32, seed2026, q8/group64, CFG2 and automatic memory policy.

Both SYSTEM records bind protocol SHA `47f750a23763cf42001064ebfbede715e05b8493fdbd6785c13e7c665332d40b`, bootstrap SHA `d3c53e9ee37892d33f59c9f4ea4fbf3e8f1fea0d8d50a083c0e84af6a1f88638` and unchanged observer SHA `e6a0ae32205ddba1cb8afd1422789bde582f5d5d932fcd79f972ab1f6599447d`. No bundle file, weight, input, precision, watchdog, runner class or resource guard was changed.

## Preserved failures and successful output

Control recorded zero added tensor evaluations. Its parameter metadata/object identity check completed, then `scheduling.py:44`, `mx.eval(text)`, raised the same Metal GPU timeout class as E16. Its 14-record trace ends with `runner_raised: RuntimeError`; no output or ASR result exists. Trace SHA: `fa2d882e81b9443d3662f6d0791e37a7b42868d54b787fcab63ddb8b27c3aeab`.

Materialize recorded exactly one added `mx.eval(parameters)` between observer-relative seconds 11.330 and 45.255, then returned the same model to the original caller. Both arms' before/after records describe 1,814 arrays and 4,206,735,360 bytes, training false, metadata SHA `dd24976e5cdb3205ec6174f2f19fb3d3f72b35af3090ae7a6411d29176498641`, with unchanged parameter objects and metadata. This is not a numeric parameter checksum. The successful 28-record trace ends with `runner_returned`; SHA `d65ff76dcbcfadd3d96fa1c6ef1743ea736ebfa6794af0a0a0a7031da317d327`. Neither trace exposes C-call events or hits its cap. CPU boundaries do not identify GPU kernels.

Independent ffprobe/decoded-sample/hash checks of the materialize output establish mono 24kHz float32, 212,640 frames / 8.86 seconds, all finite, peak 0.7071910500526428 and zero clipped samples. Raw SHA: `8d631b07055c55dd6e79b6224d9466a61d37efdb697013f6568e662ea44d81ec`. Raw audio remains private.

After the entire pair was terminal and raw validation passed, exactly one small.en CPU decode used the unchanged model SHA, installed toolchain and original four-thread/English/temperature0/no-fallback/no-previous-context/fp16false policy. Complete text:

> Also, a popular contrivance whereby lovemaking may be suspended but not stopped during the picnic season.

The source transcript has `LOVE MAKING`; compounding, case and punctuation differ. This is an ASR inspection proxy, not human intelligibility, artifact, voice-identity or quality evidence. The failed control has no transcript. No alternative recognizer or repeat decode was selected.

Initial free bytes were 45,778,935,808 / 45,787,082,752 for control/materialize; observed execution minima were 37,314,695,168 / 36,088,528,896. Both sampled pressure states 1 or 2; no disk/critical-pressure/case-deadline guard fired. No normal-detachment error was recorded. Different hosts, timing and available resources remain confounders; these are not consumer speed benchmarks.

## Independent retrieval

Both encrypted artifacts were retrieved, decrypted and checked against GitHub ZIP digest, ciphertext/archive digest, every inventory hash and the exact file set:

| Arm | Artifact | ZIP bytes | ZIP SHA256 | Inventory entries |
| --- | --- | --- | --- | --- |
| Control | `12292640234` | 24,644,676 | `1b64b6284eca4e7709348a45dfc9baef47fddc4f2e7847b69c181795d162ca86` | 65 |
| Materialize | `12293555241` | 26,456,380 | `ee0e4fca9cd2fb20f54e59830b160e41ef48407b4776da0ddad8bd5f59fc6084` | 67 |

Control ciphertext/archive SHA: `34eb2c6d08642211438f408d03415a3265549535a2c2784908e62b1c6ae5bf3d` / `f8e78286329b15034279e4c36f358500e3c39e3568910e8efc228d206d9d9f5e`. Materialize: `da9b55f29c8e29ce5f1fe4c6d0d63144cd6bcdeb8dafe9f415cc5639508d7b6a` / `41e21126622eeb0d1759e6db1c03ee938b1390f9e1d6d39b8c5f9ec0e26f21f0`.

Dated private receipts, generated/canonical inputs, configs, complete traces/logs/transcript and local-only key stay outside public Git. Remote retention is seven days. Retrieval/postprocessing retained the separate 1.5GiB local reserve; the 12GiB AuK guard was not waived and no AuK model ran on the local Mac.

## Decision

Keep the public signed app and download unchanged. Treat this as one positive investigative pair with a retained negative control, not a shipping fix. Any replication, full original five-case/control run and native/release qualification require a separate justified scope. Return the next growth cycle to useful comparison content and available search measurements rather than accumulating more same-day model attempts. No new public audio, human judgments, Google rank, conversion, external submission or IndexNow notification follows from this research result.

LibriSpeech ©2014 Vassil Panayotov · [OpenSLR SLR12](https://www.openslr.org/12) · [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). Preserve the original normalization/resampling/simulated reflections and attribution; no reader endorsement.
