# E15: lossless canonical-input transport, version 1

Frozen 20 October 2026 before any model output from this five-case extension. A separate earlier0.3.3 release-qualification run already processed the first fixture and its output was inspected; that prior exposure is not a blinded prospective quality trial. This is a follow-up to the [preserved E14 preflight failures](E03-033-PREFLIGHT.md). The original five cases, source selection, degradation parameters, model settings and ten canonical input/reference hashes remain unchanged.

## Reason and identity

The CI reconstruction matched nine of ten files exactly. Only the simulated-reflections input differed numerically, with identical source/reference/parameters and maximum absolute sample difference `5.684341886080802e-14`. Its precise hardware/compiler/library cause is not isolated. Its small magnitude is not permission to waive a hash or claim perceptual equivalence.

The canonical case-2 input was frozen on15October as SHA-256 `dc00a36cf0fe0dee058954e7c5969c72f24b3e3e5ef532663a7fe613f673ddcf`. Transport those exact old bytes, rather than selecting a new waveform. The [machine-readable contract](E03-CANONICAL-INPUTS.json) binds one observed CI base hash, that original target, full file length and a20993-byte compressed XOR fixture in an explicit base64 JSON container. Both container and decoded compressed payload have separate byte lengths and SHA-256 identities. The fixture is a lossless difference encoding over the entire WAV file; it is not a new degradation or a model output.

## Required behavior

1. Verify the frozen manifest identity, fixture identity, context, length and bounded zlib decoding. The only permitted differing input is case2/utterance`121-121726-0000`; every other input/reference and every source/parameter record must already match the original manifest. Verify actual bytes, not just declared hashes.
2. Accept either the already-canonical case-2 file or the single recorded regenerated hash. Reject any other base. For the latter, XOR its bytes with the fixed decompressed payload and require the result to match the original canonical hash exactly. No tolerance, numeric threshold, per-case tuning or skipped case is allowed.
3. Leave the complete regenerated directory untouched. Create a new canonical directory exclusively, copy the generation records, restore only those exact case-2 bytes, and annotate the new manifest/case record with honest before/after and transport provenance. Retain both directories and both prior failures in private evidence.
4. Require all ten original input/reference hashes again before app download/model execution. Only the explicitly named owner branch`codex/e03-canonical-inputs` activates this supplemental contract. The original E14 branch retains its strict regeneration-only gate.
5. Continue with the exact public signed0.3.3 image and original AuK32/seed/quantization/context/automatic-memory settings. Preserve the26GiB entry guard,12GiB execution guard, pressure/case/work deadlines and encrypted-only output transport in the [0.3.3 addendum](E03-033-ADDENDUM.md). Record this supplemental protocol's identity and restoration proof in each new attempt.

Unknown variants, missing/corrupt payloads and target/context mismatches remain failures before inference. A later new base requires separately recorded provenance and review; it is never accepted automatically. Successful data transport is not completed inference, transcript fidelity, human review or a quality comparison. Public listening/model-output audio remains gated.

## Public fixture and rights

Only the explicitly allowlisted text container (under32KB, carrying the21KB compressed difference), manifest and reconstruction code enter public Git. The fixture alone is not a playable listening file. No full new listening file or model output is published by this contract. It is reproducible data transport and carries no quality endorsement.

LibriSpeech ©2014 Vassil Panayotov · [OpenSLR SLR12](https://www.openslr.org/12) · [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). Source utterance`121-121726-0000`; original changes were resampling, normalization and simulated reflections under E03v1. The difference fixture is derived from those fixed prepared bytes. No reader endorsement is implied. Retain this attribution with the fixture and any derivative.
