# Voicy

Local speech enhancement for Apple Silicon Macs. Open a recording, enhance it with AuK, compare at the same position and export a 24-bit WAV.

- Native macOS window controls, menu bar, file dialogs and keyboard shortcuts.
- Minimal monochrome interface, built with Tauri, React and shadcn/Radix.
- AuK inference on Metal through MLX, with 32 solver steps.
- Offline processing; no account, analytics or hosted audio service.
- Original files and previous successful results remain available if processing fails.

## Requirements

Apple Silicon, macOS 14 or newer. Tested on macOS 26.6.2. Allow approximately 8 GB of storage for the full offline app and additional space for recordings; model inference uses several GB of unified memory. Intel Macs are not supported.

## Using Voicy

Open audio with **⌘O**, enhance with **⌘Return**, play/pause with **Space**, compare with **⇧⌘A**, and export with **⌘S**. Recordings are available with **⇧⌘O**. Closing the window keeps Voicy in the Dock; **⌘Q** quits it and stops its engine.

Audio formats are decoded locally. The current import limit is 20 minutes / 250 MB. Exports are mono 48 kHz PCM24; the AuK model itself operates at 24 kHz, and resampling does not restore additional bandwidth. Generative enhancement can change voice texture or damage words. Always listen to important recordings before using the result.

## Build and contribute

See [Build instructions](docs/release/BUILD.md), [macOS design and performance audit](docs/release/MACOS-AUDIT.md), and [release checks](docs/release/RELEASE.md) and [validation results](docs/release/VALIDATION.md).

The app uses the system WebKit view inside Tauri, with native macOS menus, controls and dialogs. It is not a SwiftUI application. Python and model inference run in separate processes. Source is MIT licensed; dependencies and model assets retain their own licenses. See [third-party notices](THIRD_PARTY_NOTICES.md).

Voicy is independent software and is not affiliated with Adobe, Tencent or Apple.
