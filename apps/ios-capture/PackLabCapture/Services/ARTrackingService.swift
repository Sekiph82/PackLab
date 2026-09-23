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
    func snapshot() async -> TrackingSnapshot
    func latestPose() async -> PoseSample?
    func localizationEpoch() async -> Int
    func resetDiagnostics() async -> [ResetDiagnosticEvent]
}

public extension ARTrackingService {
    func snapshot() async -> TrackingSnapshot {
        switch await state() {
        case .tracking: return TrackingSnapshot(quality: .normal, poseEvidenceEligible: true, message: "Tracking ready")
        case .limited: return TrackingSnapshot(quality: .limited, limitation: .unknown, poseEvidenceEligible: false, message: "Tracking limited")
        case .interrupted: return TrackingSnapshot(quality: .interrupted, limitation: .cameraUnavailable, poseEvidenceEligible: false, message: "Tracking interrupted")
        case .idle: return TrackingSnapshot(quality: .unavailable, poseEvidenceEligible: false, message: "Tracking idle")
        case .unavailable: return TrackingSnapshot(quality: .unavailable, poseEvidenceEligible: false, message: "Tracking unavailable")
        }
    }
    func latestPose() async -> PoseSample? { nil }
    func localizationEpoch() async -> Int { 0 }
    func resetDiagnostics() async -> [ResetDiagnosticEvent] { [] }
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
    public private(set) var resetDiagnostics: [ResetDiagnosticEvent] = []
    private var degradedFrames = 0
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
        resetDiagnostics.append(ResetDiagnosticEvent(epoch: epochCoordinator.epoch, reason: reason, state: epochCoordinator.state))
        policy.reset()
        session.run(ARWorldTrackingConfiguration(), options: options)
    }
    public func session(_ session: ARSession, cameraDidChangeTrackingState camera: ARCamera) {
        switch camera.trackingState {
        case .normal:
            degradedFrames = 0
            policy.normal()
            if epochCoordinator.state == .relocalizing { epochCoordinator.recovered(); resetDiagnostics.append(ResetDiagnosticEvent(epoch: epochCoordinator.epoch, reason: epochCoordinator.lastReason ?? .userRequested, state: epochCoordinator.state)) }
        case .limited(let reason):
            degradedFrames += 1
            switch reason { case .initializing: policy.limited(.initializing); case .excessiveMotion: policy.limited(.excessiveMotion); case .insufficientFeatures: policy.limited(.insufficientFeatures); case .relocalizing: policy.limited(.relocalizing); @unknown default: policy.limited(.unknown) }
            if degradedFrames >= 3, epochCoordinator.state != .relocalizing { reset(reason: .trackingDegraded) }
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
    public func session(_ session: ARSession, didFailWithError error: Error) { epochCoordinator.failed(); resetDiagnostics.append(ResetDiagnosticEvent(epoch: epochCoordinator.epoch, reason: .runtimeError, state: epochCoordinator.state)) }
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
    public func snapshot() async -> TrackingSnapshot { owner.policy.snapshot }
    public func latestPose() async -> PoseSample? { owner.poseBuffer.samples.last }
    public func bindPose(captureID: String, timestamp: TimeInterval, tolerance: TimeInterval = 0.1) -> PoseCaptureBinding { owner.poseBuffer.bind(captureID: captureID, timestamp: timestamp, tolerance: tolerance) }
    public func bindAcceptedStill(_ still: AcceptedStill, bridge: TimestampDomainBridge? = nil, tolerance: TimeInterval = 0.1) async -> PoseCaptureBinding? { AcceptedStillPoseBinder.bind(still: still, buffer: owner.poseBuffer, bridge: bridge, tolerance: tolerance) }
    public func localizationEpoch() async -> Int { owner.epochCoordinator.epoch }
    public func resetDiagnostics() async -> [ResetDiagnosticEvent] { owner.resetDiagnostics }
    public func reset() async { owner.reset(reason: .userRequested) }
}
#endif
