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
public final class ARWorldTrackingController: NSObject, ARSessionDelegate {
    public let session = ARSession()
    public private(set) var policy = ARTrackingLifecyclePolicy()

    public override init() { super.init(); session.delegate = self }
    public func start() {
        guard ARWorldTrackingConfiguration.isSupported else { policy.limited(.cameraUnavailable); return }
        policy.started()
        let configuration = ARWorldTrackingConfiguration()
        session.run(configuration)
    }
    public func stop() { session.pause() }
    public func session(_ session: ARSession, cameraDidChangeTrackingState camera: ARCamera) {
        switch camera.trackingState {
        case .normal: policy.normal()
        case .limited(let reason):
            switch reason { case .initializing: policy.limited(.initializing); case .excessiveMotion: policy.limited(.excessiveMotion); case .insufficientFeatures: policy.limited(.insufficientFeatures); case .relocalizing: policy.limited(.relocalizing); @unknown default: policy.limited(.unknown) }
        case .notAvailable: policy.limited(.cameraUnavailable)
        }
    }
    public func sessionWasInterrupted(_ session: ARSession) { policy.interrupted() }
    public func sessionInterruptionEnded(_ session: ARSession) { policy.reset() }
}
#endif

public struct PoseSample: Codable, Sendable, Equatable {
    public let timestamp: TimeInterval
    public let transform: [Double]
    public let tracking: TrackingQuality
    public init(timestamp: TimeInterval, transform: [Double], tracking: TrackingQuality) { self.timestamp = timestamp; self.transform = transform; self.tracking = tracking }
}

public struct AlignedPose: Codable, Sendable, Equatable {
    public let sample: PoseSample?
    public let delta: TimeInterval?
    public let status: String
    public init(sample: PoseSample?, delta: TimeInterval?, status: String) { self.sample = sample; self.delta = delta; self.status = status }
}

public enum PoseAligner {
    public static func nearest(to timestamp: TimeInterval, samples: [PoseSample], tolerance: TimeInterval = 0.1) -> AlignedPose {
        guard let candidate = samples.min(by: { abs($0.timestamp - timestamp) < abs($1.timestamp - timestamp) }) else { return AlignedPose(sample: nil, delta: nil, status: "unavailable") }
        let delta = candidate.timestamp - timestamp
        guard abs(delta) <= tolerance else { return AlignedPose(sample: nil, delta: delta, status: "stale") }
        guard candidate.tracking != .unavailable else { return AlignedPose(sample: nil, delta: delta, status: "unavailable") }
        return AlignedPose(sample: candidate, delta: delta, status: "available")
    }
}
