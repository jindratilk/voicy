# Contributing

Use synthetic recordings in tests. Do not commit audio from users, model weights, local paths, credentials, debug logs or research transcripts. Keep inference in the worker process and all runtime data local.

Run `npm --prefix web test`, `npm --prefix web run build`, the Python tests, and `cargo check --manifest-path src-tauri/Cargo.toml` before submitting changes. Add regression tests for behavioral fixes. Include an accessible keyboard path for new controls and respect reduced motion.

Report the macOS version, chip, app version and reproduction steps with a bug report. Do not attach private recordings unless you intend to share them publicly. Perceptual audio improvements need listening evidence; a higher objective score alone is insufficient.
