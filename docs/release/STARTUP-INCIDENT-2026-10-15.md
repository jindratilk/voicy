# Native startup incident — 15 October 2026

Resolved in public version **0.3.3**, verified 18 October 2026. The corrected complete app passes real AuK/export on clean macOS 14/15; the actual public Chrome/assistant/full-download/native import/enhance/playback/export/restart flow passes on the developer Mac. The website now redirects to the signed/notarized versioned assistant. [Current release qualification](0.3.3-CANDIDATE.md) distinguishes current bytes, scope and the retained failed candidate. The incident timeline below is historical.

The published Voicy 0.3.2 installer reaches **Audio engine startup timed out** on the tested Apple M4 Mac. The backend starts successfully, but the native launcher accepts only the literal backend version `0.3.0`; the bundled backend reports `0.3.1`. A successful worker run, valid code signature or notarization does not test this handshake.

The failure was reproduced from the full official download, whose SHA-256 is `7e23011e3169adff45be0126d1af9bed2e25338e15b69beb5550ec31d8fa3081`. The original app passed signature verification and Gatekeeper, and all 18 model-manifest entries matched. It was mounted read-only. The actual native error screen and engine-start log were retained privately. No customer recording was used.

## Source fix

The native launcher now requires a successful HTTP response identifying a healthy, local Voicy engine (`status=ok`, `app=voicy`, `local=true`). It continues to use the random per-launch port and authenticated session token. Component release strings no longer prevent a healthy bundled engine from opening the UI. Unhealthy, foreign, nonlocal, missing-field and unauthorized response shapes are rejected in regression tests.

This changes the native startup check, not model weights, solver settings, processing precision or authentication permissions. Two Rust regression tests passed on macOS, including the packaged backend's `0.3.1` version; seven frontend tests and the web production build passed.

## Native behavior validation

A development candidate was built with the fixed native shell, current frontend and the verified original read-only 0.3.2 runtime. It is **a local candidate, not a signed/notarized replacement release**. On this M4/24 GiB Mac:

- The main window opened instead of timing out, including after quitting and launching again.
- The first fixed E03 test WAV was imported through the native file picker and enhanced through the actual UI. This case was selected by order, not output quality.
- Enhanced playback advanced to the end of the 4.905-second recording; Original and Enhanced selection worked.
- Native Save exported mono 48 kHz PCM24 WAV with all 235,440 expected frames. The exported SHA-256 is `74d94f86a17771c55fef6c70f5dc0e602bb254f0f26a0f0e199c7e60ad5f7994`.
- During a second processing attempt, Quit displayed the busy confirmation; Keep Processing returned to the running job. Cancel preserved the original and previous result controls.
- Restart restored the recording/result. A second native export after cancellation/restart was byte-identical to the first export.
- After closing the main window, Window → Show Voicy restored the same recording/result UI.

This is one short-file workflow, not all formats, long-form reliability, subjective sound quality, a second-Mac install or full release qualification. Test inputs and exports remain outside Git. The E03 source attribution and limitations still apply.

## Website containment

The incident change pauses the website's download route before any artifact probe or redirect, returning a human-readable `503`, `noindex` and a bodyless HEAD. Home/comparison CTAs show download status and a concise notice; the prerecorded demo remains usable. Tests also cover a configured, reachable artifact to ensure the pause cannot accidentally redirect to the broken installer.

The original Cloudflare worker can still serve the preserved artifact directly; this website containment is not a claim that all historic direct links are disabled. A `v=0.3.0` query was inspected by HEAD and still returned the 0.3.2 filename/size, so it was rejected as a rollback route without downloading it.

## Outstanding release requirements

No valid local Developer ID signing identity was available (`security find-identity -v -p codesigning` returned zero). No accessible repository Actions secrets were listed for a signing pipeline. This does not establish what credentials may exist on another Mac.

Before resuming public downloads:

1. Review/merge the source fix, build a versioned candidate from that exact source, and complete the remaining release checks in [RELEASE.md](RELEASE.md), including an independent second-Mac install. Local window reopen was also verified after the initial candidate tests.
2. Use an authorized Developer ID signing environment, sign nested code/application, notarize and staple, package the DMG, then sign/notarize/staple it and verify signatures/tickets/Gatekeeper.
3. Publish the verified replacement artifact with checksums, verify a complete public download and native startup/import/enhance/export from that exact downloaded artifact.
4. Update release/version metadata and remove the explicit download pause only after those checks pass. Preserve the original artifact and incident evidence.

Do not publish the development candidate as a notarized fix, remove the pause merely because CI is green, or count technical worker evidence as native release verification. No passwords, signing keys or account exports belong in Git or chat.

## Production containment checkpoint

PR #4 merged with all CI checks passing. The website containment was verified at production source `4df60b7c8a1a62c407bd59191bbb7ed815dd3c10` on desktop, 390px and 320px mobile: indexable pages remain 200, the pause is visible, and download GET/HEAD is 503 without artifact redirect. HEAD has no body. Demo playback still works. These production checks had no metrics/API fixtures. Cloudflare CLI and Chrome were not authenticated, so distribution access also remains outstanding. No signed replacement has been published.
