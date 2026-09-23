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

public struct SessionStorageLayout: Sendable, Equatable {
    public let root: URL
    public let sessionID: String
    public init(root: URL, sessionID: String) { self.root = root; self.sessionID = sessionID }
    public var sessionRoot: URL { root.appendingPathComponent(sessionID, isDirectory: true) }
    public var metadata: URL { sessionRoot.appendingPathComponent("metadata.json") }
    public var state: URL { sessionRoot.appendingPathComponent("state.json") }
    public var images: URL { sessionRoot.appendingPathComponent("images", isDirectory: true) }
    public var previews: URL { sessionRoot.appendingPathComponent("previews", isDirectory: true) }
    public var temporary: URL { sessionRoot.appendingPathComponent("tmp", isDirectory: true) }
}

public enum SessionStorageError: Error, Sendable, Equatable { case invalidID, duplicateID, interruptedWrite, missingRecord }

public actor ScanSessionStore {
    private let layout: SessionStorageLayout
    private let fileManager: FileManager
    public init(layout: SessionStorageLayout, fileManager: FileManager = .default) { self.layout = layout; self.fileManager = fileManager }
    public func create(_ draft: NewScanDraft) throws {
        guard draft.sessionID == layout.sessionID, validID(draft.sessionID) else { throw SessionStorageError.invalidID }
        guard !fileManager.fileExists(atPath: layout.sessionRoot.path) else { throw SessionStorageError.duplicateID }
        try fileManager.createDirectory(at: layout.images, withIntermediateDirectories: true)
        try fileManager.createDirectory(at: layout.previews, withIntermediateDirectories: true)
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

#if canImport(SwiftUI)
import SwiftUI
public struct NewScanWizard: View {
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var packageType: PackageType = .bottle
    @State private var mode: CaptureModeID = .freehand
    @State private var notes = ""
    public let onStart: (NewScanDraft) -> Void
    public init(onStart: @escaping (NewScanDraft) -> Void) { self.onStart = onStart }
    public var body: some View {
        Form {
            TextField("Package name", text: $name)
            Picker("Package type", selection: $packageType) { ForEach(PackageType.allCases, id: \.self) { Text($0.rawValue.capitalized).tag($0) } }
            Picker("Capture mode", selection: $mode) { ForEach(CaptureModeID.allCases, id: \.self) { Text($0.rawValue).tag($0) } }
            TextField("Notes (optional)", text: $notes, axis: .vertical)
            HStack { Button("Cancel") { dismiss() }; Spacer(); Button("Start") { if let draft = try? NewScanDraftValidator.make(name: name, type: packageType, mode: mode, notes: notes) { onStart(draft); dismiss() } } }
        }.navigationTitle("New Scan")
    }
}
#endif
