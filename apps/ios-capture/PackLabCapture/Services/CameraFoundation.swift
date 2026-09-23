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
    public static func configure(device: AVCaptureDevice, lock: Bool) throws -> WhiteBalanceState {
        guard device.isWhiteBalanceModeSupported(.continuousAutoWhiteBalance) else { return .unavailable }
        try device.lockForConfiguration()
        defer { device.unlockForConfiguration() }
        device.whiteBalanceMode = .continuousAutoWhiteBalance
        if lock {
            guard device.isWhiteBalanceModeSupported(.locked) else { return .failed }
            device.whiteBalanceMode = .locked
            return .locked
        }
        return .stabilizing
    }
}
#endif

#if canImport(AVFoundation)
@available(iOS 17.0, *)
public enum AVFoundationExposureAdapter {
    public static func configure(device: AVCaptureDevice, bias: Float, lock: Bool) throws -> ExposureState {
        guard device.isExposureModeSupported(.continuousAutoExposure) else { return .unavailable }
        try device.lockForConfiguration()
        defer { device.unlockForConfiguration() }
        device.exposureMode = .continuousAutoExposure
        device.setExposureTargetBias(min(max(bias, device.minExposureTargetBias), device.maxExposureTargetBias))
        if lock {
            guard device.isExposureModeSupported(.locked) else { return .failed }
            device.exposureMode = .locked
            return .locked
        }
        return .metering
    }
}
#endif

#if canImport(AVFoundation) && canImport(CoreGraphics)
import AVFoundation
import CoreGraphics

@available(iOS 17.0, *)
public enum AVFoundationFocusAdapter {
    public static func configure(device: AVCaptureDevice, point: CGPoint?, lock: Bool) throws -> FocusState {
        guard device.isFocusModeSupported(.continuousAutoFocus) else { return .unavailable }
        try device.lockForConfiguration()
        defer { device.unlockForConfiguration() }
        if let point {
            guard device.isFocusPointOfInterestSupported else { return .unavailable }
            device.focusPointOfInterest = point
        }
        device.focusMode = .continuousAutoFocus
        if lock {
            guard device.isFocusModeSupported(.locked) else { return .failed }
            device.focusMode = .locked
            return .locked
        }
        return .continuous
    }
}
#endif

#if canImport(NextLevel) && canImport(UIKit)
import NextLevel
import UIKit

@MainActor
public final class NextLevelStillCaptureAdapter: StillPhotoBackend {
    private let nextLevel: NextLevel
    public init(nextLevel: NextLevel = .shared) { self.nextLevel = nextLevel }
    public func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) {
        // NextLevel delivers the original photo through its photo delegate. The
        // delegate handoff is intentionally kept here, outside SwiftUI.
        throw CameraServiceError.unavailable
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
        guard lifecycle.startIfNeeded() else { return }
        nextLevel.start()
        statusLabel.text = "Camera preview running"
    }

    public override func viewDidDisappear(_ animated: Bool) {
        super.viewDidDisappear(animated)
        guard lifecycle.stopIfNeeded() else { return }
        nextLevel.stop()
        detachPreview()
    }

    deinit { nextLevel.stop() }

    private func attachPreviewIfPossible() {
        lifecycle.attach()
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
        lifecycle.detach()
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
