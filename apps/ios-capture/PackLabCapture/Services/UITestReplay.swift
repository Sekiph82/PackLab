import Foundation
import CoreGraphics
import ImageIO
#if canImport(CoreVideo)
import CoreVideo
#endif
#if canImport(SwiftUI)
import SwiftUI
#endif

/// PL-0451 UI-test replay camera. Compiled into every configuration but inert unless the
/// app runs in the Simulator AND was launched with `-PackLabUITestReplay` (XCUITest sets
/// it; an installed app cannot be launched with arguments by a user). It replaces only the
/// ARKit camera: synthetic frames of a procedurally rendered package (no photos, no owner
/// data) with matching camera poses orbiting the package, and a base-plane raycast for Set
/// object center. Quality analysis, guidance, capture gates, persistence, finalize,
/// packaging and transfer all run the production code paths. The frames are synthetic and
/// say nothing about real image quality, ARKit tracking, lens behaviour or device thermals.
@MainActor
public final class UITestReplaySource: ObservableObject, ARTrackingService, TimestampedStillPhotoBackend {
    public static let launchArgument = "-PackLabUITestReplay"
    public static let resetArgument = "-PackLabUITestReset"
    /// Horizontal camera distance from the object center while orbiting.
    static let orbitRadius = 0.45
    public let worldIdentity = "uitest-replay-world"
    @Published public private(set) var preview: CGImage?
    public private(set) var poseBuffer = PoseBuffer()
    static let startPosition: [Double] = [0, 0.35, 0]
    private var cameraPosition: [Double] = UITestReplaySource.startPosition
    private var lookAt: [Double] = ReplayScene.base
    private var lastStillTimestamp: TimeInterval?

    public static func makeIfRequested(arguments: [String] = ProcessInfo.processInfo.arguments) -> UITestReplaySource? {
        #if targetEnvironment(simulator)
        guard arguments.contains(launchArgument) else { return nil }
        if arguments.contains(resetArgument) { resetAppData() }
        return UITestReplaySource()
        #else
        return nil
        #endif
    }

    /// Fresh install state for a UI test run: sessions, exports, sync queue and pairing.
    private static func resetAppData() {
        let fileManager = FileManager.default
        for directory in [FileManager.SearchPathDirectory.applicationSupportDirectory, .documentDirectory] {
            guard let root = fileManager.urls(for: directory, in: .userDomainMask).first, let contents = try? fileManager.contentsOfDirectory(at: root, includingPropertiesForKeys: nil) else { continue }
            for url in contents { try? fileManager.removeItem(at: url) }
        }
        DeviceCredentialStore.remove()        ReceiverReconnectIdentityStore().remove()
        SenderTransferIdentityStore().remove()
    }

    /// Row-major camera-to-world matrix looking from `cameraPosition` at `lookAt` (camera -Z).
    var transform: [Double] {
        let p = cameraPosition
        let forward = Self.normalized([lookAt[0] - p[0], lookAt[1] - p[1], lookAt[2] - p[2]])
        let z = forward.map { -$0 }
        let x = Self.normalized(Self.cross([0, 1, 0], z))
        let y = Self.cross(z, x)
        return [x[0], y[0], z[0], p[0], x[1], y[1], z[1], p[1], x[2], y[2], z[2], p[2], 0, 0, 0, 1]
    }

    /// The harness acts as the operator: it walks to the wedge the app's guidance targets
    /// (middle of the wedge and of its elevation ring) and looks at the object center.
    /// Without an object center it returns to the start pose, aiming the crosshair at the
    /// package base (what an operator does before Set object center).
    public func move(to target: CoverageSector?, center: [Double]?, configuration: OrbitCoverageConfiguration) {
        guard let center, center.count == 3 else {
            cameraPosition = Self.startPosition
            lookAt = ReplayScene.base
            renderPreview()
            return
        }
        guard let target, let ring = configuration.rings.first(where: { $0.id == target.ringID }) else { return }
        let azimuth = OrbitGuidance.wedgeCenter(azimuthIndex: target.azimuthIndex, configuration: configuration) * Double.pi / 180
        let elevation = (ring.minimumElevation + ring.maximumElevation) / 2 * Double.pi / 180
        let radius = Self.orbitRadius
        cameraPosition = [center[0] + radius * sin(azimuth), center[1] + radius * tan(elevation), center[2] - radius * cos(azimuth)]
        lookAt = center
        renderPreview()
    }

    /// Shows the current synthetic view even before a scan's live loop runs.
    func renderPreview() {
        preview = ReplayRenderer.render(camera: transform, width: 240, height: 180).cgImage()
    }

    private func recordPose(at timestamp: TimeInterval) -> PoseSample {
        let pose = PoseSample(timestamp: timestamp, transform: transform, tracking: .normal)
        poseBuffer.append(pose)
        return pose
    }

    // MARK: ARTrackingService

    public func start() async {}
    public func stop() async {}
    public func state() async -> ARTrackingServiceState { .tracking }
    public func snapshot() async -> TrackingSnapshot { TrackingSnapshot(quality: .normal, poseEvidenceEligible: true, message: "Tracking ready (UI-test replay)") }
    public func latestPose() async -> PoseSample? { recordPose(at: ProcessInfo.processInfo.systemUptime) }
    public func localizationEpoch() async -> Int { 0 }
    public func resetDiagnostics() async -> [ResetDiagnosticEvent] { [] }

    // MARK: Camera frames

    /// Live candidate frame through the production luma sampler, bound to a pose at the
    /// same timestamp (as the ARFrame path does).
    func liveFrame() -> (frame: QualityImageFrame, timestamp: TimeInterval)? {
        let render = ReplayRenderer.render(camera: transform, width: 240, height: 180)
        preview = render.cgImage()
        let timestamp = ProcessInfo.processInfo.systemUptime
        _ = recordPose(at: timestamp)
        #if canImport(CoreVideo)
        guard let buffer = render.lumaPixelBuffer() else { return nil }
        return (LiveQualityFrameSampler.qualityFrame(from: buffer), timestamp)
        #else
        return nil
        #endif
    }

    public func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) {
        let render = ReplayRenderer.render(camera: transform, width: 640, height: 480)
        guard let image = render.cgImage(), let jpeg = ReplayRenderer.jpeg(image) else { throw CameraServiceError.failed("replay_render_failed") }
        let timestamp = ProcessInfo.processInfo.systemUptime
        _ = recordPose(at: timestamp)
        lastStillTimestamp = timestamp
        return (jpeg, CaptureDimensions(width: render.width, height: render.height))
    }

    public func lastCaptureMonotonicTimestamp() async -> TimeInterval? { lastStillTimestamp }

    /// Crosshair (image centre) ray onto the table plane y = 0.
    func raycastBasePlane() -> BasePlaneHit? {
        let m = transform
        let direction = [-m[2], -m[6], -m[10]]
        guard direction[1] < -1e-6 else { return nil }
        let distance = -cameraPosition[1] / direction[1]
        let hit = [cameraPosition[0] + distance * direction[0], 0, cameraPosition[2] + distance * direction[2]]
        return BasePlaneHit(position: hit, normal: [0, 1, 0], cameraPosition: cameraPosition, method: "uitest_replay_raycast", worldIdentity: worldIdentity)
    }

    private static func normalized(_ v: [Double]) -> [Double] {
        let length = (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]).squareRoot()
        return length > 1e-12 ? v.map { $0 / length } : v
    }

    private static func cross(_ a: [Double], _ b: [Double]) -> [Double] {
        [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
    }
}

/// One synthetic RGB frame (8-bit) and its luma.
struct ReplayRender {
    let width: Int
    let height: Int
    var rgb: [UInt8]
    var luma: [UInt8]

    func cgImage() -> CGImage? {
        guard let provider = CGDataProvider(data: Data(rgb) as CFData) else { return nil }
        return CGImage(width: width, height: height, bitsPerComponent: 8, bitsPerPixel: 24, bytesPerRow: width * 3, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.none.rawValue), provider: provider, decode: nil, shouldInterpolate: true, intent: .defaultIntent)
    }

    #if canImport(CoreVideo)
    /// Bi-planar 4:2:0 full-range buffer (the ARFrame.capturedImage format) with this luma.
    func lumaPixelBuffer() -> CVPixelBuffer? {
        var created: CVPixelBuffer?
        guard CVPixelBufferCreate(kCFAllocatorDefault, width, height, kCVPixelFormatType_420YpCbCr8BiPlanarFullRange, nil, &created) == kCVReturnSuccess, let buffer = created,
              CVPixelBufferLockBaseAddress(buffer, []) == kCVReturnSuccess else { return nil }
        defer { CVPixelBufferUnlockBaseAddress(buffer, []) }
        guard let lumaBase = CVPixelBufferGetBaseAddressOfPlane(buffer, 0), let chromaBase = CVPixelBufferGetBaseAddressOfPlane(buffer, 1) else { return nil }
        let rowBytes = CVPixelBufferGetBytesPerRowOfPlane(buffer, 0)
        let pixels = lumaBase.assumingMemoryBound(to: UInt8.self)
        for y in 0..<height { for x in 0..<width { pixels[y * rowBytes + x] = luma[y * width + x] } }
        memset(chromaBase, 128, CVPixelBufferGetBytesPerRowOfPlane(buffer, 1) * CVPixelBufferGetHeightOfPlane(buffer, 1))
        return buffer
    }
    #endif
}

/// Tiny deterministic ray tracer: a matte cylindrical bottle (radius 3.5 cm, height 20 cm,
/// striped label) on a 3 cm checker table mat, lit by one directional light. Pinhole camera
/// with fx = fy = 0.8 x width (about 64 deg horizontal field of view).
enum ReplayRenderer {
    static func render(camera m: [Double], width: Int, height: Int) -> ReplayRender {
        let bx = ReplayScene.base[0], bz = ReplayScene.base[2], radius = ReplayScene.radius, top = ReplayScene.height
        let focal = Double(width) * 0.8, cx = Double(width) / 2, cy = Double(height) / 2
        let px0 = m[3], py0 = m[7], pz0 = m[11]
        let lightNorm = (0.4 * 0.4 + 0.8 * 0.8 + 0.3 * 0.3).squareRoot()
        let lx = 0.4 / lightNorm, ly = 0.8 / lightNorm, lz = 0.3 / lightNorm
        let ox = px0 - bx, oz = pz0 - bz
        var rgb = [UInt8](repeating: 0, count: width * height * 3)
        var luma = [UInt8](repeating: 0, count: width * height)
        for v in 0..<height {
            for u in 0..<width {
                let sx = (Double(u) + 0.5 - cx) / focal, sy = -(Double(v) + 0.5 - cy) / focal
                let dx = m[0] * sx + m[1] * sy - m[2], dy = m[4] * sx + m[5] * sy - m[6], dz = m[8] * sx + m[9] * sy - m[10]
                let up = dy / (dx * dx + dy * dy + dz * dz).squareRoot()
                // Background wall: soft vertical gradient.
                var r = 0.62 + 0.18 * up, g = 0.60 + 0.18 * up, b = 0.56 + 0.18 * up
                var nearest = Double.infinity
                // Bottle body.
                let qa = dx * dx + dz * dz
                if qa > 1e-12 {
                    let qb = 2 * (ox * dx + oz * dz), qc = ox * ox + oz * oz - radius * radius
                    let discriminant = qb * qb - 4 * qa * qc
                    if discriminant >= 0 {
                        let t = (-qb - discriminant.squareRoot()) / (2 * qa)
                        let y = py0 + t * dy
                        if t > 1e-4, y >= 0, y <= top {
                            nearest = t
                            let nx = (ox + t * dx) / radius, nz = (oz + t * dz) / radius
                            let shade = 0.35 + 0.65 * max(0, nx * lx + nz * lz)
                            if y > 0.06 && y < 0.15 {
                                let stripe = Int(((atan2(nx, -nz) + Double.pi) / (2 * Double.pi) * 16).rounded(.down)) % 2 == 0
                                (r, g, b) = stripe ? (0.85 * shade, 0.55 * shade, 0.20 * shade) : (0.25 * shade, 0.30 * shade, 0.55 * shade)
                            } else {
                                (r, g, b) = (0.80 * shade, 0.82 * shade, 0.85 * shade)
                            }
                        }
                    }
                }
                if dy < 0 {
                    // Bottle top.
                    let tTop = (top - py0) / dy
                    let hx = ox + tTop * dx, hz = oz + tTop * dz
                    if tTop > 1e-4, tTop < nearest, hx * hx + hz * hz <= radius * radius {
                        nearest = tTop
                        let shade = 0.35 + 0.65 * ly
                        (r, g, b) = (0.72 * shade, 0.74 * shade, 0.78 * shade)
                    }
                    // Table mat (3 cm checker) and floor beyond it.
                    let tTable = -py0 / dy
                    if tTable > 1e-4, tTable < nearest {
                        let wx = px0 + tTable * dx, wz = pz0 + tTable * dz
                        let onMat = abs(wx - bx) < 0.6 && abs(wz - bz) < 0.6
                        let checker = (Int((wx / 0.03).rounded(.down)) + Int((wz / 0.03).rounded(.down))) & 1 == 0
                        let value = (onMat ? (checker ? 0.66 : 0.40) : 0.22) * (0.35 + 0.65 * ly)
                        (r, g, b) = (value, value, value * 0.96)
                    }
                }
                r = min(0.94, max(0.04, r)); g = min(0.94, max(0.04, g)); b = min(0.94, max(0.04, b))
                let index = v * width + u
                rgb[index * 3] = UInt8((r * 255).rounded())
                rgb[index * 3 + 1] = UInt8((g * 255).rounded())
                rgb[index * 3 + 2] = UInt8((b * 255).rounded())
                luma[index] = UInt8(((0.299 * r + 0.587 * g + 0.114 * b) * 255).rounded())
            }
        }
        return ReplayRender(width: width, height: height, rgb: rgb, luma: luma)
    }

    static func jpeg(_ image: CGImage) -> Data? {
        let data = NSMutableData()
        guard let destination = CGImageDestinationCreateWithData(data as CFMutableData, "public.jpeg" as CFString, 1, nil) else { return nil }
        CGImageDestinationAddImage(destination, image, [kCGImageDestinationLossyCompressionQuality: 0.85] as CFDictionary)
        return CGImageDestinationFinalize(destination) ? data as Data : nil
    }
}

/// The synthetic package stands on a table (y = 0) at `base` in the AR world.
enum ReplayScene {
    static let base: [Double] = [0, 0, -0.5]
    static let radius = 0.035
    static let height = 0.20
}

#if canImport(SwiftUI)
/// Full-screen view of the latest synthetic frame, clearly labelled as such.
struct ReplayCameraPreview: View {
    @ObservedObject var source: UITestReplaySource
    var body: some View {
        // Overlays never change the layout size, so a filled image cannot widen the screen.
        Color.black
            .overlay { if let image = source.preview { Image(decorative: image, scale: 1).resizable().scaledToFill() } }
            .overlay(alignment: .bottomLeading) {
                Text("UI-test replay camera: synthetic rendered package").font(.caption2.bold()).foregroundStyle(.yellow)
                    .padding(4).background(.black.opacity(0.6)).padding(.bottom, 24)
            }
            .clipped()
    }
}
#endif
