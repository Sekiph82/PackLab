import Foundation

public struct TransferRequest: Sendable, Equatable {
    public let source: URL

    public init(source: URL) {
        self.source = source
    }
}

public enum TransferResult: Sendable, Equatable {
    case transferred
    case unavailable
}

public protocol TransferService: Sendable {
    func transfer(_ request: TransferRequest) async -> TransferResult
}

/// Explicit no-op seam until a later milestone defines the transfer protocol.
public struct UnavailableTransferService: TransferService {
    public init() {}

    public func transfer(_ request: TransferRequest) async -> TransferResult {
        _ = request
        return .unavailable
    }
}
