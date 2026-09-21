import Foundation

public struct DiagnosticsExportDocument: Codable, Sendable, Equatable {
    public let generatedAt: Date
    public let environment: DiagnosticsEnvironment?
    public let entries: [DiagnosticsEntry]

    public init(
        generatedAt: Date,
        environment: DiagnosticsEnvironment?,
        entries: [DiagnosticsEntry]
    ) {
        self.generatedAt = generatedAt
        self.environment = environment.map {
            DiagnosticsEnvironment(
                appVersion: $0.appVersion,
                buildNumber: $0.buildNumber,
                capabilities: $0.capabilities
            )
        }
        self.entries = entries.map {
            DiagnosticsEntry(
                sequence: $0.sequence,
                timestamp: $0.timestamp,
                level: $0.level,
                category: $0.category,
                code: $0.code,
                message: $0.message
            )
        }
    }
}

public enum DiagnosticsExportError: Error, Sendable, Equatable {
    case empty
}

/// Prepares a user-initiated local export; it never uploads or transfers data.
public struct DiagnosticsExporter: Sendable {
    public init() {}

    public func prepareUserInitiatedExport(
        from logger: DiagnosticsLogger,
        environment: DiagnosticsEnvironment? = nil
    ) async throws -> Data {
        try prepareUserInitiatedExport(
            entries: await logger.snapshot(),
            environment: environment
        )
    }

    public func prepareUserInitiatedExport(
        entries: [DiagnosticsEntry],
        environment: DiagnosticsEnvironment? = nil
    ) throws -> Data {
        guard !entries.isEmpty else {
            throw DiagnosticsExportError.empty
        }
        let document = DiagnosticsExportDocument(
            generatedAt: Date(),
            environment: environment,
            entries: entries
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.sortedKeys]
        return try encoder.encode(document)
    }
}
