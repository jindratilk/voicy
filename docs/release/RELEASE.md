# Release procedure

1. Run Python regression tests, UI tests and the frontend production build.
2. Stage a portable runtime, including pinned model assets; build `Voicy.app` with `scripts/build-voicy.sh`.
3. On an Apple Silicon Mac, verify import, enhancement, cancellation, A/B playback, native export, quit confirmation, window reopen and application restart.
4. Sign nested Mach-O files first, then the app, using `scripts/sign-macos.py --identity 'Developer ID Application: …' --app /path/to/Voicy.app`.
5. Verify with `codesign --verify --deep --strict --verbose=2`.
6. Submit a zipped signed app using `xcrun notarytool submit … --keychain-profile PROFILE --wait`. Staple an accepted ticket with `xcrun stapler staple …`, then validate it. Signing alone is not notarization.
7. Test the resulting release on a clean second Mac. A developer-machine smoke test does not replace that check.
8. Publish only the reviewed source allowlist and intended release artifacts. Never publish `.data`, `.auk`, local recordings, research artifacts, runtime logs, signing keys, or local build directories.

The full offline bundle includes several GB of model assets. Do not try to put those into Git history. GitHub release assets have their own size limits; host large model payloads separately or design an explicit verified model-download flow before publishing a smaller online installer. This release uses the full offline bundle and does not silently download models.

## Native CI coverage and the macOS 14 runner retirement

GitHub [retires its macOS 14 hosted runners on 2 November 2026](https://github.blog/changelog/2026-10-01-github-actions-macos-14-runner-image-retirement/).
The remaining October brownouts are 26, 29 and 30 October, each from 14:00 UTC
until 00:00 UTC the following day. A queued or failed job during those windows
does not establish an application regression or a compatibility pass.

The ongoing MLX baseline and download-assistant checks now declare macOS 14,
15 and 26, verifying the actual arm64 host before running their existing tests.
Adding 26 is the first preparation step; it does not complete the retirement
migration. Keep the 14 and 15 legs and retain their results. A successful
`-target arm64-apple-macos14.0` compilation on 15 or 26 is compilation evidence,
not execution on macOS 14. Baseline GPU arithmetic and download-assistant tests
also do not qualify the complete signed app or full enhancement model.

Before retiring the 14 leg, establish an adequate legitimate macOS 14 test host
and a reviewed replacement that preserves actual minimum-OS release evidence.
Do not buy larger runners, register a new runner, relax guards or silently raise
the product minimum as part of this preparation. If current minimum-OS evidence
for changed release bytes is unavailable, record that release qualification as
unavailable and keep it open. Do not relabel a 15/26 pass as a 14 pass or remove
14 merely to make CI green. Existing qualified public 0.3.3 is unaffected.

## Styled disk image

After notarizing and stapling the app, install the build-only `ds_store`, `mac_alias` and Pillow dependencies and run `python scripts/package-dmg.py --app /path/to/Voicy.app --output /path/to/Voicy-VERSION-arm64.dmg`. Sign the resulting DMG with your Developer ID, submit it with `notarytool`, staple the accepted ticket, then validate Gatekeeper and refresh checksums. The script preserves the source app and refuses to overwrite existing output.
