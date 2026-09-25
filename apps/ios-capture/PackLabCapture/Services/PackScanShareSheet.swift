import Foundation
import SwiftUI

public enum PackScanShareError: Error, Sendable, Equatable {
    case notFinalized
    case missingPackage
    case unsupportedPackage
}

public struct FinalizedPackScanShare: Sendable, Equatable {
    public let packageURL: URL
    public let packageName: String
    public let packageBytes: Int
    public let packageSHA256: String?

    public init(packageURL: URL, packageName: String, packageBytes: Int, packageSHA256: String? = nil) {
        self.packageURL = packageURL
        self.packageName = packageName
        self.packageBytes = packageBytes
        self.packageSHA256 = packageSHA256
    }
}

public struct PackScanShareCoordinator: Sendable {
    public init() {}

    /// Only an exported, regular `.packscan` file is eligible. The mutable
    /// session directory and any partial/staging file are never returned.
    public func eligiblePackage(at url: URL, finalization: SessionFinalizationRecord?) throws -> FinalizedPackScanShare {
        guard finalization?.state == .exported, finalization?.packagePath == url.path else {
            throw PackScanShareError.notFinalized
        }
        let values = try url.resourceValues(forKeys: [.isRegularFileKey, .fileSizeKey])
        guard values.isRegularFile == true else { throw PackScanShareError.missingPackage }
        guard url.pathExtension.lowercased() == "packscan" else { throw PackScanShareError.unsupportedPackage }
        guard finalization?.packageBytes == nil || finalization?.packageBytes == values.fileSize else { throw PackScanShareError.notFinalized }
        return FinalizedPackScanShare(packageURL: url, packageName: url.lastPathComponent, packageBytes: values.fileSize ?? 0, packageSHA256: finalization?.packageSHA256)
    }

    public func packageStillAvailable(_ share: FinalizedPackScanShare) -> Bool {
        guard let values = try? share.packageURL.resourceValues(forKeys: [.isRegularFileKey, .fileSizeKey]), values.isRegularFile == true, values.fileSize == share.packageBytes else { return false }
        guard let expected = share.packageSHA256 else { return true }
        guard let data = try? Data(contentsOf: share.packageURL) else { return false }
        return SourceIntegrity.digest(data) == expected
    }
}

public enum PackScanSharePresentationState: Sendable, Equatable { case idle, presenting, cancelled, completed, failed(String), missingPackage }

@MainActor
public final class PackScanSharePresentationCoordinator: ObservableObject {
    @Published public private(set) var state: PackScanSharePresentationState = .idle
    public private(set) var activeShare: FinalizedPackScanShare?
    private let eligibility: PackScanShareCoordinator
    public init(eligibility: PackScanShareCoordinator = PackScanShareCoordinator()) { self.eligibility = eligibility }
    public func prepare(url: URL, finalization: SessionFinalizationRecord?) {
        do { activeShare = try eligibility.eligiblePackage(at: url, finalization: finalization); state = .presenting }
        catch PackScanShareError.missingPackage { state = .missingPackage }
        catch { state = .failed("share_not_available") }
    }
    public func activityFinished(completed: Bool) { state = completed ? .completed : .cancelled; activeShare = nil }
    public func presentationFailed() { state = .failed("share_presentation_failed"); activeShare = nil }
    public func sourceReplacedOrDeleted() { if let activeShare, !eligibility.packageStillAvailable(activeShare) { state = .missingPackage; self.activeShare = nil } }
}

#if canImport(UIKit)
import UIKit

public final class PackScanShareActivityItem: NSObject, UIActivityItemSource {
    private let packageURL: URL
    public init(packageURL: URL) { self.packageURL = packageURL }
    public func activityViewControllerPlaceholderItem(_ activityViewController: UIActivityViewController) -> Any { packageURL }
    public func activityViewController(_ activityViewController: UIActivityViewController, itemForActivityType activityType: UIActivity.ActivityType?) -> Any? {
        guard FileManager.default.fileExists(atPath: packageURL.path) else { return nil }
        return packageURL
    }
    public func activityViewController(_ activityViewController: UIActivityViewController, subjectForActivityType activityType: UIActivity.ActivityType?) -> String? {
        packageURL.deletingPathExtension().lastPathComponent
    }
}

public struct PackScanShareSheet: UIViewControllerRepresentable {
    public let share: FinalizedPackScanShare
    public let completion: @MainActor @Sendable (Bool) -> Void

    public init(share: FinalizedPackScanShare, completion: @escaping @MainActor @Sendable (Bool) -> Void = { _ in }) {
        self.share = share
        self.completion = completion
    }

    public func makeUIViewController(context: Context) -> UIActivityViewController {
        let controller = UIActivityViewController(activityItems: [PackScanShareActivityItem(packageURL: share.packageURL)], applicationActivities: nil)
        controller.completionWithItemsHandler = { _, completed, _, _ in
            Task { @MainActor in self.completion(completed) }
        }
        return controller
    }

    public func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}
#endif
