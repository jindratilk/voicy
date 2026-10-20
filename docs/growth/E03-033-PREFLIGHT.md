# Current-release E03 preflight: two preserved failures

Observed 20 October 2026. No 0.3.3 model case ran in these attempts. Historical 0.3.2 results remain separate. This report records preparation and transport evidence, not audio quality or search performance.

| Attempt | Source | Observed outcome |
| --- | --- | --- |
| [39460153714](https://github.com/jindratilk/voicy/actions/runs/39460153714) | `9924f35352a878bfd44993ddf7a3839574049f5b` | Exact public image/signature/Gatekeeper verified; preparation failed because the minimal FFmpeg configuration omitted the PCM float muxer. No inference. |
| [39463093944](https://github.com/jindratilk/voicy/actions/runs/39463093944) | `3e94705c9f5d11e1fa9be2ce684636b3f5938228` | Corrected FFmpeg passed actual fixed-source FLAC decoding. All five cases were regenerated; nine of ten input/reference SHA-256 values matched. The case-2 input failed the original hash gate before any app download or inference. |

Both standard macOS15 hosts reported macOS15.7.9, Apple M1 (Virtual), 7516192768 bytes physical RAM and approximately 42.64 GiB initially free. This exceeds the strict 26 GiB entry gate, despite the nominal storage in GitHub's runner table. It does not guarantee future availability. The VM has less than the app's recommended 16 GB RAM and is not a consumer speed benchmark.

The two GitHub artifact ZIP digests, ciphertext hashes, decrypted archive hashes and every inventoried file were verified after local retrieval. Only encrypted evidence and non-audio receipts were uploaded. The private recipient key remained on the owner's Mac. Raw account evidence and unpublished audio stay outside public Git.

## Case-2 portability observation

The original and regenerated case-2 files have identical headers, trailers and 425280 float samples. The source FLAC, transcript, reference file and declared degradation parameters match. 7272 input samples differ numerically: maximum absolute difference `5.684341886080802e-14`, RMS difference `1.280152965817039e-16`. This is not a listening or perceptual-equivalence result.

The canonical input frozen on 15 October remains SHA-256 `dc00a36cf0fe0dee058954e7c5969c72f24b3e3e5ef532663a7fe613f673ddcf`. CI regenerated `f4de1c703a00708ea1af0e9dbdf057b5d8cd06117c11b8dbf828b65595b6b1ec`. Both used NumPy2.4.6, SciPy1.17.1 and FFmpeg9.0.1. The observed difference is confined to the input of the condition constructed with FFT convolution; its precise hardware/compiler/library cause has not been isolated.

The strict gate correctly stopped the experiment. No tolerance, alternative input, skipped case or favorable model result was accepted. A follow-up must first define a lossless, identity-bound way to transport the original canonical bytes. Preserve the regenerated variant and both failures, then require every original input/reference hash before any later model execution. That is a separate contract, not an amendment to the old results.

LibriSpeech © 2014 Vassil Panayotov · [OpenSLR SLR12](https://www.openslr.org/12) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Case2 is utterance `121-121726-0000`, resampled, normalized and given simulated reflections under the unchanged original preparation recipe. Training overlap remains unknown; no reader endorsement is implied.
