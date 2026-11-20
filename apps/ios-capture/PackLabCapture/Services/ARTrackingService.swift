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
import CoreImage
import ImageIO
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
    /// Still-capture seam. The default asks the real session; injected drivers override it
    /// to deliver ARKit's completion deterministically in tests.
    func captureHighResolutionFrame(completion: @escaping @Sendable (ARFrame?, (any Error)?) -> Void)
}

public extension ARSessionLifecycleDriver {
    func captureHighResolutionFrame(completion: @escaping @Sendable (ARFrame?, (any Error)?) -> Void) {
        #if targetEnvironment(simulator)
        completion(nil, CameraServiceError.unavailable)
        #else
        session.captureHighResolutionFrame(completion: completion)
        #endif
    }
}

@MainActor
private final class DeviceARSessionDriver: ARSessionLifecycleDriver {
    let session = ARSession()
    var isSupported: Bool { ARWorldTrackingConfiguration.isSupported }
    func run(resetTracking: Bool) {
        let configuration = ARWorldTrackingConfiguration()
        // Horizontal planes give the table/mat the object-center step raycasts onto.
        configuration.planeDetection = [.horizontal]
        #if !targetEnvironment(simulator)
        // The AR session is the app's only camera client, so its video format must also
        // serve high-resolution stills (ARSession.captureHighResolutionFrame).
        if let format = ARWorldTrackingConfiguration.recommendedVideoFormatForHighResolutionFrameCapturing {
            configuration.videoFormat = format
        }
        #endif
        session.run(configuration, options: resetTracking ? [.resetTracking, .removeExistingAnchors] : [])
    }
    func pause() { session.pause() }
}

/// The single owner of the rear camera. Preview (SharedARCameraPreview), world
/// tracking and high-resolution stills all use this one ARSession; nothing else
/// may open an AVCaptureSession on the capture screen. Camera availability is
/// reported to the recovery state machine through `onCameraSignal`.
@MainActor
public final class SharedARSessionOwner: NSObject, @preconcurrency ARSessionDelegate, ARHighResolutionFrameSource {
    public static let shared = SharedARSessionOwner()
    public let session: ARSession
    private let driver: any ARSessionLifecycleDriver
    public private(set) var policy = ARTrackingLifecyclePolicy()
    public private(set) var poseBuffer = PoseBuffer(capacity: 256)
    public private(set) var epochCoordinator = SessionEpochCoordinator()
    public private(set) var resetDiagnostics: [ResetDiagnosticEvent] = []
    /// Camera lifecycle signals for CameraRecoveryOwner (started, interruption, errors, stop).
    public var onCameraSignal: ((CameraRecoverySignal) -> Void)?
    private var degradedFrames = 0
    private var isStarted = false
    /// Signal to emit when the next camera frame proves the session is delivering again.
    private var pendingFrameSignal: CameraRecoverySignal?
    private var isEmittingInterruptionEnded = false
    private var stillContinuation: CheckedContinuation<ARCapturedStillFrame, Error>?
    private var stillToken = 0
    private init(driver: any ARSessionLifecycleDriver) { self.driver = driver; session = driver.session; super.init(); session.delegate = self }
    private override convenience init() { self.init(driver: DeviceARSessionDriver()) }
    public convenience init(injectedDriver: any ARSessionLifecycleDriver) { self.init(driver: injectedDriver) }

    public func start() {
        guard driver.isSupported else { policy.limited(.cameraUnavailable); return }
        guard !isStarted else { return }
        isStarted = true
        policy.started()
        pendingFrameSignal = .started
        driver.run(resetTracking: false)
    }
    public func stop() {
        guard isStarted else { return }
        isStarted = false
        pendingFrameSignal = nil
        cancelStillCapture(reason: "session_stopped")
        driver.pause()
        onCameraSignal?(.stopped)
    }
    public func reset(reason: ResetReason = .userRequested, options: ARSession.RunOptions = [.resetTracking, .removeExistingAnchors]) {
        guard driver.isSupported else { policy.limited(.cameraUnavailable); return }
        isStarted = true
        epochCoordinator.reset(reason: reason)
        resetDiagnostics.append(ResetDiagnosticEvent(epoch: epochCoordinator.epoch, reason: reason, state: epochCoordinator.state))
        policy.reset()
        driver.run(resetTracking: options.contains(.resetTracking))
    }

    /// Recovery restart (runtime error, or operator Retry after a blocked interruption).
    /// Skipped while the interruption-ended handler is itself resuming the session, so
    /// one recovery never runs the session twice.
    public func restartCamera(reason: ResetReason = .runtimeError) {
        guard !isEmittingInterruptionEnded else { return }
        pendingFrameSignal = .restartSucceeded
        reset(reason: reason)
    }

    /// Called for every delivered camera frame; the first frame after start/restart
    /// is the evidence that the camera is really running.
    public func noteFrameDelivered() {
        guard let signal = pendingFrameSignal else { return }
        pendingFrameSignal = nil
        onCameraSignal?(signal)
    }

    /// Latest camera frame for the live candidate-quality loop, reduced to a Sendable
    /// QualityImageFrame here so the pixel buffer never leaves the main actor. The
    /// timestamp is the ARFrame (pose buffer / CoreMotion uptime) domain.
    public func currentCandidateFrame() -> (frame: QualityImageFrame, timestamp: TimeInterval)? {
        guard isStarted, let current = session.currentFrame else { return nil }
        return (LiveQualityFrameSampler.qualityFrame(from: current.capturedImage), current.timestamp)
    }

    /// The AR world the current poses live in. Its origin moves with every new session and
    /// every tracking reset/interruption (epoch), so world-space points are only comparable
    /// within one identity.
    public var worldIdentity: String { "\(session.identifier.uuidString)#\(epochCoordinator.epoch)" }

    /// Raycasts from the image centre (the on-screen crosshair, aimed where the package
    /// touches the table) onto a horizontal surface: a detected plane's geometry, then an
    /// estimated horizontal plane, and only then a detected plane extended to infinity (which
    /// can be the floor under the table; ObjectCenterBuilder rejects hits far below the
    /// camera). Returns the hit,
    /// its surface normal and the camera position; nil when nothing horizontal is hit.
    public func raycastBasePlane() -> BasePlaneHit? {
        guard isStarted, let frame = session.currentFrame else { return nil }
        let crosshair = CGPoint(x: 0.5, y: 0.5)
        let attempts: [(target: ARRaycastQuery.Target, method: String)] = [
            (.existingPlaneGeometry, "base_plane_raycast"),
            (.estimatedPlane, "base_estimated_plane_raycast"),
            (.existingPlaneInfinite, "base_plane_infinite_raycast"),
        ]
        let camera = frame.camera.transform.columns.3
        for attempt in attempts {
            let query = frame.raycastQuery(from: crosshair, allowing: attempt.target, alignment: .horizontal)
            if let hit = session.raycast(query).first {
                let t = hit.worldTransform.columns.3
                let up = hit.worldTransform.columns.1
                return BasePlaneHit(position: [Double(t.x), Double(t.y), Double(t.z)], normal: [Double(up.x), Double(up.y), Double(up.z)], cameraPosition: [Double(camera.x), Double(camera.y), Double(camera.z)], method: attempt.method, worldIdentity: worldIdentity)
            }
        }
        return nil
    }

    /// Adds the exact pose of a captured still's frame to the shared buffer.
    public func recordCapturePose(_ sample: PoseSample) { poseBuffer.append(sample) }

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
        let tracking: TrackingQuality = policy.snapshot.quality == .normal ? .normal : policy.snapshot.quality
        poseBuffer.append(PoseSample(timestamp: frame.timestamp, transform: Self.rowMajor(frame.camera.transform), tracking: tracking))
        noteFrameDelivered()
    }
    /// Interruption (camera taken by another client, call, background): pose continuity
    /// is lost, so the epoch is invalidated, but the session is NOT re-run while the
    /// camera is held elsewhere. ARKit resumes it and calls sessionInterruptionEnded.
    public func sessionWasInterrupted(_ session: ARSession) {
        pendingFrameSignal = nil
        cancelStillCapture(reason: "camera_interrupted")
        epochCoordinator.reset(reason: .interruption)
        resetDiagnostics.append(ResetDiagnosticEvent(epoch: epochCoordinator.epoch, reason: .interruption, state: epochCoordinator.state))
        policy.interrupted()
        onCameraSignal?(.interruption)
    }
    public func sessionInterruptionEnded(_ session: ARSession) {
        if isStarted { driver.run(resetTracking: false); pendingFrameSignal = .restartSucceeded }
        policy.reset()
        isEmittingInterruptionEnded = true
        onCameraSignal?(.interruptionEnded)
        isEmittingInterruptionEnded = false
    }
    public func session(_ session: ARSession, didFailWithError error: Error) {
        isStarted = false
        pendingFrameSignal = nil
        cancelStillCapture(reason: "session_failed")
        epochCoordinator.failed()
        resetDiagnostics.append(ResetDiagnosticEvent(epoch: epochCoordinator.epoch, reason: .runtimeError, state: epochCoordinator.state))
        onCameraSignal?((error as? ARError)?.code == .cameraUnauthorized ? .permission(.denied) : .runtimeError)
    }

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

    // MARK: High-resolution stills from the same session

    public func captureHighResolutionStill() async throws -> ARCapturedStillFrame {
        guard isStarted else { throw CameraServiceError.unavailable }
        guard stillContinuation == nil else { throw CameraServiceError.failed("capture_in_flight") }
        stillToken += 1
        let token = stillToken
        return try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<ARCapturedStillFrame, Error>) in
            stillContinuation = continuation
            driver.captureHighResolutionFrame { frame, error in
                // The encode runs on a private serial queue, never on ARKit's completion
                // (main) queue; only the Sendable result hops back to the main actor.
                SharedARSessionOwner.encodeStill(frame: frame, error: error) { result in
                    Task { @MainActor [weak self] in self?.finishStill(token: token, result) }
                }
            }
        }
    }

    public func cancelStillCapture(reason: String) {
        finishStill(token: stillToken, .failure(CameraServiceError.failed(reason)))
    }

    private func finishStill(token: Int, _ result: Result<ARCapturedStillFrame, Error>) {
        guard token == stillToken, let continuation = stillContinuation else { return }
        stillContinuation = nil
        continuation.resume(with: result)
    }

    /// A missing frame fails with ARKit's error; a delivered frame is encoded off the main
    /// thread by `ARStillEncoder`.
    nonisolated static func encodeStill(frame: ARFrame?, error: (any Error)?, completion: @escaping @Sendable (Result<ARCapturedStillFrame, any Error>) -> Void) {
        guard let frame else {
            completion(.failure(error ?? CameraServiceError.failed("high_resolution_frame_missing")))
            return
        }
        #if targetEnvironment(simulator)
        _ = frame
        completion(.failure(CameraServiceError.unavailable))
        #else
        ARStillEncoder.shared.encode(frame, completion: completion)
        #endif
    }

    nonisolated static func rowMajor(_ m: simd_float4x4) -> [Double] {
        [m.columns.0.x, m.columns.1.x, m.columns.2.x, m.columns.3.x, m.columns.0.y, m.columns.1.y, m.columns.2.y, m.columns.3.y, m.columns.0.z, m.columns.1.z, m.columns.2.z, m.columns.3.z, m.columns.0.w, m.columns.1.w, m.columns.2.w, m.columns.3.w].map { Double($0) }
    }
}

#if !targetEnvironment(simulator)
/// Encodes high-resolution stills on a private serial queue with one reused CIContext.
/// `@unchecked Sendable`: both members are immutable, CIContext is documented as
/// thread-safe, and every encode runs serially on `queue`.
private final class ARStillEncoder: @unchecked Sendable {
    static let shared = ARStillEncoder()
    private let context = CIContext()
    private let queue = DispatchQueue(label: "com.packlab.capture.ar-still-encode", qos: .userInitiated)

    /// ARFrame is an immutable snapshot that is only read on the encode queue.
    private struct FrameBox: @unchecked Sendable { let frame: ARFrame }

    func encode(_ frame: ARFrame, completion: @escaping @Sendable (Result<ARCapturedStillFrame, any Error>) -> Void) {
        let box = FrameBox(frame: frame)
        queue.async { completion(self.encodeNow(box.frame)) }
    }

    /// HEIC in stored sensor orientation (EXIF orientation 1, no rotation claim) with
    /// ARKit's EXIF dictionary, plus the pose and intrinsics of that same frame.
    private func encodeNow(_ frame: ARFrame) -> Result<ARCapturedStillFrame, any Error> {
        let buffer = frame.capturedImage
        let dimensions = CaptureDimensions(width: CVPixelBufferGetWidth(buffer), height: CVPixelBufferGetHeight(buffer))
        let image = CIImage(cvPixelBuffer: buffer)
        let output = NSMutableData()
        guard let cgImage = context.createCGImage(image, from: image.extent),
              let destination = CGImageDestinationCreateWithData(output as CFMutableData, "public.heic" as CFString, 1, nil) else {
            return .failure(CameraServiceError.failed("still_encoding_failed"))
        }
        var properties: [CFString: Any] = [kCGImagePropertyOrientation: 1]
        properties[kCGImagePropertyExifDictionary] = frame.exifData
        CGImageDestinationAddImage(destination, cgImage, properties as CFDictionary)
        guard CGImageDestinationFinalize(destination) else { return .failure(CameraServiceError.failed("still_encoding_failed")) }
        let k = frame.camera.intrinsics
        let intrinsics: [Double] = [k.columns.0.x, k.columns.1.x, k.columns.2.x, k.columns.0.y, k.columns.1.y, k.columns.2.y, k.columns.0.z, k.columns.1.z, k.columns.2.z].map { Double($0) }
        let tracking: TrackingQuality
        switch frame.camera.trackingState {
        case .normal: tracking = .normal
        case .limited: tracking = .limited
        case .notAvailable: tracking = .unavailable
        }
        return .success(ARCapturedStillFrame(bytes: output as Data, dimensions: dimensions, timestamp: frame.timestamp, transform: SharedARSessionOwner.rowMajor(frame.camera.transform), intrinsics: intrinsics, tracking: tracking))
    }
}
#endif

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

#if canImport(RealityKit) && canImport(ARKit) && canImport(UIKit) && !targetEnvironment(simulator)
import RealityKit
import SwiftUI

/// Capture-screen camera preview rendered from the shared ARSession, so preview,
/// tracking and stills never compete for the camera with a second client.
struct SharedARCameraPreview: UIViewRepresentable {
    func makeUIView(context: Context) -> ARView {
        let view = ARView(frame: .zero, cameraMode: .ar, automaticallyConfigureSession: false)
        view.session = SharedARSessionOwner.shared.session
        return view
    }

    func updateUIView(_ uiView: ARView, context: Context) {}
}
#endif
