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

    public init(packageURL: URL, packageName: String, packageBytes: Int) {
        self.packageURL = packageURL
        self.packageName = packageName
        self.packageBytes = packageBytes
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
        return FinalizedPackScanShare(packageURL: url, packageName: url.lastPathComponent, packageBytes: values.fileSize ?? 0)
    }

    public func packageStillAvailable(_ share: FinalizedPackScanShare) -> Bool {
        (try? share.packageURL.resourceValues(forKeys: [.isRegularFileKey]).isRegularFile) == true
    }
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
