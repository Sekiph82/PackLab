import Foundation

public enum TrackingQuality: String, Codable, Sendable, Equatable { case normal, limited, unavailable, interrupted, recovering }
public enum TrackingLimitation: String, Codable, Sendable, Equatable { case initializing, excessiveMotion, insufficientFeatures, relocalizing, cameraUnavailable, unknown }

public struct TrackingSnapshot: Codable, Sendable, Equatable {
    public let quality: TrackingQuality
    public let limitation: TrackingLimitation?
    public let poseEvidenceEligible: Bool
    public let message: String
    public init(quality: TrackingQuality, limitation: TrackingLimitation? = nil, poseEvidenceEligible: Bool, message: String = "") { self.quality = quality; self.limitation = limitation; self.poseEvidenceEligible = poseEvidenceEligible; self.message = message }
}

public struct ARTrackingLifecyclePolicy: Sendable, Equatable {
    public private(set) var snapshot = TrackingSnapshot(quality: .unavailable, poseEvidenceEligible: false, message: "Tracking unavailable")
    public private(set) var epoch = 0
    public init() {}
    public mutating func started() { snapshot = TrackingSnapshot(quality: .limited, limitation: .initializing, poseEvidenceEligible: false, message: "Initializing tracking") }
    public mutating func normal() { snapshot = TrackingSnapshot(quality: .normal, poseEvidenceEligible: true, message: "Tracking ready") }
    public mutating func limited(_ reason: TrackingLimitation) { snapshot = TrackingSnapshot(quality: .limited, limitation: reason, poseEvidenceEligible: false, message: "Tracking limited: \(reason.rawValue)") }
    public mutating func interrupted() { snapshot = TrackingSnapshot(quality: .interrupted, limitation: .cameraUnavailable, poseEvidenceEligible: false, message: "Tracking interrupted") }
    public mutating func reset() { epoch += 1; snapshot = TrackingSnapshot(quality: .recovering, limitation: .relocalizing, poseEvidenceEligible: false, message: "Relocalizing") }
    public mutating func recovered() { snapshot = TrackingSnapshot(quality: .normal, poseEvidenceEligible: true, message: "Tracking recovered") }
}

#if canImport(ARKit) && canImport(UIKit)
import ARKit
import UIKit

@MainActor
public final class ARWorldTrackingController {
    private let owner: SharedARSessionOwner
    public var session: ARSession { owner.session }
    public var policy: ARTrackingLifecyclePolicy { owner.policy }
    public init(owner: SharedARSessionOwner = .shared) { self.owner = owner }
    public func start() { owner.start() }
    public func stop() { owner.stop() }
    public func reset() { owner.reset() }
}
#endif

/// ARFrame.timestamp is ARKit's session monotonic seconds-since-boot domain,
/// not UTC. The transform is the raw ARKit camera-to-world 4x4 matrix; values
/// are copied row-major and must remain finite before PackScan conversion.
public struct PoseSample: Codable, Sendable, Equatable {
    public let timestamp: TimeInterval
    public let transform: [Double]
    public let tracking: TrackingQuality
    public init(timestamp: TimeInterval, transform: [Double], tracking: TrackingQuality) { self.timestamp = timestamp; self.transform = transform; self.tracking = tracking }
    public var hasValidTransform: Bool { transform.count == 16 && transform.allSatisfy(\.isFinite) }
}

public struct AlignedPose: Codable, Sendable, Equatable {
    public let sample: PoseSample?
    public let delta: TimeInterval?
    public let status: String
    public init(sample: PoseSample?, delta: TimeInterval?, status: String) { self.sample = sample; self.delta = delta; self.status = status }
}

public enum PoseAligner {
    public static func nearest(to timestamp: TimeInterval, samples: [PoseSample], tolerance: TimeInterval = 0.1) -> AlignedPose {
        guard timestamp.isFinite, let candidate = samples.filter({ $0.timestamp.isFinite }).min(by: { abs($0.timestamp - timestamp) < abs($1.timestamp - timestamp) }) else { return AlignedPose(sample: nil, delta: nil, status: "unavailable") }
        let delta = candidate.timestamp - timestamp
        guard abs(delta) <= tolerance else { return AlignedPose(sample: nil, delta: delta, status: "stale") }
        guard candidate.hasValidTransform else { return AlignedPose(sample: nil, delta: delta, status: "invalid_transform") }
        guard candidate.tracking == .normal else { return AlignedPose(sample: nil, delta: delta, status: "unavailable") }
        return AlignedPose(sample: candidate, delta: delta, status: "available")
    }
}

public struct PoseBuffer: Sendable, Equatable {
    public let capacity: Int
    public private(set) var samples: [PoseSample] = []
    public init(capacity: Int = 256) { self.capacity = max(1, capacity) }
    public mutating func append(_ sample: PoseSample) {
        guard sample.timestamp.isFinite else { return }
        samples.append(sample)
        samples.sort { $0.timestamp < $1.timestamp }
        if samples.count > capacity { samples.removeFirst(samples.count - capacity) }
    }
    public func bind(captureID: String, timestamp: TimeInterval, tolerance: TimeInterval = 0.1) -> PoseCaptureBinding {
        PoseCaptureBinding(captureID: captureID, captureTimestamp: timestamp, aligned: PoseAligner.nearest(to: timestamp, samples: samples, tolerance: tolerance))
    }
}

public struct PoseCaptureBinding: Codable, Sendable, Equatable {
    public let captureID: String
    public let captureTimestamp: TimeInterval
    public let aligned: AlignedPose
    public init(captureID: String, captureTimestamp: TimeInterval, aligned: AlignedPose) { self.captureID = captureID; self.captureTimestamp = captureTimestamp; self.aligned = aligned }
}

public struct MotionSampleRecord: Codable, Sendable, Equatable {
    public let monotonicTimestamp: TimeInterval
    public let attitude: [Double]
    public let rotationRate: [Double]
    public init(monotonicTimestamp: TimeInterval, attitude: [Double], rotationRate: [Double]) { self.monotonicTimestamp = monotonicTimestamp; self.attitude = attitude; self.rotationRate = rotationRate }
    public var isValid: Bool { monotonicTimestamp.isFinite && attitude.count == 4 && rotationRate.count == 3 && attitude.allSatisfy(\.isFinite) && rotationRate.allSatisfy(\.isFinite) }
}

public struct MotionBuffer: Sendable, Equatable {
    public let capacity: Int
    public private(set) var samples: [MotionSampleRecord] = []
    public init(capacity: Int = 256) { self.capacity = max(1, capacity) }
    public mutating func append(_ sample: MotionSampleRecord) { guard sample.isValid else { return }; samples.append(sample); samples.sort { $0.monotonicTimestamp < $1.monotonicTimestamp }; if samples.count > capacity { samples.removeFirst(samples.count - capacity) } }
    public func nearest(to timestamp: TimeInterval, tolerance: TimeInterval = 0.1) -> MotionSampleRecord? { samples.min { abs($0.monotonicTimestamp - timestamp) < abs($1.monotonicTimestamp - timestamp) }.flatMap { abs($0.monotonicTimestamp - timestamp) <= tolerance ? $0 : nil } }
}

public struct MotionCaptureBinding: Codable, Sendable, Equatable {
    public let captureID: String
    public let captureTimestamp: TimeInterval
    public let sample: MotionSampleRecord?
    public let delta: TimeInterval?
    public let status: String
    public init(captureID: String, captureTimestamp: TimeInterval, sample: MotionSampleRecord?, delta: TimeInterval?, status: String) { self.captureID = captureID; self.captureTimestamp = captureTimestamp; self.sample = sample; self.delta = delta; self.status = status }
}

public enum MotionAligner {
    public static func bind(captureID: String, timestamp: TimeInterval, buffer: MotionBuffer, tolerance: TimeInterval = 0.1) -> MotionCaptureBinding {
        guard timestamp.isFinite, let candidate = buffer.samples.filter(\.isValid).min(by: { abs($0.monotonicTimestamp - timestamp) < abs($1.monotonicTimestamp - timestamp) }) else { return MotionCaptureBinding(captureID: captureID, captureTimestamp: timestamp, sample: nil, delta: nil, status: "unavailable") }
        let delta = candidate.monotonicTimestamp - timestamp
        guard abs(delta) <= tolerance else { return MotionCaptureBinding(captureID: captureID, captureTimestamp: timestamp, sample: nil, delta: delta, status: "stale") }
        return MotionCaptureBinding(captureID: captureID, captureTimestamp: timestamp, sample: candidate, delta: delta, status: "available")
    }
}

/// App-local and PackScan frames share a right-handed metre basis: X right,
/// Y up, camera-forward is -Z. Matrices are 4x4 row-major values and world
/// origin is the AR session origin. Image pixels are deliberately excluded.
public struct CoordinateTransform: Codable, Sendable, Equatable {
    public let values: [Double]
    public init(values: [Double]) { self.values = values }
    public static let identity = CoordinateTransform(values: [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
    public func multiplied(by other: CoordinateTransform) -> CoordinateTransform {
        guard values.count == 16, other.values.count == 16 else { return .identity }
        var result = Array(repeating: 0.0, count: 16)
        for row in 0..<4 { for column in 0..<4 { for index in 0..<4 { result[row * 4 + column] += values[row * 4 + index] * other.values[index * 4 + column] } } }
        return CoordinateTransform(values: result)
    }
    public var isFinite: Bool { values.count == 16 && values.allSatisfy { $0.isFinite } }
}

public enum PackScanCoordinateContract {
    public static let convention = "packscan_right_handed_x_right_y_up_z_out_of_screen_camera_forward_neg_z_v3"
    public static let units = "metres"
    public static func appLocalToPackScan(_ transform: CoordinateTransform) -> CoordinateTransform { transform }
}

public enum TrackingQualityClassifier {
    public static func classify(state: TrackingQuality, limitation: TrackingLimitation? = nil) -> TrackingSnapshot {
        switch state {
        case .normal: return TrackingSnapshot(quality: .normal, poseEvidenceEligible: true, message: "Tracking ready")
        case .limited: return TrackingSnapshot(quality: .limited, limitation: limitation ?? .unknown, poseEvidenceEligible: false, message: "Tracking limited")
        case .interrupted: return TrackingSnapshot(quality: .interrupted, limitation: .cameraUnavailable, poseEvidenceEligible: false, message: "Tracking interrupted")
        case .recovering: return TrackingSnapshot(quality: .recovering, limitation: .relocalizing, poseEvidenceEligible: false, message: "Relocalizing")
        case .unavailable: return TrackingSnapshot(quality: .unavailable, poseEvidenceEligible: false, message: "Tracking unavailable")
        }
    }
}

public enum ResetReason: String, Codable, Sendable, Equatable { case userRequested, trackingDegraded, interruption, runtimeError }
public enum RelocalizationState: String, Codable, Sendable, Equatable { case idle, relocalizing, recovered, failed }
public struct SessionEpochCoordinator: Sendable, Equatable {
    public private(set) var epoch = 0
    public private(set) var state: RelocalizationState = .idle
    public private(set) var lastReason: ResetReason?
    public init() {}
    public mutating func reset(reason: ResetReason) { epoch += 1; state = .relocalizing; lastReason = reason }
    public mutating func recovered() { state = .recovered }
    public mutating func failed() { state = .failed }
    public func accepts(poseEpoch: Int) -> Bool { poseEpoch == epoch && state == .recovered }
}

public struct PoseOverlayModel: Sendable, Equatable {
    public let visible: Bool
    public let lines: [String]
    public init(visible: Bool, lines: [String]) { self.visible = visible; self.lines = lines }
    public static func make(visible: Bool, tracking: TrackingSnapshot, epoch: Int, pose: PoseSample?) -> PoseOverlayModel {
        guard visible else { return PoseOverlayModel(visible: false, lines: []) }
        var lines = ["Tracking: \(tracking.quality.rawValue)", "Epoch: \(epoch)"]
        if let pose { lines.append(String(format: "Pose t=%.3fs", pose.timestamp)) }
        else { lines.append("Pose: unavailable") }
        return PoseOverlayModel(visible: true, lines: lines)
    }
}

public struct PoseDiagnosticRecord: Codable, Sendable, Equatable {
    public let captureID: String
    public let captureTimestamp: TimeInterval
    public let pose: AlignedPose
    public let motion: MotionSampleRecord?
    public let epoch: Int
    public init(captureID: String, captureTimestamp: TimeInterval, pose: AlignedPose, motion: MotionSampleRecord?, epoch: Int) { self.captureID = captureID; self.captureTimestamp = captureTimestamp; self.pose = pose; self.motion = motion; self.epoch = epoch }
}

public struct PoseDiagnosticsExport: Codable, Sendable, Equatable {
    public let schemaVersion = "1.0.0"
    public let timebase = "monotonic_seconds_since_boot"
    public let coordinateConvention = PackScanCoordinateContract.convention
    public let records: [PoseDiagnosticRecord]
    public init(records: [PoseDiagnosticRecord]) { self.records = records.sorted { $0.captureTimestamp < $1.captureTimestamp } }
}

public enum PoseDiagnosticsError: Error, Sendable, Equatable { case nonFinite, tooManyRecords }
public enum PoseDiagnosticsExporter {
    public static func encode(records: [PoseDiagnosticRecord], maximumRecords: Int = 10_000) throws -> Data {
        guard records.count <= maximumRecords else { throw PoseDiagnosticsError.tooManyRecords }
        for record in records {
            guard record.captureTimestamp.isFinite, record.pose.delta?.isFinite ?? true else { throw PoseDiagnosticsError.nonFinite }
            if let sample = record.pose.sample, !sample.transform.allSatisfy(\.isFinite) { throw PoseDiagnosticsError.nonFinite }
        }
        return try JSONEncoder.sorted.encode(PoseDiagnosticsExport(records: records))
    }
}

private extension JSONEncoder {
    static var sorted: JSONEncoder { let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys, .prettyPrinted]; return encoder }
}

#if canImport(CoreMotion)
import CoreMotion
@MainActor
public final class CoreMotionController {
    private let manager = CMMotionManager()
    public private(set) var buffer: MotionBuffer
    public init(capacity: Int = 256) { buffer = MotionBuffer(capacity: capacity) }
    public func start() {
        guard manager.isDeviceMotionAvailable else { return }
        manager.deviceMotionUpdateInterval = 1.0 / 60.0
        manager.startDeviceMotionUpdates(using: .xArbitraryZVertical, to: .main) { [weak self] motion, _ in
            guard let self, let motion else { return }
            self.buffer.append(MotionSampleRecord(monotonicTimestamp: motion.timestamp, attitude: [motion.attitude.quaternion.x, motion.attitude.quaternion.y, motion.attitude.quaternion.z, motion.attitude.quaternion.w], rotationRate: [motion.rotationRate.x, motion.rotationRate.y, motion.rotationRate.z]))
        }
    }
    public func stop() { manager.stopDeviceMotionUpdates() }
}
#endif
