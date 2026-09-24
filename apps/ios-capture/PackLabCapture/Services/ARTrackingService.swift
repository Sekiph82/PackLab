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

public enum ARSessionTrackingEvent: Sendable, Equatable {
    case normal
    case limited(TrackingLimitation)
    case unavailable
}

@MainActor
public protocol ARSessionLifecycleDriver: AnyObject {
    var session: ARSession { get }
    var isSupported: Bool { get }
    func run(resetTracking: Bool)
    func pause()
}

@MainActor
private final class DeviceARSessionDriver: ARSessionLifecycleDriver {
    let session = ARSession()
    var isSupported: Bool { ARWorldTrackingConfiguration.isSupported }
    func run(resetTracking: Bool) {
        let configuration = ARWorldTrackingConfiguration()
        session.run(configuration, options: resetTracking ? [.resetTracking, .removeExistingAnchors] : [])
    }
    func pause() { session.pause() }
}

@MainActor
public final class SharedARSessionOwner: NSObject, ARSessionDelegate {
    public static let shared = SharedARSessionOwner()
    public let session: ARSession
    private let driver: any ARSessionLifecycleDriver
    public private(set) var policy = ARTrackingLifecyclePolicy()
    public private(set) var poseBuffer = PoseBuffer(capacity: 256)
    public private(set) var epochCoordinator = SessionEpochCoordinator()
    public private(set) var resetDiagnostics: [ResetDiagnosticEvent] = []
    private var degradedFrames = 0
    private var isStarted = false
    private init(driver: any ARSessionLifecycleDriver) { self.driver = driver; session = driver.session; super.init(); session.delegate = self }
    private convenience init() { self.init(driver: DeviceARSessionDriver()) }
    public convenience init(injectedDriver: any ARSessionLifecycleDriver) { self.init(driver: injectedDriver) }

    public func start() {
        guard driver.isSupported else { policy.limited(.cameraUnavailable); return }
        guard !isStarted else { return }
        isStarted = true
        policy.started()
        driver.run(resetTracking: false)
    }
    public func stop() { guard isStarted else { return }; isStarted = false; driver.pause() }
    public func reset(reason: ResetReason = .userRequested, options: ARSession.RunOptions = [.resetTracking, .removeExistingAnchors]) {
        guard driver.isSupported else { policy.limited(.cameraUnavailable); return }
        isStarted = true
        epochCoordinator.reset(reason: reason)
        resetDiagnostics.append(ResetDiagnosticEvent(epoch: epochCoordinator.epoch, reason: reason, state: epochCoordinator.state))
        policy.reset()
        driver.run(resetTracking: options.contains(.resetTracking))
    }
    public func session(_ session: ARSession, cameraDidChangeTrackingState camera: ARCamera) {
        switch camera.trackingState {
        case .normal:
            applyTrackingEvent(.normal)
        case .limited(let reason):
            let limitation: TrackingLimitation
            switch reason { case .initializing: limitation = .initializing; case .excessiveMotion: limitation = .excessiveMotion; case .insufficientFeatures: limitation = .insufficientFeatures; case .relocalizing: limitation = .relocalizing; @unknown default: limitation = .unknown }
            applyTrackingEvent(.limited(limitation))
        case .notAvailable: applyTrackingEvent(.unavailable)
        }
    }
    public func session(_ session: ARSession, didUpdate frame: ARFrame) {
        let m = frame.camera.transform
        let values: [Double] = [Double(m.columns.0.x), Double(m.columns.1.x), Double(m.columns.2.x), Double(m.columns.3.x), Double(m.columns.0.y), Double(m.columns.1.y), Double(m.columns.2.y), Double(m.columns.3.y), Double(m.columns.0.z), Double(m.columns.1.z), Double(m.columns.2.z), Double(m.columns.3.z), Double(m.columns.0.w), Double(m.columns.1.w), Double(m.columns.2.w), Double(m.columns.3.w)]
        let tracking: TrackingQuality = policy.snapshot.quality == .normal ? .normal : policy.snapshot.quality
        poseBuffer.append(PoseSample(timestamp: frame.timestamp, transform: values, tracking: tracking))
    }
    public func sessionWasInterrupted(_ session: ARSession) { policy.interrupted(); reset(reason: .interruption, options: []) }
    public func sessionInterruptionEnded(_ session: ARSession) { if isStarted { driver.run(resetTracking: false) }; policy.reset() }
    public func session(_ session: ARSession, didFailWithError error: Error) { isStarted = false; epochCoordinator.failed(); resetDiagnostics.append(ResetDiagnosticEvent(epoch: epochCoordinator.epoch, reason: .runtimeError, state: epochCoordinator.state)) }

    public func applyTrackingEvent(_ event: ARSessionTrackingEvent) {
        switch event {
        case .normal:
            degradedFrames = 0
            policy.normal()
            if epochCoordinator.state == .relocalizing { epochCoordinator.recovered(); resetDiagnostics.append(ResetDiagnosticEvent(epoch: epochCoordinator.epoch, reason: epochCoordinator.lastReason ?? .userRequested, state: epochCoordinator.state)) }
        case .limited(let limitation):
            degradedFrames += 1
            policy.limited(limitation)
            if degradedFrames >= 3, epochCoordinator.state != .relocalizing { reset(reason: .trackingDegraded) }
        case .unavailable:
            policy.limited(.cameraUnavailable)
        }
    }
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
