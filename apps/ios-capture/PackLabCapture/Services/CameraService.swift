import Foundation

public enum CameraAuthorizationStatus: Sendable, Equatable {
    case unknown
    case authorized
    case denied
    case restricted
}

public enum CameraServiceState: Sendable, Equatable {
    case idle
    case running
    case unavailable
}

public enum CameraServiceError: Error, Sendable, Equatable {
    case permissionDenied
    case restricted
    case unavailable
    case failed(String)
}

public protocol CameraService: Sendable {
    func authorizationStatus() async -> CameraAuthorizationStatus
    func start() async throws
    func stop() async
    func state() async -> CameraServiceState
}

/// Foundation-only seam for a future device or NextLevel-backed camera adapter.
public actor FoundationCameraService: CameraService {
    private var currentState: CameraServiceState = .idle
    private let authorization: CameraAuthorizationStatus

    public init(authorization: CameraAuthorizationStatus = .unknown) {
        self.authorization = authorization
    }

    public func authorizationStatus() async -> CameraAuthorizationStatus {
        authorization
    }

    public func start() async throws {
        guard authorization == .authorized else {
            currentState = .unavailable
            return
        }
        currentState = .running
    }

    public func stop() async {
        currentState = .idle
    }

    public func state() async -> CameraServiceState {
        currentState
    }
}
