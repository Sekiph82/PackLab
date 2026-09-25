import Foundation

public struct PairingOffer: Codable, Sendable, Equatable {
    public let protocolName: String
    public let protocolVersion: String
    public let receiverInstanceID: String
    public let host: String
    public let port: Int
    public let pairingID: String
    public let pairingCode: String
    public let expiresAt: Double
    public let tlsCertificateFingerprint: String

    enum CodingKeys: String, CodingKey {
        case protocolName = "protocol", protocolVersion = "protocol_version", receiverInstanceID = "receiver_instance_id"
        case host, port, pairingID = "pairing_id", pairingCode = "pairing_code", expiresAt = "expires_at"
        case tlsCertificateFingerprint = "tls_certificate_fingerprint"
    }

    public init(data: Data) throws {
        self = try JSONDecoder().decode(Self.self, from: data)
        guard protocolName == PackLabTransferProtocol.name, protocolVersion == PackLabTransferProtocol.version else { throw PairingProtocolError.unsupportedVersion }
        guard !receiverInstanceID.isEmpty, !pairingID.isEmpty, !pairingCode.isEmpty, (1...65535).contains(port), !tlsCertificateFingerprint.isEmpty else { throw PairingProtocolError.malformed }
    }

    public func payloadData() throws -> Data { try JSONEncoder().encode(self) }
}

public enum PairingProtocolError: Error, Sendable, Equatable { case malformed, unsupportedVersion, expired, wrongReceiver, wrongPin, replayed }

public struct PairingCodeEntry: Sendable, Equatable {
    public let receiverInstanceID: String
    public let pairingCode: String
    public init(receiverInstanceID: String, pairingCode: String) { self.receiverInstanceID = receiverInstanceID; self.pairingCode = pairingCode.replacingOccurrences(of: "-", with: "").uppercased() }
}

/// Camera ownership is explicit so a QR scanner cannot run beside production capture.
public actor PairingCameraOwnership {
    public enum Owner: Sendable, Equatable { case idle, capture, pairingScanner }
    private var owner: Owner = .idle
    public init() {}
    public func beginCapture() -> Bool { guard owner == .idle else { return false }; owner = .capture; return true }
    public func endCapture() { if owner == .capture { owner = .idle } }
    public func beginPairingScan() -> Bool { guard owner == .idle else { return false }; owner = .pairingScanner; return true }
    public func endPairingScan() { if owner == .pairingScanner { owner = .idle } }
    public func currentOwner() -> Owner { owner }
}
