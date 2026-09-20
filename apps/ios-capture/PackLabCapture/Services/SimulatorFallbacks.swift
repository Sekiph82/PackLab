import Foundation

public enum PackLabRuntimeEnvironment: Sendable, Equatable {
    #if targetEnvironment(simulator)
    case simulator
    #else
    case physicalDevice
    #endif

    public static var current: Self {
        #if targetEnvironment(simulator)
        .simulator
        #else
        .physicalDevice
        #endif
    }
}

public struct SimulatorFallbackCapabilities: Sendable, Equatable {
    public let environment: PackLabRuntimeEnvironment
    public let cameraAvailable: Bool
    public let arTrackingAvailable: Bool
    public let motionAvailable: Bool
    public let sensorEvidenceIsSynthetic: Bool

    public init(environment: PackLabRuntimeEnvironment = .current) {
        self.environment = environment
        self.cameraAvailable = false
        self.arTrackingAvailable = false
        self.motionAvailable = false
        self.sensorEvidenceIsSynthetic = false
    }
}

/// Explicit unavailable camera seam for simulator/bootstrap initialization.
public actor SimulatorCameraService: CameraService {
    public init() {}

    public func authorizationStatus() async -> CameraAuthorizationStatus {
        .restricted
    }

    public func start() async throws {}

    public func stop() async {}

    public func state() async -> CameraServiceState {
        .unavailable
    }
}

/// Explicit unavailable AR seam; it never returns fabricated tracking evidence.
public actor SimulatorARTrackingService: ARTrackingService {
    public init() {}

    public func start() async {}

    public func stop() async {}

    public func state() async -> ARTrackingServiceState {
        .unavailable
    }
}

/// Explicit unavailable motion seam; it never manufactures sensor samples.
public actor SimulatorMotionService: MotionService {
    public init() {}

    public func start() async {}

    public func stop() async {}

    public func latestSample() async -> MotionSample? {
        nil
    }
}
