import Foundation
import SwiftUI
import UniformTypeIdentifiers
#if canImport(RealityKit) && canImport(ARKit) && !targetEnvironment(simulator)
import ARKit
import RealityKit
#endif

/// PL-0430 prototype: AR preview of an edited Design Model on iPhone.
///
/// The Windows Studio core writes a digest-bound `packlab.ar-preview-mesh.v1` JSON document
/// (`packlab_core.ar_preview`). This file validates it and, on a device, places the mesh on a
/// detected horizontal plane. The preview is a visual reference only: it carries no Scan
/// Master, measurement or mould authority, and on-device scale/tracking accuracy is not
/// validated. The feature is off unless `PackLabARPreviewEnabled` is set in user defaults.
public enum ARPreviewPackageError: Error, Sendable, Equatable {
    case tooLarge, malformed, unsupportedContract, digestMismatch, authorityInvalid, geometryInvalid
}

public struct ARPreviewPackage: Sendable, Equatable {
    public static let contract = "packlab.ar-preview-mesh.v1"
    public static let maximumBytes = 8 * 1024 * 1024
    public static let maximumVertices = 65_535
    public static let maximumTriangles = 131_072
    static let allowedScaleBases: Set<String> = [
        "MM_UNVERIFIED_TO_METRES_DISPLAY_ONLY", "RELATIVE_NORMALIZED_TO_0_1_M_DISPLAY_ONLY",
    ]

    public let designModelRevisionID: String
    public let displayScaleBasis: String
    public let positions: [SIMD3<Float>]
    public let indices: [UInt32]
    public let contentSHA256: String

    public var authorityBanner: String {
        "AR VISUAL REFERENCE ONLY · not measured · no mould authority · \(displayScaleBasis)"
    }

    /// Parse and validate; any failure rejects the whole document (fail closed).
    public static func parse(_ data: Data) throws -> ARPreviewPackage {
        guard !data.isEmpty, data.count <= maximumBytes else { throw ARPreviewPackageError.tooLarge }
        let digest = try verifiedDigest(data)
        guard let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw ARPreviewPackageError.malformed
        }
        guard root["contract"] as? String == contract else { throw ARPreviewPackageError.unsupportedContract }
        guard
            let authority = root["authority"] as? [String: Any],
            authority["class"] as? String == "AR_VISUAL_REFERENCE_ONLY",
            authority["mold_use_authorized"] as? Bool == false,
            authority["scan_master_replaced"] as? Bool == false,
            authority["on_device_scale_verified"] as? Bool == false,
            authority["physical_accuracy_validation_status"] as? String == "DEFERRED_OWNER_VALIDATION"
        else { throw ARPreviewPackageError.authorityInvalid }
        guard
            let source = root["source"] as? [String: Any],
            let revision = source["design_model_revision_id"] as? String, !revision.isEmpty,
            let basis = root["display_scale_basis"] as? String, allowedScaleBases.contains(basis),
            root["frame"] as? String == "REALITYKIT_Y_UP_METRES_ORIGIN_BASE_CENTRE",
            let rawPositions = root["positions"] as? [Double],
            let rawIndices = root["indices"] as? [Int]
        else { throw ARPreviewPackageError.malformed }
        let vertexCount = rawPositions.count / 3
        guard
            rawPositions.count % 3 == 0, (3...maximumVertices).contains(vertexCount),
            rawPositions.allSatisfy({ $0.isFinite && abs($0) <= 10.0 }),
            rawIndices.count % 3 == 0, (1...maximumTriangles).contains(rawIndices.count / 3),
            rawIndices.allSatisfy({ (0..<vertexCount).contains($0) })
        else { throw ARPreviewPackageError.geometryInvalid }
        for start in stride(from: 0, to: rawIndices.count, by: 3) {
            let triangle = Set(rawIndices[start..<(start + 3)])
            guard triangle.count == 3 else { throw ARPreviewPackageError.geometryInvalid }
        }
        let points = stride(from: 0, to: rawPositions.count, by: 3).map {
            SIMD3<Float>(Float(rawPositions[$0]), Float(rawPositions[$0 + 1]), Float(rawPositions[$0 + 2]))
        }
        return ARPreviewPackage(
            designModelRevisionID: revision,
            displayScaleBasis: basis,
            positions: points,
            indices: rawIndices.map { UInt32($0) },
            contentSHA256: digest
        )
    }

    /// The writer emits canonical JSON (sorted keys, no spaces) with `content_sha256` as the
    /// second key; removing that member yields exactly the canonical body that was hashed.
    static func verifiedDigest(_ data: Data) throws -> String {
        let prefix = Data(#""content_sha256":""#.utf8)
        guard let start = data.range(of: prefix) else { throw ARPreviewPackageError.digestMismatch }
        let hexStart = start.upperBound
        let hexEnd = hexStart + 64
        guard hexEnd + 2 <= data.endIndex, data[hexEnd] == UInt8(ascii: "\""), data[hexEnd + 1] == UInt8(ascii: ",") else {
            throw ARPreviewPackageError.digestMismatch
        }
        guard let claimed = String(data: data[hexStart..<hexEnd], encoding: .ascii),
              claimed.allSatisfy({ $0.isHexDigit && !$0.isUppercase }) else {
            throw ARPreviewPackageError.digestMismatch
        }
        var body = Data(data[data.startIndex..<start.lowerBound])
        body.append(data[(hexEnd + 2)..<data.endIndex])
        guard SourceIntegrity.digest(body) == claimed else { throw ARPreviewPackageError.digestMismatch }
        return claimed
    }
}

public enum ARPreviewFeatureFlag {
    public static let defaultsKey = "PackLabARPreviewEnabled"
    public static func isEnabled(_ defaults: UserDefaults = .standard) -> Bool { defaults.bool(forKey: defaultsKey) }
}

/// Picks a `.json` AR preview package via the Files app and shows it; device-only AR.
struct ARPreviewEntryView: View {
    @State private var importing = false
    @State private var package: ARPreviewPackage?
    @State private var message = "Choose a PackLab AR preview package (.json) exported from Windows Studio."

    var body: some View {
        VStack(spacing: 12) {
            if let package {
                Text(package.authorityBanner).font(.caption).multilineTextAlignment(.center)
                    .padding(8).background(.orange.opacity(0.85), in: RoundedRectangle(cornerRadius: 8))
                #if canImport(RealityKit) && canImport(ARKit) && !targetEnvironment(simulator)
                ARPreviewRealityView(package: package).ignoresSafeArea(edges: .bottom)
                #else
                Text("AR preview needs an iPhone with ARKit; validated package \(package.contentSHA256.prefix(12))…")
                    .foregroundStyle(.secondary)
                #endif
            } else {
                Text(message).multilineTextAlignment(.center).foregroundStyle(.secondary).padding()
            }
            Button("Open package") { importing = true }
        }
        .navigationTitle("AR Preview")
        .fileImporter(isPresented: $importing, allowedContentTypes: [.json]) { result in
            do {
                let url = try result.get()
                let scoped = url.startAccessingSecurityScopedResource()
                defer { if scoped { url.stopAccessingSecurityScopedResource() } }
                let size = try url.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? Int.max
                guard size <= ARPreviewPackage.maximumBytes else { throw ARPreviewPackageError.tooLarge }
                package = try ARPreviewPackage.parse(Data(contentsOf: url))
            } catch {
                package = nil
                message = "Package rejected (\(error)). Nothing is shown for an invalid or altered package."
            }
        }
    }
}

#if canImport(RealityKit) && canImport(ARKit) && !targetEnvironment(simulator)
struct ARPreviewRealityView: UIViewRepresentable {
    let package: ARPreviewPackage

    func makeUIView(context: Context) -> ARView {
        // Reuse the app's single shared ARSession instead of running a second one, which
        // would compete for the camera and inject resets into a scan (review P2-3). The
        // shared owner keeps its delegate, configuration and lifecycle.
        let view = ARView(frame: .zero, cameraMode: .ar, automaticallyConfigureSession: false)
        let owner = SharedARSessionOwner.shared
        view.session = owner.session
        owner.start()
        var descriptor = MeshDescriptor(name: "packlab-ar-preview")
        descriptor.positions = MeshBuffers.Positions(package.positions)
        descriptor.primitives = .triangles(package.indices)
        if let mesh = try? MeshResource.generate(from: [descriptor]) {
            let material = SimpleMaterial(color: .systemOrange.withAlphaComponent(0.8), isMetallic: false)
            let entity = ModelEntity(mesh: mesh, materials: [material])
            // No plane detection on the shared session: place the model 0.6 m ahead of and
            // 0.25 m below the current camera, in world space (visual reference only).
            var position = SIMD3<Float>(0, -0.25, -0.6)
            if let camera = owner.session.currentFrame?.camera.transform {
                let ahead = camera * SIMD4<Float>(0, -0.25, -0.6, 1)
                position = SIMD3<Float>(ahead.x, ahead.y, ahead.z)
            }
            let anchor = AnchorEntity(world: position)
            anchor.addChild(entity)
            view.scene.addAnchor(anchor)
        }
        return view
    }

    func updateUIView(_ uiView: ARView, context: Context) {}
}
#endif
