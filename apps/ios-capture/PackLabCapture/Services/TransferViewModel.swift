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
    public var progressDescription: String { "\(confirmedBytes) / \(totalBytes) bytes · \(Int(percentage))%" }
    public var canCancel: Bool { phase != .completed && phase != .cancelled }
    public var canRetry: Bool { phase == .cancelled || phase == .retryableFailure || phase == .terminalFailure }

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
    private let identityStore: SenderTransferIdentityStore

    public init(store: SenderTransferIdentityStore = SenderTransferIdentityStore()) { self.identityStore = store }

    public init(client: any ProductionTransferClient, store: SenderTransferIdentityStore = SenderTransferIdentityStore()) { self.networkClient = client; self.identityStore = store }

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
        guard let finalization = request.finalization, let share = try? PackScanShareCoordinator().eligiblePackage(at: request.source, finalization: finalization), let client = networkClient else { markFailure("finalized_package_required"); return }
        prepare(package: share)
        guard let packageData = try? Data(contentsOf: request.source) else { markFailure("finalized_package_unavailable"); return }
        let digest = SourceIntegrity.digest(packageData)
        if let expected = finalization.packageSHA256, expected != digest { markFailure("finalized_package_digest_mismatch"); return }
        let saved = identityStore.load()
        if let saved, request.transferID == nil, (saved.packageSHA256 != digest || saved.receiverInstanceID != request.receiver.receiverInstanceID) {
            markFailure("sender_identity_conflict"); return
        }
        let id = request.transferID ?? (saved?.packageSHA256 == digest && saved?.receiverInstanceID == request.receiver.receiverInstanceID ? saved?.transferID : nil) ?? UUID().uuidString
        let resolvedRequest = TransferRequest(source: request.source, receiver: request.receiver, pairingOffer: request.pairingOffer, pairingCode: request.pairingCode, transferID: id, finalization: finalization)
        networkRequest = resolvedRequest
        transferID = id; expectedSHA256 = digest
        do { try identityStore.save(SenderTransferIdentity(transferID: id, packageSHA256: digest, receiverInstanceID: request.receiver.receiverInstanceID)) } catch { markFailure("sender_identity_persist_failed"); return }
        pair(receiverIdentity: request.receiver.receiverInstanceID, transferID: id, packageSHA256: digest)
        do {
            let acknowledgement = try await client.transfer(resolvedRequest) { [weak self] status in
                Task { @MainActor in self?.applyReceiverStatus(TransferReceiverStatus(transferID: status.transferID, confirmedBytes: status.confirmedBytes, totalBytes: status.totalBytes, verified: status.state == "verified" || status.state == "complete", packageSHA256: status.packageSHA256)) }
            }
            applyCompletion(acknowledgement)
        } catch URLSessionTransferError.notVerified { markRetryable("verified_receiver_acknowledgement_required") }
        catch URLSessionTransferError.sourceDigestMismatch { markRetryable("package_digest_mismatch") }
        catch { markFailure(String(describing: error)) }
    }

    public func cancelNetworkTransfer() async {
        guard let id = transferID, let client = networkClient else { cancel(); return }
        do { try await client.cancel(transferID: id); cancel() } catch { markFailure("cancel_failed") }
    }

    public func retryNetworkTransfer() async {
        guard let id = transferID, let client = networkClient else { return }
        do {
            let status = try await client.status(transferID: id)
            guard status.transferID == id else { markRetryable("resume_identity_mismatch"); return }
            applyReceiverStatus(TransferReceiverStatus(transferID: status.transferID, confirmedBytes: status.confirmedBytes, totalBytes: status.totalBytes, verified: false, packageSHA256: status.packageSHA256))
            if let request = networkRequest {
                let resumed = TransferRequest(source: request.source, receiver: request.receiver, pairingOffer: request.pairingOffer, pairingCode: request.pairingCode, transferID: id, finalization: request.finalization)
                await startNetworkTransfer(resumed)
            }
        } catch { markFailure("resume_failed") }
    }

    /// Rebuild sender state after an app/runtime restart from the persisted
    /// identity, then use receiver status as the only progress authority.
    public func restorePersistedTransfer(_ request: TransferRequest) async {
        guard let saved = identityStore.load(), saved.receiverInstanceID == request.receiver.receiverInstanceID, let data = try? Data(contentsOf: request.source), SourceIntegrity.digest(data) == saved.packageSHA256, let finalization = request.finalization, let share = try? PackScanShareCoordinator().eligiblePackage(at: request.source, finalization: finalization), let client = networkClient else { markFailure("sender_identity_conflict"); return }
        finalizedSource = share.packageURL
        transferID = saved.transferID
        expectedSHA256 = saved.packageSHA256
        networkRequest = TransferRequest(source: request.source, receiver: request.receiver, pairingOffer: request.pairingOffer, pairingCode: request.pairingCode, transferID: saved.transferID, finalization: finalization)
        prepare(package: share)
        pair(receiverIdentity: request.receiver.receiverInstanceID, transferID: saved.transferID, packageSHA256: saved.packageSHA256)
        do {
            let status = try await client.status(transferID: saved.transferID)
            guard status.transferID == saved.transferID else { markFailure("resume_identity_mismatch"); return }
            let resumed = TransferRequest(source: request.source, receiver: request.receiver, pairingOffer: request.pairingOffer, pairingCode: request.pairingCode, transferID: saved.transferID, finalization: request.finalization)
            applyReceiverStatus(TransferReceiverStatus(transferID: status.transferID, confirmedBytes: status.confirmedBytes, totalBytes: status.totalBytes, verified: status.state == "verified" || status.state == "complete", packageSHA256: status.packageSHA256))
            await startNetworkTransfer(resumed)
        } catch { markFailure("resume_failed") }
    }

    public func discardPersistedTransfer() { identityStore.remove() }

    /// `confirmedBytes` must come from the receiver's authoritative status.
    public func applyReceiverStatus(_ status: TransferReceiverStatus) {
        guard let current = state, status.transferID == transferID, status.totalBytes == current.totalBytes, status.confirmedBytes >= current.confirmedBytes, status.confirmedBytes <= status.totalBytes else { return }
        let phase: TransferUIPhase = status.verified ? .verifying : (status.confirmedBytes == status.totalBytes ? .verifying : .transferring)
        state = TransferUIState(packageURL: current.packageURL, packageName: current.packageName, totalBytes: current.totalBytes, confirmedBytes: status.confirmedBytes, receiverIdentity: current.receiverIdentity, phase: phase)
    }

    public func applyCompletion(verified: Bool, authenticated: Bool, packageSHA256: String) {
        guard let id = transferID else { markRetryable("verified_receiver_acknowledgement_required"); return }
        applyCompletion(TransferCompletionAcknowledgement(transferID: id, packageSHA256: packageSHA256, verified: verified, authenticated: authenticated, state: "complete"))
    }

    public func applyCompletion(_ acknowledgement: TransferCompletionAcknowledgement) {
        guard let current = state,
              acknowledgement.transferID == transferID,
              acknowledgement.authenticated,
              acknowledgement.verified,
              acknowledgement.packageSHA256 == expectedSHA256,
              acknowledgement.state == "verified" || acknowledgement.state == "complete",
              current.confirmedBytes == current.totalBytes else {
            markRetryable("verified_receiver_acknowledgement_required")
            return
        }
        state = TransferUIState(packageURL: current.packageURL, packageName: current.packageName, totalBytes: current.totalBytes, confirmedBytes: current.totalBytes, receiverIdentity: current.receiverIdentity, phase: .completed)
        identityStore.remove()
    }

    public func cancel() {
        guard let current = state, current.phase != .completed else { return }
        state = TransferUIState(packageURL: current.packageURL, packageName: current.packageName, totalBytes: current.totalBytes, confirmedBytes: current.confirmedBytes, receiverIdentity: current.receiverIdentity, phase: .cancelled)
    }

    public func retryFromAuthoritativeStatus(_ status: TransferReceiverStatus) {
        guard let current = state, current.phase == .cancelled || current.phase == .retryableFailure || current.phase == .terminalFailure else { return }
        applyReceiverStatus(status)
        if let refreshed = self.state { state = TransferUIState(packageURL: refreshed.packageURL, packageName: refreshed.packageName, totalBytes: refreshed.totalBytes, confirmedBytes: refreshed.confirmedBytes, receiverIdentity: refreshed.receiverIdentity, phase: .transferring) }
    }

    private func markRetryable(_ message: String) { if let current = state { state = TransferUIState(packageURL: current.packageURL, packageName: current.packageName, totalBytes: current.totalBytes, confirmedBytes: current.confirmedBytes, receiverIdentity: current.receiverIdentity, phase: .retryableFailure, error: message) } }
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
                Text(state.progressDescription)
                ProgressView(value: state.percentage, total: 100)
                Text(state.phase.rawValue).font(.caption.monospaced())
                if let error = state.error { Text(error).foregroundStyle(.red) }
                HStack {
                    Button("Cancel") { Task { await model.cancelNetworkTransfer() } }.disabled(!state.canCancel)
                    Button("Retry") { Task { await model.retryNetworkTransfer() } }.disabled(!state.canRetry)
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
