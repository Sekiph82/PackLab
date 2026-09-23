import Foundation

public enum ARTrackingServiceState: Sendable, Equatable {
    case idle
    case tracking
    case limited
    case interrupted
    case unavailable
}

public protocol ARTrackingService: Sendable {
    func start() async
    func stop() async
    func state() async -> ARTrackingServiceState
}

/// Foundation-only seam for a future ARKit adapter owned by this service.
public actor FoundationARTrackingService: ARTrackingService {
    private var currentState: ARTrackingServiceState = .idle
    private let isAvailable: Bool

    public init(isAvailable: Bool = false) {
        self.isAvailable = isAvailable
    }

    public func start() async {
        currentState = isAvailable ? .tracking : .unavailable
    }

    public func stop() async {
        currentState = .idle
    }

    public func state() async -> ARTrackingServiceState {
        currentState
    }
}

#if canImport(ARKit) && canImport(UIKit)
import ARKit
import UIKit

@MainActor
public final class SharedARSessionOwner: NSObject, ARSessionDelegate {
    public static let shared = SharedARSessionOwner()
    public let session = ARSession()
    public private(set) var policy = ARTrackingLifecyclePolicy()
    public private(set) var poseBuffer = PoseBuffer(capacity: 256)
    public private(set) var epochCoordinator = SessionEpochCoordinator()
    private override init() { super.init(); session.delegate = self }

    public func start() {
        guard ARWorldTrackingConfiguration.isSupported else { policy.limited(.cameraUnavailable); return }
        policy.started()
        session.run(ARWorldTrackingConfiguration())
    }
    public func stop() { session.pause() }
    public func reset(reason: ResetReason = .userRequested, options: ARSession.RunOptions = [.resetTracking, .removeExistingAnchors]) {
        guard ARWorldTrackingConfiguration.isSupported else { policy.limited(.cameraUnavailable); return }
        epochCoordinator.reset(reason: reason)
        policy.reset()
        session.run(ARWorldTrackingConfiguration(), options: options)
    }
    public func session(_ session: ARSession, cameraDidChangeTrackingState camera: ARCamera) {
        switch camera.trackingState {
        case .normal: policy.normal()
        case .limited(let reason):
            switch reason { case .initializing: policy.limited(.initializing); case .excessiveMotion: policy.limited(.excessiveMotion); case .insufficientFeatures: policy.limited(.insufficientFeatures); case .relocalizing: policy.limited(.relocalizing); @unknown default: policy.limited(.unknown) }
        case .notAvailable: policy.limited(.cameraUnavailable)
        }
    }
    public func session(_ session: ARSession, didUpdate frame: ARFrame) {
        let m = frame.camera.transform
        let values: [Double] = [Double(m.columns.0.x), Double(m.columns.1.x), Double(m.columns.2.x), Double(m.columns.3.x), Double(m.columns.0.y), Double(m.columns.1.y), Double(m.columns.2.y), Double(m.columns.3.y), Double(m.columns.0.z), Double(m.columns.1.z), Double(m.columns.2.z), Double(m.columns.3.z), Double(m.columns.0.w), Double(m.columns.1.w), Double(m.columns.2.w), Double(m.columns.3.w)]
        let tracking: TrackingQuality = policy.snapshot.quality == .normal ? .normal : policy.snapshot.quality
        poseBuffer.append(PoseSample(timestamp: frame.timestamp, transform: values, tracking: tracking))
    }
    public func sessionWasInterrupted(_ session: ARSession) { policy.interrupted() }
    public func sessionInterruptionEnded(_ session: ARSession) { reset(reason: .interruption) }
}

@MainActor
public final class ARKitTrackingService: ARTrackingService {
    private let owner: SharedARSessionOwner
    public init(owner: SharedARSessionOwner = .shared) { self.owner = owner }
    public func start() async { owner.start() }
    public func stop() async { owner.stop() }
    public func state() async -> ARTrackingServiceState {
        switch owner.policy.snapshot.quality { case .normal: return .tracking; case .limited, .recovering: return .limited; case .interrupted: return .interrupted; case .unavailable: return .unavailable }
    }
    public func snapshot() -> TrackingSnapshot { owner.policy.snapshot }
    public func bindPose(captureID: String, timestamp: TimeInterval, tolerance: TimeInterval = 0.1) -> PoseCaptureBinding { owner.poseBuffer.bind(captureID: captureID, timestamp: timestamp, tolerance: tolerance) }
    public func reset() async { owner.reset(reason: .userRequested) }
}
#endif
