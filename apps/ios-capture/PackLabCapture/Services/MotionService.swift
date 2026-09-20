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

public protocol MotionService: Sendable {
    func start() async
    func stop() async
    func latestSample() async -> MotionSample?
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
}
