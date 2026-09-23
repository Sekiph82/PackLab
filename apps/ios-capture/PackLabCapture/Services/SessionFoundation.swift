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
