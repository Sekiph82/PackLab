import Foundation

public struct MotionSample: Sendable, Equatable {
    public let timestamp: TimeInterval
    public let accelerationX: Double
    public let accelerationY: Double
    public let accelerationZ: Double
    public let attitude: [Double]
    public let rotationRate: [Double]

    public init(timestamp: TimeInterval, accelerationX: Double, accelerationY: Double, accelerationZ: Double, attitude: [Double] = [], rotationRate: [Double] = []) {
        self.timestamp = timestamp
        self.accelerationX = accelerationX
        self.accelerationY = accelerationY
        self.accelerationZ = accelerationZ
        self.attitude = attitude
        self.rotationRate = rotationRate
    }
}

public enum MotionServiceState: Sendable, Equatable { case idle, running, unavailable, failed(String) }

public protocol MotionService: Sendable {
    func start() async
    func stop() async
    func latestSample() async -> MotionSample?
    func latestRecord() async -> MotionSampleRecord?
    func records() async -> [MotionSampleRecord]
    func state() async -> MotionServiceState
}

public extension MotionService {
    func bindAcceptedStill(_ still: AcceptedStill, tolerance: TimeInterval = 0.1) async -> MotionCaptureBinding? {
        guard let timestamp = still.monotonicTimestamp else { return nil }
        return MotionCaptureBinder.bind(captureID: still.captureID, timestamp: timestamp, records: [], tolerance: tolerance)
    }
}

public extension MotionService {
    func latestRecord() async -> MotionSampleRecord? { nil }
    func records() async -> [MotionSampleRecord] {
        guard let record = await latestRecord() else { return [] }
        return [record]
    }
    func bindCandidateMotion(captureID: String, timestamp: TimeInterval, tolerance: TimeInterval = 0.1) async -> MotionCaptureBinding {
        MotionCaptureBinder.bind(captureID: captureID, timestamp: timestamp, records: await records(), tolerance: tolerance)
    }
}

/// Foundation-only seam for a future Core Motion adapter.
public actor FoundationMotionService: MotionService {
    private var running = false
    private var sample: MotionSample?

    public init() {}

    public func start() async {
        running = true
    }

    public func stop() async {
        running = false
        sample = nil
    }

    public func latestSample() async -> MotionSample? {
        running ? sample : nil
    }

    public func state() async -> MotionServiceState { running ? .running : .idle }
}

#if canImport(CoreMotion)
import CoreMotion

@MainActor
public final class CoreMotionMotionService: MotionService {
    private let manager = CMMotionManager()
    private var latest: MotionSample?
    private var buffer = MotionBuffer(capacity: 256)
    private var currentState: MotionServiceState = .idle
    public init() {}
    public func start() async {
        guard manager.isDeviceMotionAvailable else { currentState = .unavailable; return }
        manager.deviceMotionUpdateInterval = 1.0 / 60.0
        manager.startDeviceMotionUpdates(using: .xArbitraryZVertical, to: .main) { [weak self] motion, error in
            guard let self else { return }
            if let error { self.currentState = .failed(error.localizedDescription); return }
            guard let motion else { self.currentState = .failed("motion_update_missing"); return }
            self.currentState = .running
            let record = MotionSampleRecord(monotonicTimestamp: motion.timestamp, attitude: [motion.attitude.quaternion.x, motion.attitude.quaternion.y, motion.attitude.quaternion.z, motion.attitude.quaternion.w], rotationRate: [motion.rotationRate.x, motion.rotationRate.y, motion.rotationRate.z])
            self.buffer.append(record)
            self.latest = MotionSample(timestamp: motion.timestamp, accelerationX: motion.userAcceleration.x, accelerationY: motion.userAcceleration.y, accelerationZ: motion.userAcceleration.z, attitude: record.attitude, rotationRate: record.rotationRate)
        }
    }
    public func stop() async { manager.stopDeviceMotionUpdates(); latest = nil; buffer = MotionBuffer(capacity: 256); currentState = .idle }
    public func latestSample() async -> MotionSample? { latest }
    public func latestRecord() async -> MotionSampleRecord? { buffer.samples.last }
    public func records() async -> [MotionSampleRecord] { buffer.samples }
    public func bindAcceptedStill(_ still: AcceptedStill, tolerance: TimeInterval = 0.1) async -> MotionCaptureBinding? {
        guard let timestamp = still.monotonicTimestamp else { return nil }
        return MotionAligner.bind(captureID: still.captureID, timestamp: timestamp, buffer: buffer, tolerance: tolerance)
    }
    public func state() async -> MotionServiceState { currentState }
}
#endif
