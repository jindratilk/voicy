import CoreServices
import CryptoKit
import Darwin
import Foundation

struct InstallerPayload: Codable {
  struct Part: Codable {
    let url: String
    let bytes: Int64
    let sha256: String
  }
  let version: String
  let bytes: Int64
  let sha256: String
  let parts: [Part]

  func validate() throws {
    let hash = try NSRegularExpression(pattern: "^[a-f0-9]{64}$")
    func validHash(_ s: String) -> Bool {
      hash.firstMatch(in: s, range: NSRange(s.startIndex..., in: s)) != nil
    }
    guard version == "0.3.3", bytes > 0, bytes <= 7_200_000_000, validHash(sha256), parts.count == 4
    else { throw InstallerFailure.invalidPayload }
    var total: Int64 = 0
    for (index, part) in parts.enumerated() {
      let suffix = String(format: "%03d", index + 1)
      guard part.bytes > 0, part.bytes <= 1_800_000_000, validHash(part.sha256),
        let url = URL(string: part.url), url.scheme == "https", url.host == "github.com",
        url.user == nil, url.password == nil, url.port == nil, url.query == nil,
        url.fragment == nil,
        url.path == "/jindratilk/voicy/releases/download/v0.3.3/Voicy-0.3.3-offline-arm64.dmg.part"
          + suffix
      else { throw InstallerFailure.invalidPayload }
      total += part.bytes
    }
    guard total == bytes else { throw InstallerFailure.invalidPayload }
  }
}

enum InstallerFailure: LocalizedError, Equatable {
  case invalidPayload, insufficientSpace, destinationExists, network, integrity, cancelled, write
  var errorDescription: String? {
    switch self {
    case .invalidPayload:
      return
        "This installer has invalid release information. Download a fresh copy from usevoicy.app."
    case .insufficientSpace:
      return "The selected disk needs at least 7 GB of free space. Choose another location."
    case .destinationExists:
      return
        "A file already exists at that location. Choose a different filename; the existing file was preserved."
    case .network: return "The download was interrupted. Check your connection and try again."
    case .integrity:
      return
        "The downloaded data did not match the verified release. No installer was opened. Please try again."
    case .cancelled: return "Download cancelled."
    case .write:
      return "The installer could not be saved. Check disk space and choose a writable location."
    }
  }
}

/// Uses a private same-volume replacement directory and descriptor-bound publication.
final class InstallerDownload: NSObject, URLSessionDataDelegate {
  private let payload: InstallerPayload
  private let destination: URL
  private var stagingDirectory: URL?
  private var stagingFD: Int32 = -1
  private var temporary: URL?
  private let queue = OperationQueue()
  private let configuration: URLSessionConfiguration
  private let progress: (Int64) -> Void
  private let completion: (Result<URL, Error>) -> Void
  private var handle: FileHandle?
  private var ownsTemporary = false
  private var task: URLSessionDataTask?
  private var partIndex = 0
  private var partBytes: Int64 = 0
  private var totalBytes: Int64 = 0
  private var partHash = SHA256()
  private var wholeHash = SHA256()
  private var finished = false
  private var lastProgress: TimeInterval = 0
  private lazy var session = URLSession(
    configuration: configuration, delegate: self, delegateQueue: queue)

  init(
    payload: InstallerPayload, destination: URL,
    configuration: URLSessionConfiguration = .ephemeral,
    progress: @escaping (Int64) -> Void, completion: @escaping (Result<URL, Error>) -> Void
  ) {
    self.payload = payload
    self.destination = destination
    self.configuration = configuration
    self.configuration.timeoutIntervalForResource = 4 * 60 * 60
    self.progress = progress
    self.completion = completion
    super.init()
    queue.maxConcurrentOperationCount = 1
    queue.qualityOfService = .utility
  }

  func start() {
    queue.addOperation { [self] in
      do {
        try payload.validate()
        guard !FileManager.default.fileExists(atPath: destination.path) else {
          throw InstallerFailure.destinationExists
        }
        let volume = try destination.deletingLastPathComponent().resourceValues(forKeys: [
          .volumeAvailableCapacityForImportantUsageKey
        ])
        guard let free = volume.volumeAvailableCapacityForImportantUsage,
          free > payload.bytes + 384_000_000
        else { throw InstallerFailure.insufficientSpace }
        // Apple's replacement directory is on the target volume, outside a shared destination.
        let stage = try FileManager.default.url(
          for: .itemReplacementDirectory, in: .userDomainMask,
          appropriateFor: destination.deletingLastPathComponent(), create: true)
        stagingDirectory = stage
        try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: stage.path)
        stagingFD = Darwin.open(stage.path, O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
        guard stagingFD >= 0 else { throw InstallerFailure.write }
        var directoryInfo = stat()
        guard fstat(stagingFD, &directoryInfo) == 0, directoryInfo.st_uid == geteuid(),
          directoryInfo.st_mode & 0o077 == 0
        else { throw InstallerFailure.write }
        temporary = stage.appendingPathComponent("payload.download")
        let fd = openat(
          stagingFD, "payload.download", O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0o600)
        guard fd >= 0 else { throw InstallerFailure.write }
        ownsTemporary = true
        handle = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
        nextPart()
      } catch { finish(.failure(error)) }
    }
  }

  func cancel(after: (() -> Void)? = nil) {
    queue.addOperation { [self] in
      if !finished { finish(.failure(InstallerFailure.cancelled)) }
      after?()
    }
  }

  private func nextPart() {
    partBytes = 0
    partHash = SHA256()
    var request = URLRequest(url: URL(string: payload.parts[partIndex].url)!)
    request.cachePolicy = .reloadIgnoringLocalCacheData
    request.timeoutInterval = 90
    request.setValue("application/octet-stream", forHTTPHeaderField: "Accept")
    request.setValue("identity", forHTTPHeaderField: "Accept-Encoding")
    task = session.dataTask(with: request)
    task!.resume()
  }

  func urlSession(
    _ session: URLSession, task: URLSessionTask,
    willPerformHTTPRedirection response: HTTPURLResponse,
    newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void
  ) {
    let allowed = [
      "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com",
    ]
    guard !finished, request.url?.scheme == "https", let host = request.url?.host,
      allowed.contains(host),
      request.url?.user == nil, request.url?.password == nil
    else {
      completionHandler(nil)
      finish(.failure(InstallerFailure.network))
      return
    }
    completionHandler(request)
  }

  func urlSession(
    _ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse,
    completionHandler: @escaping (URLSession.ResponseDisposition) -> Void
  ) {
    guard !finished, dataTask === task, let http = response as? HTTPURLResponse,
      http.statusCode == 200,
      response.expectedContentLength == payload.parts[partIndex].bytes
    else {
      completionHandler(.cancel)
      if !finished { finish(.failure(InstallerFailure.network)) }
      return
    }
    completionHandler(.allow)
  }

  func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
    guard !finished, dataTask === task else { return }
    guard Int64(data.count) <= payload.parts[partIndex].bytes - partBytes,
      Int64(data.count) <= payload.bytes - totalBytes
    else {
      finish(.failure(InstallerFailure.integrity))
      return
    }
    do {
      guard let handle else { throw InstallerFailure.write }
      try handle.write(contentsOf: data)
      partHash.update(data: data)
      wholeHash.update(data: data)
      partBytes += Int64(data.count)
      totalBytes += Int64(data.count)
      let now = Date.timeIntervalSinceReferenceDate
      if now - lastProgress > 0.2 {
        lastProgress = now
        progress(totalBytes)
      }
    } catch { finish(.failure(InstallerFailure.write)) }
  }

  private func hex(_ value: SHA256.Digest) -> String {
    value.map { String(format: "%02x", $0) }.joined()
  }

  func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
    guard !finished, task === self.task else { return }
    guard error == nil else {
      finish(.failure(InstallerFailure.network))
      return
    }
    guard partBytes == payload.parts[partIndex].bytes,
      hex(partHash.finalize()) == payload.parts[partIndex].sha256
    else {
      finish(.failure(InstallerFailure.integrity))
      return
    }
    partIndex += 1
    if partIndex < payload.parts.count {
      nextPart()
      return
    }
    guard totalBytes == payload.bytes, hex(wholeHash.finalize()) == payload.sha256 else {
      finish(.failure(InstallerFailure.integrity))
      return
    }
    do {
      guard let handle, let temporary else { throw InstallerFailure.write }
      try handle.synchronize()
      var verified = stat()
      var current = stat()
      guard fstat(handle.fileDescriptor, &verified) == 0,
        fstatat(stagingFD, "payload.download", &current, AT_SYMLINK_NOFOLLOW) == 0,
        verified.st_ino == current.st_ino, verified.st_dev == current.st_dev,
        verified.st_size == payload.bytes, current.st_mode & S_IFMT == S_IFREG
      else {
        throw InstallerFailure.integrity
      }
      // Add normal Internet-download quarantine; never bypass Gatekeeper or execute a download.
      let quarantine: [String: Any] = [
        kLSQuarantineAgentNameKey as String: "Voicy Installer",
        kLSQuarantineTypeKey as String: kLSQuarantineTypeWebDownload,
        kLSQuarantineTimeStampKey as String: Date(),
        kLSQuarantineOriginURLKey as String: URL(string: "https://usevoicy.app/")!,
        kLSQuarantineDataURLKey as String: URL(
          string: "https://github.com/jindratilk/voicy/releases/tag/v0.3.3")!,
      ]
      try (temporary as NSURL).setResourceValue(quarantine, forKey: .quarantinePropertiesKey)
      guard
        renameatx_np(stagingFD, "payload.download", AT_FDCWD, destination.path, UInt32(RENAME_EXCL))
          == 0
      else {
        throw FileManager.default.fileExists(atPath: destination.path)
          ? InstallerFailure.destinationExists : InstallerFailure.write
      }
      ownsTemporary = false
      try handle.close()
      self.handle = nil
      progress(totalBytes)
      finish(.success(destination))
    } catch { finish(.failure(error)) }
  }

  private func finish(_ result: Result<URL, Error>) {
    guard !finished else { return }
    finished = true
    task?.cancel()
    try? handle?.close()
    handle = nil
    // Cleanup is relative to our held private directory, never a replaceable destination path.
    if ownsTemporary && stagingFD >= 0 {
      _ = unlinkat(stagingFD, "payload.download", 0)
      ownsTemporary = false
    }
    if stagingFD >= 0 {
      Darwin.close(stagingFD)
      stagingFD = -1
    }
    if let stagingDirectory { _ = rmdir(stagingDirectory.path) }  // Only remove our empty directory.
    session.invalidateAndCancel()
    completion(result)
  }
}
