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

## Styled disk image

After notarizing and stapling the app, install the build-only `ds_store`, `mac_alias` and Pillow dependencies and run `python scripts/package-dmg.py --app /path/to/Voicy.app --output /path/to/Voicy-VERSION-arm64.dmg`. Sign the resulting DMG with your Developer ID, submit it with `notarytool`, staple the accepted ticket, then validate Gatekeeper and refresh checksums. The script preserves the source app and refuses to overwrite existing output.
