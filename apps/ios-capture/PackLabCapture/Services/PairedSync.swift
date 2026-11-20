import Foundation
import Security

/// PL-0452 pair once: the long-lived credential PackLab Studio issues at pairing. The
/// receiver identity (host, port, TLS pin) and device secret live only in the Keychain
/// (this device only, after first unlock); Studio keeps just the secret's SHA-256.
public struct DeviceCredential: Codable, Sendable, Equatable {
    public let receiver: ReceiverReconnectIdentity
    public let deviceID: String
    public let deviceSecret: String
    public init(receiver: ReceiverReconnectIdentity, deviceID: String, deviceSecret: String) { self.receiver = receiver; self.deviceID = deviceID; self.deviceSecret = deviceSecret }
}

public enum DeviceCredentialStore {
    private static let service = "com.packlab.capture.paired-receiver"
    private static let account = "device-credential-v1"
    /// Last Keychain status from `save` (shown when a pairing could not be remembered).
    // ponytail: process-global diagnostic only; written on the pairing path, read by one view.
    public nonisolated(unsafe) static var lastSaveStatus: OSStatus = errSecSuccess

    private static var query: [String: Any] {
        [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service, kSecAttrAccount as String: account]
    }

    public static func load() -> DeviceCredential? {
        var request = query
        request[kSecReturnData as String] = true
        request[kSecMatchLimit as String] = kSecMatchLimitOne
        var item: CFTypeRef?
        guard SecItemCopyMatching(request as CFDictionary, &item) == errSecSuccess, let data = item as? Data else { return nil }
        return try? JSONDecoder().decode(DeviceCredential.self, from: data)
    }

    @discardableResult
    public static func save(_ credential: DeviceCredential) -> Bool {
        guard let data = try? JSONEncoder().encode(credential) else { lastSaveStatus = errSecParam; return false }
        SecItemDelete(query as CFDictionary)
        var attributes = query
        attributes[kSecValueData as String] = data
        attributes[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        lastSaveStatus = SecItemAdd(attributes as CFDictionary, nil)
        return lastSaveStatus == errSecSuccess
    }

    public static func remove() { SecItemDelete(query as CFDictionary) }
}

public enum SyncDeliveryState: String, Codable, Sendable, Equatable { case queued, sending, delivered, failed }

/// One finalized scan waiting for (or done with) automatic delivery to the paired PackLab.
public struct SyncQueueItem: Codable, Sendable, Equatable {
    public let finalization: SessionFinalizationRecord
    /// Stable per package so a retry resumes the receiver's checkpoint instead of restarting.
    public let transferID: String
    public var state: SyncDeliveryState
    public var confirmedBytes: Int
    public var totalBytes: Int
    public var reason: String?
    public var attempts: Int
    public var nextAttemptAt: Date
    /// No automatic retry (e.g. pairing revoked): the operator must pair again.
    public var terminal: Bool

    public init(finalization: SessionFinalizationRecord, transferID: String = UUID().uuidString, state: SyncDeliveryState = .queued, confirmedBytes: Int = 0, totalBytes: Int? = nil, reason: String? = nil, attempts: Int = 0, nextAttemptAt: Date = Date(), terminal: Bool = false) {
        self.finalization = finalization; self.transferID = transferID; self.state = state; self.confirmedBytes = confirmedBytes
        self.totalBytes = totalBytes ?? finalization.packageBytes ?? 0; self.reason = reason; self.attempts = attempts; self.nextAttemptAt = nextAttemptAt; self.terminal = terminal
    }

    public var sessionID: String { finalization.sessionID }
    public var isPending: Bool { state == .queued || (state == .failed && !terminal) }

    public var statusText: String {
        switch state {
        case .queued: return "Queued for PackLab"
        case .sending: return "Sending \(totalBytes > 0 ? min(100, confirmedBytes * 100 / totalBytes) : 0)%"
        case .delivered: return "Delivered to PackLab"
        case .failed: return "Failed: \(reason ?? "unknown error")" + (terminal ? "" : " — retrying automatically")
        }
    }

    /// 5 s, 10 s, 20 s ... capped at 5 minutes.
    public static func retryDelay(afterAttempts attempts: Int) -> TimeInterval {
        min(300, 5 * pow(2, Double(min(10, max(0, attempts - 1)))))
    }
}

/// Sends finalized scans to the paired PackLab without operator clicks: each scan is queued
/// at Finalize, sent when the receiver is reachable over the pinned TLS channel with a fresh
/// device session, retried with backoff, and the queue survives app restarts.
@MainActor
public final class PairedSyncService: ObservableObject {
    public static let shared = PairedSyncService()
    @Published public private(set) var items: [String: SyncQueueItem] = [:]
    private let queueURL: URL
    private let credential: @MainActor () -> DeviceCredential?
    private let autoStart: Bool
    private var worker: Task<Void, Never>?
    private var rerun = false

    public nonisolated static var defaultQueueURL: URL {
        FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!.appendingPathComponent("PackLabSync", isDirectory: true).appendingPathComponent("queue.json")
    }

    public init(queueURL: URL = PairedSyncService.defaultQueueURL, credential: @escaping @MainActor () -> DeviceCredential? = { DeviceCredentialStore.load() }, autoStart: Bool = true) {
        self.queueURL = queueURL
        self.credential = credential
        self.autoStart = autoStart
        if let data = try? Data(contentsOf: queueURL), let stored = try? JSONDecoder().decode([SyncQueueItem].self, from: data) {
            for var item in stored {
                // Interrupted by an app exit mid-send: resume from the receiver checkpoint.
                if item.state == .sending { item.state = .queued; item.nextAttemptAt = Date() }
                items[item.sessionID] = item
            }
        }
    }

    public var isPaired: Bool { credential() != nil }

    /// Queues a finalized scan for the paired PackLab; false when this phone is not paired.
    @discardableResult
    public func enqueue(_ record: SessionFinalizationRecord) -> Bool {
        guard record.state == .exported, record.packagePath != nil, credential() != nil else { return false }
        if let existing = items[record.sessionID], existing.finalization.packageSHA256 == record.packageSHA256, existing.state == .delivered || existing.state == .sending { return true }
        let transferID = items[record.sessionID].flatMap { $0.finalization.packageSHA256 == record.packageSHA256 ? $0.transferID : nil } ?? UUID().uuidString
        items[record.sessionID] = SyncQueueItem(finalization: record, transferID: transferID)
        persist()
        kick()
        return true
    }

    /// A manual Send to PackLab that completed outside the queue.
    public func markDelivered(_ record: SessionFinalizationRecord) {
        let bytes = record.packageBytes ?? 0
        items[record.sessionID] = SyncQueueItem(finalization: record, transferID: items[record.sessionID]?.transferID ?? UUID().uuidString, state: .delivered, confirmedBytes: bytes, totalBytes: bytes)
        persist()
    }

    /// Starts (or re-arms) the background sender; a no-op when nothing is pending.
    public func kick() {
        guard autoStart else { return }
        guard worker == nil else { rerun = true; return }
        worker = Task { [weak self] in
            while !Task.isCancelled {
                guard let service = self else { return }
                service.rerun = false
                let wait = await service.runDueItems()
                if wait == nil && !service.rerun { break }
                try? await Task.sleep(nanoseconds: UInt64(max(1, min(30, wait ?? 1)) * 1_000_000_000))
            }
            self?.worker = nil
        }
    }

    /// Sends every due item once; seconds until the next retry, or nil when nothing is pending.
    func runDueItems() async -> TimeInterval? {
        for id in items.keys.sorted() {
            guard let item = items[id], item.isPending, item.nextAttemptAt <= Date() else { continue }
            await send(id)
        }
        let next = items.values.filter(\.isPending).map(\.nextAttemptAt).min()
        return next.map { max(1, $0.timeIntervalSinceNow) }
    }

    private func send(_ id: String) async {
        guard var item = items[id] else { return }
        guard let credential = credential() else { update(id, failure: "this phone is not paired — tap Send to PackLab to pair", terminal: true); return }
        guard let path = item.finalization.packagePath, FileManager.default.fileExists(atPath: path) else { update(id, failure: "the finalized package is missing on this phone", terminal: true); return }
        item.state = .sending
        item.attempts += 1
        item.reason = nil
        items[id] = item
        persist()
        let client = URLSessionTransferClient(identity: credential.receiver)
        do {
            try await client.openDeviceSession(credential)
        } catch URLSessionTransferError.server(let code) where code == "device_revoked" || code == "unpaired" {
            // Studio revoked (or no longer knows) this phone: forget the pairing, stop retrying.
            DeviceCredentialStore.remove()
            update(id, failure: code == "device_revoked" ? "this phone was unpaired in PackLab Studio — pair again" : "PackLab no longer knows this phone — pair again", terminal: true)
            return
        } catch {
            update(id, failure: "PackLab not reachable (\(Self.describe(error)))", terminal: false)
            return
        }
        do {
            _ = try await client.transfer(TransferRequest(source: URL(fileURLWithPath: path), receiver: credential.receiver, transferID: item.transferID, finalization: item.finalization)) { [weak self] status in
                Task { @MainActor in self?.progress(id, confirmed: status.confirmedBytes, total: status.totalBytes) }
            }
            guard var done = items[id] else { return }
            done.state = .delivered
            done.confirmedBytes = done.totalBytes
            done.reason = nil
            items[id] = done
            persist()
        } catch {
            update(id, failure: "send failed (\(Self.describe(error)))", terminal: false)
        }
    }

    private func progress(_ id: String, confirmed: Int, total: Int) {
        guard var item = items[id], item.state == .sending else { return }
        item.confirmedBytes = confirmed
        item.totalBytes = total
        items[id] = item
    }

    private func update(_ id: String, failure reason: String, terminal: Bool) {
        guard var item = items[id] else { return }
        item.state = .failed
        item.reason = reason
        item.terminal = terminal
        item.nextAttemptAt = Date().addingTimeInterval(SyncQueueItem.retryDelay(afterAttempts: item.attempts))
        items[id] = item
        persist()
    }

    private func persist() {
        let ordered = items.values.sorted { $0.sessionID < $1.sessionID }
        guard let data = try? JSONEncoder().encode(ordered) else { return }
        try? FileManager.default.createDirectory(at: queueURL.deletingLastPathComponent(), withIntermediateDirectories: true)
        try? data.write(to: queueURL, options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
    }

    private static func describe(_ error: any Error) -> String {
        if case .server(let code)? = error as? URLSessionTransferError { return code }
        if let urlError = error as? URLError { return "network error \(urlError.code.rawValue)" }
        return String(describing: error)
    }
}
