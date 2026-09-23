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
    public init(sessionID: String = UUID().uuidString, packageName: String, packageType: PackageType, captureMode: CaptureModeID, notes: String = "", createdAt: Date = Date()) { self.sessionID = sessionID; self.packageName = packageName; self.packageType = packageType; self.captureMode = captureMode; self.notes = notes; self.createdAt = createdAt }
}

public enum NewScanDraftError: Error, Sendable, Equatable { case emptyName, nameTooLong, notesTooLong }
public enum NewScanDraftValidator {
    public static let maximumNameLength = 120
    public static let maximumNotesLength = 500
    public static func make(name: String, type: PackageType, mode: CaptureModeID, notes: String = "", now: Date = Date(), sessionID: String = UUID().uuidString) throws -> NewScanDraft {
        let normalizedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        let normalizedNotes = notes.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !normalizedName.isEmpty else { throw NewScanDraftError.emptyName }
        guard normalizedName.count <= maximumNameLength else { throw NewScanDraftError.nameTooLong }
        guard normalizedNotes.count <= maximumNotesLength else { throw NewScanDraftError.notesTooLong }
        return NewScanDraft(sessionID: sessionID, packageName: normalizedName, packageType: type, captureMode: mode, notes: normalizedNotes, createdAt: now)
    }
}

public struct NewScanWorkflowModel: Sendable, Equatable {
    public enum State: Sendable, Equatable { case editing, validationFailed(String), started(NewScanDraft), cancelled }
    public private(set) var state: State = .editing
    public init() {}
    public mutating func start(name: String, type: PackageType, mode: CaptureModeID, notes: String = "", now: Date = Date(), sessionID: String = UUID().uuidString) -> NewScanDraft? {
        do { let draft = try NewScanDraftValidator.make(name: name, type: type, mode: mode, notes: notes, now: now, sessionID: sessionID); state = .started(draft); return draft }
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
}

public enum SessionStorageError: Error, Sendable, Equatable { case invalidID, duplicateID, interruptedWrite, missingRecord }

public struct AcceptedCaptureRecord: Codable, Sendable, Equatable {
    public let captureID: String
    public let sequence: Int
    public let sourceFilename: String
    public let metadataFilename: String
    public let acceptedAt: Date
    public init(captureID: String, sequence: Int, sourceFilename: String, metadataFilename: String, acceptedAt: Date = Date()) { self.captureID = captureID; self.sequence = sequence; self.sourceFilename = sourceFilename; self.metadataFilename = metadataFilename; self.acceptedAt = acceptedAt }
}

public enum SessionReopenDisposition: Sendable, Equatable { case resumable(PersistedSessionState), blocked(String) }

public actor ScanSessionStore {
    private let layout: SessionStorageLayout
    private let fileManager: FileManager
    public init(layout: SessionStorageLayout, fileManager: FileManager = .default) { self.layout = layout; self.fileManager = fileManager }
    public func create(_ draft: NewScanDraft) throws {
        guard draft.sessionID == layout.sessionID, validID(draft.sessionID) else { throw SessionStorageError.invalidID }
        guard !fileManager.fileExists(atPath: layout.sessionRoot.path) else { throw SessionStorageError.duplicateID }
        try fileManager.createDirectory(at: layout.images, withIntermediateDirectories: true)
        try fileManager.createDirectory(at: layout.previews, withIntermediateDirectories: true)
        try fileManager.createDirectory(at: layout.photoRecords, withIntermediateDirectories: true)
        try fileManager.createDirectory(at: layout.temporary, withIntermediateDirectories: true)
        try atomicWrite(JSONEncoder().encode(draft), to: layout.metadata)
        try atomicWrite(Data("{\"accepted\":0}".utf8), to: layout.state)
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
        do {
            try source.write(to: sourceURL, options: .atomic)
            try atomicWrite(metadata, to: recordURL)
            try atomicWrite(state, to: layout.state)
        } catch {
            try? fileManager.removeItem(at: sourceURL)
            try? fileManager.removeItem(at: recordURL)
            throw error
        }
    }

    public func reopen(requiredSourceIDs: Set<String>, supportedVersion: String = "1.0.0") throws -> SessionReopenDisposition {
        try recoverStaleTemps()
        guard let stateData = try? Data(contentsOf: layout.state), let state = try? JSONDecoder().decode(PersistedSessionState.self, from: stateData) else { return .blocked("missing_state") }
        let sourceIDs = try fileManager.contentsOfDirectory(at: layout.images, includingPropertiesForKeys: nil).map { $0.deletingPathExtension().lastPathComponent }
        let disposition = SessionResumeValidator.disposition(state: state, requiredSourceIDs: Set(sourceIDs).union(requiredSourceIDs), supportedVersion: supportedVersion)
        switch disposition { case .resumable: return .resumable(state); case .blocked(let reason): return .blocked(reason); case .discardRequired: return .blocked("discard_required") }
    }

    private func recoverStaleTemps() throws {
        guard let files = try? fileManager.contentsOfDirectory(at: layout.temporary, includingPropertiesForKeys: nil) else { return }
        for file in files where file.lastPathComponent.contains(".tmp-") || file.pathExtension == "tmp" { try? fileManager.removeItem(at: file) }
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
    public init(layout: SessionStorageLayout, fileManager: FileManager = .default) { self.layout = layout; self.fileManager = fileManager }

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
        try appendAudit(audit)
        for path in [recordURL.path, entry.sourcePath, entry.previewPath ?? ""] where !path.isEmpty { try? fileManager.removeItem(atPath: path) }
    }

    public func retake(replacing id: String, source: Data, record: AcceptedCaptureRecord, metadata: Data) throws {
        guard record.captureID != id else { throw GalleryMutationError.invalidReplacement }
        guard try load().contains(where: { $0.id == id }) else { throw GalleryMutationError.notFound }
        let sourceURL = layout.images.appendingPathComponent(record.sourceFilename)
        let recordURL = layout.photoRecords.appendingPathComponent(record.metadataFilename)
        guard !fileManager.fileExists(atPath: sourceURL.path), !fileManager.fileExists(atPath: recordURL.path) else { throw SessionStorageError.duplicateID }
        try source.write(to: sourceURL, options: .atomic)
        try metadata.write(to: recordURL, options: .atomic)
        try appendAudit(GalleryAuditEvent(action: "retake", captureID: id, replacementID: record.captureID))
    }

    private func appendAudit(_ event: GalleryAuditEvent) throws {
        let url = layout.sessionRoot.appendingPathComponent("gallery-audit.json")
        var events = (try? JSONDecoder().decode([GalleryAuditEvent].self, from: Data(contentsOf: url))) ?? []
        events.append(event)
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        try encoder.encode(events).write(to: url, options: .atomic)
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
    public func discover() -> [SessionResumeCandidate] {
        guard let directories = try? fileManager.contentsOfDirectory(at: root, includingPropertiesForKeys: [.isDirectoryKey]) else { return [] }
        return directories.filter { $0.hasDirectoryPath }.map { directory in
            let id = directory.lastPathComponent
            let layout = SessionStorageLayout(root: root, sessionID: id)
            let draft = (try? Data(contentsOf: layout.metadata)).flatMap { try? JSONDecoder().decode(NewScanDraft.self, from: $0) }
            let state = (try? Data(contentsOf: layout.state)).flatMap { try? JSONDecoder().decode(PersistedSessionState.self, from: $0) }
            let sourceIDs = Set((try? fileManager.contentsOfDirectory(at: layout.images, includingPropertiesForKeys: nil).map { $0.deletingPathExtension().lastPathComponent }) ?? [])
            let disposition = SessionResumeValidator.disposition(state: state, requiredSourceIDs: sourceIDs)
            return SessionResumeCandidate(id: id, draft: draft, disposition: disposition, state: state)
        }.sorted { $0.id < $1.id }
    }
}

public enum FinalizationError: Error, Sendable, Equatable { case missingPhoto, invalidMetadataBinding, checksumFailure, invalidManifest, packagingFailed }
public struct FinalizationInput: Sendable { public let manifest: Data; public let payloads: [String: Data]; public let destination: URL; public init(manifest: Data, payloads: [String: Data], destination: URL) { self.manifest = manifest; self.payloads = payloads; self.destination = destination } }
public struct SessionFinalizer: Sendable {
    public init() {}
    public func validate(_ input: FinalizationInput) throws {
        guard let object = try? JSONSerialization.jsonObject(with: input.manifest) as? [String: Any], let payloads = object["payloads"] as? [[String: Any]], payloads.contains(where: { ($0["path"] as? String)?.hasPrefix("images/") == true }), input.payloads.keys.contains("metadata/photos.json") else { throw FinalizationError.missingPhoto }
        for item in payloads {
            guard let path = item["path"] as? String, let bytes = input.payloads[path], let size = item["size_bytes"] as? Int, bytes.count == size else { throw FinalizationError.checksumFailure }
        }
    }
    public func finalize(_ input: FinalizationInput) throws {
        do { try validate(input); try PackScanWriter().write(manifestJSON: input.manifest, payloads: input.payloads, to: input.destination) }
        catch let error as FinalizationError { throw error }
        catch { throw FinalizationError.packagingFailed }
    }
}

public struct ScanHistoryEntry: Sendable, Equatable, Identifiable {
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

public enum DeletionError: Error, Sendable, Equatable { case confirmationRequired, outsideRoot, symlinkEscape, partialFailure }
public struct SessionDeletionPlan: Sendable, Equatable {
    public let root: URL
    public let session: URL
    public init(root: URL, session: URL) { self.root = root.standardizedFileURL; self.session = session.standardizedFileURL }
    public func validate(confirmed: Bool, fileManager: FileManager = .default) throws {
        guard confirmed else { throw DeletionError.confirmationRequired }
        let rootPath = root.resolvingSymlinksInPath.path
        let sessionPath = session.resolvingSymlinksInPath.path
        guard sessionPath != rootPath, sessionPath.hasPrefix(rootPath + "/") else { throw DeletionError.outsideRoot }
        guard sessionPath == session.path else { throw DeletionError.symlinkEscape }
        _ = fileManager
    }
}
public actor SafeSessionDeleter {
    private let fileManager: FileManager
    public init(fileManager: FileManager = .default) { self.fileManager = fileManager }
    public func delete(plan: SessionDeletionPlan, confirmed: Bool) throws {
        try plan.validate(confirmed: confirmed, fileManager: fileManager)
        guard fileManager.fileExists(atPath: plan.session.path) else { return }
        do { try fileManager.removeItem(at: plan.session) } catch { throw DeletionError.partialFailure }
    }
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
    @State private var validationMessage: String?
    public let onStart: (NewScanDraft) -> Void
    public init(onStart: @escaping (NewScanDraft) -> Void) { self.onStart = onStart }
    public var body: some View {
        Form {
            TextField("Package name", text: $name)
            Picker("Package type", selection: $packageType) { ForEach(PackageType.allCases, id: \.self) { Text($0.rawValue.capitalized).tag($0) } }
            Picker("Capture mode", selection: $mode) { ForEach(CaptureModeID.allCases, id: \.self) { Text($0.rawValue).tag($0) } }
            TextField("Notes (optional)", text: $notes, axis: .vertical)
            if let validationMessage { Text(validationMessage).foregroundStyle(.red).accessibilityAddTraits(.isStaticText) }
            HStack {
                Button("Cancel") { dismiss() }
                Spacer()
                Button("Start") {
                    do {
                        let draft = try NewScanDraftValidator.make(name: name, type: packageType, mode: mode, notes: notes)
                        onStart(draft); dismiss()
                    } catch let error as NewScanDraftError {
                        validationMessage = "Cannot start scan: \(error)"
                    } catch { validationMessage = "Cannot start scan." }
                }
            }
        }.navigationTitle("New Scan")
    }
}

public struct AcceptedFrameGalleryView: View {
    @State private var entries: [GalleryEntry] = []
    @State private var message: String?
    private let store: SessionGalleryStore
    public init(store: SessionGalleryStore) { self.store = store }
    public var body: some View {
        List(entries) { entry in
            HStack {
                if let previewPath = entry.previewPath, FileManager.default.fileExists(atPath: previewPath), let image = UIImage(contentsOfFile: previewPath) { Image(uiImage: image).resizable().scaledToFit().frame(width: 64, height: 64) }
                else { Image(systemName: "photo.badge.exclamationmark").frame(width: 64, height: 64) }
                VStack(alignment: .leading) { Text(entry.id); Text(entry.status).font(.caption).foregroundStyle(entry.status == "accepted" ? .secondary : .orange) }
            }
        }.overlay { if let message { Text(message).foregroundStyle(.red) } }.task { do { entries = try await store.load() } catch { message = "Gallery data is unavailable." } }
            .navigationTitle("Accepted Frames")
    }
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
#endif
