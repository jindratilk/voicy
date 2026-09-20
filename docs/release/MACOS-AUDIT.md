# macOS implementation audit

Reviewed 20 September 2026. Primary sources:

- [Apple: Designing for macOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-macos/): standard window controls, resizing, full screen, menus, file workflows and keyboard access.
- [Apple: Toolbars](https://developer.apple.com/design/human-interface-guidelines/toolbars): integrate the toolbar into the window frame; give controls space and avoid overcrowding.
- [Apple: Minimize Timer Usage](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/power_efficiency_guidelines_osx/Timers.html): event notifications instead of perpetual polling.
- [Apple: App icons](https://developer.apple.com/design/human-interface-guidelines/app-icons): consistent silhouette, recognizability and appropriate optical margins.
- [Tauri configuration](https://v2.tauri.app/reference/config/): public overlay titlebar and traffic-light positioning APIs, without private macOS APIs.
- [Tauri menus](https://v2.tauri.app/learn/window-menu/): native application menus, standard editing actions and accelerators.
- [Tauri signing](https://v2.tauri.app/distribute/sign/macos/) and [Apple notarization](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution): Developer ID, hardened runtime, nested code signing, notarization and stapling are distinct steps.

## Applied

A single 64-point draggable titlebar replaces the duplicated browser-style header. macOS supplies the actual close/minimize/full-screen buttons. The title is centered; history remains an icon. The body has no marketing text or outlined cards. Window resizing, full-screen, Dock reopen, standard menus and keyboard shortcuts use platform APIs. Closing the window hides it while processing continues; Quit warns when an operation is running.

The audio engine runs outside the UI process. Startup does not import PyTorch or MLX. Server-sent events replace 1.2-second history polling. The player uses one metadata-preloaded audio element and preserves time across A/B switches. Exports stream to a temporary file beside the destination before atomic replacement. The application gets its own random loopback port and authenticated session, avoiding accidental reuse of old app servers. Library deletion is recoverable under `.trash`.

The release bundle owns Python, FFmpeg, model source and weights. User recordings and mutable preferences live in Application Support. No developer virtual environment, Homebrew executable or source checkout is required at runtime. Logs rotate at 5 MB and can be opened from Help.

## Scope

Voicy remains a Tauri application with a system WebKit view; it is not a SwiftUI rewrite. The integration uses native macOS windows, menus and dialogs. The generative AuK model can alter vocal identity or words; interface polish and software tests do not prove perfect speech restoration. The full offline build is large because it includes model weights. Intel Macs are not supported by the MLX engine.
