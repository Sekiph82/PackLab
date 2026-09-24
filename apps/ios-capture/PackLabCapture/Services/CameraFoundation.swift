import CryptoKit
import Foundation
#if canImport(ImageIO)
import ImageIO
#endif

public enum PreviewSurfaceState: Sendable, Equatable {
    case loading
    case running
    case denied
    case restricted
    case simulatorUnavailable
    case unavailable
    case error(String)
}

/// Framework-free lifecycle policy used by the preview adapter and its tests.
public struct PreviewLifecyclePolicy: Sendable, Equatable {
    public private(set) var isStarted = false
    public private(set) var attachmentCount = 0

    public init() {}

    public var canStart: Bool { !isStarted }

    public mutating func beginAuthorizedStart(_ status: CameraAuthorizationStatus) -> Bool {
        guard status == .authorized, !isStarted else { return false }
        return true
    }

    public mutating func markStartedAfterSuccessfulStart() {
        isStarted = true
    }

    @discardableResult
    public mutating func startIfNeeded() -> Bool {
        guard !isStarted else { return false }
        isStarted = true
        return true
    }

    @discardableResult
    public mutating func stopIfNeeded() -> Bool {
        guard isStarted else { return false }
        isStarted = false
        return true
    }

    public mutating func attach() { attachmentCount += 1 }
    public mutating func detach() { attachmentCount = max(0, attachmentCount - 1) }

    @discardableResult
    public mutating func attachIfNeeded() -> Bool {
        guard attachmentCount == 0 else { return false }
        attach()
        return true
    }

    @discardableResult
    public mutating func detachIfNeeded() -> Bool {
        guard attachmentCount > 0 else { return false }
        detach()
        return true
    }
}

/// Platform-neutral driver used by the UIKit bridge.  Keeping the lifecycle
/// contract here makes the real controller testable without manufacturing an
/// AVCaptureSession on a developer workstation.
@MainActor
public protocol PreviewSessionDriver: AnyObject {
    var isAttached: Bool { get }
    var isRunning: Bool { get }
    func attach() throws
    func detach()
    func start() throws
    func stop()
}

@MainActor
public final class PreviewBridgeController {
    private let driver: any PreviewSessionDriver
    private var lifecycle = PreviewLifecyclePolicy()
    public private(set) var state: PreviewSurfaceState = .loading
    public var onStateChange: ((PreviewSurfaceState) -> Void)?

    public init(driver: any PreviewSessionDriver) { self.driver = driver }

    public func appear(authorization: CameraAuthorizationStatus) {
        switch authorization {
        case .denied:
            stopAndDetach(); publish(.denied)
        case .restricted:
            stopAndDetach(); publish(.restricted)
        case .unknown:
            publish(.loading)
        case .authorized:
            startAuthorized()
        }
    }

    public func disappear() {
        stopAndDetach()
        publish(.loading)
    }

    public func restart(authorization: CameraAuthorizationStatus) {
        stopAndDetach()
        guard authorization == .authorized else { appear(authorization: authorization); return }
        startAuthorized()
    }

    private func startAuthorized() {
        guard lifecycle.beginAuthorizedStart(.authorized) else { return }
        do {
            if lifecycle.attachIfNeeded() { try driver.attach() }
            try driver.start()
            lifecycle.markStartedAfterSuccessfulStart()
            publish(.running)
        } catch {
            _ = lifecycle.stopIfNeeded()
            driver.stop()
            if lifecycle.detachIfNeeded() { driver.detach() }
            publish(.error((error as NSError).localizedDescription))
        }
    }

    private func stopAndDetach() {
        if lifecycle.stopIfNeeded() { driver.stop() }
        if lifecycle.detachIfNeeded() { driver.detach() }
    }

    private func publish(_ next: PreviewSurfaceState) {
        state = next
        onStateChange?(next)
    }
}

public enum PreviewAuthorizationResolver {
    public static func state(for status: CameraAuthorizationStatus) -> PreviewSurfaceState {
        switch status {
        case .unknown: return .loading
        case .authorized: return .loading
        case .denied: return .denied
        case .restricted: return .restricted
        }
    }

    public static func state(for error: CameraServiceError) -> PreviewSurfaceState {
        switch error {
        case .permissionDenied: return .denied
        case .restricted: return .restricted
        case .unavailable: return .unavailable
        case .failed(let message): return .error(message)
        }
    }
}

public enum CameraPosition: String, Sendable, Equatable, Codable {
    case front
    case back
    case unspecified
}

public enum CameraDeviceKind: String, Sendable, Equatable, Codable {
    case wideAngle
    case ultraWide
    case telephoto
    case dual
    case dualWide
    case triple
    case other
}

public struct CameraDeviceDescriptor: Sendable, Equatable, Codable {
    public let position: CameraPosition
    public let kind: CameraDeviceKind
    public let stableID: String

    public init(position: CameraPosition, kind: CameraDeviceKind, stableID: String) {
        self.position = position
        self.kind = kind
        self.stableID = stableID
    }
}

public struct CameraLensIdentity: Sendable, Equatable, Codable {
    public let identifier: String
    public let position: CameraPosition
    public let kind: CameraDeviceKind

    public init(identifier: String, position: CameraPosition, kind: CameraDeviceKind) {
        self.identifier = identifier
        self.position = position
        self.kind = kind
    }
}

public enum CameraSelectionResult: Sendable, Equatable {
    case selected(CameraLensIdentity)
    case unavailable
    case ambiguous([CameraDeviceDescriptor])
    case unsupported
}

public enum CameraDeviceSelector {
    public static func selectMainRearWide(from candidates: [CameraDeviceDescriptor]) -> CameraSelectionResult {
        let rearWide = candidates.filter { $0.position == .back && $0.kind == .wideAngle }
        guard !rearWide.isEmpty else { return candidates.isEmpty ? .unavailable : .unsupported }
        guard rearWide.count == 1, let selected = rearWide.first else { return .ambiguous(rearWide) }
        return .selected(CameraLensIdentity(identifier: selected.stableID, position: selected.position, kind: selected.kind))
    }
}

public struct CaptureDimensions: Sendable, Equatable, Codable {
    public let width: Int
    public let height: Int
    public init(width: Int, height: Int) { self.width = width; self.height = height }
}

public struct AcceptedStill: Sendable, Equatable {
    public let captureID: String
    public let sourceBytes: Data
    public let dimensions: CaptureDimensions
    public let capturedAt: Date
    public let monotonicTimestamp: TimeInterval?
    public init(captureID: String, sourceBytes: Data, dimensions: CaptureDimensions, capturedAt: Date, monotonicTimestamp: TimeInterval? = nil) {
        self.captureID = captureID; self.sourceBytes = sourceBytes; self.dimensions = dimensions; self.capturedAt = capturedAt; self.monotonicTimestamp = monotonicTimestamp
    }
}

public enum StillCaptureResult: Sendable, Equatable {
    case accepted(AcceptedStill)
    case rejected(String)
}

public actor StillCaptureGate {
    private var inFlight = false
    public init() {}
    public func begin() -> Bool { guard !inFlight else { return false }; inFlight = true; return true }
    public func end() { inFlight = false }
    public func isBusy() -> Bool { inFlight }
}

/// Deterministic capture completion guard shared by the delegate adapter and
/// its injected tests. Exactly one terminal result is allowed for a request.
public struct StillCaptureLifecycle: Sendable, Equatable {
    public enum State: Sendable, Equatable { case idle, inFlight, accepted, failed }
    public private(set) var state: State = .idle
    public init() {}
    public mutating func begin() -> Bool {
        guard state == .idle else { return false }
        state = .inFlight
        return true
    }
    public mutating func complete(success: Bool) -> Bool {
        guard state == .inFlight else { return false }
        state = success ? .accepted : .failed
        return true
    }
    public mutating func reset() { state = .idle }
}

public protocol StillPhotoBackend: Sendable {
    func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions)
}

public protocol TimestampedStillPhotoBackend: StillPhotoBackend {
    func lastCaptureMonotonicTimestamp() async -> TimeInterval?
}

@MainActor
public protocol StillPhotoDriverDelegate: AnyObject {
    func stillPhotoDriver(_ driver: any StillPhotoDriver, didFinish bytes: Data, dimensions: CaptureDimensions)
    func stillPhotoDriverDidFinishWithoutData(_ driver: any StillPhotoDriver)
}

@MainActor
public protocol StillPhotoDriver: AnyObject {
    var canCapturePhoto: Bool { get }
    var delegate: (any StillPhotoDriverDelegate)? { get set }
    func capturePhoto()
    func cancelPhotoCapture()
}

/// The exact-once continuation boundary shared by the production NextLevel
/// adapter and injected driver tests.  The driver is deliberately tiny: the
/// Apple framework remains an outer adapter while this object owns admission,
/// cancellation, duplicate callbacks and lens identity checks.
@MainActor
public final class StillPhotoAdapterCore: NSObject, TimestampedStillPhotoBackend, StillPhotoDriverDelegate {
    private let driver: any StillPhotoDriver
    public let selectedLens: CameraLensIdentity
    private let activeLensIdentifier: () -> String?
    private var continuation: CheckedContinuation<(bytes: Data, dimensions: CaptureDimensions), Error>?
    private var lastCaptureTimestamp: TimeInterval?

    public init(driver: any StillPhotoDriver, selectedLens: CameraLensIdentity, activeLensIdentifier: @escaping () -> String?) {
        self.driver = driver
        self.selectedLens = selectedLens
        self.activeLensIdentifier = activeLensIdentifier
        super.init()
        driver.delegate = self
    }

    public func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) {
        guard continuation == nil else { throw CameraServiceError.failed("capture_in_flight") }
        guard activeLensIdentifier() == selectedLens.identifier else { throw CameraServiceError.failed("selected_lens_mismatch") }
        guard driver.canCapturePhoto else { throw CameraServiceError.unavailable }
        lastCaptureTimestamp = nil
        return try await withTaskCancellationHandler(operation: {
            try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<(bytes: Data, dimensions: CaptureDimensions), Error>) in
                self.continuation = continuation
                self.driver.capturePhoto()
            }
        }, onCancel: { [weak self] in
            Task { @MainActor in self?.cancel(reason: "capture_cancelled") }
        })
    }

    public func cancel(reason: String = "session_stopped") {
        driver.cancelPhotoCapture()
        finish(.failure(CameraServiceError.failed(reason)))
    }

    public func lastCaptureMonotonicTimestamp() async -> TimeInterval? { lastCaptureTimestamp }

    public func stillPhotoDriver(_ driver: any StillPhotoDriver, didFinish bytes: Data, dimensions: CaptureDimensions) {
        guard !bytes.isEmpty, dimensions.width > 0, dimensions.height > 0 else {
            finish(.failure(CameraServiceError.failed("photo_data_or_dimensions_missing")))
            return
        }
        lastCaptureTimestamp = ProcessInfo.processInfo.systemUptime
        finish(.success((bytes: bytes, dimensions: dimensions)))
    }

    public func stillPhotoDriverDidFinishWithoutData(_ driver: any StillPhotoDriver) {
        finish(.failure(CameraServiceError.failed("photo_capture_completed_without_data")))
    }

    private func finish(_ result: Result<(bytes: Data, dimensions: CaptureDimensions), Error>) {
        guard let continuation else { return }
        self.continuation = nil
        continuation.resume(with: result)
    }
}

public actor HealthGatedStillPhotoBackend: TimestampedStillPhotoBackend {
    private let backend: any StillPhotoBackend
    private var admission = CaptureAdmissionController()
    public init(backend: any StillPhotoBackend) { self.backend = backend }
    public func update(_ admission: CaptureAdmissionController) { self.admission = admission }
    public func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) {
        guard admission.allowsCapture else { throw CameraServiceError.failed(admission.rejectReason() ?? "capture_blocked") }
        return try await backend.requestOriginalStill()
    }
    public func lastCaptureMonotonicTimestamp() async -> TimeInterval? {
        guard let timestamped = backend as? any TimestampedStillPhotoBackend else { return nil }
        return await timestamped.lastCaptureMonotonicTimestamp()
    }
}

/// The capture-runtime-owned admission boundary.  DeviceHealthMonitor updates
/// this same instance; callers cannot bypass the hard-stop by invoking the
/// underlying photo backend directly.
public actor AdmissionControlledStillCaptureService {
    private let service: HighResolutionStillCaptureService
    private let gatedBackend: HealthGatedStillPhotoBackend
    public init(backend: any StillPhotoBackend) {
        gatedBackend = HealthGatedStillPhotoBackend(backend: backend)
        service = HighResolutionStillCaptureService(backend: gatedBackend)
    }
    public func updateAdmission(_ admission: CaptureAdmissionController) async { await gatedBackend.update(admission) }
    public func capture(now: Date = Date(), captureID: String = UUID().uuidString) async -> StillCaptureResult { await service.capture(now: now, captureID: captureID) }
}

public actor HighResolutionStillCaptureService {
    private let backend: any StillPhotoBackend
    private let gate = StillCaptureGate()
    public init(backend: any StillPhotoBackend) { self.backend = backend }

    public func capture(now: Date = Date(), captureID: String = UUID().uuidString) async -> StillCaptureResult {
        guard await gate.begin() else { return .rejected("capture_in_flight") }
        defer { Task { await gate.end() } }
        do {
            let source = try await backend.requestOriginalStill()
            guard !source.bytes.isEmpty, source.dimensions.width > 0, source.dimensions.height > 0 else {
                return .rejected("invalid_source")
            }
            let timestamp: TimeInterval
            if let timestamped = backend as? any TimestampedStillPhotoBackend { timestamp = await timestamped.lastCaptureMonotonicTimestamp() ?? ProcessInfo.processInfo.systemUptime }
            else { timestamp = ProcessInfo.processInfo.systemUptime }
            return .accepted(AcceptedStill(captureID: captureID, sourceBytes: source.bytes, dimensions: source.dimensions, capturedAt: now, monotonicTimestamp: timestamp))
        } catch { return .rejected("capture_failed") }
    }
}

/// Production accepted-still boundary.  The source record is derived from
/// the captured bytes before the immutable source is persisted, so metadata
/// cannot be supplied by a nearby test helper or caller-side placeholder.
public actor AcceptedStillCapturePipeline {
    private let service: HighResolutionStillCaptureService
    private let sourceStore: OriginalSourceStore
    public init(backend: any StillPhotoBackend, sourceRoot: URL) {
        service = HighResolutionStillCaptureService(backend: backend)
        sourceStore = OriginalSourceStore(root: sourceRoot)
    }

    public func captureAndPersist(captureID: String, filename: String, orientation: String = "unknown", now: Date = Date()) async throws -> (still: AcceptedStill, source: OriginalSourceRecord) {
        let result = await service.capture(now: now, captureID: captureID)
        guard case .accepted(let still) = result else { throw CameraServiceError.failed("capture_rejected") }
        let source = try OriginalSourceRecord.fromSource(captureID: still.captureID, filename: filename, dimensions: still.dimensions, orientation: orientation, bytes: still.sourceBytes)
        _ = try await sourceStore.persist(record: source, bytes: still.sourceBytes)
        return (still, source)
    }
}

public enum SourceValueStatus: String, Codable, Sendable { case available, unavailable, notRecorded = "not_recorded", estimated }

public struct SourceMeasurement: Codable, Sendable, Equatable {
    public let status: SourceValueStatus
    public let value: Double?
    public let unit: String?
    public let source: String?
    public init(status: SourceValueStatus, value: Double? = nil, unit: String? = nil, source: String? = nil) {
        self.status = status; self.value = value; self.unit = unit; self.source = source
    }
}

public struct OriginalSourceRecord: Codable, Sendable, Equatable {
    public let captureID: String
    public let filename: String
    public let dimensions: CaptureDimensions
    public let orientation: String
    public let sha256: String
    public let metadataBytes: Data
    public init(captureID: String, filename: String, dimensions: CaptureDimensions, orientation: String, sha256: String, metadataBytes: Data = Data()) {
        self.captureID = captureID; self.filename = filename; self.dimensions = dimensions; self.orientation = orientation; self.sha256 = sha256; self.metadataBytes = metadataBytes
    }

    public static func fromSource(captureID: String, filename: String, dimensions: CaptureDimensions, orientation: String, bytes: Data) throws -> OriginalSourceRecord {
        if let decoded = SourceMetadataExtractor.decodedDimensions(from: bytes), decoded != dimensions { throw SourceMetadataError.dimensionMismatch }
        OriginalSourceRecord(captureID: captureID, filename: filename, dimensions: dimensions, orientation: orientation, sha256: SourceIntegrity.digest(bytes), metadataBytes: try SourceMetadataExtractor.extract(from: bytes))
    }
}

public enum SourceIntegrityError: Error, Sendable, Equatable { case empty, digestMismatch, dimensionMismatch, sourceOverwritten }

public enum SourceIntegrity {
    public static func digest(_ bytes: Data) -> String { SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined() }

    public static func validate(record: OriginalSourceRecord, bytes: Data, dimensions: CaptureDimensions) throws {
        guard !bytes.isEmpty else { throw SourceIntegrityError.empty }
        guard record.sha256 == digest(bytes) else { throw SourceIntegrityError.digestMismatch }
        guard record.dimensions == dimensions else { throw SourceIntegrityError.dimensionMismatch }
    }

    public static func derivativePath(for record: OriginalSourceRecord) -> String {
        "previews/\(record.captureID)-thumbnail.jpg"
    }

    public static func validateDerivative(_ derivative: URL, master: URL, fileManager: FileManager = .default) throws {
        guard derivative.standardizedFileURL != master.standardizedFileURL else { throw SourceIntegrityError.sourceOverwritten }
        guard !derivative.standardizedFileURL.path.hasPrefix(master.deletingLastPathComponent().standardizedFileURL.path + "/") || derivative.standardizedFileURL != master.standardizedFileURL else { throw SourceIntegrityError.sourceOverwritten }
        _ = fileManager
    }
}

public enum SourceMetadataError: Error, Sendable, Equatable { case unsupported, malformed, dimensionMismatch }

public enum SourceMetadataExtractor {
    public static func extract(from bytes: Data) throws -> Data {
        #if canImport(ImageIO)
        guard let source = CGImageSourceCreateWithData(bytes as CFData, nil), CGImageSourceGetCount(source) > 0 else { throw SourceMetadataError.unsupported }
        guard let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) else { throw SourceMetadataError.malformed }
        return try PropertyListSerialization.data(fromPropertyList: properties, format: .binary, options: 0)
        #else
        guard !bytes.isEmpty else { throw SourceMetadataError.unsupported }
        return Data()
        #endif
    }

    public static func decodedDimensions(from bytes: Data) -> CaptureDimensions? {
        #if canImport(ImageIO)
        guard let source = CGImageSourceCreateWithData(bytes as CFData, nil), let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any], let width = properties[kCGImagePropertyPixelWidth] as? NSNumber, let height = properties[kCGImagePropertyPixelHeight] as? NSNumber else { return nil }
        return CaptureDimensions(width: width.intValue, height: height.intValue)
        #else
        return nil
        #endif
    }
}

public enum SourcePersistenceError: Error, Sendable, Equatable { case invalidName, sourceOverwritten, recordWriteFailed }

/// Persists the immutable original and its source record together. The source
/// file is never replaced; derivatives are intentionally outside this API.
public actor OriginalSourceStore {
    private let root: URL
    private let fileManager: FileManager

    public init(root: URL, fileManager: FileManager = .default) {
        self.root = root
        self.fileManager = fileManager
    }

    public func persist(record: OriginalSourceRecord, bytes: Data) throws -> URL {
        guard !record.captureID.isEmpty,
              record.captureID.allSatisfy({ $0.isLetter || $0.isNumber || $0 == "-" || $0 == "_" }),
              !record.filename.isEmpty,
              !record.filename.contains("/"),
              !record.filename.contains("\\") else { throw SourcePersistenceError.invalidName }
        try fileManager.createDirectory(at: root, withIntermediateDirectories: true)
        try SourceIntegrity.validate(record: record, bytes: bytes, dimensions: record.dimensions)
        let sourceURL = root.appendingPathComponent(record.filename)
        if fileManager.fileExists(atPath: sourceURL.path) {
            guard let existing = try? Data(contentsOf: sourceURL), SourceIntegrity.digest(existing) == record.sha256 else {
                throw SourcePersistenceError.sourceOverwritten
            }
            guard let existingRecord = try? load(recordID: record.captureID), existingRecord == record else { throw SourcePersistenceError.recordWriteFailed }
            return sourceURL
        }
        if let decoded = SourceMetadataExtractor.decodedDimensions(from: bytes), decoded != record.dimensions { throw SourcePersistenceError.recordWriteFailed }
        do {
            try bytes.write(to: sourceURL, options: .atomic)
            let recordURL = root.appendingPathComponent("\(record.captureID).source.json")
            let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
            try encoder.encode(record).write(to: recordURL, options: .atomic)
            return sourceURL
        } catch {
            try? fileManager.removeItem(at: sourceURL)
            throw SourcePersistenceError.recordWriteFailed
        }
    }

    public func load(recordID: String) throws -> OriginalSourceRecord {
        let url = root.appendingPathComponent("\(recordID).source.json")
        guard let data = try? Data(contentsOf: url), let record = try? JSONDecoder().decode(OriginalSourceRecord.self, from: data) else {
            throw SourcePersistenceError.recordWriteFailed
        }
        return record
    }
}

public struct PhotoCaptureMetadata: Codable, Sendable, Equatable {
    public let photoID: String
    public let imagePath: String
    public let sequence: Int
    public let originalFilename: String
    public let pixelDimensions: CaptureDimensions
    public let orientation: String
    public let lensIdentity: CameraLensIdentity
    public let focalLengthMM: SourceMeasurement
    public let exposureSeconds: SourceMeasurement
    public let iso: SourceMeasurement
    public let whiteBalanceKelvin: SourceMeasurement
    public let captureTimestamp: Date
    public init(photoID: String, imagePath: String, sequence: Int, originalFilename: String, pixelDimensions: CaptureDimensions, orientation: String, lensIdentity: CameraLensIdentity, focalLengthMM: SourceMeasurement, exposureSeconds: SourceMeasurement, iso: SourceMeasurement, whiteBalanceKelvin: SourceMeasurement, captureTimestamp: Date) {
        self.photoID = photoID; self.imagePath = imagePath; self.sequence = sequence; self.originalFilename = originalFilename; self.pixelDimensions = pixelDimensions; self.orientation = orientation; self.lensIdentity = lensIdentity; self.focalLengthMM = focalLengthMM; self.exposureSeconds = exposureSeconds; self.iso = iso; self.whiteBalanceKelvin = whiteBalanceKelvin; self.captureTimestamp = captureTimestamp
    }
}

public enum AcceptedPhotoMetadataFactory {
    public static func withCaptureReadings(
        _ metadata: PhotoCaptureMetadata,
        exposure: ExposureCaptureBinding?,
        whiteBalance: WhiteBalanceCaptureBinding?
    ) -> PhotoCaptureMetadata {
        PhotoCaptureMetadata(
            photoID: metadata.photoID, imagePath: metadata.imagePath, sequence: metadata.sequence,
            originalFilename: metadata.originalFilename, pixelDimensions: metadata.pixelDimensions,
            orientation: metadata.orientation, lensIdentity: metadata.lensIdentity,
            focalLengthMM: metadata.focalLengthMM,
            exposureSeconds: exposure.map { SourceMeasurement(status: .available, value: $0.reading.exposureSeconds, unit: "s", source: "device_api") } ?? metadata.exposureSeconds,
            iso: exposure.map { SourceMeasurement(status: .available, value: Double($0.reading.iso), unit: "iso", source: "device_api") } ?? metadata.iso,
            whiteBalanceKelvin: whiteBalance.map { SourceMeasurement(status: .available, value: $0.reading.temperatureKelvin, unit: "K", source: "device_api") } ?? metadata.whiteBalanceKelvin,
            captureTimestamp: metadata.captureTimestamp
        )
    }
}

public enum PackScanOrientationValue: String, Codable, Sendable { case portrait, landscape, square, unknown }
public enum PackScanMeasurementSource: String, Codable, Sendable { case exif, deviceAPI = "device_api", operator, derived, unknown }

public struct PackScanNumericMeasurement: Codable, Sendable, Equatable {
    public let status: SourceValueStatus
    public let value: Double?
    public let unit: String?
    public let source: PackScanMeasurementSource?
    public init(status: SourceValueStatus, value: Double? = nil, unit: String? = nil, source: PackScanMeasurementSource? = nil) {
        self.status = status; self.value = value; self.unit = unit; self.source = source
    }
}

public struct PackScanISOMeasurement: Codable, Sendable, Equatable {
    public let status: SourceValueStatus
    public let value: Int?
    public let unit: String?
    public let source: PackScanMeasurementSource?
    public init(status: SourceValueStatus, value: Int? = nil, unit: String? = nil, source: PackScanMeasurementSource? = nil) {
        self.status = status; self.value = value; self.unit = unit; self.source = source
    }
}

public struct PackScanOrientation: Codable, Sendable, Equatable {
    public let value: PackScanOrientationValue
    public let rotationDegrees: Int?
    public let source: PackScanMeasurementSource
    public init(value: PackScanOrientationValue, rotationDegrees: Int? = nil, source: PackScanMeasurementSource) {
        self.value = value; self.rotationDegrees = rotationDegrees; self.source = source
    }
    enum CodingKeys: String, CodingKey { case value, rotationDegrees = "rotation_degrees", source }
}

/// Strict M02 PackScan wire object. App-only lens/timestamp values remain in
/// this separate internal record and are never encoded into the photo object.
public struct PackScanPhotoMetadataWire: Codable, Sendable, Equatable {
    public let photoID: String
    public let imagePath: String
    public let sequence: Int
    public let originalFilename: String
    public let pixelDimensions: CaptureDimensions
    public let orientation: PackScanOrientation
    public let focalLengthMM: PackScanNumericMeasurement
    public let exposure: PackScanNumericMeasurement
    public let iso: PackScanISOMeasurement
    public let whiteBalanceKelvin: PackScanNumericMeasurement

    public init(photoID: String, imagePath: String, sequence: Int, originalFilename: String, pixelDimensions: CaptureDimensions, orientation: PackScanOrientation, focalLengthMM: PackScanNumericMeasurement, exposure: PackScanNumericMeasurement, iso: PackScanISOMeasurement, whiteBalanceKelvin: PackScanNumericMeasurement) {
        self.photoID = photoID; self.imagePath = imagePath; self.sequence = sequence; self.originalFilename = originalFilename; self.pixelDimensions = pixelDimensions; self.orientation = orientation; self.focalLengthMM = focalLengthMM; self.exposure = exposure; self.iso = iso; self.whiteBalanceKelvin = whiteBalanceKelvin
    }

    enum CodingKeys: String, CodingKey { case photoID = "photo_id", imagePath = "image_path", sequence, originalFilename = "original_filename", pixelDimensions = "pixel_dimensions", orientation, focalLengthMM = "focal_length_mm", exposure, iso, whiteBalanceKelvin = "white_balance_kelvin" }

    public static func from(_ metadata: PhotoCaptureMetadata) throws -> PackScanPhotoMetadataWire {
        func source(_ value: String?) -> PackScanMeasurementSource? { value.flatMap(PackScanMeasurementSource.init(rawValue:)) }
        func numeric(_ value: SourceMeasurement, unit: String, range: ClosedRange<Double>) throws -> PackScanNumericMeasurement {
            switch value.status {
            case .available, .estimated:
                guard let raw = value.value, raw.isFinite, range.contains(raw), value.unit == nil || value.unit == unit, source(value.source) != nil else { throw PhotoMetadataBindingError.schemaViolation }
                return PackScanNumericMeasurement(status: value.status, value: raw, unit: unit, source: source(value.source))
            case .unavailable, .notRecorded:
                guard value.value == nil else { throw PhotoMetadataBindingError.schemaViolation }
                return PackScanNumericMeasurement(status: value.status)
            }
        }
        guard metadata.photoID.count > 0, metadata.photoID.count <= 128,
              metadata.photoID.first?.isLetter == true || metadata.photoID.first?.isNumber == true,
              metadata.photoID.allSatisfy({ $0.isLetter || $0.isNumber || ".-_".contains($0) }),
              metadata.sequence >= 0, metadata.pixelDimensions.width > 0, metadata.pixelDimensions.height > 0,
              !metadata.originalFilename.isEmpty, !metadata.originalFilename.contains("/"), !metadata.originalFilename.contains("\\") else { throw PhotoMetadataBindingError.schemaViolation }
        let isoValue: Int?
        if let raw = metadata.iso.value {
            guard metadata.iso.status == .available || metadata.iso.status == .estimated,
                  raw.isFinite, raw.rounded() == raw, raw >= 1, raw <= 1_000_000,
                  metadata.iso.unit == nil || metadata.iso.unit == "iso",
                  source(metadata.iso.source) != nil else { throw PhotoMetadataBindingError.schemaViolation }
            isoValue = Int(raw)
        } else {
            guard metadata.iso.status == .unavailable || metadata.iso.status == .notRecorded else { throw PhotoMetadataBindingError.schemaViolation }
            isoValue = nil
        }
        let orientationValue = PackScanOrientationValue(rawValue: metadata.orientation.lowercased()) ?? .unknown
        return PackScanPhotoMetadataWire(
            photoID: metadata.photoID, imagePath: metadata.imagePath, sequence: metadata.sequence,
            originalFilename: metadata.originalFilename, pixelDimensions: metadata.pixelDimensions,
            orientation: PackScanOrientation(value: orientationValue, source: .exif),
            focalLengthMM: try numeric(metadata.focalLengthMM, unit: "mm", range: 0.000001...1_000_000),
            exposure: try numeric(metadata.exposureSeconds, unit: "s", range: 0.000001...1_000_000),
            iso: PackScanISOMeasurement(status: metadata.iso.status, value: isoValue, unit: isoValue == nil ? nil : "iso", source: isoValue == nil ? nil : source(metadata.iso.source)),
            whiteBalanceKelvin: try numeric(metadata.whiteBalanceKelvin, unit: "K", range: 1000...100000)
        )
    }
}

public struct PackScanPhotoMetadataDocument: Codable, Sendable, Equatable {
    public let schemaVersion: String
    public let photos: [PackScanPhotoMetadataWire]
    public init(photos: [PackScanPhotoMetadataWire]) { self.schemaVersion = "1.0.0"; self.photos = photos }
    enum CodingKeys: String, CodingKey { case schemaVersion = "schema_version", photos }
}

public struct PhotoCaptureAppMetadata: Codable, Sendable, Equatable {
    public let lensIdentity: CameraLensIdentity
    public let captureTimestamp: Date
    public init(lensIdentity: CameraLensIdentity, captureTimestamp: Date) { self.lensIdentity = lensIdentity; self.captureTimestamp = captureTimestamp }
}

public enum AcceptedPhotoPersistenceError: Error, Sendable, Equatable { case duplicatePhoto, invalidContract, writeFailed }

/// Atomic wire-document persistence for an accepted source/metadata pair.
/// The immutable source is written first through `OriginalSourceStore`; the
/// metadata document is replaced only after the pair has passed binding.
public actor AcceptedPhotoMetadataStore {
    private let sourceStore: OriginalSourceStore
    private let sourceRoot: URL
    private let metadataURL: URL
    private let fileManager: FileManager

    public init(sourceRoot: URL, metadataURL: URL, fileManager: FileManager = .default) {
        self.sourceRoot = sourceRoot
        self.sourceStore = OriginalSourceStore(root: sourceRoot, fileManager: fileManager)
        self.metadataURL = metadataURL
        self.fileManager = fileManager
    }

    public func persist(metadata: PhotoCaptureMetadata, source: OriginalSourceRecord, bytes: Data) async throws {
        do {
            try recoverInterruptedTransaction()
            try PhotoMetadataBinding.validate(metadata: metadata, source: source, bytes: bytes)
            let wire = try PackScanPhotoMetadataWire.from(metadata)
            var document = try loadDocument()
            guard !document.photos.contains(where: { $0.photoID == wire.photoID }) else { throw AcceptedPhotoPersistenceError.duplicatePhoto }
            document = PackScanPhotoMetadataDocument(photos: document.photos + [wire])
            let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
            try fileManager.createDirectory(at: metadataURL.deletingLastPathComponent(), withIntermediateDirectories: true)
            let markerURL = metadataURL.deletingLastPathComponent().appendingPathComponent(".accepted-transaction.json")
            let marker: [String: String] = ["capture_id": source.captureID, "source": source.filename, "record": "\(source.captureID).source.json"]
            try JSONSerialization.data(withJSONObject: marker, options: [.sortedKeys]).write(to: markerURL, options: .atomic)
            _ = try await sourceStore.persist(record: source, bytes: bytes)
            var stagedMarker = marker; stagedMarker["stage"] = "source_staged"
            try JSONSerialization.data(withJSONObject: stagedMarker, options: [.sortedKeys]).write(to: markerURL, options: .atomic)
            let temp = metadataURL.deletingLastPathComponent().appendingPathComponent(".photos-\(UUID().uuidString).tmp")
            do {
                try encoder.encode(document).write(to: temp, options: .atomic)
                if fileManager.fileExists(atPath: metadataURL.path) { try fileManager.replaceItemAt(metadataURL, withItemAt: temp, backupItemName: nil, options: .usingNewMetadataOnly) }
                else { try fileManager.moveItem(at: temp, to: metadataURL) }
                try? fileManager.removeItem(at: markerURL)
            } catch {
                try? fileManager.removeItem(at: temp)
                throw AcceptedPhotoPersistenceError.writeFailed
            }
        } catch let error as AcceptedPhotoPersistenceError { throw error }
        catch { throw AcceptedPhotoPersistenceError.invalidContract }
    }

    private func recoverInterruptedTransaction() throws {
        let markerURL = metadataURL.deletingLastPathComponent().appendingPathComponent(".accepted-transaction.json")
        guard let data = try? Data(contentsOf: markerURL), let marker = try? JSONSerialization.jsonObject(with: data) as? [String: String], let captureID = marker["capture_id"], let sourceName = marker["source"], let document = try? loadDocument() else { return }
        if document.photos.contains(where: { $0.photoID == captureID }) { try? fileManager.removeItem(at: markerURL); return }
        try? fileManager.removeItem(at: sourceRoot.appendingPathComponent(sourceName))
        try? fileManager.removeItem(at: sourceRoot.appendingPathComponent("\(captureID).source.json"))
        try? fileManager.removeItem(at: markerURL)
    }

    private func loadDocument() throws -> PackScanPhotoMetadataDocument {
        guard fileManager.fileExists(atPath: metadataURL.path) else { return PackScanPhotoMetadataDocument(photos: []) }
        guard let data = try? Data(contentsOf: metadataURL), let document = try? JSONDecoder().decode(PackScanPhotoMetadataDocument.self, from: data) else { throw AcceptedPhotoPersistenceError.writeFailed }
        return document
    }
}

public enum PhotoMetadataBindingError: Error, Sendable, Equatable { case missingSource, idMismatch, pathMismatch, digestMismatch, schemaViolation }

public enum PhotoMetadataBinding {
    public static func validate(metadata: PhotoCaptureMetadata, source: OriginalSourceRecord, bytes: Data) throws {
        guard !bytes.isEmpty else { throw PhotoMetadataBindingError.missingSource }
        guard metadata.photoID == source.captureID else { throw PhotoMetadataBindingError.idMismatch }
        guard metadata.imagePath == "images/\(source.filename)" else { throw PhotoMetadataBindingError.pathMismatch }
        guard metadata.pixelDimensions == source.dimensions, SourceIntegrity.digest(bytes) == source.sha256 else { throw PhotoMetadataBindingError.digestMismatch }
    }
}

public enum CameraRecoveryState: String, Sendable, Codable, Equatable { case idle, starting, running, interrupted, restarting, denied, restricted, unavailable, failed }
public enum CameraRecoveryEvent: Sendable, Equatable { case requestStart, started, permissionDenied, permissionRestricted, interrupted, interruptionEnded, runtimeError, restartSucceeded, restartFailed, stop }

public struct CameraRecoveryMachine: Sendable, Equatable {
    public private(set) var state: CameraRecoveryState = .idle
    public private(set) var retryCount = 0
    public init() {}
    @discardableResult
    public mutating func apply(_ event: CameraRecoveryEvent) -> CameraRecoveryState {
        switch event {
        case .requestStart: state = .starting
        case .started, .restartSucceeded: state = .running; retryCount = 0
        case .permissionDenied: state = .denied
        case .permissionRestricted: state = .restricted
        case .interrupted: state = .interrupted
        case .interruptionEnded: if state == .interrupted { state = .restarting }
        case .runtimeError: retryCount += 1; state = retryCount < 3 ? .restarting : .failed
        case .restartFailed: retryCount += 1; state = retryCount < 3 ? .restarting : .failed
        case .stop: state = .idle
        }
        return state
    }

    public var userMessage: String {
        switch state {
        case .denied: return "Camera permission is denied. Enable it in Settings."
        case .restricted: return "Camera access is restricted on this device."
        case .interrupted, .restarting: return "Camera interrupted. Reconnecting…"
        case .failed: return "Camera could not restart. Return to the capture screen and try again."
        case .unavailable: return "Camera is unavailable."
        default: return ""
        }
    }
}

public enum CameraRecoverySignal: Sendable, Equatable { case permission(CameraAuthorizationStatus), interruption, interruptionEnded, runtimeError, started, restartSucceeded, restartFailed, stopped }

public struct CameraRecoveryIntegrationModel: Sendable, Equatable {
    public private(set) var machine = CameraRecoveryMachine()
    public private(set) var acceptedCaptureIDs: Set<String> = []
    public private(set) var inFlightCaptureID: String?
    public init() {}
    public mutating func beginCapture(id: String) -> Bool {
        guard inFlightCaptureID == nil, machine.state == .idle || machine.state == .running else { return false }
        inFlightCaptureID = id; return true
    }
    public mutating func acceptCapture() {
        if let id = inFlightCaptureID { acceptedCaptureIDs.insert(id) }
        inFlightCaptureID = nil
    }
    public mutating func signal(_ signal: CameraRecoverySignal) {
        switch signal {
        case .interruption: inFlightCaptureID = nil; _ = machine.apply(.interrupted)
        case .runtimeError: inFlightCaptureID = nil; _ = machine.apply(.runtimeError)
        case .interruptionEnded: _ = machine.apply(.interruptionEnded)
        case .permission(.denied): _ = machine.apply(.permissionDenied)
        case .permission(.restricted): _ = machine.apply(.permissionRestricted)
        case .permission: _ = machine.apply(.requestStart)
        case .started: _ = machine.apply(.started)
        case .restartSucceeded: _ = machine.apply(.restartSucceeded)
        case .restartFailed: _ = machine.apply(.restartFailed)
        case .stopped: _ = machine.apply(.stop)
        }
    }
}

#if canImport(AVFoundation)
import AVFoundation

@available(iOS 17.0, *)
@MainActor
public final class CameraRecoveryOwner {
    public private(set) var machine = CameraRecoveryMachine()
    public private(set) var registrationCount = 0
    private var observerTokens: [NSObjectProtocol] = []
    private var stateObservers: [UUID: (CameraRecoveryState, String) -> Void] = [:]
    private var cancelInFlight: (() -> Void)?
    private var restartSession: (() -> Void)?
    public var onStateChange: ((CameraRecoveryState, String) -> Void)?

    public init() {}

    @discardableResult
    public func addStateObserver(_ observer: @escaping (CameraRecoveryState, String) -> Void) -> UUID {
        let token = UUID()
        stateObservers[token] = observer
        return token
    }

    public func removeStateObserver(_ token: UUID) { stateObservers.removeValue(forKey: token) }

    public func setInFlightCancellation(_ cancellation: (() -> Void)?) { cancelInFlight = cancellation }
    public func setSessionRestart(_ restart: (() -> Void)?) { restartSession = restart }

    public func register(session: AVCaptureSession, notificationCenter: NotificationCenter = .default) {
        guard observerTokens.isEmpty else { return }
        registrationCount += 1
        let names: [(Notification.Name, CameraRecoverySignal)] = [
            (AVCaptureSession.wasInterruptedNotification, .interruption),
            (AVCaptureSession.interruptionEndedNotification, .interruptionEnded),
            (AVCaptureSession.runtimeErrorNotification, .runtimeError)
        ]
        observerTokens = names.map { name, signal in
            notificationCenter.addObserver(forName: name, object: session, queue: .main) { [weak self] _ in
                Task { @MainActor in self?.handle(signal) }
            }
        }
    }

    public func unregister(notificationCenter: NotificationCenter = .default) {
        for token in observerTokens { notificationCenter.removeObserver(token) }
        observerTokens.removeAll()
    }

    public func handle(_ signal: CameraRecoverySignal) {
        switch signal {
        case .permission(.denied): _ = machine.apply(.permissionDenied)
        case .permission(.restricted): _ = machine.apply(.permissionRestricted)
        case .permission: _ = machine.apply(.requestStart)
        case .interruption: cancelInFlight?(); _ = machine.apply(.interrupted)
        case .interruptionEnded:
            if machine.apply(.interruptionEnded) == .restarting { restartSession?() }
        case .runtimeError:
            cancelInFlight?()
            if machine.apply(.runtimeError) == .restarting { restartSession?() }
        case .started: _ = machine.apply(.started)
        case .restartSucceeded: _ = machine.apply(.restartSucceeded)
        case .restartFailed: _ = machine.apply(.restartFailed)
        case .stopped: _ = machine.apply(.stop)
        }
        onStateChange?(machine.state, machine.userMessage)
        for observer in stateObservers.values { observer(machine.state, machine.userMessage) }
    }

}
#endif

public enum ThermalCondition: String, Sendable, Codable, Equatable { case nominal, fair, serious, critical, unavailable }
public struct DeviceHealthSnapshot: Sendable, Equatable {
    public let thermal: ThermalCondition
    public let availableStorageBytes: Int64?
    public let batteryLevel: Double?
    public let batteryStateAvailable: Bool
    public init(thermal: ThermalCondition, availableStorageBytes: Int64?, batteryLevel: Double?, batteryStateAvailable: Bool) { self.thermal = thermal; self.availableStorageBytes = availableStorageBytes; self.batteryLevel = batteryLevel; self.batteryStateAvailable = batteryStateAvailable }
}
public enum HealthSeverity: String, Sendable, Codable, Equatable { case normal, warning, hardStop }
public struct HealthDecision: Sendable, Equatable { public let severity: HealthSeverity; public let messages: [String]; public init(severity: HealthSeverity, messages: [String]) { self.severity = severity; self.messages = messages } }

public enum DeviceHealthPolicy {
    public static let minimumStorageBytes: Int64 = 250 * 1024 * 1024
    public static let warningStorageBytes: Int64 = 1024 * 1024 * 1024
    public static func evaluate(_ snapshot: DeviceHealthSnapshot) -> HealthDecision {
        var messages: [String] = []; var severity = HealthSeverity.normal
        switch snapshot.thermal {
        case .critical: severity = .hardStop; messages.append("Thermal state is critical; stop capture.")
        case .serious: severity = maxSeverity(severity, .warning); messages.append("Device is hot; capture may stop.")
        case .fair: severity = maxSeverity(severity, .warning); messages.append("Device temperature is elevated.")
        default: break
        }
        if let storage = snapshot.availableStorageBytes {
            if storage < minimumStorageBytes { severity = .hardStop; messages.append("Storage is critically low.") }
            else if storage < warningStorageBytes { severity = maxSeverity(severity, .warning); messages.append("Storage is running low.") }
        }
        if let battery = snapshot.batteryLevel, battery < 0.10 { severity = maxSeverity(severity, .warning); messages.append("Battery is below 10%.") }
        return HealthDecision(severity: severity, messages: messages)
    }
    private static func maxSeverity(_ lhs: HealthSeverity, _ rhs: HealthSeverity) -> HealthSeverity {
        [lhs, rhs].max { rank($0) < rank($1) } ?? .normal
    }
    private static func rank(_ severity: HealthSeverity) -> Int { severity == .normal ? 0 : severity == .warning ? 1 : 2 }
}

public protocol DeviceHealthProvider: Sendable {
    func snapshot() -> DeviceHealthSnapshot
}

public struct UnavailableDeviceHealthProvider: DeviceHealthProvider {
    public init() {}
    public func snapshot() -> DeviceHealthSnapshot { DeviceHealthSnapshot(thermal: .unavailable, availableStorageBytes: nil, batteryLevel: nil, batteryStateAvailable: false) }
}

public enum DeviceHealthCaptureGate: Sendable, Equatable {
    case ready(HealthDecision)
    case warning(HealthDecision)
    case hardStop(HealthDecision)
    public var allowsCapture: Bool { if case .hardStop = self { return false }; return true }
    public static func evaluate(_ snapshot: DeviceHealthSnapshot) -> DeviceHealthCaptureGate {
        let decision = DeviceHealthPolicy.evaluate(snapshot)
        switch decision.severity { case .normal: return .ready(decision); case .warning: return .warning(decision); case .hardStop: return .hardStop(decision) }
    }
}

public struct CaptureAdmissionController: Sendable, Equatable {
    public private(set) var gate: DeviceHealthCaptureGate = .ready(DeviceHealthPolicy.evaluate(UnavailableDeviceHealthProvider().snapshot()))
    public init() {}
    public mutating func update(_ gate: DeviceHealthCaptureGate) { self.gate = gate }
    public var allowsCapture: Bool { gate.allowsCapture }
    public func rejectReason() -> String? { if case .hardStop(let decision) = gate { return decision.messages.joined(separator: " ") }; return nil }
}

public actor DeviceHealthMonitor {
    private let provider: any DeviceHealthProvider
    private var loop: Task<Void, Never>?
    private var latest: DeviceHealthCaptureGate = .ready(DeviceHealthPolicy.evaluate(UnavailableDeviceHealthProvider().snapshot()))
    public init(provider: any DeviceHealthProvider) { self.provider = provider }
    public func preflight() -> DeviceHealthCaptureGate { latest = DeviceHealthCaptureGate.evaluate(provider.snapshot()); return latest }
    public func current() -> DeviceHealthCaptureGate { latest }
    public func start(intervalNanoseconds: UInt64 = 2_000_000_000, onUpdate: @escaping @Sendable (DeviceHealthCaptureGate) async -> Void) {
        guard loop == nil else { return }
        loop = Task { [weak self, provider] in
            while !Task.isCancelled {
                let gate = DeviceHealthCaptureGate.evaluate(provider.snapshot())
                await self?.record(gate)
                await onUpdate(gate)
                try? await Task.sleep(nanoseconds: intervalNanoseconds)
            }
        }
    }
    public func stop() { loop?.cancel(); loop = nil }
    private func record(_ gate: DeviceHealthCaptureGate) { latest = gate }
}

#if canImport(UIKit)
import UIKit

public struct PhysicalDeviceHealthProvider: DeviceHealthProvider {
    public init() {}
    public func snapshot() -> DeviceHealthSnapshot {
        let thermal: ThermalCondition
        switch ProcessInfo.processInfo.thermalState {
        case .nominal: thermal = .nominal
        case .fair: thermal = .fair
        case .serious: thermal = .serious
        case .critical: thermal = .critical
        @unknown default: thermal = .unavailable
        }
        let capacity = try? URL(fileURLWithPath: NSHomeDirectory()).resourceValues(forKeys: [.volumeAvailableCapacityForImportantUsageKey]).volumeAvailableCapacityForImportantUsage
        let device = UIDevice.current
        device.isBatteryMonitoringEnabled = true
        let batteryAvailable = device.batteryState != .unknown && device.batteryLevel >= 0
        return DeviceHealthSnapshot(thermal: thermal, availableStorageBytes: capacity, batteryLevel: batteryAvailable ? Double(device.batteryLevel) : nil, batteryStateAvailable: batteryAvailable)
    }
}
#endif

public enum FocusState: String, Sendable, Codable, Equatable { case unavailable, focusing, continuous, locked, failed }
public struct FocusCapabilities: Sendable, Equatable { public let point: Bool; public let lock: Bool; public init(point: Bool, lock: Bool) { self.point = point; self.lock = lock } }

public struct FocusPolicy: Sendable, Equatable {
    public private(set) var state: FocusState = .unavailable
    public init() {}
    public mutating func begin(capabilities: FocusCapabilities) -> FocusState {
        state = capabilities.point ? .focusing : .unavailable; return state
    }
    public mutating func stabilize() -> FocusState { if state == .focusing { state = .continuous }; return state }
    public mutating func lock(capabilities: FocusCapabilities) -> FocusState {
        state = state == .continuous && capabilities.lock ? .locked : .failed; return state
    }
}

public actor CameraConfigurationCoordinator {
    public init() {}
    public func perform<T: Sendable>(_ operation: @Sendable () throws -> T) rethrows -> T { try operation() }
}

public struct CameraCaptureControlState: Sendable, Equatable {
    public let lens: CameraLensIdentity?
    public let focus: FocusState
    public let exposure: ExposureState
    public let whiteBalance: WhiteBalanceState
    public let message: String?
    public init(lens: CameraLensIdentity?, focus: FocusState = .unavailable, exposure: ExposureState = .unavailable, whiteBalance: WhiteBalanceState = .unavailable, message: String? = nil) {
        self.lens = lens; self.focus = focus; self.exposure = exposure; self.whiteBalance = whiteBalance; self.message = message
    }
}

public struct CameraCaptureControlModel: Sendable, Equatable {
    public private(set) var state: CameraCaptureControlState
    public init(lens: CameraLensIdentity? = nil) { state = CameraCaptureControlState(lens: lens) }
    public mutating func setFocus(_ value: FocusState) { state = CameraCaptureControlState(lens: state.lens, focus: value, exposure: state.exposure, whiteBalance: state.whiteBalance, message: state.message) }
    public mutating func setExposure(_ value: ExposureState) { state = CameraCaptureControlState(lens: state.lens, focus: state.focus, exposure: value, whiteBalance: state.whiteBalance, message: state.message) }
    public mutating func setWhiteBalance(_ value: WhiteBalanceState) { state = CameraCaptureControlState(lens: state.lens, focus: state.focus, exposure: state.exposure, whiteBalance: value, message: state.message) }
    public mutating func message(_ value: String?) { state = CameraCaptureControlState(lens: state.lens, focus: state.focus, exposure: state.exposure, whiteBalance: state.whiteBalance, message: value) }
}

/// Runtime sink shared by physical AVFoundation controls and the SwiftUI
/// capture view model.  Physical adapters publish observed state here; the
/// view never infers focus/exposure/WB from a button tap.
@MainActor
public final class CameraControlRuntimeBridge {
    public private(set) var state: CameraCaptureControlState
    public var onStateChange: ((CameraCaptureControlState) -> Void)?
    public init(lens: CameraLensIdentity) { state = CameraCaptureControlState(lens: lens) }
    public func setFocus(_ value: FocusState) { state = CameraCaptureControlState(lens: state.lens, focus: value, exposure: state.exposure, whiteBalance: state.whiteBalance, message: state.message); onStateChange?(state) }
    public func setExposure(_ value: ExposureState) { state = CameraCaptureControlState(lens: state.lens, focus: state.focus, exposure: value, whiteBalance: state.whiteBalance, message: state.message); onStateChange?(state) }
    public func setWhiteBalance(_ value: WhiteBalanceState) { state = CameraCaptureControlState(lens: state.lens, focus: state.focus, exposure: state.exposure, whiteBalance: value, message: state.message); onStateChange?(state) }
    public func setMessage(_ value: String?) { state = CameraCaptureControlState(lens: state.lens, focus: state.focus, exposure: state.exposure, whiteBalance: state.whiteBalance, message: value); onStateChange?(state) }
}

public enum ExposureState: String, Sendable, Codable, Equatable { case unavailable, metering, locked, failed }
public struct ExposureCapabilities: Sendable, Equatable { public let minBias: Float; public let maxBias: Float; public let lock: Bool; public init(minBias: Float, maxBias: Float, lock: Bool) { self.minBias = minBias; self.maxBias = maxBias; self.lock = lock } }

public struct ExposurePolicy: Sendable, Equatable {
    public private(set) var state: ExposureState = .unavailable
    public private(set) var targetBias: Float?
    public init() {}
    public mutating func meter(capabilities: ExposureCapabilities, requestedBias: Float = 0) -> ExposureState {
        guard capabilities.minBias <= capabilities.maxBias else { state = .failed; return state }
        targetBias = min(max(requestedBias, capabilities.minBias), capabilities.maxBias)
        state = .metering; return state
    }
    public mutating func lock(capabilities: ExposureCapabilities) -> ExposureState {
        state = state == .metering && capabilities.lock ? .locked : .failed; return state
    }
}

public struct ExposureCaptureReading: Sendable, Equatable {
    public let exposureSeconds: Double
    public let iso: Int
    public let bias: Float
    public init(exposureSeconds: Double, iso: Int, bias: Float) {
        self.exposureSeconds = exposureSeconds; self.iso = iso; self.bias = bias
    }
    public var isValid: Bool { exposureSeconds > 0 && exposureSeconds.isFinite && iso >= 1 && bias.isFinite }
}

public enum ExposureCaptureBindingError: Error, Sendable, Equatable { case unavailable, invalidReading }

public struct ExposureCaptureBinding: Sendable, Equatable {
    public let reading: ExposureCaptureReading
    public private(set) var state: ExposureState
    public init(reading: ExposureCaptureReading, state: ExposureState = .metering) throws {
        guard reading.isValid else { throw ExposureCaptureBindingError.invalidReading }
        guard state == .metering || state == .locked else { throw ExposureCaptureBindingError.unavailable }
        self.reading = reading; self.state = state
    }
    public mutating func lock() { state = .locked }
}

public enum WhiteBalanceState: String, Sendable, Codable, Equatable { case unavailable, stabilizing, locked, failed }
public struct WhiteBalanceCapabilities: Sendable, Equatable { public let continuous: Bool; public let lock: Bool; public init(continuous: Bool, lock: Bool) { self.continuous = continuous; self.lock = lock } }

public struct WhiteBalancePolicy: Sendable, Equatable {
    public private(set) var state: WhiteBalanceState = .unavailable
    public private(set) var temperatureKelvin: Double?
    public init() {}
    public mutating func stabilize(capabilities: WhiteBalanceCapabilities, reportedKelvin: Double? = nil) -> WhiteBalanceState {
        guard capabilities.continuous else { state = .unavailable; return state }
        temperatureKelvin = reportedKelvin
        state = .stabilizing; return state
    }
    public mutating func lock(capabilities: WhiteBalanceCapabilities, reportedKelvin: Double? = nil) -> WhiteBalanceState {
        guard state == .stabilizing, capabilities.lock else { state = .failed; return state }
        temperatureKelvin = reportedKelvin
        state = .locked; return state
    }
}

public struct WhiteBalanceCaptureReading: Sendable, Equatable {
    public let temperatureKelvin: Double
    public init(temperatureKelvin: Double) { self.temperatureKelvin = temperatureKelvin }
    public var isValid: Bool { temperatureKelvin.isFinite && temperatureKelvin >= 1000 && temperatureKelvin <= 100000 }
}

public enum WhiteBalanceCaptureBindingError: Error, Sendable, Equatable { case unavailable, invalidReading }

public struct WhiteBalanceCaptureBinding: Sendable, Equatable {
    public let reading: WhiteBalanceCaptureReading
    public private(set) var state: WhiteBalanceState
    public init(reading: WhiteBalanceCaptureReading, state: WhiteBalanceState = .stabilizing) throws {
        guard reading.isValid else { throw WhiteBalanceCaptureBindingError.invalidReading }
        guard state == .stabilizing || state == .locked else { throw WhiteBalanceCaptureBindingError.unavailable }
        self.reading = reading; self.state = state
    }
    public mutating func lock() { state = .locked }
}

#if canImport(AVFoundation) && canImport(CoreGraphics)
import AVFoundation
import CoreGraphics

public enum CameraConfigurationError: Error, Sendable, Equatable { case nonSelectedDevice, stabilizationRequired }
public enum CameraDeviceFocusMode: String, Sendable, Equatable { case continuousAutoFocus, locked }
public enum CameraDeviceExposureMode: String, Sendable, Equatable { case continuousAutoExposure, locked }
public enum CameraDeviceWhiteBalanceMode: String, Sendable, Equatable { case continuousAutoWhiteBalance, locked }

/// Production-used seam for the physical AVCaptureDevice and deterministic adapter fixtures.
@MainActor
public protocol CameraDeviceControlDriver: AnyObject {
    var uniqueID: String { get }
    var position: AVCaptureDevice.Position { get }
    var supportsContinuousFocus: Bool { get }
    var supportsLockedFocus: Bool { get }
    var supportsFocusPoint: Bool { get }
    var isAdjustingFocus: Bool { get }
    func setFocusPoint(_ point: CGPoint)
    func setFocusMode(_ mode: CameraDeviceFocusMode)
    var supportsContinuousExposure: Bool { get }
    var supportsLockedExposure: Bool { get }
    var minExposureTargetBias: Float { get }
    var maxExposureTargetBias: Float { get }
    var exposureDurationSeconds: Double { get }
    var iso: Float { get }
    var exposureTargetBias: Float { get }
    func setExposureTargetBias(_ bias: Float)
    func setExposureMode(_ mode: CameraDeviceExposureMode)
    var supportsContinuousWhiteBalance: Bool { get }
    var supportsLockedWhiteBalance: Bool { get }
    var isAdjustingWhiteBalance: Bool { get }
    func observedTemperatureKelvin() -> Double?
    func setWhiteBalanceMode(_ mode: CameraDeviceWhiteBalanceMode)
    func lockForConfiguration() throws
    func unlockForConfiguration()
}

@available(iOS 17.0, *)
@MainActor
public final class AVFoundationCameraDeviceControlDriver: CameraDeviceControlDriver {
    public let device: AVCaptureDevice
    public init(device: AVCaptureDevice) { self.device = device }
    public var uniqueID: String { device.uniqueID }
    public var position: AVCaptureDevice.Position { device.position }
    public var supportsContinuousFocus: Bool { device.isFocusModeSupported(.continuousAutoFocus) }
    public var supportsLockedFocus: Bool { device.isFocusModeSupported(.locked) }
    public var supportsFocusPoint: Bool { device.isFocusPointOfInterestSupported }
    public var isAdjustingFocus: Bool { device.isAdjustingFocus }
    public func setFocusPoint(_ point: CGPoint) { device.focusPointOfInterest = point }
    public func setFocusMode(_ mode: CameraDeviceFocusMode) { device.focusMode = mode == .continuousAutoFocus ? .continuousAutoFocus : .locked }
    public var supportsContinuousExposure: Bool { device.isExposureModeSupported(.continuousAutoExposure) }
    public var supportsLockedExposure: Bool { device.isExposureModeSupported(.locked) }
    public var minExposureTargetBias: Float { device.minExposureTargetBias }
    public var maxExposureTargetBias: Float { device.maxExposureTargetBias }
    public var exposureDurationSeconds: Double { device.exposureDuration.seconds }
    public var iso: Float { device.iso }
    public var exposureTargetBias: Float { device.exposureTargetBias }
    public func setExposureTargetBias(_ bias: Float) { device.setExposureTargetBias(bias, completionHandler: nil) }
    public func setExposureMode(_ mode: CameraDeviceExposureMode) { device.exposureMode = mode == .continuousAutoExposure ? .continuousAutoExposure : .locked }
    public var supportsContinuousWhiteBalance: Bool { device.isWhiteBalanceModeSupported(.continuousAutoWhiteBalance) }
    public var supportsLockedWhiteBalance: Bool { device.isWhiteBalanceModeSupported(.locked) }
    public var isAdjustingWhiteBalance: Bool { device.isAdjustingWhiteBalance }
    public func observedTemperatureKelvin() -> Double? {
        let values = device.temperatureAndTintValues(for: device.deviceWhiteBalanceGains)
        return Double(values.temperature)
    }
    public func setWhiteBalanceMode(_ mode: CameraDeviceWhiteBalanceMode) { device.whiteBalanceMode = mode == .continuousAutoWhiteBalance ? .continuousAutoWhiteBalance : .locked }
    public func lockForConfiguration() throws { try device.lockForConfiguration() }
    public func unlockForConfiguration() { device.unlockForConfiguration() }
}

@available(iOS 17.0, *)
@MainActor
public final class CameraDeviceConfigurationCoordinator {
    public let selectedLens: CameraLensIdentity
    public let driver: any CameraDeviceControlDriver
    private var focusObservedStable = false
    private var whiteBalanceObservedStable = false

    public init(driver: any CameraDeviceControlDriver, selectedLens: CameraLensIdentity) { self.driver = driver; self.selectedLens = selectedLens }
    public convenience init(device: AVCaptureDevice, selectedLens: CameraLensIdentity) { self.init(driver: AVFoundationCameraDeviceControlDriver(device: device), selectedLens: selectedLens) }
    public var selectedDeviceIdentifier: String { driver.uniqueID }
    public var isSelectedDevice: Bool { driver.uniqueID == selectedLens.identifier && driver.position == .back && selectedLens.position == .back && selectedLens.kind == .wideAngle }
    public func requireSelected(_ candidate: any CameraDeviceControlDriver) throws { guard isSelectedDevice, candidate.uniqueID == driver.uniqueID else { throw CameraConfigurationError.nonSelectedDevice } }
    public func requireSelected(_ candidate: AVCaptureDevice) throws { guard isSelectedDevice, candidate.uniqueID == driver.uniqueID else { throw CameraConfigurationError.nonSelectedDevice } }
    public func observeFocus(isAdjusting: Bool) throws { try requireSelected(driver); if !isAdjusting { focusObservedStable = true } }
    public func observeWhiteBalance(isAdjusting: Bool) throws { try requireSelected(driver); if !isAdjusting { whiteBalanceObservedStable = true } }
    public var focusIsStable: Bool { focusObservedStable }
    public var whiteBalanceIsStable: Bool { whiteBalanceObservedStable }
    public func withLockedDevice<T>(_ operation: (any CameraDeviceControlDriver) throws -> T) throws -> T {
        try driver.lockForConfiguration(); defer { driver.unlockForConfiguration() }; return try operation(driver)
    }
}

@available(iOS 17.0, *)
@MainActor
public final class AVFoundationCameraControlComposition {
    public let coordinator: CameraDeviceConfigurationCoordinator
    public let controls: CameraControlRuntimeBridge
    public init(device: AVCaptureDevice, selectedLens: CameraLensIdentity) { self.init(driver: AVFoundationCameraDeviceControlDriver(device: device), selectedLens: selectedLens) }
    public init(driver: any CameraDeviceControlDriver, selectedLens: CameraLensIdentity) { coordinator = CameraDeviceConfigurationCoordinator(driver: driver, selectedLens: selectedLens); controls = CameraControlRuntimeBridge(lens: selectedLens) }
    public var selectedDeviceIdentifier: String { coordinator.selectedDeviceIdentifier }
    public func configureFocus() { do { controls.setFocus(try AVFoundationFocusAdapter.configure(driver: coordinator.driver, point: nil, coordinator: coordinator)) } catch { controls.setFocus(.failed); controls.setMessage("Focus unavailable") } }
    public func observeFocus() { do { controls.setFocus(try AVFoundationFocusAdapter.observe(driver: coordinator.driver, coordinator: coordinator)) } catch { controls.setFocus(.failed); controls.setMessage("Focus unavailable") } }
    public func lockFocus() { do { controls.setFocus(try AVFoundationFocusAdapter.lock(driver: coordinator.driver, coordinator: coordinator)) } catch { controls.setFocus(.failed); controls.setMessage("Focus is still stabilizing") } }
    public func configureExposure(bias: Float) { do { controls.setExposure(try AVFoundationExposureAdapter.configure(driver: coordinator.driver, bias: bias, coordinator: coordinator)) } catch { controls.setExposure(.failed); controls.setMessage("Exposure unavailable") } }
    public func lockExposure() { do { controls.setExposure(try AVFoundationExposureAdapter.lock(driver: coordinator.driver, coordinator: coordinator)) } catch { controls.setExposure(.failed); controls.setMessage("Exposure unavailable") } }
    public func configureWhiteBalance() { do { controls.setWhiteBalance(try AVFoundationWhiteBalanceAdapter.configure(driver: coordinator.driver, coordinator: coordinator)) } catch { controls.setWhiteBalance(.failed); controls.setMessage("White balance unavailable") } }
    public func observeWhiteBalance() { do { controls.setWhiteBalance(try AVFoundationWhiteBalanceAdapter.observe(driver: coordinator.driver, coordinator: coordinator)) } catch { controls.setWhiteBalance(.failed); controls.setMessage("White balance unavailable") } }
    public func lockWhiteBalance() { do { controls.setWhiteBalance(try AVFoundationWhiteBalanceAdapter.lock(driver: coordinator.driver, coordinator: coordinator)) } catch { controls.setWhiteBalance(.failed); controls.setMessage("White balance is still stabilizing") } }
    public func acceptedMetadata(_ base: PhotoCaptureMetadata) throws -> PhotoCaptureMetadata {
        let exposure = try ExposureCaptureBinding(reading: AVFoundationExposureAdapter.observedReading(driver: coordinator.driver, coordinator: coordinator), state: .locked)
        guard let temperature = AVFoundationWhiteBalanceAdapter.observedTemperatureKelvin(driver: coordinator.driver) else { throw WhiteBalanceCaptureBindingError.invalidReading }
        let whiteBalance = try WhiteBalanceCaptureBinding(reading: temperature, state: .locked)
        return AcceptedPhotoMetadataFactory.withCaptureReadings(base, exposure: exposure, whiteBalance: whiteBalance)
    }
}

@available(iOS 17.0, *)
@MainActor
public enum AVFoundationFocusAdapter {
    public static func configure(driver: any CameraDeviceControlDriver, point: CGPoint?, lock: Bool = false, coordinator: CameraDeviceConfigurationCoordinator) throws -> FocusState {
        try coordinator.requireSelected(driver); guard driver.supportsContinuousFocus else { return .unavailable }; guard !lock else { return try lock(driver: driver, coordinator: coordinator) }
        return try coordinator.withLockedDevice { configuredDriver in
            if let point { guard configuredDriver.supportsFocusPoint else { return .unavailable }; configuredDriver.setFocusPoint(point) }
            configuredDriver.setFocusMode(.continuousAutoFocus); return .focusing
        }
    }
    public static func configure(device: AVCaptureDevice, point: CGPoint?, lock: Bool = false, coordinator: CameraDeviceConfigurationCoordinator) throws -> FocusState { try configure(driver: AVFoundationCameraDeviceControlDriver(device: device), point: point, lock: lock, coordinator: coordinator) }
    public static func lock(driver: any CameraDeviceControlDriver, coordinator: CameraDeviceConfigurationCoordinator) throws -> FocusState {
        try coordinator.requireSelected(driver); guard coordinator.focusIsStable, !driver.isAdjustingFocus else { throw CameraConfigurationError.stabilizationRequired }; guard driver.supportsLockedFocus else { return .failed }; return try coordinator.withLockedDevice { $0.setFocusMode(.locked); return .locked }
    }
    public static func lock(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator) throws -> FocusState { try lock(driver: AVFoundationCameraDeviceControlDriver(device: device), coordinator: coordinator) }
    public static func observe(driver: any CameraDeviceControlDriver, coordinator: CameraDeviceConfigurationCoordinator) throws -> FocusState { try coordinator.requireSelected(driver); try coordinator.observeFocus(isAdjusting: driver.isAdjustingFocus); return driver.isAdjustingFocus ? .focusing : .continuous }
    public static func observe(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator) throws -> FocusState { try observe(driver: AVFoundationCameraDeviceControlDriver(device: device), coordinator: coordinator) }
}

@available(iOS 17.0, *)
@MainActor
public enum AVFoundationExposureAdapter {
    public static func configure(driver: any CameraDeviceControlDriver, bias: Float, lock: Bool = false, coordinator: CameraDeviceConfigurationCoordinator) throws -> ExposureState {
        try coordinator.requireSelected(driver); guard driver.supportsContinuousExposure else { return .unavailable }
        let result = try coordinator.withLockedDevice { configuredDriver in configuredDriver.setExposureMode(.continuousAutoExposure); configuredDriver.setExposureTargetBias(min(max(bias, configuredDriver.minExposureTargetBias), configuredDriver.maxExposureTargetBias)); return ExposureState.metering }
        _ = lock; return result
    }
    public static func configure(device: AVCaptureDevice, bias: Float, lock: Bool = false, coordinator: CameraDeviceConfigurationCoordinator) throws -> ExposureState { try configure(driver: AVFoundationCameraDeviceControlDriver(device: device), bias: bias, lock: lock, coordinator: coordinator) }
    public static func lock(driver: any CameraDeviceControlDriver, coordinator: CameraDeviceConfigurationCoordinator) throws -> ExposureState { try coordinator.requireSelected(driver); guard driver.supportsLockedExposure else { return .failed }; return try coordinator.withLockedDevice { $0.setExposureMode(.locked); return .locked } }
    public static func lock(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator) throws -> ExposureState { try lock(driver: AVFoundationCameraDeviceControlDriver(device: device), coordinator: coordinator) }
    public static func observedReading(driver: any CameraDeviceControlDriver, coordinator: CameraDeviceConfigurationCoordinator) throws -> ExposureCaptureReading { try coordinator.requireSelected(driver); let reading = ExposureCaptureReading(exposureSeconds: driver.exposureDurationSeconds, iso: Int(driver.iso), bias: driver.exposureTargetBias); guard reading.isValid else { throw ExposureCaptureBindingError.invalidReading }; return reading }
    public static func observedReading(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator) throws -> ExposureCaptureReading { try observedReading(driver: AVFoundationCameraDeviceControlDriver(device: device), coordinator: coordinator) }
}

@available(iOS 17.0, *)
@MainActor
public enum AVFoundationWhiteBalanceAdapter {
    public static func configure(driver: any CameraDeviceControlDriver, lock: Bool = false, coordinator: CameraDeviceConfigurationCoordinator) throws -> WhiteBalanceState {
        try coordinator.requireSelected(driver); guard driver.supportsContinuousWhiteBalance else { return .unavailable }; guard !lock else { return try self.lock(driver: driver, coordinator: coordinator) }; return try coordinator.withLockedDevice { $0.setWhiteBalanceMode(.continuousAutoWhiteBalance); return .stabilizing }
    }
    public static func configure(device: AVCaptureDevice, lock: Bool = false, coordinator: CameraDeviceConfigurationCoordinator) throws -> WhiteBalanceState { try configure(driver: AVFoundationCameraDeviceControlDriver(device: device), lock: lock, coordinator: coordinator) }
    public static func lock(driver: any CameraDeviceControlDriver, coordinator: CameraDeviceConfigurationCoordinator) throws -> WhiteBalanceState { try coordinator.requireSelected(driver); guard coordinator.whiteBalanceIsStable, !driver.isAdjustingWhiteBalance else { throw CameraConfigurationError.stabilizationRequired }; guard driver.supportsLockedWhiteBalance else { return .failed }; return try coordinator.withLockedDevice { $0.setWhiteBalanceMode(.locked); return .locked } }
    public static func lock(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator) throws -> WhiteBalanceState { try lock(driver: AVFoundationCameraDeviceControlDriver(device: device), coordinator: coordinator) }
    public static func observedTemperatureKelvin(driver: any CameraDeviceControlDriver) -> WhiteBalanceCaptureReading? { guard let temperature = driver.observedTemperatureKelvin() else { return nil }; let reading = WhiteBalanceCaptureReading(temperatureKelvin: temperature); return reading.isValid ? reading : nil }
    public static func observedTemperatureKelvin(device: AVCaptureDevice) -> WhiteBalanceCaptureReading? { observedTemperatureKelvin(driver: AVFoundationCameraDeviceControlDriver(device: device)) }
    public static func observe(driver: any CameraDeviceControlDriver, coordinator: CameraDeviceConfigurationCoordinator) throws -> WhiteBalanceState { try coordinator.requireSelected(driver); try coordinator.observeWhiteBalance(isAdjusting: driver.isAdjustingWhiteBalance); return .stabilizing }
    public static func observe(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator) throws -> WhiteBalanceState { try observe(driver: AVFoundationCameraDeviceControlDriver(device: device), coordinator: coordinator) }
}
#endif

#if canImport(NextLevel) && canImport(UIKit)
import NextLevel
import UIKit
#if canImport(AVFoundation)
import AVFoundation
#endif

@MainActor
private final class NextLevelStillPhotoDriver: NSObject, StillPhotoDriver, NextLevelPhotoDelegate {
    private let nextLevel: NextLevel
    weak var delegate: (any StillPhotoDriverDelegate)?
    var canCapturePhoto: Bool { nextLevel.canCapturePhoto }
    init(nextLevel: NextLevel) {
        self.nextLevel = nextLevel
        super.init()
    }
    func capturePhoto() { nextLevel.photoConfiguration.isHighResolutionEnabled = true; nextLevel.photoDelegate = self; nextLevel.capturePhoto() }
    func cancelPhotoCapture() { if nextLevel.photoDelegate === self { nextLevel.photoDelegate = nil }; nextLevel.stop() }

    public func nextLevel(_ nextLevel: NextLevel, output: AVCapturePhotoOutput, willBeginCaptureFor resolvedSettings: AVCaptureResolvedPhotoSettings, photoConfiguration: NextLevelPhotoConfiguration) {}
    public func nextLevel(_ nextLevel: NextLevel, output: AVCapturePhotoOutput, willCapturePhotoFor resolvedSettings: AVCaptureResolvedPhotoSettings, photoConfiguration: NextLevelPhotoConfiguration) {}
    public func nextLevel(_ nextLevel: NextLevel, output: AVCapturePhotoOutput, didCapturePhotoFor resolvedSettings: AVCaptureResolvedPhotoSettings, photoConfiguration: NextLevelPhotoConfiguration) {}

    public func nextLevel(_ nextLevel: NextLevel, didFinishProcessingPhoto photo: AVCapturePhoto, photoDict: [String: Any], photoConfiguration: NextLevelPhotoConfiguration) {
        guard let bytes = photo.fileDataRepresentation(), !bytes.isEmpty else {
            delegate?.stillPhotoDriverDidFinishWithoutData(self)
            return
        }
        let dimensions = photo.resolvedSettings.photoDimensions
        guard dimensions.width > 0, dimensions.height > 0 else {
            delegate?.stillPhotoDriverDidFinishWithoutData(self)
            return
        }
        delegate?.stillPhotoDriver(self, didFinish: bytes, dimensions: CaptureDimensions(width: Int(dimensions.width), height: Int(dimensions.height)))
    }

    public func nextLevelDidCompletePhotoCapture(_ nextLevel: NextLevel) {
        delegate?.stillPhotoDriverDidFinishWithoutData(self)
    }
}

@MainActor
public final class NextLevelStillCaptureAdapter: NSObject, TimestampedStillPhotoBackend {
    private let driver: NextLevelStillPhotoDriver
    private let core: StillPhotoAdapterCore
    public let selectedLens: CameraLensIdentity
    public init(nextLevel: NextLevel, selectedLens: CameraLensIdentity, activeLensIdentifier: @escaping () -> String?) {
        let driver = NextLevelStillPhotoDriver(nextLevel: nextLevel)
        self.driver = driver
        self.selectedLens = selectedLens
        self.core = StillPhotoAdapterCore(driver: driver, selectedLens: selectedLens, activeLensIdentifier: activeLensIdentifier)
        super.init()
    }
    public func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) { try await core.requestOriginalStill() }
    public func lastCaptureMonotonicTimestamp() async -> TimeInterval? { await core.lastCaptureMonotonicTimestamp() }
    public func sessionDidStop() { core.cancel() }
    #if canImport(AVFoundation)
    public func bind(to recoveryOwner: CameraRecoveryOwner) { recoveryOwner.setInFlightCancellation { [weak self] in self?.sessionDidStop() } }
    #endif
}

@MainActor
public final class NextLevelStillCaptureComposition {
    public let selectedLens: CameraLensIdentity
    public let adapter: NextLevelStillCaptureAdapter
    public init(nextLevel: NextLevel, candidates: [CameraDeviceDescriptor], activeLensIdentifier: @escaping () -> String?, recoveryOwner: CameraRecoveryOwner) throws {
        guard case .selected(let lens) = CameraDeviceSelector.selectMainRearWide(from: candidates) else { throw CameraServiceError.unavailable }
        selectedLens = lens
        adapter = NextLevelStillCaptureAdapter(nextLevel: nextLevel, selectedLens: lens, activeLensIdentifier: activeLensIdentifier)
        adapter.bind(to: recoveryOwner)
    }
}
#endif

#if canImport(UIKit) && canImport(AVFoundation) && canImport(NextLevel)
import AVFoundation
import NextLevel
import UIKit

@MainActor
private final class NextLevelPreviewDriver: PreviewSessionDriver {
    private let nextLevel: NextLevel
    var attachHandler: (() -> Void)?
    var detachHandler: (() -> Void)?
    private(set) var isAttached = false
    private(set) var isRunning = false

    init(nextLevel: NextLevel) { self.nextLevel = nextLevel }
    func attach() throws { attachHandler?(); isAttached = true }
    func detach() { detachHandler?(); isAttached = false }
    func start() throws { try nextLevel.start(); isRunning = true }
    func stop() { nextLevel.stop(); isRunning = false }
}

/// UIKit owns the actual NextLevel preview layer; SwiftUI only presents it.
@MainActor
public final class NextLevelPreviewViewController: UIViewController {
    private let nextLevel: NextLevel
    private let statusLabel = UILabel()
    private let previewDriver: NextLevelPreviewDriver
    private lazy var bridge = PreviewBridgeController(driver: previewDriver)
    private var previewLayer: AVCaptureVideoPreviewLayer?
    private let recoveryOwner: CameraRecoveryOwner
    private let onReady: ((NextLevel) -> Void)?
    private var recoveryObserverToken: UUID?
    private var didNotifyReady = false

    public init(nextLevel: NextLevel = .shared, recoveryOwner: CameraRecoveryOwner, onReady: ((NextLevel) -> Void)? = nil) {
        self.nextLevel = nextLevel
        self.recoveryOwner = recoveryOwner
        self.onReady = onReady
        self.previewDriver = NextLevelPreviewDriver(nextLevel: nextLevel)
        super.init(nibName: nil, bundle: nil)
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) { nil }

    public override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .black
        statusLabel.textColor = .white
        statusLabel.textAlignment = .center
        statusLabel.numberOfLines = 0
        statusLabel.text = "Preparing camera…"
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(statusLabel)
        NSLayoutConstraint.activate([
            statusLabel.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 16),
            statusLabel.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -16),
            statusLabel.centerYAnchor.constraint(equalTo: view.centerYAnchor)
        ])
        previewDriver.attachHandler = { [weak self] in self?.attachPreviewIfPossible() }
        previewDriver.detachHandler = { [weak self] in self?.detachPreview() }
        bridge.onStateChange = { [weak self] state in self?.show(state) }
        recoveryObserverToken = recoveryOwner.addStateObserver { [weak self] state, message in
            guard let self else { return }
            if message.isEmpty { self.show(state == .running ? .running : .loading) }
            else { self.show(.error(message)) }
        }
    }

    public override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        if let session = previewLayer?.session { recoveryOwner.register(session: session) }
        recoveryOwner.setSessionRestart { [weak self] in self?.restartAuthorizedPreview() }
        let authorization = AVCaptureDevice.authorizationStatus(for: .video)
        switch authorization {
        case .denied:
            recoveryOwner.handle(.permission(.denied))
            bridge.appear(authorization: .denied)
            return
        case .restricted:
            recoveryOwner.handle(.permission(.restricted))
            bridge.appear(authorization: .restricted)
            return
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                Task { @MainActor in
                    guard let self else { return }
                    if granted { self.recoveryOwner.handle(.permission(.authorized)); self.startAuthorizedPreview() }
                    else { self.recoveryOwner.handle(.permission(.denied)); self.bridge.appear(authorization: .denied) }
                }
            }
        case .authorized:
            recoveryOwner.handle(.permission(.authorized))
            startAuthorizedPreview()
        @unknown default:
            show(.unavailable)
        }
        if bridge.state == .running { notifyReadyIfNeeded() }
    }

    public override func viewDidDisappear(_ animated: Bool) {
        super.viewDidDisappear(animated)
        bridge.disappear()
        recoveryOwner.handle(.stopped)
        recoveryOwner.unregister()
    }

    deinit {
        if let recoveryObserverToken { recoveryOwner.removeStateObserver(recoveryObserverToken) }
        nextLevel.stop()
    }

    private func attachPreviewIfPossible() {
        guard previewLayer == nil else { return }
        let layer = nextLevel.previewLayer
        layer.videoGravity = .resizeAspectFill
        layer.frame = view.bounds
        view.layer.insertSublayer(layer, at: 0)
        previewLayer = layer
    }

    private func detachPreview() {
        previewLayer?.removeFromSuperlayer()
        previewLayer = nil
    }

    private func startAuthorizedPreview() {
        bridge.appear(authorization: .authorized)
        if bridge.state == .running { if let session = previewLayer?.session { recoveryOwner.register(session: session) }; recoveryOwner.handle(.started); notifyReadyIfNeeded() }
        else if case .error = bridge.state { recoveryOwner.handle(.runtimeError) }
    }

    private func notifyReadyIfNeeded() {
        guard !didNotifyReady else { return }
        didNotifyReady = true
        onReady?(nextLevel)
    }

    private func restartAuthorizedPreview() {
        let authorization = AVCaptureDevice.authorizationStatus(for: .video) == .authorized ? CameraAuthorizationStatus.authorized : .denied
        bridge.restart(authorization: authorization)
        if bridge.state == .running { recoveryOwner.handle(.restartSucceeded) } else { recoveryOwner.handle(.restartFailed) }
    }

    private func show(_ state: PreviewSurfaceState) {
        switch state {
        case .running:
            statusLabel.isHidden = true
        case .loading:
            statusLabel.isHidden = false; statusLabel.text = "Preparing camera…"
        case .denied: statusLabel.text = "Camera permission is denied. Enable it in Settings."
        case .restricted: statusLabel.text = "Camera access is restricted on this device."
        case .unavailable, .simulatorUnavailable: statusLabel.text = "Camera is unavailable on this device."
        case .error(let message): statusLabel.text = message
        }
        if state != .running { statusLabel.isHidden = false }
    }
}

public struct NextLevelPreviewBridge: UIViewControllerRepresentable {
    private let recoveryOwner: CameraRecoveryOwner
    private let onReady: ((NextLevel) -> Void)?
    public init(recoveryOwner: CameraRecoveryOwner, onReady: ((NextLevel) -> Void)? = nil) { self.recoveryOwner = recoveryOwner; self.onReady = onReady }
    public func makeUIViewController(context: Context) -> NextLevelPreviewViewController { NextLevelPreviewViewController(recoveryOwner: recoveryOwner, onReady: onReady) }
    public func updateUIViewController(_ controller: NextLevelPreviewViewController, context: Context) {}
}

@available(iOS 17.0, *)
public enum AVFoundationCameraDiscovery {
    public static func rearCandidates() -> [CameraDeviceDescriptor] {
        let types: [AVCaptureDevice.DeviceType] = [
            .builtInWideAngleCamera, .builtInUltraWideCamera, .builtInTelephotoCamera,
            .builtInDualCamera, .builtInDualWideCamera, .builtInTripleCamera
        ]
        let session = AVCaptureDevice.DiscoverySession(
            deviceTypes: types,
            mediaType: .video,
            position: .back
        )
        return session.devices.map(descriptor(for:)).sorted { $0.stableID < $1.stableID }
    }

    public static func rearDevice(for lens: CameraLensIdentity) -> AVCaptureDevice? {
        let types: [AVCaptureDevice.DeviceType] = [
            .builtInWideAngleCamera, .builtInUltraWideCamera, .builtInTelephotoCamera,
            .builtInDualCamera, .builtInDualWideCamera, .builtInTripleCamera
        ]
        return AVCaptureDevice.DiscoverySession(deviceTypes: types, mediaType: .video, position: .back)
            .devices.first { $0.uniqueID == lens.identifier }
    }

    private static func descriptor(for device: AVCaptureDevice) -> CameraDeviceDescriptor {
        let kind: CameraDeviceKind
        switch device.deviceType {
        case .builtInWideAngleCamera: kind = .wideAngle
        case .builtInUltraWideCamera: kind = .ultraWide
        case .builtInTelephotoCamera: kind = .telephoto
        case .builtInDualCamera: kind = .dual
        case .builtInDualWideCamera: kind = .dualWide
        case .builtInTripleCamera: kind = .triple
        default: kind = .other
        }
        let position: CameraPosition = device.position == .back ? .back : device.position == .front ? .front : .unspecified
        return CameraDeviceDescriptor(position: position, kind: kind, stableID: device.uniqueID)
    }
}
#else
/// Simulator and non-Apple builds never manufacture image data.
public struct NextLevelPreviewBridge: Sendable { public init() {} }
#endif
