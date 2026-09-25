import Foundation

public struct TransferRequest: Sendable, Equatable {
    public let source: URL
    public let receiver: ReceiverReconnectIdentity
    public let pairingOffer: PairingOffer?
    public let pairingCode: String?
    public let transferID: String?
    public let finalization: SessionFinalizationRecord?
    public init(source: URL, receiver: ReceiverReconnectIdentity, pairingOffer: PairingOffer? = nil, pairingCode: String? = nil, transferID: String? = nil, finalization: SessionFinalizationRecord? = nil) { self.source = source; self.receiver = receiver; self.pairingOffer = pairingOffer; self.pairingCode = pairingCode; self.transferID = transferID; self.finalization = finalization }
}

public enum TransferResult: Sendable, Equatable { case transferred, unavailable, failed(String) }

public protocol TransferService: Sendable {
    func transfer(_ request: TransferRequest) async -> TransferResult
    func cancel() async
}

public protocol ProductionTransferClient: Sendable {
    func transfer(_ request: TransferRequest, progress: @escaping @Sendable (TransferStatusMessage) -> Void) async throws -> TransferCompletionAcknowledgement
    func cancel(transferID: String) async throws
    func status(transferID: String) async throws -> TransferStatusMessage
}

public enum URLSessionTransferError: Error, Sendable, Equatable { case invalidSource, invalidResponse, server(String), notVerified, cancelled }

public final class URLSessionTransferClient: NSObject, ProductionTransferClient, @unchecked Sendable {
    private let identity: ReceiverReconnectIdentity
    private let session: URLSession
    private let sessionToken: String?
    private var activeToken: String?
    public init(identity: ReceiverReconnectIdentity, sessionToken: String? = nil, session: URLSession? = nil) {
        self.identity = identity; self.sessionToken = sessionToken; self.activeToken = sessionToken
        if let session { self.session = session }
        else {
            let configuration = URLSessionConfiguration.ephemeral
            #if canImport(Security)
            self.session = URLSession(configuration: configuration, delegate: PinnedReceiverSessionDelegate(expectedFingerprint: identity.tlsCertificateFingerprint), delegateQueue: nil)
            #else
            self.session = URLSession(configuration: configuration)
            #endif
        }
    }
    public func transfer(_ request: TransferRequest, progress: @escaping @Sendable (TransferStatusMessage) -> Void) async throws -> TransferCompletionAcknowledgement {
        guard let data = try? Data(contentsOf: request.source) else { throw URLSessionTransferError.invalidSource }
        let digest = SourceIntegrity.digest(data)
        let transferID = request.transferID ?? UUID().uuidString
        var token = sessionToken
        if let offer = request.pairingOffer, let code = request.pairingCode { token = try await pair(offer: offer, code: code); activeToken = token }
        let create = TransferCreateMessage(receiverID: request.receiver.receiverInstanceID, transferID: transferID, captureID: request.source.deletingPathExtension().lastPathComponent, packageName: request.source.lastPathComponent, totalBytes: data.count, packageSHA256: digest)
        _ = try await send(path: "/v1/transfers", method: "POST", body: try JSONEncoder().encode(create), token: token)
        var status = try await status(transferID: transferID, token: token); progress(status)
        while status.nextOffset < data.count {
            let offset = status.nextOffset; let end = min(data.count, offset + 256 * 1024); let chunk = data.subdata(in: offset..<end)
            let chunkMessage = TransferChunkMessage(transferID: transferID, offset: offset, length: chunk.count, chunkSHA256: SourceIntegrity.digest(chunk))
            _ = try await send(path: "/v1/transfers/\(transferID)/chunks", method: "POST", body: chunk, token: token, headers: ["X-PackLab-Offset": String(offset), "X-PackLab-Chunk-SHA256": chunkMessage.chunkSHA256])
            status = try await status(transferID: transferID, token: token); progress(status)
        }
        let response = try await send(path: "/v1/transfers/\(transferID)/complete", method: "POST", body: nil, token: token)
        let acknowledgement = try JSONDecoder().decode(TransferCompletionAcknowledgement.self, from: response)
        guard acknowledgement.authenticated, acknowledgement.verified, acknowledgement.packageSHA256 == digest else { throw URLSessionTransferError.notVerified }
        return acknowledgement
    }
    public func cancel(transferID: String) async throws { _ = try await send(path: "/v1/transfers/\(transferID)/cancel", method: "POST", body: nil, token: activeToken) }
    public func status(transferID: String) async throws -> TransferStatusMessage { try await status(transferID: transferID, token: activeToken) }
    private func status(transferID: String, token: String?) async throws -> TransferStatusMessage { let data = try await send(path: "/v1/transfers/\(transferID)", method: "GET", body: nil, token: token); return try JSONDecoder().decode(TransferStatusMessage.self, from: data) }
    private func pair(offer: PairingOffer, code: String) async throws -> String {
        let value: [String: Any] = ["offer": try JSONSerialization.jsonObject(with: offer.payloadData()), "pairing_code": code, "tls_certificate_fingerprint": offer.tlsCertificateFingerprint]
        let response = try await send(path: "/v1/pair", method: "POST", body: try JSONSerialization.data(withJSONObject: value), token: nil)
        guard let object = try JSONSerialization.jsonObject(with: response) as? [String: Any], let token = object["session_token"] as? String else { throw URLSessionTransferError.invalidResponse }
        return token
    }
    private func send(path: String, method: String, body: Data?, token: String?, headers: [String: String] = [:]) async throws -> Data {
        let url = URL(string: "https://\(identity.host):\(identity.port)\(path)")!
        var request = URLRequest(url: url); request.httpMethod = method; request.httpBody = body; request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token { request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }; headers.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        let (data, response) = try await session.data(for: request); guard let http = response as? HTTPURLResponse else { throw URLSessionTransferError.invalidResponse }
        guard (200..<300).contains(http.statusCode) else { let code = ((try? JSONSerialization.jsonObject(with: data)) as? [String: Any])?["error_code"] as? String ?? "server_error"; throw URLSessionTransferError.server(code) }
        return data
    }
}

public struct ProductionTransferService: TransferService {
    private let client: any ProductionTransferClient
    public init(client: any ProductionTransferClient) { self.client = client }
    public func transfer(_ request: TransferRequest) async -> TransferResult {
        do { _ = try await client.transfer(request, progress: { _ in }); return .transferred } catch is CancellationError { return .failed("cancelled") } catch { return .failed(String(describing: error)) }
    }
    public func cancel() async {}
}

/// Retained only as an explicit test/unsupported-platform implementation;
/// production composition uses `ProductionTransferService`.
public struct UnavailableTransferService: TransferService {
    public init() {}
    public func transfer(_ request: TransferRequest) async -> TransferResult { _ = request; return .unavailable }
    public func cancel() async {}
}
