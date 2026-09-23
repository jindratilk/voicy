# Validation evidence

Voicy 0.3.0, Apple Silicon, macOS 26.6.2. These are development-machine results, not a claim of universal compatibility or best-in-world speech quality.

- Python regression suite: 35 passed, using the bundled audio-only FFmpeg.
- Player regression suite: 7 passed, including React Strict Mode, rapid A/B switches, retained playhead, playback errors and duplicate export protection.
- Frontend production build and Rust compilation: passed.
- Native file picker imported an 18.965-second M4A. The bundled AuK 32 worker completed in 138.17 seconds on the test machine. This is a single run under concurrent development load, not a general speed benchmark.
- A/B playback retained position in macOS WebKit. Native Save exported a finite, mono 48 kHz PCM24 WAV with the same 18.965-second duration.
- Backend import measurement: 0.400 seconds / 58.6 MiB peak RSS after lazy imports, compared with 1.592 seconds / 239.2 MiB when eagerly importing Torch and SciPy. These figures measure backend imports only, excluding WebKit, model inference and GPU memory.
- The audio-only processor adapter was compared with upstream Qwen preprocessing: all 32,000 samples were exactly equal for the tested local WAV segment.
- Developer ID signing with hardened runtime and nested code verification passed. A relocated signed MLX worker completed a 3-second AuK 32 sample in 48.03 seconds with 3.66 GiB peak process RSS. This measures the worker only.
- Final native-app pass: the full 18.965-second recording completed in 162.87 seconds. Its exported PCM samples were exactly identical to the earlier successful export (maximum absolute sample difference 0). The native quit sheet was visible and Keep Processing returned to the app.
- No user recordings are included in the app bundle or source release. Application Support holds the mutable library and caches.

The approved AuK settings remain 32 steps, q8/group64, seed 2026 and the existing context-overlap joining. UI and packaging changes do not establish an improvement in perceptual audio quality.

Apple app notarization has since completed; see the publication checks below. A clean second-Mac test and a full fresh model bootstrap have not been independently verified. See `RELEASE.md` for the release procedure.

## Runtime optimization validation — 22 September 2026

- Backend regression suite: **43 passed**. Four MLX-only tests are skipped in the ordinary Python environment and were run separately with the bundled Python: **4 passed**.
- Test discovery is now restricted to `tests/`; an initial unscoped invocation collected ignored research scripts and generated third-party package tests and failed during collection. The scoped application suite passed.
- Three measured fresh-worker runs per variant, after one warmup each: 96.022 s reference median, 95.282 s candidate median. This 0.77% observed reduction is small, with overlapping ranges; do not advertise a significant acceleration.
- All eight full reference outputs have identical float32 PCM hashes, including both chunks and the join. Model weights/settings/precision are unchanged.
- Memory policy tests cover 16, 32 and 128 GiB, insufficient headroom, warning/critical pressure, unknown system information and pressure transitions. Physical hardware testing was limited to the M5/32 GiB Mac.
- Updated Python resources were assembled into the existing native shell; no frontend or Rust binary changes were needed. Developer ID resource signing and deep/strict signature verification passed.
- The previously signed application and approved speech checkpoint were preserved before replacement. Notarization was deferred at this stage and subsequently completed as recorded below.

- Native smoke test: import via the macOS file dialog and enhancement through Voicy completed successfully in 114.68 seconds. This is a single application run, not a speedup comparison. The original saved app runtime was then run on the identical newly decoded input and mastered with the same bundled FFmpeg: all **910,336 PCM24 samples at 48 kHz matched exactly**, maximum difference 0.
- Re-importing the M4A differed from the historical decoded WAV by at most 8.940697e-08 in float32 input; comparing those different inputs was rejected as an optimization regression test. Repeated decoding with the current unchanged FFmpeg matched the new import. The native quality comparison above therefore uses identical decoded input.
- The final UI capture encountered ScreenCaptureKit error -3811 after enhancement was launched. Completion was verified from the app's stored job state and actual WAV. No new export-dialog or final-screen capture pass is claimed in this iteration; those controls were unchanged.

## Publication checks — 22 September 2026

- Apple accepted the signed application submission (`c8bc93a9-8762-4e73-896b-3f8e64861a4b`). Its ticket was stapled and validated. Deep/strict code verification passed; Gatekeeper returned `accepted`, `source=Notarized Developer ID`.
- The signed compressed DMG passed `hdiutil verify`. The app inside the mounted final image also passed ticket validation and Gatekeeper. The actual image was visually checked in Finder, including its background, icon positions and Applications link. Apple also accepted the disk image (`41eedfac-841e-4e50-9dd6-48ec013226db`); its ticket was stapled and validated, and Gatekeeper accepted its primary signature. The DMG log has the same 11 reviewed data-archive warnings and no errors.
- The Apple app log includes 11 archive-unpacking warnings for vendor test data: ten legacy Joblib serialized fixtures and one SciPy NPZ containing two NumPy arrays. The data formats were inspected without unpickling them. There were no error-severity issues, and Apple marked the application ready for distribution. These warnings are not described as a clean, warning-free notarization.
- Repository history and source files were checked for private material. The binary audit inspected 13,846 text files for the release credentials and found no matches. No user recordings are bundled. The audio fixtures in the Python runtime are public SciPy test data; PEM files are Certifi public certificate-authority bundles.
- Website authentication, origin checks, session tampering, expiry and logout were checked. Fourteen unit tests cover authentication, download availability, byte-range parsing and full-versus-partial download responses. Public production API checks also passed.
- The actual prerecorded A/B player was checked for playback progress, pause, position retention and version switching. Mobile widths of 320 and 390 pixels and a 1440-pixel desktop viewport were checked; the 320-pixel decorative overflow was fixed. Reduced motion is supported.
- The final mobile Lighthouse run after contrast fixes and local font preloading scored **99 performance / 100 accessibility / 100 best practices / 100 SEO**, with FCP 1.4 s, LCP 2.0 s, TBT 0 ms and CLS 0. Earlier performance runs varied between 82 and 98. These are laboratory samples, not field performance or a search-ranking guarantee.
- Google Search Console domain ownership was verified, and the sitemap was successfully processed with two URLs discovered. Indexing and rankings are separate outcomes.

- The published R2 artifact passed byte comparisons at the beginning, middle and end. The public download endpoint returns 200 for full downloads and HEAD, 206 for valid ranges, and 416 for an out-of-bounds range. Temporary authenticated upload routes were removed after publication.

- A complete download through `https://usevoicy.app/api/download` returned HTTP 200 and all **6,527,846,904 bytes**. Its SHA-256 matched the signed original: `b1763ccf03a3c89316fca0ffa0d7a5fc1b66f4499b1a9b668af3abaec45e5a10`. Ticket validation and Gatekeeper both passed on this downloaded copy (`Notarized Developer ID`).

## Recording limits removed — 0.3.1

- Removed the 20-minute duration and 250 MB import caps from decoding, HTTP upload, native file selection and the desktop interface. Decoding no longer truncates the source with FFmpeg `-t`.
- Removed fixed two-minute processing/transfer deadlines. Native requests retain a connection-establishment timeout, which does not limit recording duration or transfer duration.
- RF64 is selected for large WAV outputs; ordinary files retain the previous PCM subtype. Actual RF64 input decoding passed with the bundled audio-only FFmpeg.
- Regression tests accept a 251 MiB file through the actual HTTP multipart upload endpoint and preserve audio after the former 20-minute boundary. The backend suite passed 47 tests with four MLX-only skips, including RF64 input decoding. Desktop player tests: 7 passed. Desktop production build, Rust release build, website production build and 14 website tests passed.
- A two-hour recording of 691,200,044 input bytes passed decoding, analysis and PCM24 export with all 345,600,000 frames retained, including its final tone. This verifies long-file handling, not two hours of AI inference or a guarantee of arbitrary-length processing on every machine.
- On a fixed short input, decoding and both mastering modes returned PCM identical to 0.3.0. Model settings, weights and sampling arithmetic were not changed. Available RAM and disk space still bound practical capacity; the model runner retains audio and chunks in memory.
- The signed 0.3.0 and 0.3.1 application runtimes processed the same three-second speech sample through AuK and mastering. All 144,000 PCM samples matched exactly (maximum difference 0). The harness uses the application's isolated Python environment and private cache directories; an initial harness invocation incorrectly included user-site packages and was corrected before this comparison.

- The 0.3.1 app and DMG were accepted by Apple; stapled-ticket validation and Gatekeeper checks passed for both. Apple returned the same eleven warnings concerning bundled vendor test-data archives noted for 0.3.0, with no error-severity issues. Final DMG SHA-256: `6152bcf9b856fc714c7ad3f2427331eb364713b4aac84f5011cb11fcd87021d8`.
- Website redirects now include the release version to avoid reusing a previously cached installer. All 14 website tests and the production build passed after this change.
- The final R2 upload verified all 98 part MD5 values and the completed multipart ETag against local data. Public download checks passed after deployment propagated: HTTP 200 with the 0.3.1 filename and all 6,512,579,193 bytes declared, exact beginning/middle/end byte ranges, and HTTP 416 for an out-of-bounds range. This release used complete upload integrity checks plus public range checks, rather than a second full download. The temporary authenticated uploader Worker was deleted after verification.

## Exact AuK execution — 0.3.2

The model, weights, 32 sampling steps, q8/group64 precision, CFG 2, seed 2026,
12-second context, four-second overlap and audio joins are unchanged.

- Exact-order Metal operations preserve individual float operations; final-block
  feed-forward work for discarded context tokens is omitted. Text projections
  are reused only within the same sampling call.
- Two independent chunks share loaded model stages when current headroom allows.
  Under pressure the worker uses one chunk and releases retained VAE weights.
  Synthetic budget tests cover 16, 32 and 128 GiB, normal/unknown/critical pressure
  and boundary conditions. These are policy tests, not physical-device benchmarks.
- The native ATen frontend is built against bundled Torch 2.14.0 with a relative
  loader path. It checks Qwen configuration, tokenizer and processor hashes before
  using fixed input-independent constants. Recording features are always fresh.
- The integrated worker matched all 455,168 native float32 samples of the approved
  18.965-second recording, including the overlap join. Four interleaved packaged
  runtime runs also matched bit for bit. See `EXACT-EXECUTION-0.3.2.json` for times,
  memory and limitations. Float WAV verification compares `uint32` views of the
  native float32 samples; it never rounds those samples to integer PCM.
- 23 targeted worker/chunking/memory tests, seven UI tests, real Metal operation
  equivalence and existing real-MLX embedding reuse tests passed. Vite and the
  native Tauri release build passed.

The earlier isolated research benchmark measured 1.292× (84.387 → 65.301 s).
Release qualification under concurrent user load measured 1.661× using two
runs per variant; that more variable result is not a stronger general speed claim.
All hardware results above are from one M5 Mac with 32 GB RAM. No 10× or
cross-hardware quality/performance claim is made. AuK-Flash and distillation
experiments are not included in the release.

Release qualification additionally exercised enhancement and final 48 kHz PCM24
mastering directly from the signed, relocated application: all 144,000 exported
samples matched 0.3.1. The app and final DMG were accepted by Apple, stapled and
accepted by Gatekeeper. The mounted DMG passed its filesystem checksum, app
signature and ticket checks; all 27 relevant runtime code files matched the
qualified app. It contains no Voicy recording library.

Apple reported the previous eleven vendor test-data archive warnings and one
additional warning for `constants.npz`. The added archive passed ZIP CRC checks
and contains only two numeric NumPy arrays (token IDs and mel filters), with no
executables or object/pickle arrays. There were no error-severity issues.

The final installer is 6,513,528,823 bytes. SHA-256:
`7e23011e3169adff45be0126d1af9bed2e25338e15b69beb5550ec31d8fa3081`.
R2 upload verified all 98 part MD5 values and the completed multipart ETag against
the local final artifact. Public verification checks the declared filename/size,
exact beginning/middle/end byte ranges and rejection of an invalid range; it does
not claim a second complete download.
