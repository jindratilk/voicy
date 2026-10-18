import CryptoKit
import Foundation

private final class FixtureProtocol: URLProtocol {
  enum Mode { case valid, corrupt, truncated, wrongStatus, hang, collision }
  static var mode = Mode.valid
  static var parts: [Data] = []
  static var collision: (() -> Void)?
  override class func canInit(with request: URLRequest) -> Bool { true }
  override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
  override func startLoading() {
    let index = Int(request.url!.lastPathComponent.suffix(3))! - 1
    let mode = Self.mode
    var bytes = Self.parts[index]
    if mode == .collision { Self.collision?() }
    let response = HTTPURLResponse(
      url: request.url!, statusCode: mode == .wrongStatus ? 503 : 200, httpVersion: "HTTP/1.1",
      headerFields: ["Content-Length": String(bytes.count)])!
    client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
    if mode == .corrupt { bytes[0] ^= 1 }
    if mode == .truncated { bytes.removeLast() }
    if mode == .hang {
      client?.urlProtocol(self, didLoad: bytes.prefix(bytes.count / 2))
      return
    }
    client?.urlProtocol(self, didLoad: bytes)
    client?.urlProtocolDidFinishLoading(self)
  }
  override func stopLoading() {}
}

@main
struct DownloadCoreTests {
  static func hash(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
  }
  static func main() throws {
    let root = FileManager.default.temporaryDirectory.appendingPathComponent(
      "voicy-installer-test-" + UUID().uuidString)
    try FileManager.default.createDirectory(at: root, withIntermediateDirectories: false)
    defer { try? FileManager.default.removeItem(at: root) }
    let parts = (1...4).map { Data(repeating: UInt8($0), count: 131072) }
    FixtureProtocol.parts = parts
    let all = parts.reduce(into: Data()) { $0.append($1) }
    let payload = InstallerPayload(
      version: "0.3.3", bytes: Int64(all.count), sha256: hash(all),
      parts: parts.enumerated().map { i, data in
        InstallerPayload.Part(
          url:
            "https://github.com/jindratilk/voicy/releases/download/v0.3.3/Voicy-0.3.3-offline-arm64.dmg.part"
            + String(format: "%03d", i + 1), bytes: Int64(data.count), sha256: hash(data))
      })
    try payload.validate()
    let sentinel = root.appendingPathComponent("keep.txt")
    try Data("user data".utf8).write(to: sentinel)
    var passed: [String] = []
    for mode in [FixtureProtocol.Mode.valid, .corrupt, .truncated, .wrongStatus, .hang, .collision]
    {
      FixtureProtocol.mode = mode
      let target = root.appendingPathComponent("result-" + String(passed.count) + ".dmg")
      FixtureProtocol.collision = { try! Data("preserve collision".utf8).write(to: target) }
      let done = DispatchSemaphore(value: 0)
      var result: Result<URL, Error>?
      var worker: InstallerDownload!
      let configuration = URLSessionConfiguration.ephemeral
      configuration.protocolClasses = [FixtureProtocol.self]
      worker = InstallerDownload(
        payload: payload, destination: target, configuration: configuration,
        progress: { _ in if mode == .hang { worker.cancel() } },
        completion: { r in
          result = r
          done.signal()
        })
      worker.start()
      precondition(done.wait(timeout: .now() + 15) == .success, "download test timed out")
      switch result! {
      case .success(let url):
        precondition(mode == .valid)
        precondition(try! Data(contentsOf: url) == all)
        let props = try url.resourceValues(forKeys: [.quarantinePropertiesKey])
        precondition(props.quarantineProperties != nil)
        passed.append("complete file matches every part and whole SHA; quarantine applied")
      case .failure(let error):
        precondition(mode != .valid)
        if mode == .collision {
          precondition(try! Data(contentsOf: target) == Data("preserve collision".utf8))
          precondition(error as? InstallerFailure == .destinationExists)
        } else {
          precondition(!FileManager.default.fileExists(atPath: target.path))
        }
        if mode == .hang { precondition(error as? InstallerFailure == .cancelled) }
        passed.append("reject/clean " + String(describing: mode))
      }
      precondition(
        try! FileManager.default.contentsOfDirectory(atPath: root.path).allSatisfy {
          !$0.hasPrefix(".Voicy-")
        })
      precondition(try! Data(contentsOf: sentinel) == Data("user data".utf8))
    }
    // Reject a pre-existing destination before any request, preserving its bytes.
    let config = URLSessionConfiguration.ephemeral
    config.protocolClasses = [FixtureProtocol.self]
    let done = DispatchSemaphore(value: 0)
    var preserved = false
    let worker = InstallerDownload(
      payload: payload, destination: sentinel, configuration: config, progress: { _ in },
      completion: { r in
        if case .failure(let e) = r { preserved = e as? InstallerFailure == .destinationExists }
        done.signal()
      })
    worker.start()
    precondition(done.wait(timeout: .now() + 15) == .success)
    precondition(preserved)
    precondition(try! Data(contentsOf: sentinel) == Data("user data".utf8))
    passed.append("pre-existing destination is never overwritten")
    let wrong = InstallerPayload(
      version: payload.version, bytes: payload.bytes, sha256: String(repeating: "0", count: 64),
      parts: payload.parts)
    FixtureProtocol.mode = .valid
    let badTarget = root.appendingPathComponent("bad-whole.dmg")
    let badDone = DispatchSemaphore(value: 0)
    var rejected = false
    let badWorker = InstallerDownload(
      payload: wrong, destination: badTarget, configuration: config, progress: { _ in },
      completion: { r in
        if case .failure(let e) = r { rejected = e as? InstallerFailure == .integrity }
        badDone.signal()
      })
    badWorker.start()
    precondition(badDone.wait(timeout: .now() + 15) == .success)
    precondition(rejected && !FileManager.default.fileExists(atPath: badTarget.path))
    passed.append("whole-hash mismatch rejected even with valid parts")
    print(
      String(
        data: try JSONSerialization.data(
          withJSONObject: ["passed": passed], options: .prettyPrinted), encoding: .utf8)!)
  }
}
