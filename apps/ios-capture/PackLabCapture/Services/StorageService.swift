import Foundation

public protocol StorageService: Sendable {
    func store(_ data: Data, named name: String) async throws -> URL
    func remove(_ url: URL) async throws
}

public enum StorageServiceError: Error, Sendable, Equatable {
    case invalidName
}

/// Minimal local storage seam. Product-specific formats and retention are deferred.
public actor LocalStorageService: StorageService {
    private let rootDirectory: URL
    private let fileManager: FileManager

    public init(rootDirectory: URL, fileManager: FileManager = .default) {
        self.rootDirectory = rootDirectory
        self.fileManager = fileManager
    }

    public func store(_ data: Data, named name: String) async throws -> URL {
        guard !name.isEmpty, name.last != "/", !name.contains("..") else {
            throw StorageServiceError.invalidName
        }
        try fileManager.createDirectory(at: rootDirectory, withIntermediateDirectories: true)
        let destination = rootDirectory.appendingPathComponent(name, isDirectory: false)
        try data.write(to: destination, options: .atomic)
        return destination
    }

    public func remove(_ url: URL) async throws {
        guard url.deletingLastPathComponent() == rootDirectory else {
            throw StorageServiceError.invalidName
        }
        if fileManager.fileExists(atPath: url.path) {
            try fileManager.removeItem(at: url)
        }
    }
}
