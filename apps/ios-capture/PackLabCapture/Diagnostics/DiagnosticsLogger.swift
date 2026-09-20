import Foundation

public enum DiagnosticsLevel: String, Codable, Sendable {
    case info
    case warning
    case error
}

public struct DiagnosticsEnvironment: Codable, Sendable, Equatable {
    public let appVersion: String
    public let buildNumber: String
    public let capabilities: [String]

    public init(appVersion: String, buildNumber: String, capabilities: [String]) {
        self.appVersion = appVersion
        self.buildNumber = buildNumber
        self.capabilities = capabilities.sorted()
    }
}

public struct DiagnosticsEntry: Codable, Sendable, Equatable {
    public let sequence: Int
    public let timestamp: Date
    public let level: DiagnosticsLevel
    public let category: String
    public let code: String
    public let message: String

    public init(
        sequence: Int,
        timestamp: Date,
        level: DiagnosticsLevel,
        category: String,
        code: String,
        message: String
    ) {
        self.sequence = sequence
        self.timestamp = timestamp
        self.level = level
        self.category = category
        self.code = code
        self.message = message
    }
}

/// Bounded, local-only diagnostics storage. Callers provide event codes and non-sensitive messages.
public actor DiagnosticsLogger {
    private let capacity: Int
    private var nextSequence = 0
    private var buffer: [DiagnosticsEntry] = []

    public init(capacity: Int = 200) {
        self.capacity = max(1, capacity)
    }

    public func record(
        level: DiagnosticsLevel = .info,
        category: String,
        code: String,
        message: String
    ) {
        let entry = DiagnosticsEntry(
            sequence: nextSequence,
            timestamp: Date(),
            level: level,
            category: category,
            code: code,
            message: message
        )
        nextSequence += 1
        buffer.append(entry)
        if buffer.count > capacity {
            buffer.removeFirst(buffer.count - capacity)
        }
    }

    public func snapshot() -> [DiagnosticsEntry] {
        buffer
    }

    public func clear() {
        buffer.removeAll(keepingCapacity: true)
    }
}
