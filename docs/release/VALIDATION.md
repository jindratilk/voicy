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
- The signed compressed DMG passed `hdiutil verify`. The app inside the mounted final image also passed ticket validation and Gatekeeper. The actual image was visually checked in Finder, including its background, icon positions and Applications link. The disk image's own notarization is still in progress; publication of the download is gated on that result.
- The Apple app log includes 11 archive-unpacking warnings for vendor test data: ten legacy Joblib serialized fixtures and one SciPy NPZ containing two NumPy arrays. The data formats were inspected without unpickling them. There were no error-severity issues, and Apple marked the application ready for distribution. These warnings are not described as a clean, warning-free notarization.
- Repository history and source files were checked for private material. The binary audit inspected 13,846 text files for the release credentials and found no matches. No user recordings are bundled. The audio fixtures in the Python runtime are public SciPy test data; PEM files are Certifi public certificate-authority bundles.
- Website authentication, origin checks, session tampering, expiry and logout were checked. Ten unit tests cover authentication, download availability and byte-range parsing. Public production API checks also passed.
- The actual prerecorded A/B player was checked for playback progress, pause, position retention and version switching. Mobile widths of 320 and 390 pixels and a 1440-pixel desktop viewport were checked; the 320-pixel decorative overflow was fixed. Reduced motion is supported.
- The final mobile Lighthouse run after contrast fixes and local font preloading scored **99 performance / 100 accessibility / 100 best practices / 100 SEO**, with FCP 1.4 s, LCP 2.0 s, TBT 0 ms and CLS 0. Earlier performance runs varied between 82 and 98. These are laboratory samples, not field performance or a search-ranking guarantee.
- Google Search Console domain ownership was verified, and the sitemap was successfully processed with two URLs discovered. Indexing and rankings are separate outcomes.
