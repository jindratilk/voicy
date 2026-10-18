import AppKit
import UniformTypeIdentifiers

@main
final class VoicyInstaller: NSObject, NSApplicationDelegate, NSWindowDelegate {
  private var window: NSWindow!
  private var payload: InstallerPayload?
  private var download: InstallerDownload?
  private var saved: URL?
  private let status = NSTextField(wrappingLabelWithString: "")
  private let progress = NSProgressIndicator()
  private let primary = NSButton(title: "Download offline app", target: nil, action: nil)
  private let cancel = NSButton(title: "Cancel", target: nil, action: nil)

  static func main() {
    let app = NSApplication.shared
    let delegate = VoicyInstaller()
    app.delegate = delegate
    app.setActivationPolicy(.regular)
    withExtendedLifetime(delegate) { app.run() }
  }

  func applicationDidFinishLaunching(_ notification: Notification) {
    let menu = NSMenu()
    let item = NSMenuItem()
    let appMenu = NSMenu()
    appMenu.addItem(
      withTitle: "About Voicy Installer",
      action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
    appMenu.addItem(.separator())
    appMenu.addItem(
      withTitle: "Quit Voicy Installer", action: #selector(NSApplication.terminate(_:)),
      keyEquivalent: "q")
    item.submenu = appMenu
    menu.addItem(item)
    NSApp.mainMenu = menu
    window = NSWindow(
      contentRect: NSRect(x: 0, y: 0, width: 440, height: 420),
      styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
    window.title = "Voicy Installer"
    window.delegate = self
    window.appearance = NSAppearance(named: .darkAqua)
    window.isReleasedWhenClosed = false
    window.center()
    let content = window.contentView!
    content.wantsLayer = true
    content.layer?.backgroundColor = NSColor(calibratedWhite: 0.035, alpha: 1).cgColor
    let icon = NSImageView(image: NSApp.applicationIconImage)
    icon.widthAnchor.constraint(equalToConstant: 64).isActive = true
    icon.heightAnchor.constraint(equalToConstant: 64).isActive = true
    let title = NSTextField(labelWithString: "Voicy, ready to run offline.")
    title.font = .systemFont(ofSize: 23, weight: .medium)
    let description = NSTextField(
      wrappingLabelWithString:
        "Download the complete app and speech models once. Your recordings stay on your Mac.")
    description.alignment = .center
    description.textColor = .secondaryLabelColor
    let requirements = NSTextField(
      labelWithString: "Apple Silicon · macOS 14+ · 16 GB memory recommended")
    requirements.font = .systemFont(ofSize: 11)
    requirements.textColor = .secondaryLabelColor
    status.alignment = .center
    status.font = .systemFont(ofSize: 12)
    status.textColor = .secondaryLabelColor
    progress.isIndeterminate = false
    progress.minValue = 0
    progress.maxValue = 1
    progress.setAccessibilityLabel("Download progress")
    primary.target = self
    primary.action = #selector(startOrOpen)
    primary.keyEquivalent = "\r"
    primary.bezelStyle = .rounded
    cancel.target = self
    cancel.action = #selector(cancelDownload)
    cancel.bezelStyle = .rounded
    cancel.isHidden = true
    let buttons = NSStackView(views: [primary, cancel])
    buttons.orientation = .horizontal
    buttons.spacing = 12
    let stack = NSStackView(views: [
      icon, title, description, requirements, progress, status, buttons,
    ])
    stack.orientation = .vertical
    stack.alignment = .centerX
    stack.spacing = 18
    stack.translatesAutoresizingMaskIntoConstraints = false
    content.addSubview(stack)
    NSLayoutConstraint.activate([
      stack.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 28),
      stack.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -28),
      stack.centerYAnchor.constraint(equalTo: content.centerYAnchor),
      description.widthAnchor.constraint(equalTo: stack.widthAnchor),
      status.widthAnchor.constraint(equalTo: stack.widthAnchor),
      progress.widthAnchor.constraint(equalTo: stack.widthAnchor),
    ])
    do {
      guard let url = Bundle.main.url(forResource: "payload", withExtension: "json") else {
        throw InstallerFailure.invalidPayload
      }
      let data = try JSONDecoder().decode(InstallerPayload.self, from: Data(contentsOf: url))
      try data.validate()
      payload = data
      status.stringValue =
        "Download: " + ByteCountFormatter.string(fromByteCount: data.bytes, countStyle: .file)
        + ". Allow at least 7 GB free."
    } catch {
      status.stringValue = InstallerFailure.invalidPayload.localizedDescription
      primary.isEnabled = false
    }
    window.makeKeyAndOrderFront(nil)
    NSApp.activate(ignoringOtherApps: true)
  }

  @objc private func startOrOpen() {
    if let saved {
      NSWorkspace.shared.activateFileViewerSelecting([saved])
      return
    }
    guard let payload, download == nil else { return }
    let panel = NSSavePanel()
    panel.title = "Save the complete Voicy app"
    panel.nameFieldStringValue = "Voicy-0.3.3-offline-arm64.dmg"
    panel.allowedContentTypes = [.diskImage]
    panel.canCreateDirectories = true
    panel.beginSheetModal(for: window) { [weak self] result in
      guard let self, result == .OK, let destination = panel.url else { return }
      self.primary.isEnabled = false
      self.cancel.isHidden = false
      self.status.stringValue = "Downloading and checking the release…"
      self.download = InstallerDownload(
        payload: payload, destination: destination,
        progress: { [weak self] bytes in
          DispatchQueue.main.async {
            self?.progress.doubleValue = Double(bytes) / Double(payload.bytes)
            self?.status.stringValue =
              ByteCountFormatter.string(fromByteCount: bytes, countStyle: .file) + " of "
              + ByteCountFormatter.string(fromByteCount: payload.bytes, countStyle: .file)
          }
        },
        completion: { [weak self] result in
          DispatchQueue.main.async {
            guard let self else { return }
            self.download = nil
            self.cancel.isHidden = true
            self.primary.isEnabled = true
            switch result {
            case .success(let url):
              self.saved = url
              self.primary.title = "Show in Finder"
              self.status.stringValue =
                "Verified and saved. Open the disk image in Finder, then drag Voicy to Applications."
              NSWorkspace.shared.activateFileViewerSelecting([url])
            case .failure(let error):
              self.progress.doubleValue = 0
              self.status.stringValue = error.localizedDescription
            }
          }
        })
      self.download!.start()
    }
  }

  @objc private func cancelDownload() { download?.cancel() }
  func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
  func windowShouldClose(_ sender: NSWindow) -> Bool {
    if download != nil {
      NSApp.terminate(nil)
      return false
    }
    return true
  }
  func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
    guard let download else { return .terminateNow }
    let alert = NSAlert()
    alert.messageText = "Stop downloading Voicy?"
    alert.informativeText = "The incomplete download will be removed. You can download again later."
    alert.addButton(withTitle: "Keep downloading")
    alert.addButton(withTitle: "Stop and quit")
    guard alert.runModal() == .alertSecondButtonReturn else { return .terminateCancel }
    download.cancel { DispatchQueue.main.async { NSApp.reply(toApplicationShouldTerminate: true) } }
    return .terminateLater
  }
}
