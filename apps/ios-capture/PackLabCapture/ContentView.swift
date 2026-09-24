import SwiftUI
#if canImport(AVFoundation) && canImport(NextLevel)
import AVFoundation
import NextLevel
#endif

@MainActor
final class CaptureRuntimeViewModel: ObservableObject {
    @Published private(set) var tracking = TrackingSnapshot(quality: .unavailable, poseEvidenceEligible: false, message: "Tracking unavailable")
    @Published private(set) var epoch = 0
    @Published private(set) var pose: PoseSample?
    @Published private(set) var motion: MotionSampleRecord?
    @Published private(set) var health: DeviceHealthCaptureGate = .ready(DeviceHealthPolicy.evaluate(UnavailableDeviceHealthProvider().snapshot()))
    @Published private(set) var controls = CameraCaptureControlModel()
    @Published private(set) var admission = CaptureAdmissionController()
    @Published private(set) var trackingDiagnostics: [TrackingDiagnosticEvent] = []
    @Published private(set) var resetDiagnostics: [ResetDiagnosticEvent] = []
    @Published private(set) var cameraRecoveryState: CameraRecoveryState = .idle
    @Published private(set) var cameraRecoveryMessage = ""
    private let trackingService: any ARTrackingService
    private let motionService: any MotionService
    private let healthMonitor: DeviceHealthMonitor
    private let diagnostics = DiagnosticsLogger()
    private var trackingRecoveryPolicy = TrackingRecoveryPolicy(requiredStableNormalFrames: 3)
    private var updateTask: Task<Void, Never>?
    private var captureAdmissionService: AdmissionControlledStillCaptureService?
    private var cameraControlBridge: CameraControlRuntimeBridge?
    private var isRunning = false

    init() {
        #if targetEnvironment(simulator)
        trackingService = SimulatorARTrackingService()
        motionService = SimulatorMotionService()
        healthMonitor = DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider())
        #elseif canImport(ARKit)
        trackingService = ARKitTrackingService()
        motionService = CoreMotionMotionService()
        healthMonitor = DeviceHealthMonitor(provider: PhysicalDeviceHealthProvider())
        #else
        trackingService = FoundationARTrackingService(isAvailable: false)
        motionService = FoundationMotionService()
        healthMonitor = DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider())
        #endif
    }

    init(trackingService: any ARTrackingService, motionService: any MotionService, healthMonitor: DeviceHealthMonitor) {
        self.trackingService = trackingService
        self.motionService = motionService
        self.healthMonitor = healthMonitor
    }

    func start() async {
        isRunning = true
        await trackingService.start()
        await motionService.start()
        health = await healthMonitor.preflight()
        admission.update(health)
        if let service = captureAdmissionService { await service.updateAdmission(admission) }
        await healthMonitor.start { [weak self] gate in
            await MainActor.run {
                self?.health = gate
                self?.admission.update(gate)
            }
            if let service = await MainActor.run(body: { self?.captureAdmissionService }) {
                let current = await MainActor.run(body: { self?.admission ?? CaptureAdmissionController() })
                await service.updateAdmission(current)
            }
        }
        updateTask?.cancel()
        updateTask = Task { [weak self] in
            while !Task.isCancelled {
                await self?.refresh()
                try? await Task.sleep(nanoseconds: 100_000_000)
            }
        }
        await refresh()
    }

    func stop() async {
        isRunning = false
        updateTask?.cancel()
        updateTask = nil
        await healthMonitor.stop()
        await trackingService.stop()
        await motionService.stop()
    }

    func refresh() async {
        guard isRunning else { return }
        let raw = await trackingService.snapshot()
        trackingRecoveryPolicy.update(state: raw.quality, limitation: raw.limitation)
        trackingDiagnostics = trackingRecoveryPolicy.diagnostics
        tracking = trackingRecoveryPolicy.snapshot
        pose = await trackingService.latestPose()
        motion = await motionService.latestRecord()
        epoch = await trackingService.localizationEpoch()
        resetDiagnostics = await trackingService.resetDiagnostics()
        await diagnostics.record(category: "tracking", code: raw.quality.rawValue, message: raw.message)
    }

    func admitCapture() -> Bool {
        admission.allowsCapture
    }

    /// Installs the same health-gated backend used by the production camera
    /// composition. Tests inject a deterministic StillPhotoBackend; the UI
    /// and physical request therefore share one admission boundary.
    func bindStillCaptureBackend(_ backend: any StillPhotoBackend) async {
        let service = AdmissionControlledStillCaptureService(backend: backend)
        await service.updateAdmission(admission)
        captureAdmissionService = service
    }

    #if canImport(AVFoundation) && canImport(NextLevel)
    func bindProductionCamera(nextLevel: NextLevel, recoveryOwner: CameraRecoveryOwner, activeLensIdentifier: @escaping () -> String?) async throws {
        let composition = try NextLevelStillCaptureComposition(nextLevel: nextLevel, candidates: AVFoundationCameraDiscovery.rearCandidates(), activeLensIdentifier: activeLensIdentifier, recoveryOwner: recoveryOwner)
        recoveryOwner.onStateChange = { [weak self] state, message in self?.updateCameraRecovery(state: state, message: message) }
        await bindStillCaptureBackend(composition.adapter)
    }
    #endif

    func captureAcceptedStill(captureID: String = UUID().uuidString) async -> StillCaptureResult {
        guard let service = captureAdmissionService else { return .rejected("capture_backend_unavailable") }
        return await service.capture(captureID: captureID)
    }

    func updateCameraRecovery(state: CameraRecoveryState, message: String) {
        cameraRecoveryState = state
        cameraRecoveryMessage = message
    }

    func bindCameraControls(_ bridge: CameraControlRuntimeBridge) {
        cameraControlBridge = bridge
        bridge.onStateChange = { [weak self] state in
            self?.updateControlState(lens: state.lens, focus: state.focus, exposure: state.exposure, whiteBalance: state.whiteBalance, message: state.message)
        }
        updateControlState(lens: bridge.state.lens, focus: bridge.state.focus, exposure: bridge.state.exposure, whiteBalance: bridge.state.whiteBalance, message: bridge.state.message)
    }

    func updateControlState(lens: CameraLensIdentity?, focus: FocusState? = nil, exposure: ExposureState? = nil, whiteBalance: WhiteBalanceState? = nil, message: String? = nil) {
        var next = CameraCaptureControlModel(lens: lens ?? controls.state.lens)
        next.setFocus(focus ?? controls.state.focus)
        next.setExposure(exposure ?? controls.state.exposure)
        next.setWhiteBalance(whiteBalance ?? controls.state.whiteBalance)
        next.message(message ?? controls.state.message)
        controls = next
    }

    var overlay: PoseOverlayModel { PoseOverlayModel.make(visible: true, tracking: tracking, epoch: epoch, pose: pose, motion: motion) }
    var healthMessage: String? {
        switch health {
        case .ready: return nil
        case .warning(let decision), .hardStop(let decision): return decision.messages.joined(separator: " ")
        }
    }

    deinit { updateTask?.cancel() }
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
                    Text("Focus: \(runtime.controls.state.focus.rawValue) · Exposure: \(runtime.controls.state.exposure.rawValue) · WB: \(runtime.controls.state.whiteBalance.rawValue)").font(.caption2).foregroundStyle(.white).padding(.top, 4)
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
            .sheet(isPresented: $showNewScan) { NavigationStack { NewScanWizard { draft in
                Task { do { let store = ScanSessionStore(layout: SessionStorageLayout(root: ContentView.sessionRoot, sessionID: draft.sessionID)); try await store.create(draft); await ContentView.sessionRegistry.install(ActiveScanSession(draft: draft, state: PersistedSessionState(sessionID: draft.sessionID, nextSequence: 0, epoch: 0, acceptedIDs: []))) } catch { } }
                showNewScan = false
            } } }
            .sheet(isPresented: $showResume) { NavigationStack { SessionResumeView(root: ContentView.sessionRoot, onResume: { candidate in
                if let draft = candidate.draft, let state = candidate.state { Task { await ContentView.sessionRegistry.install(ActiveScanSession(draft: draft, state: state)) } }
                showResume = false
            }, onDiscard: { candidate in
                Task { let plan = SessionDeletionPlan(root: ContentView.sessionRoot, candidate: candidate); _ = try? await SafeSessionDeleter().deleteDetailed(plan: plan, confirmed: true) }
                showResume = false
            }) } }
            .task { await runtime.start(); let candidates = await SessionDiscoveryService(root: ContentView.sessionRoot).discover(); showResume = !candidates.isEmpty }
        }
    }

    private static var sessionRoot: URL { FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!.appendingPathComponent("PackLabSessions", isDirectory: true) }
    private static let sessionRegistry = ActiveScanSessionRegistry()
}

#Preview { ContentView() }
