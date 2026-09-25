import Combine
import Foundation

public enum TransferUIPhase: String, Sendable, Equatable {
    case pairingRequired = "pairing_required"
    case connecting
    case transferring
    case verifying
    case completed
    case cancelled
    case retryableFailure = "retryable_failure"
    case terminalFailure = "terminal_failure"
}

public struct TransferUIState: Sendable, Equatable {
    public let packageURL: URL
    public let packageName: String
    public let totalBytes: Int
    public let confirmedBytes: Int
    public let receiverIdentity: String?
    public let phase: TransferUIPhase
    public let error: String?

    public var percentage: Double { totalBytes == 0 ? 0 : min(100, Double(confirmedBytes) / Double(totalBytes) * 100) }

    public init(packageURL: URL, packageName: String, totalBytes: Int, confirmedBytes: Int = 0, receiverIdentity: String? = nil, phase: TransferUIPhase = .pairingRequired, error: String? = nil) {
        self.packageURL = packageURL
        self.packageName = packageName
        self.totalBytes = totalBytes
        self.confirmedBytes = confirmedBytes
        self.receiverIdentity = receiverIdentity
        self.phase = phase
        self.error = error
    }
}

public struct TransferReceiverStatus: Sendable, Equatable {
    public let transferID: String
    public let confirmedBytes: Int
    public let totalBytes: Int
    public let verified: Bool
    public let packageSHA256: String
    public init(transferID: String, confirmedBytes: Int, totalBytes: Int, verified: Bool, packageSHA256: String) {
        self.transferID = transferID; self.confirmedBytes = confirmedBytes; self.totalBytes = totalBytes; self.verified = verified; self.packageSHA256 = packageSHA256
    }
}

@MainActor
public final class TransferViewModel: ObservableObject {
    @Published public private(set) var state: TransferUIState?
    private var finalizedSource: URL?
    private var transferID: String?
    private var expectedSHA256: String?

    public init() {}

    public func prepare(package: FinalizedPackScanShare) {
        finalizedSource = package.packageURL
        state = TransferUIState(packageURL: package.packageURL, packageName: package.packageName, totalBytes: package.packageBytes)
    }

    public func pair(receiverIdentity: String, transferID: String, packageSHA256: String) {
        guard let current = state else { return }
        self.transferID = transferID; self.expectedSHA256 = packageSHA256
        state = TransferUIState(packageURL: current.packageURL, packageName: current.packageName, totalBytes: current.totalBytes, receiverIdentity: receiverIdentity, phase: .connecting)
    }

    /// `confirmedBytes` must come from the receiver's authoritative status.
    public func applyReceiverStatus(_ status: TransferReceiverStatus) {
        guard let current = state, status.transferID == transferID, status.totalBytes == current.totalBytes, status.confirmedBytes >= current.confirmedBytes, status.confirmedBytes <= status.totalBytes else { return }
        let phase: TransferUIPhase = status.verified ? .verifying : (status.confirmedBytes == status.totalBytes ? .verifying : .transferring)
        state = TransferUIState(packageURL: current.packageURL, packageName: current.packageName, totalBytes: current.totalBytes, confirmedBytes: status.confirmedBytes, receiverIdentity: current.receiverIdentity, phase: phase)
    }

    public func applyCompletion(verified: Bool, authenticated: Bool, packageSHA256: String) {
        guard let current = state, authenticated, verified, packageSHA256 == expectedSHA256, current.confirmedBytes == current.totalBytes else {
            state = state.map { TransferUIState(packageURL: $0.packageURL, packageName: $0.packageName, totalBytes: $0.totalBytes, confirmedBytes: $0.confirmedBytes, receiverIdentity: $0.receiverIdentity, phase: .retryableFailure, error: "verified_receiver_acknowledgement_required") }
            return
        }
        state = TransferUIState(packageURL: current.packageURL, packageName: current.packageName, totalBytes: current.totalBytes, confirmedBytes: current.totalBytes, receiverIdentity: current.receiverIdentity, phase: .completed)
    }

    public func cancel() {
        guard let current = state, current.phase != .completed else { return }
        state = TransferUIState(packageURL: current.packageURL, packageName: current.packageName, totalBytes: current.totalBytes, confirmedBytes: current.confirmedBytes, receiverIdentity: current.receiverIdentity, phase: .cancelled)
    }

    public func retryFromAuthoritativeStatus(_ status: TransferReceiverStatus) {
        guard let current = state, current.phase == .cancelled || current.phase == .retryableFailure else { return }
        applyReceiverStatus(status)
        if let refreshed = self.state { state = TransferUIState(packageURL: refreshed.packageURL, packageName: refreshed.packageName, totalBytes: refreshed.totalBytes, confirmedBytes: refreshed.confirmedBytes, receiverIdentity: refreshed.receiverIdentity, phase: .transferring) }
    }

    public func sourceStillAvailable() -> Bool {
        guard let finalizedSource else { return false }
        return FileManager.default.fileExists(atPath: finalizedSource.path)
    }
}
