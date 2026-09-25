import Foundation

public enum PackLabTransferProtocol {
    public static let name = "packlab-transfer"
    public static let version = "1"
    public static let requiredTransport = "https"
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
}
