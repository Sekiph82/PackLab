import Foundation

public enum PackLabTransferProtocol {
    public static let name = "packlab-transfer"
    public static let version = "1"
    public static let requiredTransport = "https"
}

public enum TransferWireError: Error, Sendable, Equatable { case unsupportedVersion, insecureTransport, malformed }
public enum TransferWireValidation {
    public static func validate(protocolName: String, version: String, transport: String? = nil) throws {
        guard protocolName == PackLabTransferProtocol.name else { throw TransferWireError.malformed }
        guard version == PackLabTransferProtocol.version else { throw TransferWireError.unsupportedVersion }
        if let transport, transport != PackLabTransferProtocol.requiredTransport { throw TransferWireError.insecureTransport }
    }
}

private enum TransferWireDecoder {
    static func envelope(_ decoder: Decoder, message: String? = nil) throws -> (protocolName: String, version: String, container: KeyedDecodingContainer<AnyCodingKey>) {
        let container = try decoder.container(keyedBy: AnyCodingKey.self)
        let name = try container.decode(String.self, forKey: AnyCodingKey("protocol"))
        let version = try container.decode(String.self, forKey: AnyCodingKey("protocol_version"))
        guard name == PackLabTransferProtocol.name else { throw TransferWireError.malformed }
        guard version == PackLabTransferProtocol.version else { throw TransferWireError.unsupportedVersion }
        if let message, try container.decode(String.self, forKey: AnyCodingKey("message")) != message { throw TransferWireError.malformed }
        return (name, version, container)
    }
}

private struct AnyCodingKey: CodingKey {
    let stringValue: String
    let intValue: Int? = nil
    init(_ string: String) { stringValue = string }
    init?(stringValue: String) { self.init(stringValue) }
    init?(intValue: Int) { return nil }
}

public struct TransferCreateMessage: Codable, Sendable, Equatable {
    public let message = "create_transfer"
    public let protocolName = PackLabTransferProtocol.name
    public let protocolVersion: String
    public let transport: String
    public let receiverID: String
    public let transferID: String
    public let captureID: String
    public let packageName: String
    public let totalBytes: Int
    public let packageSHA256: String

    enum CodingKeys: String, CodingKey {
        case message, protocolName = "protocol", protocolVersion = "protocol_version", transport
        case receiverID = "receiver_id", transferID = "transfer_id", captureID = "capture_id"
        case packageName = "package_name", totalBytes = "total_bytes", packageSHA256 = "package_sha256"
    }

    public init(receiverID: String, transferID: String, captureID: String, packageName: String, totalBytes: Int, packageSHA256: String) {
        self.protocolVersion = PackLabTransferProtocol.version
        self.transport = PackLabTransferProtocol.requiredTransport
        self.receiverID = receiverID
        self.transferID = transferID
        self.captureID = captureID
        self.packageName = packageName
        self.totalBytes = totalBytes
        self.packageSHA256 = packageSHA256
    }

    public init(from decoder: Decoder) throws {
        let (_, version, values) = try TransferWireDecoder.envelope(decoder, message: "create_transfer")
        protocolVersion = version
        transport = try values.decode(String.self, forKey: AnyCodingKey("transport"))
        receiverID = try values.decode(String.self, forKey: AnyCodingKey("receiver_id"))
        transferID = try values.decode(String.self, forKey: AnyCodingKey("transfer_id"))
        captureID = try values.decode(String.self, forKey: AnyCodingKey("capture_id"))
        packageName = try values.decode(String.self, forKey: AnyCodingKey("package_name"))
        totalBytes = try values.decode(Int.self, forKey: AnyCodingKey("total_bytes"))
        packageSHA256 = try values.decode(String.self, forKey: AnyCodingKey("package_sha256"))
        try TransferWireValidation.validate(protocolName: PackLabTransferProtocol.name, version: version, transport: transport)
    }
}

public struct TransferChunkMessage: Codable, Sendable, Equatable {
    public let message = "put_chunk"
    public let protocolName = PackLabTransferProtocol.name
    public let protocolVersion = PackLabTransferProtocol.version
    public let transferID: String
    public let offset: Int
    public let length: Int
    public let chunkSHA256: String
    enum CodingKeys: String, CodingKey { case message, protocolName = "protocol", protocolVersion = "protocol_version", transferID = "transfer_id", offset, length, chunkSHA256 = "chunk_sha256" }

    public init(from decoder: Decoder) throws {
        let (_, _, values) = try TransferWireDecoder.envelope(decoder, message: "put_chunk")
        transferID = try values.decode(String.self, forKey: AnyCodingKey("transfer_id"))
        offset = try values.decode(Int.self, forKey: AnyCodingKey("offset"))
        length = try values.decode(Int.self, forKey: AnyCodingKey("length"))
        chunkSHA256 = try values.decode(String.self, forKey: AnyCodingKey("chunk_sha256"))
    }
}

public struct TransferStatusMessage: Codable, Sendable, Equatable {
    public let message = "transfer_status"
    public let protocolName = PackLabTransferProtocol.name
    public let protocolVersion: String
    public let transferID: String
    public let confirmedBytes: Int
    public let totalBytes: Int
    public let state: String
    public let packageSHA256: String
    public let nextOffset: Int
    enum CodingKeys: String, CodingKey { case message, protocolName = "protocol", protocolVersion = "protocol_version", transferID = "transfer_id", confirmedBytes = "confirmed_bytes", totalBytes = "total_bytes", state, packageSHA256 = "package_sha256", nextOffset = "next_offset" }
    public init(transferID: String, confirmedBytes: Int, totalBytes: Int, state: String, packageSHA256: String, nextOffset: Int) {
        self.protocolVersion = PackLabTransferProtocol.version; self.transferID = transferID; self.confirmedBytes = confirmedBytes; self.totalBytes = totalBytes; self.state = state; self.packageSHA256 = packageSHA256; self.nextOffset = nextOffset
    }
    public init(from decoder: Decoder) throws {
        let (_, version, values) = try TransferWireDecoder.envelope(decoder, message: "transfer_status")
        protocolVersion = version
        transferID = try values.decode(String.self, forKey: AnyCodingKey("transfer_id"))
        confirmedBytes = try values.decode(Int.self, forKey: AnyCodingKey("confirmed_bytes"))
        totalBytes = try values.decode(Int.self, forKey: AnyCodingKey("total_bytes"))
        state = try values.decode(String.self, forKey: AnyCodingKey("state"))
        packageSHA256 = try values.decode(String.self, forKey: AnyCodingKey("package_sha256"))
        nextOffset = try values.decode(Int.self, forKey: AnyCodingKey("next_offset"))
    }
}

public struct TransferControlMessage: Codable, Sendable, Equatable {
    public let message: String
    public let protocolName = PackLabTransferProtocol.name
    public let protocolVersion = PackLabTransferProtocol.version
    public let transferID: String
    enum CodingKeys: String, CodingKey { case message, protocolName = "protocol", protocolVersion = "protocol_version", transferID = "transfer_id" }
    public init(action: String, transferID: String) { self.message = action; self.transferID = transferID }
    public init(from decoder: Decoder) throws {
        let (_, _, values) = try TransferWireDecoder.envelope(decoder)
        message = try values.decode(String.self, forKey: AnyCodingKey("message"))
        guard message == "cancel" || message == "resume" else { throw TransferWireError.malformed }
        transferID = try values.decode(String.self, forKey: AnyCodingKey("transfer_id"))
    }
}

public struct TransferCompletionAcknowledgement: Codable, Sendable, Equatable {
    public let message = "completion_acknowledgement"
    public let protocolName = PackLabTransferProtocol.name
    public let protocolVersion = PackLabTransferProtocol.version
    public let transferID: String
    public let packageSHA256: String
    public let verified: Bool
    public let authenticated: Bool
    public let state: String
    enum CodingKeys: String, CodingKey { case message, protocolName = "protocol", protocolVersion = "protocol_version", transferID = "transfer_id", packageSHA256 = "package_sha256", verified, authenticated, state }
    public init(transferID: String, packageSHA256: String, verified: Bool, authenticated: Bool, state: String) { self.transferID = transferID; self.packageSHA256 = packageSHA256; self.verified = verified; self.authenticated = authenticated; self.state = state }
    public init(from decoder: Decoder) throws {
        let (_, _, values) = try TransferWireDecoder.envelope(decoder, message: "completion_acknowledgement")
        transferID = try values.decode(String.self, forKey: AnyCodingKey("transfer_id"))
        packageSHA256 = try values.decode(String.self, forKey: AnyCodingKey("package_sha256"))
        verified = try values.decode(Bool.self, forKey: AnyCodingKey("verified"))
        authenticated = try values.decode(Bool.self, forKey: AnyCodingKey("authenticated"))
        state = try values.decode(String.self, forKey: AnyCodingKey("state"))
    }
}

public struct TransferErrorEnvelope: Codable, Sendable, Equatable {
    public let message = "error"
    public let protocolName = PackLabTransferProtocol.name
    public let protocolVersion = PackLabTransferProtocol.version
    public let errorCode: String
    public let error: String
    enum CodingKeys: String, CodingKey { case message, protocolName = "protocol", protocolVersion = "protocol_version", errorCode = "error_code", error }
    public init(from decoder: Decoder) throws {
        let (_, _, values) = try TransferWireDecoder.envelope(decoder, message: "error")
        errorCode = try values.decode(String.self, forKey: AnyCodingKey("error_code"))
        error = try values.decode(String.self, forKey: AnyCodingKey("error"))
    }
}
