import Foundation

public enum DiagnosticsSanitizer {
    public static func sanitize(_ value: String, maxLength: Int = 512) -> String {
        var sanitized = value
        sanitized = replace(
            pattern: #"(?i)\b(api[_-]?key|access[_-]?token|authorization|bearer|password|passwd|secret|private[_-]?key|client[_-]?secret|credential|token)\b\s*[:=]\s*["']?[^"'\s,;]+["']?"#,
            in: sanitized,
            with: "[REDACTED_SECRET]"
        )
        sanitized = replace(
            pattern: #"(?i)([?&](?:api[_-]?key|access[_-]?token|token|secret|password)=)[^&#\s]+"#,
            in: sanitized,
            with: "$1[REDACTED_SECRET]"
        )
        sanitized = replace(
            pattern: #"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"#,
            in: sanitized,
            with: "Bearer [REDACTED_SECRET]"
        )
        sanitized = replace(
            pattern: #"\b(?:eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|gh[pousr]_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)\b"#,
            in: sanitized,
            with: "[REDACTED_TOKEN]"
        )
        sanitized = replace(
            pattern: #"(?i)(?:[A-Z]:[\\/]+Users[\\/]+[^\\/\s]+(?:[\\/]+[^\s]*)*|/Users/[^/\s]+(?:/[^/\s]*)*|/home/[^/\s]+(?:/[^/\s]*)*)"#,
            in: sanitized,
            with: "[USER_PATH]"
        )
        sanitized = replace(pattern: #"[\x00-\x1F\x7F]"#, in: sanitized, with: " ")
        sanitized = sanitized.split(whereSeparator: \.isWhitespace).joined(separator: " ")
        sanitized = String(sanitized.prefix(max(1, maxLength))).trimmingCharacters(in: .whitespacesAndNewlines)
        return sanitized.isEmpty ? "[EMPTY]" : sanitized
    }

    public static func sanitizeCapability(_ value: String) -> String {
        let sanitized = sanitize(value, maxLength: 128)
        var result = ""
        for scalar in sanitized.lowercased().unicodeScalars {
            if CharacterSet.alphanumerics.contains(scalar) || scalar == "." || scalar == "-" || scalar == "_" {
                result.unicodeScalars.append(scalar)
            } else {
                result.append("-")
            }
        }
        result = result.replacingOccurrences(of: #"-+"#, with: "-", options: .regularExpression)
        result = result.trimmingCharacters(in: CharacterSet(charactersIn: "-"))
        return String(result.prefix(128)).isEmpty ? "unknown" : String(result.prefix(128))
    }

    private static func replace(pattern: String, in value: String, with replacement: String) -> String {
        guard let expression = try? NSRegularExpression(pattern: pattern) else {
            return value
        }
        let range = NSRange(value.startIndex..<value.endIndex, in: value)
        return expression.stringByReplacingMatches(in: value, range: range, withTemplate: replacement)
    }
}

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
        self.appVersion = DiagnosticsSanitizer.sanitize(appVersion, maxLength: 64)
        self.buildNumber = DiagnosticsSanitizer.sanitize(buildNumber, maxLength: 64)
        self.capabilities = Array(Set(capabilities.map(DiagnosticsSanitizer.sanitizeCapability))).sorted()
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
        self.category = DiagnosticsSanitizer.sanitize(category, maxLength: 128)
        self.code = DiagnosticsSanitizer.sanitize(code, maxLength: 128)
        self.message = DiagnosticsSanitizer.sanitize(message)
    }
}

/// Bounded, local-only diagnostics storage with an enforced privacy boundary.
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
