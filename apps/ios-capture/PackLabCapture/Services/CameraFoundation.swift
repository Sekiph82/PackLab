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

public actor HealthGatedStillPhotoBackend: StillPhotoBackend {
    private let backend: any StillPhotoBackend
    private var admission = CaptureAdmissionController()
    public init(backend: any StillPhotoBackend) { self.backend = backend }
    public func update(_ admission: CaptureAdmissionController) { self.admission = admission }
    public func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) {
        guard admission.allowsCapture else { throw CameraServiceError.failed(admission.rejectReason() ?? "capture_blocked") }
        return try await backend.requestOriginalStill()
    }
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
            return .accepted(AcceptedStill(captureID: captureID, sourceBytes: source.bytes, dimensions: source.dimensions, capturedAt: now, monotonicTimestamp: ProcessInfo.processInfo.systemUptime))
        } catch { return .rejected("capture_failed") }
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
            guard raw.isFinite, raw.rounded() == raw, raw >= 1, raw <= 1_000_000, source(metadata.iso.source) != nil else { throw PhotoMetadataBindingError.schemaViolation }
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

public enum CameraRecoverySignal: Sendable, Equatable { case permission(CameraAuthorizationStatus), interruption, interruptionEnded, runtimeError, started, stopped }

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
    private var cancelInFlight: (() -> Void)?
    private var restartSession: (() -> Void)?
    public var onStateChange: ((CameraRecoveryState, String) -> Void)?

    public init() {}

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
        case .stopped: _ = machine.apply(.stop)
        }
        onStateChange?(machine.state, machine.userMessage)
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

#if canImport(AVFoundation)
public enum CameraConfigurationError: Error, Sendable, Equatable { case nonSelectedDevice, stabilizationRequired }

@available(iOS 17.0, *)
public enum AVFoundationWhiteBalanceAdapter {
    public static func configure(device: AVCaptureDevice, lock: Bool = false, coordinator: CameraDeviceConfigurationCoordinator) throws -> WhiteBalanceState {
        try coordinator.requireSelected(device)
        guard device.isWhiteBalanceModeSupported(.continuousAutoWhiteBalance) else { return .unavailable }
        guard !lock else { return try self.lock(device: device, coordinator: coordinator) }
        return try coordinator.withLockedDevice { $0.whiteBalanceMode = .continuousAutoWhiteBalance; return .stabilizing }
    }

    public static func lock(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator) throws -> WhiteBalanceState {
        try coordinator.requireSelected(device)
        guard coordinator.whiteBalanceIsStable, !device.isAdjustingWhiteBalance else { throw CameraConfigurationError.stabilizationRequired }
        guard device.isWhiteBalanceModeSupported(.locked) else { return .failed }
        return try coordinator.withLockedDevice { $0.whiteBalanceMode = .locked; return .locked }
    }

    public static func observedTemperatureKelvin(device: AVCaptureDevice) -> WhiteBalanceCaptureReading? {
        let values = device.temperatureAndTintValues(for: device.deviceWhiteBalanceGains)
        let reading = WhiteBalanceCaptureReading(temperatureKelvin: Double(values.temperature))
        return reading.isValid ? reading : nil
    }

    public static func observe(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator) throws -> WhiteBalanceState {
        try coordinator.requireSelected(device)
        try coordinator.observeWhiteBalance(isAdjusting: device.isAdjustingWhiteBalance)
        return device.isAdjustingWhiteBalance ? .stabilizing : .stabilizing
    }
}
#endif

#if canImport(AVFoundation)
@available(iOS 17.0, *)
@MainActor
public final class CameraDeviceConfigurationCoordinator {
    public let selectedLens: CameraLensIdentity
    public let device: AVCaptureDevice
    private var focusObservedStable = false
    private var whiteBalanceObservedStable = false

    public init(device: AVCaptureDevice, selectedLens: CameraLensIdentity) {
        self.device = device
        self.selectedLens = selectedLens
    }

    public var isSelectedDevice: Bool {
        device.uniqueID == selectedLens.identifier && device.position == .back && selectedLens.position == .back && selectedLens.kind == .wideAngle
    }

    public func requireSelected(_ candidate: AVCaptureDevice) throws {
        guard isSelectedDevice, candidate.uniqueID == device.uniqueID else { throw CameraConfigurationError.nonSelectedDevice }
    }
    public func observeFocus(isAdjusting: Bool) throws { try requireSelected(device); if !isAdjusting { focusObservedStable = true } }
    public func observeWhiteBalance(isAdjusting: Bool) throws { try requireSelected(device); if !isAdjusting { whiteBalanceObservedStable = true } }
    public var focusIsStable: Bool { focusObservedStable }
    public var whiteBalanceIsStable: Bool { whiteBalanceObservedStable }

    public func withLockedDevice<T>(_ operation: (AVCaptureDevice) throws -> T) throws -> T {
        try device.lockForConfiguration()
        defer { device.unlockForConfiguration() }
        return try operation(device)
    }
}

@available(iOS 17.0, *)
public enum AVFoundationExposureAdapter {
    public static func configure(device: AVCaptureDevice, bias: Float, lock: Bool = false, coordinator: CameraDeviceConfigurationCoordinator) throws -> ExposureState {
        try coordinator.requireSelected(device)
        guard device.isExposureModeSupported(.continuousAutoExposure) else { return .unavailable }
        let result = try withConfiguration(device: device, coordinator: coordinator) { configuredDevice in
            configuredDevice.exposureMode = .continuousAutoExposure
            configuredDevice.setExposureTargetBias(min(max(bias, configuredDevice.minExposureTargetBias), configuredDevice.maxExposureTargetBias))
            return ExposureState.metering
        }
        // Locking is a separate operation so callers can wait for observed
        // metering stabilization. The legacy flag is intentionally ignored.
        _ = lock
        return result
    }

    public static func lock(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator) throws -> ExposureState {
        try coordinator.requireSelected(device)
        guard device.isExposureModeSupported(.locked) else { return .failed }
        return try configureLocked(device: device, coordinator: coordinator) { $0.exposureMode = .locked; return .locked }
    }

    public static func observedReading(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator) throws -> ExposureCaptureReading {
        try coordinator.requireSelected(device)
        let reading = ExposureCaptureReading(exposureSeconds: device.exposureDuration.seconds, iso: Int(device.iso), bias: device.exposureTargetBias)
        guard reading.isValid else { throw ExposureCaptureBindingError.invalidReading }
        return reading
    }

    private static func configureLocked<T>(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator, operation: (AVCaptureDevice) throws -> T) throws -> T {
        try coordinator.requireSelected(device)
        return try coordinator.withLockedDevice(operation)
    }

    private static func withConfiguration<T>(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator, operation: (AVCaptureDevice) throws -> T) throws -> T {
        try coordinator.requireSelected(device)
        return try coordinator.withLockedDevice(operation)
    }
}
#endif

#if canImport(AVFoundation) && canImport(CoreGraphics)
import AVFoundation
import CoreGraphics

@available(iOS 17.0, *)
public enum AVFoundationFocusAdapter {
    public static func configure(device: AVCaptureDevice, point: CGPoint?, lock: Bool = false, coordinator: CameraDeviceConfigurationCoordinator) throws -> FocusState {
        try coordinator.requireSelected(device)
        guard device.isFocusModeSupported(.continuousAutoFocus) else { return .unavailable }
        guard !lock else { return try lock(device: device, coordinator: coordinator) }
        let operation: (AVCaptureDevice) throws -> FocusState = { configuredDevice in
            if let point {
                guard configuredDevice.isFocusPointOfInterestSupported else { return .unavailable }
                configuredDevice.focusPointOfInterest = point
            }
            configuredDevice.focusMode = .continuousAutoFocus
            return .focusing
        }
        return try coordinator.withLockedDevice(operation)
    }

    public static func lock(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator) throws -> FocusState {
        try coordinator.requireSelected(device)
        guard coordinator.focusIsStable, !device.isAdjustingFocus else { throw CameraConfigurationError.stabilizationRequired }
        guard device.isFocusModeSupported(.locked) else { return .failed }
        return try coordinator.withLockedDevice { $0.focusMode = .locked; return .locked }
    }

    public static func observe(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator) throws -> FocusState {
        try coordinator.requireSelected(device)
        try coordinator.observeFocus(isAdjusting: device.isAdjustingFocus)
        return device.isAdjustingFocus ? .focusing : .continuous
    }
}
#endif

#if canImport(NextLevel) && canImport(UIKit)
import NextLevel
import UIKit
#if canImport(AVFoundation)
import AVFoundation
#endif

@MainActor
public final class NextLevelStillCaptureAdapter: NSObject, StillPhotoBackend, NextLevelPhotoDelegate {
    private let nextLevel: NextLevel
    public let selectedLens: CameraLensIdentity
    private let activeLensIdentifier: () -> String?
    private var continuation: CheckedContinuation<(bytes: Data, dimensions: CaptureDimensions), Error>?
    public init(nextLevel: NextLevel, selectedLens: CameraLensIdentity, activeLensIdentifier: @escaping () -> String?) {
        self.nextLevel = nextLevel
        self.selectedLens = selectedLens
        self.activeLensIdentifier = activeLensIdentifier
    }

    public func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) {
        guard continuation == nil else { throw CameraServiceError.failed("capture_in_flight") }
        guard activeLensIdentifier() == selectedLens.identifier else { throw CameraServiceError.failed("selected_lens_mismatch") }
        nextLevel.photoConfiguration.isHighResolutionEnabled = true
        nextLevel.photoDelegate = self
        return try await withTaskCancellationHandler(operation: {
            try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<(bytes: Data, dimensions: CaptureDimensions), Error>) in
                self.continuation = continuation
                guard self.nextLevel.canCapturePhoto else {
                    self.finish(.failure(CameraServiceError.unavailable))
                    return
                }
                self.nextLevel.capturePhoto()
            }
        }, onCancel: {
            Task { @MainActor in self.finish(.failure(CameraServiceError.failed("capture_cancelled"))) }
        })
    }

    public func sessionDidStop() { finish(.failure(CameraServiceError.failed("session_stopped"))) }

    #if canImport(AVFoundation)
    public func bind(to recoveryOwner: CameraRecoveryOwner) {
        recoveryOwner.setInFlightCancellation { [weak self] in self?.sessionDidStop() }
    }
    #endif

    private func finish(_ result: Result<(bytes: Data, dimensions: CaptureDimensions), Error>) {
        guard let continuation else { return }
        self.continuation = nil
        if nextLevel.photoDelegate === self { nextLevel.photoDelegate = nil }
        continuation.resume(with: result)
    }

    public func nextLevel(_ nextLevel: NextLevel, output: AVCapturePhotoOutput, willBeginCaptureFor resolvedSettings: AVCaptureResolvedPhotoSettings, photoConfiguration: NextLevelPhotoConfiguration) {}
    public func nextLevel(_ nextLevel: NextLevel, output: AVCapturePhotoOutput, willCapturePhotoFor resolvedSettings: AVCaptureResolvedPhotoSettings, photoConfiguration: NextLevelPhotoConfiguration) {}
    public func nextLevel(_ nextLevel: NextLevel, output: AVCapturePhotoOutput, didCapturePhotoFor resolvedSettings: AVCaptureResolvedPhotoSettings, photoConfiguration: NextLevelPhotoConfiguration) {}

    public func nextLevel(_ nextLevel: NextLevel, didFinishProcessingPhoto photo: AVCapturePhoto, photoDict: [String: Any], photoConfiguration: NextLevelPhotoConfiguration) {
        guard let bytes = photo.fileDataRepresentation(), !bytes.isEmpty else {
            finish(.failure(CameraServiceError.failed("photo_data_missing")))
            return
        }
        let dimensions = photo.resolvedSettings.photoDimensions
        guard dimensions.width > 0, dimensions.height > 0 else {
            finish(.failure(CameraServiceError.failed("photo_dimensions_missing")))
            return
        }
        finish(.success((bytes: bytes, dimensions: CaptureDimensions(width: Int(dimensions.width), height: Int(dimensions.height)))))
    }

    public func nextLevelDidCompletePhotoCapture(_ nextLevel: NextLevel) {
        if continuation != nil { finish(.failure(CameraServiceError.failed("photo_capture_completed_without_data"))) }
    }
}
#endif

#if canImport(UIKit) && canImport(AVFoundation) && canImport(NextLevel)
import AVFoundation
import NextLevel
import UIKit

/// UIKit owns the actual NextLevel preview layer; SwiftUI only presents it.
@MainActor
public final class NextLevelPreviewViewController: UIViewController {
    private let nextLevel: NextLevel
    private let statusLabel = UILabel()
    private var lifecycle = PreviewLifecyclePolicy()
    private var previewLayer: AVCaptureVideoPreviewLayer?
    private let recoveryOwner = CameraRecoveryOwner()

    public init(nextLevel: NextLevel = .shared) {
        self.nextLevel = nextLevel
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
        attachPreviewIfPossible()
    }

    public override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        if previewLayer == nil { attachPreviewIfPossible() }
        if let session = previewLayer?.session { recoveryOwner.register(session: session) }
        recoveryOwner.setSessionRestart { [weak self] in self?.restartAuthorizedPreview() }
        let authorization = AVCaptureDevice.authorizationStatus(for: .video)
        switch authorization {
        case .denied:
            recoveryOwner.handle(.permission(.denied))
            statusLabel.isHidden = false; statusLabel.text = "Camera permission is denied. Enable it in Settings."
            return
        case .restricted:
            recoveryOwner.handle(.permission(.restricted))
            statusLabel.isHidden = false; statusLabel.text = "Camera access is restricted on this device."
            return
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                Task { @MainActor in
                    guard let self else { return }
                    if granted { self.recoveryOwner.handle(.permission(.authorized)); self.startAuthorizedPreview() }
                    else { self.recoveryOwner.handle(.permission(.denied)); self.show(.denied) }
                }
            }
        case .authorized:
            recoveryOwner.handle(.permission(.authorized))
            startAuthorizedPreview()
        @unknown default:
            show(.unavailable)
        }
    }

    public override func viewDidDisappear(_ animated: Bool) {
        super.viewDidDisappear(animated)
        _ = lifecycle.stopIfNeeded()
        nextLevel.stop()
        recoveryOwner.handle(.stopped)
        recoveryOwner.unregister()
        detachPreview()
    }

    deinit { nextLevel.stop() }

    private func attachPreviewIfPossible() {
        lifecycle.attachIfNeeded()
        let layer = nextLevel.previewLayer
        layer.videoGravity = .resizeAspectFill
        layer.frame = view.bounds
        view.layer.insertSublayer(layer, at: 0)
        previewLayer = layer
        statusLabel.isHidden = true
    }

    private func detachPreview() {
        previewLayer?.removeFromSuperlayer()
        previewLayer = nil
        lifecycle.detachIfNeeded()
    }

    private func startAuthorizedPreview() {
        guard lifecycle.beginAuthorizedStart(.authorized) else { return }
        do {
            try nextLevel.start()
            lifecycle.markStartedAfterSuccessfulStart()
            recoveryOwner.handle(.started)
            statusLabel.isHidden = true
        } catch {
            _ = lifecycle.stopIfNeeded()
            recoveryOwner.handle(.runtimeError)
            show(.error("Camera failed to start. Try again."))
        }
    }

    private func restartAuthorizedPreview() {
        guard AVCaptureDevice.authorizationStatus(for: .video) == .authorized else { recoveryOwner.handle(.permission(.denied)); return }
        nextLevel.stop()
        do { try nextLevel.start(); recoveryOwner.handle(.restartSucceeded) }
        catch { recoveryOwner.handle(.restartFailed); show(.error("Camera failed to restart. Try again.")) }
    }

    private func show(_ state: PreviewSurfaceState) {
        statusLabel.isHidden = false
        switch state {
        case .denied: statusLabel.text = "Camera permission is denied. Enable it in Settings."
        case .restricted: statusLabel.text = "Camera access is restricted on this device."
        case .unavailable, .simulatorUnavailable: statusLabel.text = "Camera is unavailable on this device."
        case .error(let message): statusLabel.text = message
        default: statusLabel.text = "Camera is unavailable."
        }
    }
}

public struct NextLevelPreviewBridge: UIViewControllerRepresentable {
    public init() {}
    public func makeUIViewController(context: Context) -> NextLevelPreviewViewController { NextLevelPreviewViewController() }
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
