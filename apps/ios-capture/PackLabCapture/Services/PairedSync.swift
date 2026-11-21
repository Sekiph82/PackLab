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
        } catch URLSessionTransferError.clockSkew(let seconds) {
            // Still retried with backoff (fixing the clock heals it), but never shown as "not reachable".
            update(id, failure: Self.clockSkewReason(seconds), terminal: false)
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

    nonisolated static func clockSkewReason(_ seconds: Int?) -> String {
        let advice = "set Settings > General > Date & Time to Set Automatically"
        guard let seconds else { return "phone clock is off — \(advice)" }
        let minutes = max(1, (abs(seconds) + 30) / 60)
        return "phone clock is \(minutes) min \(seconds > 0 ? "ahead of" : "behind") PackLab — \(advice)"
    }

    private static func describe(_ error: any Error) -> String {
        if case .server(let code)? = error as? URLSessionTransferError { return code }
        if let urlError = error as? URLError { return "network error \(urlError.code.rawValue)" }
        return String(describing: error)
    }
}

// MARK: - PL-0429 remote capture control

public enum RemoteAction: String, Codable, Sendable { case capture, finish }
public enum RemoteOutcome: String, Codable, Sendable { case captured, refused, finished, failed }

/// One-shot request from the paired PackLab Studio, delivered on the phone's own long-poll.
public struct RemoteCommand: Codable, Sendable, Equatable {
    public let commandID: String
    public let action: RemoteAction
    public let expiresInMs: Int
    enum CodingKeys: String, CodingKey { case commandID = "command_id", action, expiresInMs = "expires_in_ms" }
    public init(commandID: String, action: RemoteAction, expiresInMs: Int) { self.commandID = commandID; self.action = action; self.expiresInMs = expiresInMs }
}

public struct RemoteCommandResult: Codable, Sendable, Equatable {
    public let commandID: String
    public let action: RemoteAction
    public let outcome: RemoteOutcome
    public let reasons: [String]
    public let message: String
    enum CodingKeys: String, CodingKey { case commandID = "command_id", action, outcome, reasons, message }
    /// Reasons are the receiver's `^[a-z0-9_]{1,64}$` codes (at most 8); text is bounded.
    public init(commandID: String, action: RemoteAction, outcome: RemoteOutcome, reasons: [String] = [], message: String = "") {
        self.commandID = commandID; self.action = action; self.outcome = outcome
        self.reasons = Array(reasons.filter(RemoteControlStatus.isReasonCode).prefix(8))
        self.message = RemoteControlStatus.clip(message, 256)
    }
    public static func refused(_ command: RemoteCommand, _ reason: String, _ message: String) -> RemoteCommandResult {
        RemoteCommandResult(commandID: command.commandID, action: command.action, outcome: .refused, reasons: [reason], message: message)
    }
    /// One line for the phone screen.
    public var summary: String {
        let what = action == .capture ? "PackLab remote capture" : "PackLab remote finish"
        switch outcome {
        case .captured, .finished: return "\(what): \(outcome.rawValue)"
        case .refused, .failed: return "\(what) \(outcome.rawValue): \(message.isEmpty ? reasons.joined(separator: ", ") : message)"
        }
    }
}

/// What the phone shows Studio about the active scan (nil when no scan is active).
public struct RemoteScanSnapshot: Sendable, Equatable {
    public let scanName: String
    public let coverageCaptured: Int
    public let coverageTotal: Int
    public let instruction: String
    public init(scanName: String, coverageCaptured: Int, coverageTotal: Int, instruction: String) { self.scanName = scanName; self.coverageCaptured = coverageCaptured; self.coverageTotal = coverageTotal; self.instruction = instruction }
}

/// `POST /v1/control/status` body: no image stream, no measurements, bounded under 4 KB.
public struct RemoteControlStatus: Codable, Sendable, Equatable {
    public let scanActive: Bool
    public let controlEnabled: Bool
    public let scanName: String
    public let coverageCaptured: Int
    public let coverageTotal: Int
    public let instruction: String
    public let lastResult: RemoteCommandResult?
    enum CodingKeys: String, CodingKey { case scanActive = "scan_active", controlEnabled = "control_enabled", scanName = "scan_name", coverageCaptured = "coverage_captured", coverageTotal = "coverage_total", instruction, lastResult = "last_result" }
    public init(controlEnabled: Bool, scan: RemoteScanSnapshot?, lastResult: RemoteCommandResult?) {
        scanActive = scan != nil; self.controlEnabled = controlEnabled
        scanName = Self.clip(scan?.scanName ?? "", 128)
        coverageCaptured = min(1000, max(0, scan?.coverageCaptured ?? 0))
        coverageTotal = min(1000, max(0, scan?.coverageTotal ?? 0))
        instruction = Self.clip(scan?.instruction ?? "", 256)
        self.lastResult = lastResult
    }
    /// The receiver counts Unicode scalars, so clip by scalars (not grapheme clusters).
    static func clip(_ text: String, _ limit: Int) -> String {
        var scalars = String.UnicodeScalarView()
        scalars.append(contentsOf: text.unicodeScalars.prefix(limit))
        return String(scalars)
    }
    private static let reasonBytes = Set("abcdefghijklmnopqrstuvwxyz0123456789_".utf8)
    static func isReasonCode(_ reason: String) -> Bool {
        !reason.isEmpty && reason.utf8.count <= 64 && reason.utf8.allSatisfy { reasonBytes.contains($0) }
    }
}

/// PL-0429: lets the paired PackLab Studio request Manual Capture or Finalize while a scan is
/// active and the operator allowed it ("Allow PackLab to trigger captures", default off). The
/// phone always initiates: it long-polls the paired receiver over the pinned TLS channel with
/// a device session; Studio never connects to the phone. A request runs the normal Manual
/// Capture path with every production gate, so Studio is refused exactly like a tap.
@MainActor
public final class RemoteCaptureController: ObservableObject {
    public static let shared = RemoteCaptureController()
    /// Never persisted: every app launch starts with remote capture off (security review LOW-3).
    @Published public var enabled = false
    @Published public private(set) var connection = "off"
    @Published public private(set) var lastResult: RemoteCommandResult?
    /// The active scan, or nil when none (bound by the capture screen).
    public var scan: @MainActor () -> RemoteScanSnapshot? = { nil }
    /// Runs an accepted request through the production capture / finalize path.
    public var perform: @MainActor (RemoteCommand) async -> RemoteCommandResult = { RemoteCommandResult.refused($0, "not_ready", "the capture screen is not ready") }
    private let credential: @MainActor () -> DeviceCredential?
    private var executed: [String] = []
    private var poller: URLSessionTransferClient?
    private var statusClient: URLSessionTransferClient?
    private var lastPosted: RemoteControlStatus?
    private var pushing = false
    private var loops: [Task<Void, Never>] = []

    public init(credential: @escaping @MainActor () -> DeviceCredential? = { DeviceCredentialStore.load() }) {
        self.credential = credential
    }

    public var currentStatus: RemoteControlStatus { RemoteControlStatus(controlEnabled: enabled, scan: scan(), lastResult: lastResult) }

    /// Checks one delivered request on the phone side, then runs it. Disabled control, no
    /// active scan, an expired or an already handled request never touch the camera.
    @discardableResult
    public func handle(_ command: RemoteCommand) async -> RemoteCommandResult {
        let result: RemoteCommandResult
        if executed.contains(command.commandID) {
            result = .refused(command, "replayed_command", "this request was already handled")
        } else if !enabled {
            result = .refused(command, "remote_control_disabled", "remote capture is turned off on the phone")
        } else if command.expiresInMs <= 0 {
            result = .refused(command, "command_expired", "the request expired before it reached the phone")
        } else if scan() == nil {
            result = .refused(command, "no_active_scan", "no scan is active on the phone")
        } else {
            executed.append(command.commandID)
            if executed.count > 64 { executed.removeFirst() }
            result = await perform(command)
        }
        lastResult = result
        return result
    }

    /// Starts the poll and status loops once per app run; both stay off the network unless
    /// control is allowed, a scan is active and the phone is paired.
    public func start() {
        guard loops.isEmpty else { return }
        loops.append(Task { [weak self] in
            while !Task.isCancelled {
                guard let self else { return }
                let pause = await self.cycle()
                if pause > 0 { try? await Task.sleep(nanoseconds: UInt64(pause) * 1_000_000_000) }
            }
        })
        // Live status (coverage, instruction) between polls, sent only when it changed.
        loops.append(Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 1_000_000_000)
                guard let self else { return }
                if self.poller != nil { try? await self.pushStatus() }
            }
        })
    }

    /// One long-poll round; seconds to pause before the next.
    func cycle() async -> Int {
        guard enabled, scan() != nil, let credential = credential() else {
            // Tell Studio once that control ended (switched off or scan finished).
            if let statusClient, lastPosted != nil { try? await statusClient.postRemoteStatus(currentStatus) }
            poller = nil; statusClient = nil; lastPosted = nil
            connection = enabled ? "waiting for a scan on a paired phone" : "off"
            return 1
        }
        do {
            if poller == nil {
                let fresh = URLSessionTransferClient(identity: credential.receiver)
                try await fresh.openDeviceSession(credential)
                poller = fresh
                statusClient = URLSessionTransferClient(identity: credential.receiver, sessionToken: fresh.currentSessionToken)
                lastPosted = nil
            }
            guard let client = poller else { return 1 }
            try await pushStatus()
            connection = "connected to PackLab"
            if let command = try await client.nextRemoteCommand() {
                await handle(command)
                try await pushStatus()
            }
            return 0
        } catch URLSessionTransferError.server(let code) where code == "device_revoked" {
            // Revoke in Studio ends control; the operator must pair again.
            poller = nil; statusClient = nil; lastPosted = nil
            enabled = false
            connection = "this phone was unpaired in PackLab Studio"
            return 1
        } catch {
            // Expired session token, receiver stopped or network loss: reconnect with a fresh session.
            poller = nil; statusClient = nil; lastPosted = nil
            connection = "PackLab not reachable — retrying"
            return 3
        }
    }

    private func pushStatus() async throws {
        let status = currentStatus
        // One push at a time; a skipped change goes out on the next 1 s status tick.
        guard !pushing, status != lastPosted, let statusClient else { return }
        pushing = true
        defer { pushing = false }
        lastPosted = status
        do {
            try await statusClient.postRemoteStatus(status)
        } catch URLSessionTransferError.server("unknown_command") {
            // Studio restarted and no longer knows that request: drop the stale result.
            lastResult = nil
            lastPosted = nil
        } catch {
            lastPosted = nil
            throw error
        }
    }
}
