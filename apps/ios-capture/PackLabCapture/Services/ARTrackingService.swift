import Foundation

public enum ARTrackingServiceState: Sendable, Equatable {
    case idle
    case tracking
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
