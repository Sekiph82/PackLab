import Foundation

public struct MotionSample: Sendable, Equatable {
    public let timestamp: TimeInterval
    public let accelerationX: Double
    public let accelerationY: Double
    public let accelerationZ: Double

    public init(timestamp: TimeInterval, accelerationX: Double, accelerationY: Double, accelerationZ: Double) {
        self.timestamp = timestamp
        self.accelerationX = accelerationX
        self.accelerationY = accelerationY
        self.accelerationZ = accelerationZ
    }
}

public enum MotionServiceState: Sendable, Equatable { case idle, running, unavailable, failed(String) }

public protocol MotionService: Sendable {
    func start() async
    func stop() async
    func latestSample() async -> MotionSample?
    func state() async -> MotionServiceState
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
            self.latest = MotionSample(timestamp: motion.timestamp, accelerationX: motion.userAcceleration.x, accelerationY: motion.userAcceleration.y, accelerationZ: motion.userAcceleration.z)
        }
    }
    public func stop() async { manager.stopDeviceMotionUpdates(); latest = nil; currentState = .idle }
    public func latestSample() async -> MotionSample? { latest }
    public func state() async -> MotionServiceState { currentState }
}
#endif
