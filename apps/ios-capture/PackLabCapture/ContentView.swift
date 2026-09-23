import SwiftUI

@MainActor
final class CaptureRuntimeViewModel: ObservableObject {
    @Published private(set) var tracking = TrackingSnapshot(quality: .unavailable, poseEvidenceEligible: false, message: "Tracking unavailable")
    @Published private(set) var epoch = 0
    @Published private(set) var pose: PoseSample?
    @Published private(set) var motion: MotionSampleRecord?
    @Published private(set) var health: DeviceHealthCaptureGate = .ready(DeviceHealthPolicy.evaluate(UnavailableDeviceHealthProvider().snapshot()))
    private let trackingService: any ARTrackingService
    private let healthMonitor: DeviceHealthMonitor

    init() {
        #if targetEnvironment(simulator)
        trackingService = SimulatorARTrackingService()
        healthMonitor = DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider())
        #elseif canImport(ARKit)
        trackingService = ARKitTrackingService()
        healthMonitor = DeviceHealthMonitor(provider: PhysicalDeviceHealthProvider())
        #else
        trackingService = FoundationARTrackingService(isAvailable: false)
        healthMonitor = DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider())
        #endif
    }

    func start() async {
        await trackingService.start()
        tracking = await trackingService.snapshot()
        pose = await trackingService.latestPose()
        health = await healthMonitor.preflight()
    }

    var overlay: PoseOverlayModel { PoseOverlayModel.make(visible: true, tracking: tracking, epoch: epoch, pose: pose, motion: motion) }
    var healthMessage: String? {
        switch health {
        case .ready: return nil
        case .warning(let decision), .hardStop(let decision): return decision.messages.joined(separator: " ")
        }
    }
}

struct ContentView: View {
    @State private var showPoseDebug = false
    @State private var showNewScan = false
    @State private var showResume = false
    @StateObject private var runtime = CaptureRuntimeViewModel()

    var body: some View {
        NavigationStack {
            ZStack {
                #if targetEnvironment(simulator)
                VStack(spacing: 12) {
                    Image(systemName: "camera.slash").font(.largeTitle)
                    Text("Camera unavailable in Simulator").font(.headline)
                    Text("No synthetic camera image is shown. Use an iPhone to preview a capture.")
                        .multilineTextAlignment(.center).foregroundStyle(.secondary)
                }.padding()
                #else
                NextLevelPreviewBridge().ignoresSafeArea()
                #endif

                VStack {
                    if let healthMessage = runtime.healthMessage {
                        Text(healthMessage).font(.caption).multilineTextAlignment(.center)
                            .padding(8).background(.black.opacity(0.72), in: Capsule()).foregroundStyle(.white).padding(.top)
                    }
                    Spacer()
                    if runtime.tracking.poseEvidenceEligible == false {
                        Text(runtime.tracking.message).font(.caption)
                            .padding(8).background(.black.opacity(0.65), in: Capsule()).foregroundStyle(.white).padding()
                    } else {
                        Text("PackLab Capture").font(.headline)
                            .padding(8).background(.black.opacity(0.65), in: Capsule()).foregroundStyle(.white).padding()
                    }
                }

                if showPoseDebug {
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(runtime.overlay.lines, id: \.self) { line in
                            Text(line).font(.caption.monospaced()).foregroundStyle(.white)
                        }
                    }
                    .padding(8).background(.black.opacity(0.7), in: RoundedRectangle(cornerRadius: 8))
                    .padding().frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing).allowsHitTesting(false)
                }
            }
            .navigationTitle("PackLab")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) { Button("New Scan") { showNewScan = true } }
                ToolbarItem(placement: .topBarTrailing) { Button(showPoseDebug ? "Hide Debug" : "Show Debug") { showPoseDebug.toggle() } }
            }
            .sheet(isPresented: $showNewScan) { NavigationStack { NewScanWizard { _ in showNewScan = false } } }
            .sheet(isPresented: $showResume) { NavigationStack { SessionResumeView(root: ContentView.sessionRoot, onResume: { _ in showResume = false }, onDiscard: { _ in showResume = false }) } }
            .task { await runtime.start(); let candidates = await SessionDiscoveryService(root: ContentView.sessionRoot).discover(); showResume = !candidates.isEmpty }
        }
    }

    private static var sessionRoot: URL { FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!.appendingPathComponent("PackLabSessions", isDirectory: true) }
}

#Preview { ContentView() }
