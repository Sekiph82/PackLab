import Foundation

public enum CaptureModeID: String, Codable, Sendable, CaseIterable { case freehand, guidedOrbit = "guided_orbit", turntable }
public enum PackageType: String, Codable, Sendable, CaseIterable { case bottle, jar, jerrycan, tube, sachet, other }
public struct NewScanDraft: Codable, Sendable, Equatable {
    public let sessionID: String
    public let packageName: String
    public let packageType: PackageType
    public let captureMode: CaptureModeID
    public let notes: String
    public let createdAt: Date
    public let presetID: PackagingPresetID?
    public let preflight: ScanPreflightResult?
    public let treatmentMode: TransparentTreatmentMode?
    public init(sessionID: String = UUID().uuidString, packageName: String, packageType: PackageType, captureMode: CaptureModeID, notes: String = "", createdAt: Date = Date(), presetID: PackagingPresetID? = nil, preflight: ScanPreflightResult? = nil, treatmentMode: TransparentTreatmentMode? = nil) { self.sessionID = sessionID; self.packageName = packageName; self.packageType = packageType; self.captureMode = captureMode; self.notes = notes; self.createdAt = createdAt; self.presetID = presetID; self.preflight = preflight; self.treatmentMode = treatmentMode }
}

public enum NewScanDraftError: Error, Sendable, Equatable { case emptyName, nameTooLong, notesTooLong }
public enum NewScanDraftValidator {
    public static let maximumNameLength = 120
    public static let maximumNotesLength = 500
    public static func make(name: String, type: PackageType, mode: CaptureModeID, notes: String = "", now: Date = Date(), sessionID: String = UUID().uuidString, presetID: PackagingPresetID? = nil, preflight: ScanPreflightResult? = nil, treatmentMode: TransparentTreatmentMode? = nil) throws -> NewScanDraft {
        let normalizedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        let normalizedNotes = notes.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !normalizedName.isEmpty else { throw NewScanDraftError.emptyName }
        guard normalizedName.count <= maximumNameLength else { throw NewScanDraftError.nameTooLong }
        guard normalizedNotes.count <= maximumNotesLength else { throw NewScanDraftError.notesTooLong }
        return NewScanDraft(sessionID: sessionID, packageName: normalizedName, packageType: type, captureMode: mode, notes: normalizedNotes, createdAt: now, presetID: presetID, preflight: preflight, treatmentMode: treatmentMode)
    }
}

public struct NewScanWorkflowModel: Sendable, Equatable {
    public enum State: Sendable, Equatable { case editing, validationFailed(String), started(NewScanDraft), cancelled }
    public private(set) var state: State = .editing
    public init() {}
    public mutating func start(name: String, type: PackageType, mode: CaptureModeID, notes: String = "", now: Date = Date(), sessionID: String = UUID().uuidString, presetID: PackagingPresetID? = nil, preflight: ScanPreflightResult? = nil, treatmentMode: TransparentTreatmentMode? = nil) -> NewScanDraft? {
        do { let draft = try NewScanDraftValidator.make(name: name, type: type, mode: mode, notes: notes, now: now, sessionID: sessionID, presetID: presetID, preflight: preflight, treatmentMode: treatmentMode); state = .started(draft); return draft }
        catch let error as NewScanDraftError { state = .validationFailed(String(describing: error)); return nil }
        catch { state = .validationFailed("invalid") ; return nil }
    }
    public mutating func cancel() { state = .cancelled }
}

public struct SessionStorageLayout: Sendable, Equatable {
    public let root: URL
    public let sessionID: String
    public init(root: URL, sessionID: String) { self.root = root; self.sessionID = sessionID }
    public var sessionRoot: URL { root.appendingPathComponent(sessionID, isDirectory: true) }
    public var metadata: URL { sessionRoot.appendingPathComponent("metadata.json") }
    public var state: URL { sessionRoot.appendingPathComponent("state.json") }
    public var images: URL { sessionRoot.appendingPathComponent("images", isDirectory: true) }
    public var previews: URL { sessionRoot.appendingPathComponent("previews", isDirectory: true) }
    public var photoRecords: URL { sessionRoot.appendingPathComponent("records", isDirectory: true) }
    public var temporary: URL { sessionRoot.appendingPathComponent("tmp", isDirectory: true) }
    public var galleryAudit: URL { sessionRoot.appendingPathComponent("gallery-audit.json") }
    public var finalization: URL { sessionRoot.appendingPathComponent("finalization.json") }
}

public enum SessionStorageError: Error, Sendable, Equatable { case invalidID, duplicateID, interruptedWrite, missingRecord }

public enum SessionTransactionStage: String, Codable, Sendable, Equatable { case prepared, sourceStaged, recordStaged, stateStaged, sourceCommitted, recordCommitted, stateCommitted, committed }
public struct SessionTransactionMarker: Codable, Sendable, Equatable {
    public let captureID: String
    public let sourceFilename: String
    public let recordFilename: String
    public let stage: SessionTransactionStage
    public init(captureID: String, sourceFilename: String, recordFilename: String, stage: SessionTransactionStage) { self.captureID = captureID; self.sourceFilename = sourceFilename; self.recordFilename = recordFilename; self.stage = stage }
}

public struct AcceptedCaptureRecord: Codable, Sendable, Equatable {
    public let captureID: String
    public let sequence: Int
    public let sourceFilename: String
    public let metadataFilename: String
    public let acceptedAt: Date
    public let poseBinding: PoseCaptureBinding?
    public let motionBinding: MotionCaptureBinding?
    public let passMetadata: CapturePassMetadata?
    public let manualAudit: ManualCaptureAudit?
    public init(captureID: String, sequence: Int, sourceFilename: String, metadataFilename: String, acceptedAt: Date = Date(), poseBinding: PoseCaptureBinding? = nil, motionBinding: MotionCaptureBinding? = nil, passMetadata: CapturePassMetadata? = nil, manualAudit: ManualCaptureAudit? = nil) { self.captureID = captureID; self.sequence = sequence; self.sourceFilename = sourceFilename; self.metadataFilename = metadataFilename; self.acceptedAt = acceptedAt; self.poseBinding = poseBinding; self.motionBinding = motionBinding; self.passMetadata = passMetadata; self.manualAudit = manualAudit }
}

public enum SessionReopenDisposition: Sendable, Equatable { case resumable(PersistedSessionState), blocked(String) }

public actor ScanSessionStore {
    private let layout: SessionStorageLayout
    private let fileManager: FileManager
    private let failureInjector: (@Sendable (String) -> Bool)?
    public init(layout: SessionStorageLayout, fileManager: FileManager = .default, failureInjector: (@Sendable (String) -> Bool)? = nil) { self.layout = layout; self.fileManager = fileManager; self.failureInjector = failureInjector }
    public func create(_ draft: NewScanDraft) throws {
        guard draft.sessionID == layout.sessionID, validID(draft.sessionID) else { throw SessionStorageError.invalidID }
        guard !fileManager.fileExists(atPath: layout.sessionRoot.path) else { throw SessionStorageError.duplicateID }
        try fileManager.createDirectory(at: layout.images, withIntermediateDirectories: true)
        try fileManager.createDirectory(at: layout.previews, withIntermediateDirectories: true)
        try fileManager.createDirectory(at: layout.photoRecords, withIntermediateDirectories: true)
        try fileManager.createDirectory(at: layout.temporary, withIntermediateDirectories: true)
        try atomicWrite(JSONEncoder().encode(draft), to: layout.metadata)
        try atomicWrite(JSONEncoder().encode(PersistedSessionState(sessionID: draft.sessionID, nextSequence: 0, epoch: 0, acceptedIDs: [])), to: layout.state)
    }
    public func writeState(_ data: Data) throws { try atomicWrite(data, to: layout.state) }
    public func storeSource(_ data: Data, named name: String) throws -> URL {
        guard validID(name), !name.contains("/") else { throw SessionStorageError.invalidID }
        let destination = layout.images.appendingPathComponent(name)
        guard !fileManager.fileExists(atPath: destination.path) else { throw SessionStorageError.duplicateID }
        try data.write(to: destination, options: .atomic); return destination
    }

    public func storeAcceptedCapture(source: Data, record: AcceptedCaptureRecord, metadata: Data, state: Data) throws {
        guard validID(record.captureID), record.sequence >= 0 else { throw SessionStorageError.invalidID }
        let sourceName = record.sourceFilename
        let recordName = record.metadataFilename
        guard validID(sourceName.replacingOccurrences(of: ".", with: "_")), validID(recordName.replacingOccurrences(of: ".", with: "_")) else { throw SessionStorageError.invalidID }
        let sourceURL = layout.images.appendingPathComponent(sourceName)
        let recordURL = layout.photoRecords.appendingPathComponent(recordName)
        guard !fileManager.fileExists(atPath: sourceURL.path), !fileManager.fileExists(atPath: recordURL.path) else { throw SessionStorageError.duplicateID }
        let transaction = layout.temporary.appendingPathComponent(".txn-\(record.captureID)-\(UUID().uuidString)", isDirectory: true)
        try fileManager.createDirectory(at: transaction, withIntermediateDirectories: true)
        let sourceStage = transaction.appendingPathComponent(sourceName)
        let recordStage = transaction.appendingPathComponent(recordName)
        let stateStage = transaction.appendingPathComponent("state.json")
        let previousState = transaction.appendingPathComponent("previous-state.json")
        let markerURL = transaction.appendingPathComponent("marker.json")
        do {
            try perform("transaction.prepare", { try Data(contentsOf: layout.state).write(to: previousState, options: .atomic) })
            try writeMarker(SessionTransactionMarker(captureID: record.captureID, sourceFilename: sourceName, recordFilename: recordName, stage: .prepared), to: markerURL)
            try perform("transaction.sourceStage", { try source.write(to: sourceStage, options: .atomic) })
            try writeMarker(SessionTransactionMarker(captureID: record.captureID, sourceFilename: sourceName, recordFilename: recordName, stage: .sourceStaged), to: markerURL)
            let canonicalRecord = (try? JSONDecoder().decode(AcceptedCaptureRecord.self, from: metadata)) ?? record
            try perform("transaction.recordStage", { try JSONEncoder().encode(canonicalRecord).write(to: recordStage, options: .atomic) })
            try writeMarker(SessionTransactionMarker(captureID: record.captureID, sourceFilename: sourceName, recordFilename: recordName, stage: .recordStaged), to: markerURL)
            try perform("transaction.stateStage", { try state.write(to: stateStage, options: .atomic) })
            try writeMarker(SessionTransactionMarker(captureID: record.captureID, sourceFilename: sourceName, recordFilename: recordName, stage: .stateStaged), to: markerURL)
            try perform("transaction.sourceCommit", { try fileManager.moveItem(at: sourceStage, to: sourceURL) })
            try writeMarker(SessionTransactionMarker(captureID: record.captureID, sourceFilename: sourceName, recordFilename: recordName, stage: .sourceCommitted), to: markerURL)
            try perform("transaction.recordCommit", { try fileManager.moveItem(at: recordStage, to: recordURL) })
            try writeMarker(SessionTransactionMarker(captureID: record.captureID, sourceFilename: sourceName, recordFilename: recordName, stage: .recordCommitted), to: markerURL)
            try perform("transaction.stateCommit", { try atomicWrite(state, to: layout.state) })
            try writeMarker(SessionTransactionMarker(captureID: record.captureID, sourceFilename: sourceName, recordFilename: recordName, stage: .stateCommitted), to: markerURL)
            try writeMarker(SessionTransactionMarker(captureID: record.captureID, sourceFilename: sourceName, recordFilename: recordName, stage: .committed), to: markerURL)
            try fileManager.removeItem(at: transaction)
        } catch {
            throw error
        }
    }

    /// Accepted capture entry point used by the capture flow.  Pose and motion
    /// are bound from the shutter-aligned still timestamp before the canonical
    /// record enters the same source/record/state transaction.
    public func storeAcceptedCapture(still: AcceptedStill, record: AcceptedCaptureRecord, metadata: Data, state: Data, poses: PoseBuffer, motion: MotionBuffer, bridge: TimestampDomainBridge? = nil) throws {
        let evidence = AcceptedStillEvidenceBinder.bind(still: still, poses: poses, motion: motion, bridge: bridge)
        let enriched = AcceptedCaptureRecord(captureID: record.captureID, sequence: record.sequence, sourceFilename: record.sourceFilename, metadataFilename: record.metadataFilename, acceptedAt: record.acceptedAt, poseBinding: evidence.pose ?? record.poseBinding, motionBinding: evidence.motion ?? record.motionBinding, passMetadata: record.passMetadata, manualAudit: record.manualAudit)
        try storeAcceptedCapture(source: still.sourceBytes, record: enriched, metadata: metadata, state: state)
    }

    public func reopen(requiredSourceIDs: Set<String>, supportedVersion: String = "1.0.0") throws -> SessionReopenDisposition {
        try recoverStaleTemps()
        guard let stateData = try? Data(contentsOf: layout.state), let state = try? JSONDecoder().decode(PersistedSessionState.self, from: stateData) else { return .blocked("missing_state") }
        guard state.sessionID == layout.sessionID else { return .blocked("session_id_mismatch") }
        let sourceIDs = Set((try? fileManager.contentsOfDirectory(at: layout.images, includingPropertiesForKeys: nil).map { $0.deletingPathExtension().lastPathComponent }) ?? [])
        let records = (try? fileManager.contentsOfDirectory(at: layout.photoRecords, includingPropertiesForKeys: nil).compactMap { url -> AcceptedCaptureRecord? in guard let data = try? Data(contentsOf: url) else { return nil }; return try? JSONDecoder().decode(AcceptedCaptureRecord.self, from: data) }) ?? []
        let recordIDs = Set(records.map(\.captureID))
        let recordsValid = records.allSatisfy { record in
            !record.sourceFilename.isEmpty && !record.sourceFilename.contains("/") && !record.sourceFilename.contains("\\") && fileManager.fileExists(atPath: layout.images.appendingPathComponent(record.sourceFilename).path)
        }
        guard recordsValid, Set(state.acceptedIDs).isSubset(of: sourceIDs), Set(state.acceptedIDs).isSubset(of: recordIDs) else { return .blocked("missing_or_corrupt_record") }
        let disposition = SessionResumeValidator.disposition(state: state, requiredSourceIDs: sourceIDs.union(requiredSourceIDs), supportedVersion: supportedVersion)
        switch disposition { case .resumable: return .resumable(state); case .blocked(let reason): return .blocked(reason); case .discardRequired: return .blocked("discard_required") }
    }

    private func recoverStaleTemps() throws {
        guard let files = try? fileManager.contentsOfDirectory(at: layout.temporary, includingPropertiesForKeys: nil) else { return }
        for file in files {
            if file.lastPathComponent.hasPrefix(".txn-") { try recoverTransaction(at: file) }
            else if file.lastPathComponent.contains(".tmp-") || file.pathExtension == "tmp" { try? fileManager.removeItem(at: file) }
        }
    }

    private func writeMarker(_ marker: SessionTransactionMarker, to url: URL) throws { try JSONEncoder().encode(marker).write(to: url, options: .atomic) }
    private func recoverTransaction(at transaction: URL) throws {
        guard let markerData = try? Data(contentsOf: transaction.appendingPathComponent("marker.json")), let marker = try? JSONDecoder().decode(SessionTransactionMarker.self, from: markerData) else { throw SessionStorageError.interruptedWrite }
        let sourceURL = layout.images.appendingPathComponent(marker.sourceFilename)
        let recordURL = layout.photoRecords.appendingPathComponent(marker.recordFilename)
        let stagedSource = transaction.appendingPathComponent(marker.sourceFilename)
        let stagedRecord = transaction.appendingPathComponent(marker.recordFilename)
        let stagedState = transaction.appendingPathComponent("state.json")
        let previousState = transaction.appendingPathComponent("previous-state.json")
        let hasFinals = fileManager.fileExists(atPath: sourceURL.path) && fileManager.fileExists(atPath: recordURL.path)
        let stateMatches = (try? Data(contentsOf: layout.state)) == (try? Data(contentsOf: stagedState))
        if marker.stage == .committed || marker.stage == .stateCommitted || (hasFinals && stateMatches) {
            try? fileManager.removeItem(at: transaction)
            return
        }
        // Any incomplete publication is rolled back to the exact pre-capture
        // state.  This handles a crash after either final move as well as a
        // crash before state replacement, without trusting the marker alone.
        if let oldState = try? Data(contentsOf: previousState) { try atomicWrite(oldState, to: layout.state) }
        for url in [sourceURL, recordURL, stagedSource, stagedRecord, stagedState] where fileManager.fileExists(atPath: url.path) { try? fileManager.removeItem(at: url) }
        try? fileManager.removeItem(at: transaction)
    }
    private func perform(_ label: String, _ operation: () throws -> Void) throws {
        if failureInjector?(label) == true { throw SessionStorageError.interruptedWrite }
        try operation()
    }
    private func atomicWrite(_ data: Data, to destination: URL) throws {
        let temporary = layout.temporary.appendingPathComponent(".\(destination.lastPathComponent).tmp-\(UUID().uuidString)")
        do {
            try data.write(to: temporary, options: .atomic)
            if fileManager.fileExists(atPath: destination.path) { try fileManager.replaceItemAt(destination, withItemAt: temporary, backupItemName: nil, options: .usingNewMetadataOnly) }
            else { try fileManager.moveItem(at: temporary, to: destination) }
        }
        catch { try? fileManager.removeItem(at: temporary); if errorIsInterruption(error) { throw SessionStorageError.interruptedWrite }; throw error }
    }
    private func validID(_ value: String) -> Bool { !value.isEmpty && value.count <= 128 && value.allSatisfy { $0.isLetter || $0.isNumber || $0 == "-" || $0 == "_" }
    }
    private func errorIsInterruption(_ error: Error) -> Bool { (error as NSError).code == NSUserCancelledError }
}

public struct GalleryEntry: Sendable, Equatable, Identifiable {
    public let id: String
    public let previewPath: String?
    public let sourcePath: String
    public let sequence: Int
    public let status: String
    public init(id: String, previewPath: String?, sourcePath: String, sequence: Int, status: String = "accepted") { self.id = id; self.previewPath = previewPath; self.sourcePath = sourcePath; self.sequence = sequence; self.status = status }
}
public enum GalleryMutationError: Error, Sendable, Equatable { case notFound, confirmationRequired, invalidReplacement }
public struct GalleryModel: Sendable, Equatable {
    public private(set) var entries: [GalleryEntry]
    public private(set) var replacementTrace: [String: String] = [:]
    public init(entries: [GalleryEntry]) { self.entries = entries.sorted { $0.sequence < $1.sequence } }
    public mutating func delete(id: String, confirmed: Bool) throws { guard confirmed else { throw GalleryMutationError.confirmationRequired }; guard entries.contains(where: { $0.id == id }) else { throw GalleryMutationError.notFound }; entries.removeAll { $0.id == id } }
    public mutating func retake(replacing id: String, with replacement: GalleryEntry) throws { guard entries.contains(where: { $0.id == id }), replacement.id != id else { throw GalleryMutationError.invalidReplacement }; replacementTrace[id] = replacement.id; entries.append(replacement); entries.sort { $0.sequence < $1.sequence } }
}

public enum GalleryLoadError: Error, Sendable, Equatable { case corruptRecord(String) }
public struct GalleryAuditEvent: Codable, Sendable, Equatable {
    public let action: String
    public let captureID: String
    public let replacementID: String?
    public let timestamp: Date
    public init(action: String, captureID: String, replacementID: String? = nil, timestamp: Date = Date()) { self.action = action; self.captureID = captureID; self.replacementID = replacementID; self.timestamp = timestamp }
}

public actor SessionGalleryStore {
    private let layout: SessionStorageLayout
    private let fileManager: FileManager
    private let failureInjector: (@Sendable (String) -> Bool)?
    public init(layout: SessionStorageLayout, fileManager: FileManager = .default, failureInjector: (@Sendable (String) -> Bool)? = nil) { self.layout = layout; self.fileManager = fileManager; self.failureInjector = failureInjector }

    public func load() throws -> [GalleryEntry] {
        guard let files = try? fileManager.contentsOfDirectory(at: layout.photoRecords, includingPropertiesForKeys: nil) else { return [] }
        return try files.filter { $0.pathExtension == "json" }.compactMap { file in
            guard let data = try? Data(contentsOf: file), let record = try? JSONDecoder().decode(AcceptedCaptureRecord.self, from: data) else { throw GalleryLoadError.corruptRecord(file.lastPathComponent) }
            let source = layout.images.appendingPathComponent(record.sourceFilename)
            let preview = layout.previews.appendingPathComponent("\(record.captureID)-thumbnail.jpg")
            let status = fileManager.fileExists(atPath: source.path) && fileManager.fileExists(atPath: preview.path) ? "accepted" : "degraded"
            return GalleryEntry(id: record.captureID, previewPath: preview.path, sourcePath: source.path, sequence: record.sequence, status: status)
        }.sorted { $0.sequence < $1.sequence }
    }

    public func delete(id: String, confirmed: Bool) throws {
        guard confirmed else { throw GalleryMutationError.confirmationRequired }
        let entries = try load()
        guard let entry = entries.first(where: { $0.id == id }) else { throw GalleryMutationError.notFound }
        let recordURL = layout.photoRecords.appendingPathComponent("\(id).json")
        let audit = GalleryAuditEvent(action: "delete", captureID: id)
        var state = try loadState()
        state = PersistedSessionState(sessionID: state.sessionID, schemaVersion: state.schemaVersion, nextSequence: state.nextSequence, epoch: state.epoch, acceptedIDs: state.acceptedIDs.filter { $0 != id }, rejectedIDs: state.rejectedIDs, replacementTrace: state.replacementTrace.filter { $0.key != id && $0.value != id })
        let files = [recordURL, URL(fileURLWithPath: entry.sourcePath), entry.previewPath.map(URL.init(fileURLWithPath:))].compactMap { $0 }
        try mutate(files: files) {
            for url in files where fileManager.fileExists(atPath: url.path) { try perform("delete.\(url.lastPathComponent)") { try fileManager.removeItem(at: url) } }
            try persist(state: state, audit: audit)
        }
    }

    public func retake(replacing id: String, source: Data, record: AcceptedCaptureRecord, metadata: Data) throws {
        guard record.captureID != id else { throw GalleryMutationError.invalidReplacement }
        guard try load().contains(where: { $0.id == id }) else { throw GalleryMutationError.notFound }
        let sourceURL = layout.images.appendingPathComponent(record.sourceFilename)
        let recordURL = layout.photoRecords.appendingPathComponent(record.metadataFilename)
        guard !fileManager.fileExists(atPath: sourceURL.path), !fileManager.fileExists(atPath: recordURL.path) else { throw SessionStorageError.duplicateID }
        let canonicalRecord = (try? JSONDecoder().decode(AcceptedCaptureRecord.self, from: metadata)) ?? record
        let oldEntry = try load().first { $0.id == id }
        let oldFiles = [layout.photoRecords.appendingPathComponent("\(id).json"), layout.images.appendingPathComponent(oldEntry?.sourcePath.split(separator: "/").last.map(String.init) ?? "\(id).heic"), oldEntry?.previewPath.map(URL.init(fileURLWithPath:))].compactMap { $0 }
        var state = try loadState()
        let accepted = state.acceptedIDs.map { $0 == id ? record.captureID : $0 }
        let trace = state.replacementTrace.merging([id: record.captureID]) { _, replacement in replacement }
        let next = max(state.nextSequence, record.sequence + 1)
        let updated = PersistedSessionState(sessionID: state.sessionID, schemaVersion: state.schemaVersion, nextSequence: next, epoch: state.epoch, acceptedIDs: accepted, rejectedIDs: state.rejectedIDs, replacementTrace: trace)
        let files = oldFiles + [sourceURL, recordURL]
        try mutate(files: files) {
            try perform("retake.source") { try source.write(to: sourceURL, options: .atomic) }
            try perform("retake.record") { try JSONEncoder().encode(canonicalRecord).write(to: recordURL, options: .atomic) }
            try persist(state: updated, audit: GalleryAuditEvent(action: "retake", captureID: id, replacementID: record.captureID))
            for url in oldFiles where url != sourceURL && url != recordURL && fileManager.fileExists(atPath: url.path) { try perform("retake.remove.\(url.lastPathComponent)") { try fileManager.removeItem(at: url) } }
        }
    }

    private func loadState() throws -> PersistedSessionState {
        guard let data = try? Data(contentsOf: layout.state), let state = try? JSONDecoder().decode(PersistedSessionState.self, from: data) else { throw SessionStorageError.missingRecord }
        return state
    }

    private func persist(state: PersistedSessionState, audit event: GalleryAuditEvent) throws {
        let url = layout.galleryAudit
        var events = (try? JSONDecoder().decode([GalleryAuditEvent].self, from: Data(contentsOf: url))) ?? []
        events.append(event)
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        let stateData = try encoder.encode(state)
        let auditData = try encoder.encode(events)
        let stateTemp = layout.temporary.appendingPathComponent(".gallery-state-\(UUID().uuidString).tmp")
        let auditTemp = layout.temporary.appendingPathComponent(".gallery-audit-\(UUID().uuidString).tmp")
        try perform("mutation.stateStage") { try stateData.write(to: stateTemp, options: .atomic) }
        try perform("mutation.auditStage") { try auditData.write(to: auditTemp, options: .atomic) }
        if fileManager.fileExists(atPath: layout.state.path) { try perform("mutation.stateCommit") { try fileManager.replaceItemAt(layout.state, withItemAt: stateTemp, backupItemName: nil, options: .usingNewMetadataOnly) } } else { try perform("mutation.stateCommit") { try fileManager.moveItem(at: stateTemp, to: layout.state) } }
        if fileManager.fileExists(atPath: url.path) { try perform("mutation.auditCommit") { try fileManager.replaceItemAt(url, withItemAt: auditTemp, backupItemName: nil, options: .usingNewMetadataOnly) } } else { try perform("mutation.auditCommit") { try fileManager.moveItem(at: auditTemp, to: url) } }
    }

    private func mutate(files: [URL], operation: () throws -> Void) throws {
        let stateURL = layout.state
        let auditURL = layout.galleryAudit
        var backup: [String: Data?] = [:]
        for url in files + [stateURL, auditURL] { backup[url.path] = try? Data(contentsOf: url) }
        do { try operation() }
        catch {
            for (path, data) in backup {
                let url = URL(fileURLWithPath: path)
                if let data { try? data.write(to: url, options: .atomic) }
                else { try? fileManager.removeItem(at: url) }
            }
            throw error
        }
    }

    private func perform(_ label: String, _ operation: () throws -> Void) throws {
        if failureInjector?(label) == true { throw SessionStorageError.interruptedWrite }
        try operation()
    }
}

public enum ResumeDisposition: Sendable, Equatable { case resumable, discardRequired, blocked(String) }
public struct PersistedSessionState: Codable, Sendable, Equatable {
    public let sessionID: String
    public let schemaVersion: String
    public let nextSequence: Int
    public let epoch: Int
    public let acceptedIDs: [String]
    public let rejectedIDs: [String]
    public let replacementTrace: [String: String]
    public init(sessionID: String, schemaVersion: String = "1.0.0", nextSequence: Int, epoch: Int, acceptedIDs: [String], rejectedIDs: [String] = [], replacementTrace: [String: String] = [:]) { self.sessionID = sessionID; self.schemaVersion = schemaVersion; self.nextSequence = nextSequence; self.epoch = epoch; self.acceptedIDs = acceptedIDs; self.rejectedIDs = rejectedIDs; self.replacementTrace = replacementTrace }
    enum CodingKeys: String, CodingKey { case sessionID, schemaVersion, nextSequence, epoch, acceptedIDs, rejectedIDs, replacementTrace }
    public init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        sessionID = try values.decode(String.self, forKey: .sessionID); schemaVersion = try values.decode(String.self, forKey: .schemaVersion); nextSequence = try values.decode(Int.self, forKey: .nextSequence); epoch = try values.decode(Int.self, forKey: .epoch); acceptedIDs = try values.decode([String].self, forKey: .acceptedIDs); rejectedIDs = try values.decodeIfPresent([String].self, forKey: .rejectedIDs) ?? []; replacementTrace = try values.decodeIfPresent([String: String].self, forKey: .replacementTrace) ?? [:]
    }
}
public enum SessionResumeValidator {
    public static func disposition(state: PersistedSessionState?, requiredSourceIDs: Set<String>, supportedVersion: String = "1.0.0") -> ResumeDisposition {
        guard let state else { return .blocked("missing_state") }
        guard state.schemaVersion == supportedVersion else { return .blocked("version_mismatch") }
        guard state.nextSequence >= state.acceptedIDs.count else { return .blocked("invalid_sequence") }
        guard Set(state.acceptedIDs).isSubset(of: requiredSourceIDs) else { return .blocked("missing_source") }
        return .resumable
    }
}

public struct SessionResumeCandidate: Sendable, Equatable, Identifiable {
    public let id: String
    public let draft: NewScanDraft?
    public let disposition: ResumeDisposition
    public let state: PersistedSessionState?
    public init(id: String, draft: NewScanDraft?, disposition: ResumeDisposition, state: PersistedSessionState?) { self.id = id; self.draft = draft; self.disposition = disposition; self.state = state }
}

public actor SessionDiscoveryService {
    private let root: URL
    private let fileManager: FileManager
    public init(root: URL, fileManager: FileManager = .default) { self.root = root; self.fileManager = fileManager }
    public func discover() async -> [SessionResumeCandidate] {
        guard let directories = try? fileManager.contentsOfDirectory(at: root, includingPropertiesForKeys: [.isDirectoryKey]) else { return [] }
        return directories.filter { $0.hasDirectoryPath }.map { directory in
            let id = directory.lastPathComponent
            let layout = SessionStorageLayout(root: root, sessionID: id)
            let draft = (try? Data(contentsOf: layout.metadata)).flatMap { try? JSONDecoder().decode(NewScanDraft.self, from: $0) }
            var state = (try? Data(contentsOf: layout.state)).flatMap { try? JSONDecoder().decode(PersistedSessionState.self, from: $0) }
            let sourceIDs = Set((try? fileManager.contentsOfDirectory(at: layout.images, includingPropertiesForKeys: nil).map { $0.deletingPathExtension().lastPathComponent }) ?? [])
            let disposition: ResumeDisposition
            if let state {
                do {
                    let reopened = try await ScanSessionStore(layout: layout).reopen(requiredSourceIDs: [])
                    switch reopened { case .resumable(let authoritative): state = authoritative; disposition = .resumable; case .blocked(let reason): disposition = .blocked(reason) }
                } catch { disposition = .blocked("corrupt_transaction") }
            } else { disposition = .blocked("missing_state") }
            return SessionResumeCandidate(id: id, draft: draft, disposition: disposition, state: state)
        }.sorted { $0.id < $1.id }
    }
}

public struct ActiveScanSession: Sendable, Equatable {
    public let draft: NewScanDraft
    public let state: PersistedSessionState
    public init(draft: NewScanDraft, state: PersistedSessionState) { self.draft = draft; self.state = state }
}

public actor ActiveScanSessionRegistry {
    private var active: ActiveScanSession?
    public init() {}
    public func install(_ session: ActiveScanSession) { active = session }
    public func current() -> ActiveScanSession? { active }
    public func clear() { active = nil }
}

public enum FinalizationError: Error, Sendable, Equatable { case missingPhoto, invalidMetadataBinding, checksumFailure, invalidManifest, packagingFailed }
public struct FinalizationInput: Sendable { public let manifest: Data; public let payloads: [String: Data]; public let destination: URL; public let sessionRoot: URL?; public init(manifest: Data, payloads: [String: Data], destination: URL, sessionRoot: URL? = nil) { self.manifest = manifest; self.payloads = payloads; self.destination = destination; self.sessionRoot = sessionRoot } }
public struct SessionFinalizer: Sendable {
    private let failureInjector: (@Sendable (String) -> Bool)?
    public init(failureInjector: (@Sendable (String) -> Bool)? = nil) { self.failureInjector = failureInjector }
    public func validate(_ input: FinalizationInput) throws {
        guard let object = try? JSONSerialization.jsonObject(with: input.manifest) as? [String: Any], object["schema_version"] as? String == PackScanWriter.schemaVersion, let captureID = object["capture_id"] as? String, !captureID.isEmpty, let declared = object["payloads"] as? [[String: Any]], declared.count >= 2, let checksums = object["checksums"] as? [String: Any], checksums["algorithm"] as? String == "sha256", checksums["canonicalization"] as? String == PackScanWriter.checksumCanonicalization else { throw FinalizationError.invalidManifest }
        let paths = declared.compactMap { $0["path"] as? String }
        guard paths.count == declared.count, Set(paths).count == paths.count, Set(input.payloads.keys) == Set(paths), paths.allSatisfy(safePayloadPath) else { throw FinalizationError.invalidManifest }
        guard input.payloads.keys.contains("metadata/photos.json"), declared.contains(where: { ($0["path"] as? String)?.hasPrefix("images/") == true }) else { throw FinalizationError.missingPhoto }
        guard let metadataBytes = input.payloads["metadata/photos.json"], let document = try? JSONDecoder().decode(PackScanPhotoMetadataDocument.self, from: metadataBytes), !document.photos.isEmpty else { throw FinalizationError.invalidMetadataBinding }
        for photo in document.photos {
            guard let bytes = input.payloads[photo.imagePath], !bytes.isEmpty else { throw FinalizationError.invalidMetadataBinding }
            guard photo.imagePath == "images/\(photo.originalFilename)", photo.sequence >= 0, photo.pixelDimensions.width > 0, photo.pixelDimensions.height > 0 else { throw FinalizationError.invalidMetadataBinding }
        }
        for item in declared {
            guard let path = item["path"] as? String, item["kind"] is String, item["required"] is Bool, item["authority"] is String, let bytes = input.payloads[path], let size = item["size_bytes"] as? Int, bytes.count == size else { throw FinalizationError.checksumFailure }
            guard let digest = item["sha256"] as? String, digest.count == 64, digest == digest.lowercased(), digest == SourceIntegrity.digest(bytes) else { throw FinalizationError.checksumFailure }
        }
    }
    public func finalize(_ input: FinalizationInput) throws {
        do {
            try validate(input)
            let fileManager = FileManager.default
            guard let sessionRoot = input.sessionRoot else {
                try PackScanWriter().write(manifestJSON: input.manifest, payloads: input.payloads, to: input.destination)
                return
            }
            let finalizationURL = sessionRoot.appendingPathComponent("finalization.json")
            let packageTemp = input.destination.deletingLastPathComponent().appendingPathComponent(".packscan-\(UUID().uuidString).partial")
            let recordTemp = sessionRoot.appendingPathComponent(".finalization-\(UUID().uuidString).tmp")
            let oldRecord = try? Data(contentsOf: finalizationURL)
            var packageCommitted = false
            do {
                try PackScanWriter().write(manifestJSON: input.manifest, payloads: input.payloads, to: packageTemp)
                let record = SessionFinalizationRecord(sessionID: sessionRoot.lastPathComponent, state: .exported, packagePath: input.destination.path)
                if failureInjector?("finalization.record") == true { throw FinalizationError.packagingFailed }
                try JSONEncoder().encode(record).write(to: recordTemp, options: .atomic)
                if failureInjector?("finalization.packageCommit") == true { throw FinalizationError.packagingFailed }
                try fileManager.moveItem(at: packageTemp, to: input.destination)
                packageCommitted = true
                if failureInjector?("finalization.recordCommit") == true { throw FinalizationError.packagingFailed }
                if fileManager.fileExists(atPath: finalizationURL.path) { try fileManager.replaceItemAt(finalizationURL, withItemAt: recordTemp, backupItemName: nil, options: .usingNewMetadataOnly) } else { try fileManager.moveItem(at: recordTemp, to: finalizationURL) }
            } catch {
                try? fileManager.removeItem(at: packageTemp)
                if packageCommitted { try? fileManager.removeItem(at: input.destination) }
                try? fileManager.removeItem(at: recordTemp)
                if let oldRecord { try? oldRecord.write(to: finalizationURL, options: .atomic) }
                else { try? fileManager.removeItem(at: finalizationURL) }
                throw error
            }
        }
        catch let error as FinalizationError { throw error }
        catch { throw FinalizationError.packagingFailed }
    }

    private func safePayloadPath(_ path: String) -> Bool { !path.isEmpty && !path.hasPrefix("/") && !path.contains("\\") && !path.contains(":") && !path.split(separator: "/", omittingEmptySubsequences: false).contains { $0.isEmpty || $0 == "." || $0 == ".." } }
}

public struct ScanHistoryEntry: Codable, Sendable, Equatable, Identifiable {
    public let id: String
    public let packageName: String
    public let packageType: PackageType?
    public let date: Date?
    public let previewPath: String?
    public let exportState: String
    public let degradedReason: String?
    public init(id: String, packageName: String, packageType: PackageType?, date: Date?, previewPath: String?, exportState: String, degradedReason: String? = nil) { self.id = id; self.packageName = packageName; self.packageType = packageType; self.date = date; self.previewPath = previewPath; self.exportState = exportState; self.degradedReason = degradedReason }
}
public struct ScanHistoryIndex: Sendable, Equatable {
    public init() {}
    public func sorted(_ entries: [ScanHistoryEntry]) -> [ScanHistoryEntry] { entries.sorted { ($0.date ?? .distantPast, $0.id) > ($1.date ?? .distantPast, $1.id) } }
    public func degraded(id: String, reason: String) -> ScanHistoryEntry { ScanHistoryEntry(id: id, packageName: "Unavailable scan", packageType: nil, date: nil, previewPath: nil, exportState: "unavailable", degradedReason: reason) }
}

public enum SessionFinalizationState: String, Codable, Sendable, Equatable { case inProgress = "in_progress", exported }
public struct SessionFinalizationRecord: Codable, Sendable, Equatable {
    public let sessionID: String
    public let state: SessionFinalizationState
    public let packagePath: String?
    public init(sessionID: String, state: SessionFinalizationState, packagePath: String? = nil) { self.sessionID = sessionID; self.state = state; self.packagePath = packagePath }
}

public actor LocalScanHistoryStore {
    private let root: URL
    private let fileManager: FileManager
    public init(root: URL, fileManager: FileManager = .default) { self.root = root; self.fileManager = fileManager }
    public func load() -> [ScanHistoryEntry] {
        guard let directories = try? fileManager.contentsOfDirectory(at: root, includingPropertiesForKeys: [.isDirectoryKey]) else { return [] }
        let index = ScanHistoryIndex()
        return index.sorted(directories.filter { $0.hasDirectoryPath }.map { directory in
            let id = directory.lastPathComponent
            let layout = SessionStorageLayout(root: root, sessionID: id)
            guard let metadata = try? Data(contentsOf: layout.metadata), let draft = try? JSONDecoder().decode(NewScanDraft.self, from: metadata) else { return index.degraded(id: id, reason: "corrupt_metadata") }
            let preview = (try? fileManager.contentsOfDirectory(at: layout.previews, includingPropertiesForKeys: nil).first { $0.pathExtension.lowercased() == "jpg" || $0.pathExtension.lowercased() == "jpeg" })
            let finalizationURL = directory.appendingPathComponent("finalization.json")
            let finalizationData = try? Data(contentsOf: finalizationURL)
            let finalization = finalizationData.flatMap { try? JSONDecoder().decode(SessionFinalizationRecord.self, from: $0) }
            if finalizationData != nil && finalization == nil { return ScanHistoryEntry(id: id, packageName: draft.packageName, packageType: draft.packageType, date: draft.createdAt, previewPath: preview?.path, exportState: "corrupt", degradedReason: "corrupt_finalization") }
            if let finalization, finalization.sessionID != id { return ScanHistoryEntry(id: id, packageName: draft.packageName, packageType: draft.packageType, date: draft.createdAt, previewPath: preview?.path, exportState: "corrupt", degradedReason: "invalid_finalization_identity") }
            guard let preview else { return ScanHistoryEntry(id: id, packageName: draft.packageName, packageType: draft.packageType, date: draft.createdAt, previewPath: nil, exportState: finalization?.state.rawValue ?? "in_progress", degradedReason: "missing_preview") }
            guard let finalization else { return ScanHistoryEntry(id: id, packageName: draft.packageName, packageType: draft.packageType, date: draft.createdAt, previewPath: preview.path, exportState: "in_progress") }
            if finalization.state == .exported {
                guard let packagePath = finalization.packagePath, fileManager.fileExists(atPath: packagePath), (try? URL(fileURLWithPath: packagePath).resourceValues(forKeys: [.isRegularFileKey]).isRegularFile) == true else {
                    return ScanHistoryEntry(id: id, packageName: draft.packageName, packageType: draft.packageType, date: draft.createdAt, previewPath: preview.path, exportState: "corrupt", degradedReason: "missing_exported_package")
                }
            }
            return ScanHistoryEntry(id: id, packageName: draft.packageName, packageType: draft.packageType, date: draft.createdAt, previewPath: preview.path, exportState: finalization.state.rawValue)
        })
    }
}

public enum DeletionError: Error, Sendable, Equatable { case confirmationRequired, outsideRoot, symlinkEscape, nonAuthoritative, partialFailure }
public struct SessionDeletionPlan: Sendable, Equatable {
    public let root: URL
    public let session: URL
    public let sessionID: String
    public let authoritative: Bool
    public let candidateDisposition: ResumeDisposition?
    public init(root: URL, session: URL) { self.root = root.standardizedFileURL; self.session = session.standardizedFileURL; self.sessionID = session.lastPathComponent; self.authoritative = false; self.candidateDisposition = nil }
    public init(root: URL, candidate: SessionResumeCandidate) { self.root = root.standardizedFileURL; self.session = root.appendingPathComponent(candidate.id, isDirectory: true).standardizedFileURL; self.sessionID = candidate.id; self.authoritative = true; self.candidateDisposition = candidate.disposition }
    public func validate(confirmed: Bool, fileManager: FileManager = .default) throws {
        guard confirmed else { throw DeletionError.confirmationRequired }
        guard authoritative else { throw DeletionError.nonAuthoritative }
        guard candidateDisposition == .resumable else { throw DeletionError.outsideRoot }
        let rootPath = root.resolvingSymlinksInPath.path
        let sessionPath = session.resolvingSymlinksInPath.path
        guard sessionPath != rootPath, sessionPath.hasPrefix(rootPath + "/") || sessionPath.hasPrefix(rootPath + "\\") else { throw DeletionError.outsideRoot }
        guard sessionPath == session.path else { throw DeletionError.symlinkEscape }
        guard !sessionID.isEmpty, sessionID == session.lastPathComponent, sessionID.allSatisfy({ $0.isLetter || $0.isNumber || $0 == "-" || $0 == "_" }) else { throw DeletionError.outsideRoot }
        if let enumerator = fileManager.enumerator(at: session, includingPropertiesForKeys: [.isSymbolicLinkKey], options: []) {
            for case let url as URL in enumerator where (try? url.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink) == true { throw DeletionError.symlinkEscape }
        }
    }
}

public struct DeletionReport: Sendable, Equatable { public let sessionID: String; public let removedPaths: [String]; public let failures: [String]; public init(sessionID: String, removedPaths: [String], failures: [String]) { self.sessionID = sessionID; self.removedPaths = removedPaths; self.failures = failures } }
public actor SafeSessionDeleter {
    private let fileManager: FileManager
    private let failureInjector: (@Sendable (String) -> Bool)?
    public init(fileManager: FileManager = .default, failureInjector: (@Sendable (String) -> Bool)? = nil) { self.fileManager = fileManager; self.failureInjector = failureInjector }
    public func delete(plan: SessionDeletionPlan, confirmed: Bool) throws {
        let report = try deleteDetailed(plan: plan, confirmed: confirmed)
        if !report.failures.isEmpty { throw DeletionError.partialFailure }
    }
    public func deleteDetailed(plan: SessionDeletionPlan, confirmed: Bool, historyIndex: URL? = nil) throws -> DeletionReport {
        try plan.validate(confirmed: confirmed, fileManager: fileManager)
        guard fileManager.fileExists(atPath: plan.session.path) else { return DeletionReport(sessionID: plan.sessionID, removedPaths: [], failures: ["missing_session"]) }
        var removed: [String] = []; var failures: [String] = []
        if failureInjector?(plan.session.path) == true { failures.append(plan.session.path) }
        else { do { try fileManager.removeItem(at: plan.session); removed.append(plan.session.path) } catch { failures.append(plan.session.path) } }
        let historyURL = historyIndex ?? plan.root.appendingPathComponent("history.json")
        if fileManager.fileExists(atPath: historyURL.path) {
            do {
                let entries = try JSONDecoder().decode([ScanHistoryEntry].self, from: Data(contentsOf: historyURL)).filter { $0.id != plan.sessionID }
                if failureInjector?(historyURL.path) == true { throw DeletionError.partialFailure }
                try JSONEncoder().encode(entries).write(to: historyURL, options: .atomic)
                removed.append(historyURL.path)
            } catch { failures.append(historyURL.path) }
        }
        return DeletionReport(sessionID: plan.sessionID, removedPaths: removed, failures: failures)
    }
}

public enum NewScanActionCoordinator {
    @discardableResult
    public static func start(workflow: inout NewScanWorkflowModel, name: String, type: PackageType, mode: CaptureModeID, notes: String, presetID: PackagingPresetID? = nil, preflight: ScanPreflightResult? = nil, treatmentMode: TransparentTreatmentMode? = nil, onStart: (NewScanDraft) -> Void) -> Bool {
        guard let draft = workflow.start(name: name, type: type, mode: mode, notes: notes, presetID: presetID, preflight: preflight, treatmentMode: treatmentMode) else { return false }
        onStart(draft)
        return true
    }
    public static func cancel(workflow: inout NewScanWorkflowModel) { workflow.cancel() }
}

#if canImport(SwiftUI)
import SwiftUI
#if canImport(UIKit)
import UIKit
#endif
public struct NewScanWizard: View {
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var packageType: PackageType = .bottle
    @State private var mode: CaptureModeID = .freehand
    @State private var notes = ""
    @State private var presetID: PackagingPresetID = .matteHDPE
    @State private var guidanceAcknowledged = false
    @State private var transparentTreatment: TransparentTreatmentMode = .none
    @State private var validationMessage: String?
    @State private var workflow = NewScanWorkflowModel()
    public let admission: CaptureAdmissionController
    public let onStart: (NewScanDraft) -> Void
    public init(admission: CaptureAdmissionController = CaptureAdmissionController(), onStart: @escaping (NewScanDraft) -> Void) { self.admission = admission; self.onStart = onStart }
    public var body: some View {
        Form {
            TextField("Package name", text: $name)
            Picker("Package type", selection: $packageType) { ForEach(PackageType.allCases, id: \.self) { Text($0.rawValue.capitalized).tag($0) } }
            Picker("Capture mode", selection: $mode) { ForEach(CaptureModeID.allCases, id: \.self) { Text($0.rawValue).tag($0) } }
            Picker("Packaging preset", selection: $presetID) { ForEach(PackagingPresetID.allCases, id: \.self) { Text(PackagingPresetCatalog.preset(for: $0).displayName).tag($0) } }
            if presetID == .transparent {
                Picker("Transparent preparation treatment", selection: $transparentTreatment) { ForEach(TransparentTreatmentMode.allCases, id: \.self) { Text($0.rawValue).tag($0) } }
                Text("Treatment is operator-selected and not physical verification. None cannot be represented as treated.").font(.caption).foregroundStyle(.orange)
            }
            Toggle("Lighting and preparation guidance understood", isOn: $guidanceAcknowledged)
            TextField("Notes (optional)", text: $notes, axis: .vertical)
            if let validationMessage { Text(validationMessage).foregroundStyle(.red).accessibilityAddTraits(.isStaticText) }
            HStack {
                Button("Cancel") { NewScanActionCoordinator.cancel(workflow: &workflow); dismiss() }
                Spacer()
                Button("Start") {
                    let preset = PackagingPresetCatalog.preset(for: presetID)
                    let selectedTreatment = presetID == .transparent ? transparentTreatment : nil
                    if presetID == .transparent && !TransparentPreparationEvaluation(acknowledged: guidanceAcknowledged, treatment: transparentTreatment).mayStart {
                        validationMessage = "Transparent preparation acknowledgement and a non-none treatment are required."
                        return
                    }
                    let preflight = ScanSuitabilityPreflight.evaluate(ScanPreflightInput(preset: preset, admission: admission, cameraReady: true, sessionReady: true, storageAvailable: true, calibration: .ownerRequired, preparationAcknowledged: guidanceAcknowledged, environmentGuidanceAcknowledged: guidanceAcknowledged, transparentTreatment: transparentTreatment))
                    guard preflight.canStart else {
                        validationMessage = preflight.issues.filter { $0.severity == .blocker }.map(\.message).joined(separator: " ")
                        return
                    }
                    if NewScanActionCoordinator.start(workflow: &workflow, name: name, type: packageType, mode: mode, notes: notes, presetID: presetID, preflight: preflight, treatmentMode: selectedTreatment, onStart: onStart) { dismiss() }
                    else if case .validationFailed(let message) = workflow.state { validationMessage = "Cannot start scan: \(message)" }
                }
            }
        }.navigationTitle("New Scan")
    }
}

public struct AcceptedFrameGalleryView: View {
    @State private var entries: [GalleryEntry] = []
    @State private var message: String?
    @State private var deleteTarget: GalleryEntry?
    private let store: SessionGalleryStore
    public let onRetake: ((GalleryEntry) async throws -> RetakeCapturePayload)?
    public init(store: SessionGalleryStore, onRetake: ((GalleryEntry) async throws -> RetakeCapturePayload)? = nil) { self.store = store; self.onRetake = onRetake }
    public var body: some View {
        List(entries) { entry in
            HStack {
                if let previewPath = entry.previewPath, FileManager.default.fileExists(atPath: previewPath), let image = UIImage(contentsOfFile: previewPath) { Image(uiImage: image).resizable().scaledToFit().frame(width: 64, height: 64) }
                else { Image(systemName: "photo.badge.exclamationmark").frame(width: 64, height: 64) }
                VStack(alignment: .leading) { Text(entry.id); Text(entry.status).font(.caption).foregroundStyle(entry.status == "accepted" ? .secondary : .orange) }
                Spacer()
                Button("Retake") {
                    guard let onRetake else { message = "Retake is unavailable for \(entry.id)."; return }
                    Task {
                        do {
                            let replacement = try await onRetake(entry)
                            try await store.retake(replacing: entry.id, source: replacement.source, record: replacement.record, metadata: replacement.metadata)
                            entries = try await store.load()
                        } catch { message = "Retake failed; no state was accepted." }
                    }
                }
                Button("Delete", role: .destructive) { deleteTarget = entry }
            }
        }.overlay { if let message { Text(message).foregroundStyle(.red) } }.confirmationDialog("Delete this accepted frame?", item: $deleteTarget) { entry in
            Button("Delete \(entry.id)", role: .destructive) { Task { do { try await store.delete(id: entry.id, confirmed: true); entries = try await store.load() } catch { message = "Delete failed; no state was accepted." } } }
        }.task { do { entries = try await store.load() } catch { message = "Gallery data is unavailable." } }
            .navigationTitle("Accepted Frames")
    }
}

public struct RetakeCapturePayload: Sendable {
    public let source: Data
    public let record: AcceptedCaptureRecord
    public let metadata: Data
    public init(source: Data, record: AcceptedCaptureRecord, metadata: Data) { self.source = source; self.record = record; self.metadata = metadata }
}

public struct SessionResumeView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var candidates: [SessionResumeCandidate] = []
    private let discovery: SessionDiscoveryService
    public let onResume: (SessionResumeCandidate) -> Void
    public let onDiscard: (SessionResumeCandidate) -> Void
    public init(root: URL, onResume: @escaping (SessionResumeCandidate) -> Void, onDiscard: @escaping (SessionResumeCandidate) -> Void) {
        discovery = SessionDiscoveryService(root: root); self.onResume = onResume; self.onDiscard = onDiscard
    }
    public var body: some View {
        List(candidates) { candidate in
            VStack(alignment: .leading) {
                Text(candidate.draft?.packageName ?? candidate.id)
                switch candidate.disposition {
                case .resumable:
                    Button("Resume") { onResume(candidate); dismiss() }
                    Button("Discard") { onDiscard(candidate); dismiss() }.foregroundStyle(.red)
                case .blocked(let reason): Text("Blocked: \(reason)").foregroundStyle(.red)
                case .discardRequired: Text("Discard required").foregroundStyle(.orange)
                }
            }
        }.task { candidates = await discovery.discover() }.navigationTitle("Resume Scan")
    }
}

public struct LocalScanHistoryView: View {
    @State private var entries: [ScanHistoryEntry] = []
    private let store: LocalScanHistoryStore
    public init(root: URL) { store = LocalScanHistoryStore(root: root) }
    public var body: some View {
        List(entries) { entry in
            HStack {
                if let path = entry.previewPath, let image = UIImage(contentsOfFile: path) { Image(uiImage: image).resizable().scaledToFit().frame(width: 64, height: 64) }
                else { Image(systemName: "exclamationmark.triangle").frame(width: 64, height: 64) }
                VStack(alignment: .leading) { Text(entry.packageName); Text(entry.exportState).font(.caption); if let reason = entry.degradedReason { Text(reason).foregroundStyle(.orange).font(.caption2) } }
            }
        }.task { entries = await store.load() }.navigationTitle("Scan History")
    }
}

public struct SessionDeletionView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var showConfirmation = false
    @State private var errorMessage: String?
    private let plan: SessionDeletionPlan
    private let deleter = SafeSessionDeleter()
    public init(root: URL, candidate: SessionResumeCandidate) { plan = SessionDeletionPlan(root: root, candidate: candidate) }
    public var body: some View {
        VStack(spacing: 16) {
            Text("Delete scan?").font(.title2)
            Text("This permanently removes session \(plan.sessionID), its accepted originals, previews, records, and temporary files.").multilineTextAlignment(.center)
            Button("Delete \(plan.sessionID)", role: .destructive) { showConfirmation = true }
            Button("Cancel") { dismiss() }
            if let errorMessage { Text(errorMessage).foregroundStyle(.red) }
        }.padding().confirmationDialog("Delete this scan?", isPresented: $showConfirmation) { Button("Delete", role: .destructive) { Task { do { let report = try await deleter.deleteDetailed(plan: plan, confirmed: true); if report.failures.isEmpty { dismiss() } else { errorMessage = "Deletion incomplete: \(report.failures.joined(separator: ", "))" } } catch { errorMessage = "Deletion failed: \(error)" } } }; Button("Cancel", role: .cancel) {} }
    }
}
#endif
