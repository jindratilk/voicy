# Release candidate validation

Voicy 0.3.0, Apple Silicon, macOS 26.6.2. These are development-machine results, not a claim of universal compatibility or best-in-world speech quality.

- Python regression suite: 35 passed, using the bundled audio-only FFmpeg.
- Player regression suite: 7 passed, including React Strict Mode, rapid A/B switches, retained playhead, playback errors and duplicate export protection.
- Frontend production build and Rust compilation: passed.
- Native file picker imported an 18.965-second M4A. The bundled AuK 32 worker completed in 138.17 seconds on the test machine. This is a single run under concurrent development load, not a general speed benchmark.
- A/B playback retained position in macOS WebKit. Native Save exported a finite, mono 48 kHz PCM24 WAV with the same 18.965-second duration.
- Backend import measurement: 0.400 seconds / 58.6 MiB peak RSS after lazy imports, compared with 1.592 seconds / 239.2 MiB when eagerly importing Torch and SciPy. These figures measure backend imports only, excluding WebKit, model inference and GPU memory.
- The audio-only processor adapter was compared with upstream Qwen preprocessing: all 32,000 samples were exactly equal for the tested local WAV segment.
- No user recordings are included in the app bundle or source release. Application Support holds the mutable library and caches.

The approved AuK settings remain 32 steps, q8/group64, seed 2026 and the existing context-overlap joining. UI and packaging changes do not establish an improvement in perceptual audio quality.

Apple notarization is intentionally deferred. A clean second-Mac test and a full fresh model bootstrap remain release qualification steps. Signing is not notarization. See `RELEASE.md` for the procedure.
