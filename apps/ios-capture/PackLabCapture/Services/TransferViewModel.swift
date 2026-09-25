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

public struct SenderTransferIdentity: Codable, Sendable, Equatable {
    public let transferID: String
    public let packageSHA256: String
    public let receiverInstanceID: String
    public init(transferID: String, packageSHA256: String, receiverInstanceID: String) { self.transferID = transferID; self.packageSHA256 = packageSHA256; self.receiverInstanceID = receiverInstanceID }
}

public final class SenderTransferIdentityStore: @unchecked Sendable {
    private let defaults: UserDefaults
    private let key = "packlab.sender.transfer.identity.v1"
    public init(defaults: UserDefaults = .standard) { self.defaults = defaults }
    public func save(_ identity: SenderTransferIdentity) throws { defaults.set(try JSONEncoder().encode(identity), forKey: key) }
    public func load() -> SenderTransferIdentity? { guard let data = defaults.data(forKey: key) else { return nil }; return try? JSONDecoder().decode(SenderTransferIdentity.self, from: data) }
    public func remove() { defaults.removeObject(forKey: key) }
}

@MainActor
public final class TransferViewModel: ObservableObject {
    @Published public private(set) var state: TransferUIState?
    private var finalizedSource: URL?
    private var transferID: String?
    private var expectedSHA256: String?
    private var networkClient: (any ProductionTransferClient)?
    private var networkRequest: TransferRequest?

    public init() {}

    public init(client: any ProductionTransferClient) { self.networkClient = client }

    public func bind(client: any ProductionTransferClient) { networkClient = client }

    public func prepare(package: FinalizedPackScanShare) {
        finalizedSource = package.packageURL
        state = TransferUIState(packageURL: package.packageURL, packageName: package.packageName, totalBytes: package.packageBytes)
    }

    public func pair(receiverIdentity: String, transferID: String, packageSHA256: String) {
        guard let current = state else { return }
        self.transferID = transferID; self.expectedSHA256 = packageSHA256
        state = TransferUIState(packageURL: current.packageURL, packageName: current.packageName, totalBytes: current.totalBytes, receiverIdentity: receiverIdentity, phase: .connecting)
    }

    public func startNetworkTransfer(_ request: TransferRequest) async {
        networkRequest = request
        guard let finalization = request.finalization, let share = try? PackScanShareCoordinator().eligiblePackage(at: request.source, finalization: finalization), let client = networkClient else { markFailure("finalized_package_required"); return }
        prepare(package: share)
        let id = request.transferID ?? UUID().uuidString
        pair(receiverIdentity: request.receiver.receiverInstanceID, transferID: id, packageSHA256: (try? SourceIntegrity.digest(Data(contentsOf: request.source))) ?? "")
        do {
            let acknowledgement = try await client.transfer(TransferRequest(source: request.source, receiver: request.receiver, pairingOffer: request.pairingOffer, pairingCode: request.pairingCode, transferID: id, finalization: finalization)) { [weak self] status in
                Task { @MainActor in self?.applyReceiverStatus(TransferReceiverStatus(transferID: status.transferID, confirmedBytes: status.confirmedBytes, totalBytes: status.totalBytes, verified: status.state == "verified" || status.state == "complete", packageSHA256: status.packageSHA256)) }
            }
            applyCompletion(acknowledgement)
        } catch { markFailure(String(describing: error)) }
    }

    public func cancelNetworkTransfer() async {
        guard let id = transferID, let client = networkClient else { cancel(); return }
        do { try await client.cancel(transferID: id); cancel() } catch { markFailure("cancel_failed") }
    }

    public func retryNetworkTransfer() async {
        guard let id = transferID, let client = networkClient else { return }
        do { let status = try await client.status(transferID: id); applyReceiverStatus(TransferReceiverStatus(transferID: status.transferID, confirmedBytes: status.confirmedBytes, totalBytes: status.totalBytes, verified: false, packageSHA256: status.packageSHA256)); if let request = networkRequest { await startNetworkTransfer(request) } } catch { markFailure("resume_failed") }
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

    public func applyCompletion(_ acknowledgement: TransferCompletionAcknowledgement) {
        applyCompletion(verified: acknowledgement.verified, authenticated: acknowledgement.authenticated, packageSHA256: acknowledgement.packageSHA256)
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

    private func markFailure(_ message: String) { if let current = state { state = TransferUIState(packageURL: current.packageURL, packageName: current.packageName, totalBytes: current.totalBytes, confirmedBytes: current.confirmedBytes, receiverIdentity: current.receiverIdentity, phase: .terminalFailure, error: message) } }

    public func sourceStillAvailable() -> Bool {
        guard let finalizedSource else { return false }
        return FileManager.default.fileExists(atPath: finalizedSource.path)
    }
}

#if canImport(SwiftUI)
import SwiftUI
public struct TransferScreen: View {
    @ObservedObject private var model: TransferViewModel
    public init(model: TransferViewModel) { self.model = model }
    public var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            if let state = model.state {
                Text(state.packageName).font(.headline)
                if let receiver = state.receiverIdentity { Text("Receiver: \(receiver)").font(.caption) }
                Text("\(state.confirmedBytes) / \(state.totalBytes) bytes · \(Int(state.percentage))%")
                ProgressView(value: state.percentage, total: 100)
                Text(state.phase.rawValue).font(.caption.monospaced())
                if let error = state.error { Text(error).foregroundStyle(.red) }
                HStack {
                    Button("Cancel") { Task { await model.cancelNetworkTransfer() } }.disabled(state.phase == .completed || state.phase == .cancelled)
                    Button("Retry") { Task { await model.retryNetworkTransfer() } }.disabled(state.phase != .cancelled && state.phase != .retryableFailure && state.phase != .terminalFailure)
                }
            } else { Text("No finalized package selected") }
        }.padding().navigationTitle("Send to PackLab")
    }
}

public struct FinalizedTransferWorkflowView: View {
    public let share: FinalizedPackScanShare
    public let finalization: SessionFinalizationRecord
    @StateObject private var pairing = PairingCoordinator()
    @StateObject private var model = TransferViewModel()
    @State private var started = false
    public init(share: FinalizedPackScanShare, finalization: SessionFinalizationRecord) { self.share = share; self.finalization = finalization }
    public var body: some View {
        Group {
            if case .paired(let identity) = pairing.state {
                TransferScreen(model: model).onAppear {
                    guard !started else { return }; started = true; model.bind(client: URLSessionTransferClient(identity: identity)); Task { await model.startNetworkTransfer(TransferRequest(source: share.packageURL, receiver: identity, pairingOffer: pairing.pairedOffer, pairingCode: pairing.pairedOffer?.pairingCode, finalization: finalization)) }
                }
            } else { PairingView(coordinator: pairing) }
        }.navigationTitle("Send to PackLab")
    }
}
#endif
