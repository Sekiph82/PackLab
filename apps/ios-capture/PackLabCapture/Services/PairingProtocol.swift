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

public protocol ProductionCameraLifecycle: Sendable {
    func stopAndReleaseForPairing() async -> Bool
    func restoreAfterPairing() async
}

/// MainActor-owned bridge to the real capture session.  QR ownership is not
/// granted until the production camera has actually stopped and released its
/// AVCapture/NextLevel session.
@MainActor
public final class ProductionCaptureCameraLifecycle: @unchecked Sendable, ProductionCameraLifecycle {
    public static let shared = ProductionCaptureCameraLifecycle()
    private var stopHandler: (() -> Bool)?
    private var restoreHandler: (() -> Void)?
    private init() {}
    public func install(stop: @escaping () -> Bool, restore: @escaping () -> Void) { stopHandler = stop; restoreHandler = restore }
    public func clear() { stopHandler = nil; restoreHandler = nil }
    public nonisolated func stopAndReleaseForPairing() async -> Bool { await MainActor.run { stopHandler?() ?? false } }
    public nonisolated func restoreAfterPairing() async { await MainActor.run { restoreHandler?() } }
}

public struct PairingCodeEntry: Sendable, Equatable {
    public let receiverInstanceID: String
    public let pairingCode: String
    public init(receiverInstanceID: String, pairingCode: String) { self.receiverInstanceID = receiverInstanceID; self.pairingCode = pairingCode.replacingOccurrences(of: "-", with: "").uppercased() }
}

public struct ReceiverReconnectIdentity: Codable, Sendable, Equatable {
    public let receiverInstanceID: String
    public let host: String
    public let port: Int
    public let tlsCertificateFingerprint: String
    public init(receiverInstanceID: String, host: String, port: Int, tlsCertificateFingerprint: String) {
        self.receiverInstanceID = receiverInstanceID; self.host = host; self.port = port; self.tlsCertificateFingerprint = tlsCertificateFingerprint
    }
}

public final class ReceiverReconnectIdentityStore: @unchecked Sendable {
    private let defaults: UserDefaults
    private let key = "packlab.receiver.reconnect.identity.v1"
    public init(defaults: UserDefaults = .standard) { self.defaults = defaults }
    public func save(_ identity: ReceiverReconnectIdentity) throws { defaults.set(try JSONEncoder().encode(identity), forKey: key) }
    public func load() -> ReceiverReconnectIdentity? {
        guard let data = defaults.data(forKey: key) else { return nil }
        return try? JSONDecoder().decode(ReceiverReconnectIdentity.self, from: data)
    }
    public func remove() { defaults.removeObject(forKey: key) }
}

public enum PairingCoordinatorState: Sendable, Equatable { case idle, scanning, awaitingCode, paired(ReceiverReconnectIdentity), failed(String) }

@MainActor
public final class PairingCoordinator: ObservableObject {
    @Published public private(set) var state: PairingCoordinatorState = .idle
    public let cameraOwnership: PairingCameraOwnership
    private let identityStore: ReceiverReconnectIdentityStore
    private let now: @Sendable () -> Date
    public private(set) var pairedOffer: PairingOffer?
    public init(cameraOwnership: PairingCameraOwnership = PairingCameraOwnership(lifecycle: ProductionCaptureCameraLifecycle.shared), identityStore: ReceiverReconnectIdentityStore = ReceiverReconnectIdentityStore(), now: @escaping @Sendable () -> Date = Date.init) { self.cameraOwnership = cameraOwnership; self.identityStore = identityStore; self.now = now }
    public func beginManualEntry() { state = .awaitingCode }
    public func beginQRScan() async -> Bool { let acquired = await cameraOwnership.beginPairingScan(); if acquired { state = .scanning }; return acquired }
    public func finishQRScan() async { await cameraOwnership.endPairingScan(); if case .scanning = state { state = .idle } }
    public func accept(offer: PairingOffer, receiverInstanceID: String, manualCode: String? = nil) throws -> ReceiverReconnectIdentity {
        guard offer.receiverInstanceID == receiverInstanceID else { throw PairingProtocolError.wrongReceiver }
        guard offer.expiresAt > now().timeIntervalSince1970 else { throw PairingProtocolError.expired }
        guard let manualCode, manualCode.replacingOccurrences(of: "-", with: "").uppercased() == offer.pairingCode else { throw PairingProtocolError.malformed }
        let identity = ReceiverReconnectIdentity(receiverInstanceID: offer.receiverInstanceID, host: offer.host, port: offer.port, tlsCertificateFingerprint: offer.tlsCertificateFingerprint)
        try identityStore.save(identity); pairedOffer = offer; state = .paired(identity); return identity
    }
    public func acceptQRPayload(_ data: Data, receiverInstanceID: String) throws -> ReceiverReconnectIdentity {
        let offer = try PairingOffer(data: data)
        return try accept(offer: offer, receiverInstanceID: receiverInstanceID, manualCode: offer.pairingCode)
    }
    public func acceptManual(host: String, port: Int, receiverInstanceID: String, pairingID: String, fingerprint: String, code: String, expiresAt: Date) throws -> ReceiverReconnectIdentity {
        let offer = PairingOffer(protocolName: PackLabTransferProtocol.name, protocolVersion: PackLabTransferProtocol.version, receiverInstanceID: receiverInstanceID, host: host.trimmingCharacters(in: .whitespacesAndNewlines), port: port, pairingID: pairingID.trimmingCharacters(in: .whitespacesAndNewlines), pairingCode: code, expiresAt: expiresAt.timeIntervalSince1970, tlsCertificateFingerprint: fingerprint.trimmingCharacters(in: .whitespacesAndNewlines).lowercased())
        return try accept(offer: offer, receiverInstanceID: receiverInstanceID, manualCode: code)
    }
    public func restoredIdentity() -> ReceiverReconnectIdentity? { identityStore.load() }
    public func fail(_ message: String) { state = .failed(message) }
}

#if canImport(SwiftUI)
import SwiftUI
public struct PairingView: View {
    @StateObject private var coordinator: PairingCoordinator
    @State private var code = ""
    @State private var host = ""
    @State private var port = "8443"
    @State private var receiverID = ""
    @State private var pairingID = ""
    @State private var fingerprint = ""
    @State private var expiresAt = Date().addingTimeInterval(120)
    @State private var showScanner = false
    public let offer: PairingOffer?
    public init(offer: PairingOffer? = nil, coordinator: PairingCoordinator = PairingCoordinator()) { self.offer = offer; _coordinator = StateObject(wrappedValue: coordinator) }
    public var body: some View {
        Form {
            Section("Pair PackLab receiver") {
                TextField("Receiver host", text: $host).textInputAutocapitalization(.never)
                TextField("Receiver port", text: $port).keyboardType(.numberPad)
                TextField("Receiver instance ID", text: $receiverID).textInputAutocapitalization(.never)
                TextField("Pairing ID", text: $pairingID).textInputAutocapitalization(.never)
                TextField("TLS fingerprint", text: $fingerprint).textInputAutocapitalization(.never)
                TextField("Pairing code", text: $code).textInputAutocapitalization(.characters)
                Button("Pair manually") {
                    do {
                        if let offer { _ = try coordinator.accept(offer: offer, receiverInstanceID: offer.receiverInstanceID, manualCode: code) }
                        else { _ = try coordinator.acceptManual(host: host, port: Int(port) ?? 0, receiverInstanceID: receiverID, pairingID: pairingID, fingerprint: fingerprint, code: code, expiresAt: expiresAt) }
                    } catch { coordinator.fail("Pairing failed") }
                }
                Button("Scan QR offer") {
                    Task { if await coordinator.beginQRScan() { showScanner = true } else { coordinator.fail("Production camera is still in use") } }
                }
                if case .paired(let identity) = coordinator.state { Text("Paired with \(identity.receiverInstanceID)") }
                if case .failed(let message) = coordinator.state { Text(message).foregroundStyle(.red) }
            }
        }.navigationTitle("Pair receiver")
            #if canImport(AVFoundation) && canImport(UIKit)
            .sheet(isPresented: $showScanner, onDismiss: { Task { await coordinator.finishQRScan() } }) {
                PairingQRScannerView { payload in
                    guard let offer = try? PairingOffer(data: payload) else { return }
                    do { _ = try coordinator.accept(offer: offer, receiverInstanceID: offer.receiverInstanceID, manualCode: offer.pairingCode); showScanner = false } catch { coordinator.fail("Invalid QR offer") }
                }
            }
            #endif
    }
}
#endif

#if canImport(AVFoundation) && canImport(UIKit) && canImport(SwiftUI)
import AVFoundation
import UIKit

public struct PairingQRScannerView: UIViewControllerRepresentable {
    public let onPayload: @Sendable (Data) -> Void
    public init(onPayload: @escaping @Sendable (Data) -> Void) { self.onPayload = onPayload }
    public func makeUIViewController(context: Context) -> PairingQRScannerController { PairingQRScannerController(onPayload: onPayload) }
    public func updateUIViewController(_ controller: PairingQRScannerController, context: Context) {}
}

public final class PairingQRScannerController: UIViewController, AVCaptureMetadataOutputObjectsDelegate {
    private let onPayload: @Sendable (Data) -> Void
    private let session = AVCaptureSession()
    public init(onPayload: @escaping @Sendable (Data) -> Void) { self.onPayload = onPayload; super.init(nibName: nil, bundle: nil) }
    required init?(coder: NSCoder) { return nil }
    public override func viewDidLoad() {
        super.viewDidLoad(); view.backgroundColor = .black
        guard let device = AVCaptureDevice.default(for: .video), let input = try? AVCaptureDeviceInput(device: device), session.canAddInput(input) else { return }
        session.addInput(input)
        let output = AVCaptureMetadataOutput(); guard session.canAddOutput(output) else { return }; session.addOutput(output); output.setMetadataObjectsDelegate(self, queue: .main); output.metadataObjectTypes = [.qr]
        let preview = AVCaptureVideoPreviewLayer(session: session); preview.videoGravity = .resizeAspectFill; preview.frame = view.bounds; view.layer.addSublayer(preview)
        session.startRunning()
    }
    public func metadataOutput(_ output: AVCaptureMetadataOutput, didOutput metadataObjects: [AVMetadataObject], from connection: AVCaptureConnection) {
        guard let value = (metadataObjects.first as? AVMetadataMachineReadableCodeObject)?.stringValue, let data = value.data(using: .utf8) else { return }
        onPayload(data); session.stopRunning()
    }
}
#endif

/// Camera ownership is explicit so a QR scanner cannot run beside production capture.
public actor PairingCameraOwnership {
    public enum Owner: Sendable, Equatable { case idle, capture, pairingScanner }
    private var owner: Owner = .idle
    private let lifecycle: any ProductionCameraLifecycle
    @MainActor public init(lifecycle: any ProductionCameraLifecycle = ProductionCaptureCameraLifecycle.shared) { self.lifecycle = lifecycle }
    public func beginCapture() -> Bool { guard owner == .idle else { return false }; owner = .capture; return true }
    public func endCapture() { if owner == .capture { owner = .idle } }
    public func beginPairingScan() async -> Bool { guard owner == .idle, await lifecycle.stopAndReleaseForPairing() else { return false }; owner = .pairingScanner; return true }
    public func endPairingScan() async { if owner == .pairingScanner { owner = .idle; await lifecycle.restoreAfterPairing() } }
    public func currentOwner() -> Owner { owner }
}
