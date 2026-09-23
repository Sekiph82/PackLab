import CryptoKit
import Foundation

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
    public init(captureID: String, sourceBytes: Data, dimensions: CaptureDimensions, capturedAt: Date) {
        self.captureID = captureID; self.sourceBytes = sourceBytes; self.dimensions = dimensions; self.capturedAt = capturedAt
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
            return .accepted(AcceptedStill(captureID: captureID, sourceBytes: source.bytes, dimensions: source.dimensions, capturedAt: now))
        } catch { return .rejected("capture_failed") }
    }
}

public enum SourceValueStatus: String, Codable, Sendable { case available, unavailable, notRecorded }

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
            return sourceURL
        }
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

public enum PhotoMetadataBindingError: Error, Sendable, Equatable { case missingSource, idMismatch, pathMismatch, digestMismatch }

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
        case .runtimeError: state = .failed
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

#if canImport(AVFoundation)
@available(iOS 17.0, *)
public enum AVFoundationWhiteBalanceAdapter {
    public static func configure(device: AVCaptureDevice, lock: Bool = false, coordinator: CameraDeviceConfigurationCoordinator? = nil) throws -> WhiteBalanceState {
        guard device.isWhiteBalanceModeSupported(.continuousAutoWhiteBalance) else { return .unavailable }
        guard !lock else { return try lock(device: device, coordinator: coordinator) }
        if let coordinator { return try coordinator.withLockedDevice { $0.whiteBalanceMode = .continuousAutoWhiteBalance; return .stabilizing } }
        try device.lockForConfiguration(); defer { device.unlockForConfiguration() }
        device.whiteBalanceMode = .continuousAutoWhiteBalance
        return .stabilizing
    }

    public static func lock(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator? = nil) throws -> WhiteBalanceState {
        guard device.isWhiteBalanceModeSupported(.locked) else { return .failed }
        if let coordinator { return try coordinator.withLockedDevice { $0.whiteBalanceMode = .locked; return .locked } }
        try device.lockForConfiguration(); defer { device.unlockForConfiguration() }
        device.whiteBalanceMode = .locked
        return .locked
    }
}
#endif

#if canImport(AVFoundation)
@available(iOS 17.0, *)
@MainActor
public final class CameraDeviceConfigurationCoordinator {
    public let selectedLens: CameraLensIdentity
    public let device: AVCaptureDevice

    public init(device: AVCaptureDevice, selectedLens: CameraLensIdentity) {
        self.device = device
        self.selectedLens = selectedLens
    }

    public var isSelectedDevice: Bool {
        device.uniqueID == selectedLens.identifier && device.position == .back && selectedLens.position == .back && selectedLens.kind == .wideAngle
    }

    public func withLockedDevice<T>(_ operation: (AVCaptureDevice) throws -> T) throws -> T {
        try device.lockForConfiguration()
        defer { device.unlockForConfiguration() }
        return try operation(device)
    }
}

@available(iOS 17.0, *)
public enum AVFoundationExposureAdapter {
    public static func configure(device: AVCaptureDevice, bias: Float, lock: Bool = false, coordinator: CameraDeviceConfigurationCoordinator? = nil) throws -> ExposureState {
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

    public static func lock(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator? = nil) throws -> ExposureState {
        guard device.isExposureModeSupported(.locked) else { return .failed }
        return try configureLocked(device: device, coordinator: coordinator) { $0.exposureMode = .locked; return .locked }
    }

    private static func configureLocked<T>(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator?, operation: (AVCaptureDevice) throws -> T) throws -> T {
        if let coordinator { return try coordinator.withLockedDevice(operation) }
        try device.lockForConfiguration(); defer { device.unlockForConfiguration() }; return try operation(device)
    }

    private static func withConfiguration<T>(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator?, operation: (AVCaptureDevice) throws -> T) throws -> T {
        if let coordinator { return try coordinator.withLockedDevice(operation) }
        try device.lockForConfiguration(); defer { device.unlockForConfiguration() }; return try operation(device)
    }
}
#endif

#if canImport(AVFoundation) && canImport(CoreGraphics)
import AVFoundation
import CoreGraphics

@available(iOS 17.0, *)
public enum AVFoundationFocusAdapter {
    public static func configure(device: AVCaptureDevice, point: CGPoint?, lock: Bool = false, coordinator: CameraDeviceConfigurationCoordinator? = nil) throws -> FocusState {
        guard device.isFocusModeSupported(.continuousAutoFocus) else { return .unavailable }
        guard !lock else { return try lock(device: device, coordinator: coordinator) }
        let operation: (AVCaptureDevice) throws -> FocusState = { configuredDevice in
            if let point {
                guard configuredDevice.isFocusPointOfInterestSupported else { return .unavailable }
                configuredDevice.focusPointOfInterest = point
            }
            configuredDevice.focusMode = .continuousAutoFocus
            return .continuous
        }
        if let coordinator { return try coordinator.withLockedDevice(operation) }
        try device.lockForConfiguration(); defer { device.unlockForConfiguration() }; return try operation(device)
    }

    public static func lock(device: AVCaptureDevice, coordinator: CameraDeviceConfigurationCoordinator? = nil) throws -> FocusState {
        guard device.isFocusModeSupported(.locked) else { return .failed }
        if let coordinator { return try coordinator.withLockedDevice { $0.focusMode = .locked; return .locked } }
        try device.lockForConfiguration(); defer { device.unlockForConfiguration() }
        device.focusMode = .locked
        return .locked
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
    private var continuation: CheckedContinuation<(bytes: Data, dimensions: CaptureDimensions), Error>?
    public init(nextLevel: NextLevel = .shared) { self.nextLevel = nextLevel }

    public func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) {
        guard continuation == nil else { throw CameraServiceError.failed("capture_in_flight") }
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
        guard lifecycle.startIfNeeded() else { return }
        let authorization = AVCaptureDevice.authorizationStatus(for: .video)
        switch authorization {
        case .denied:
            statusLabel.isHidden = false; statusLabel.text = "Camera permission is denied. Enable it in Settings."
            return
        case .restricted:
            statusLabel.isHidden = false; statusLabel.text = "Camera access is restricted on this device."
            return
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                Task { @MainActor in
                    guard let self else { return }
                    if granted { self.startAuthorizedPreview() }
                    else { self.show(.denied) }
                }
            }
        case .authorized:
            startAuthorizedPreview()
        @unknown default:
            show(.unavailable)
        }
    }

    public override func viewDidDisappear(_ animated: Bool) {
        super.viewDidDisappear(animated)
        guard lifecycle.stopIfNeeded() else { return }
        nextLevel.stop()
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
        nextLevel.start()
        statusLabel.isHidden = true
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
