import SwiftUI
import Foundation
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
    @Published private(set) var m04Evaluation: M04CandidateQualityEvaluation?
    @Published private(set) var m04Coverage = OrbitCoverageModel().snapshot()
    @Published private(set) var m04CoverageTarget: CoverageSector?
    @Published private(set) var m04CoverageActive = false
    private let trackingService: any ARTrackingService
    private let motionService: any MotionService
    private let healthMonitor: DeviceHealthMonitor
    private let diagnostics = DiagnosticsLogger()
    private var trackingRecoveryPolicy = TrackingRecoveryPolicy(requiredStableNormalFrames: 3)
    private var updateTask: Task<Void, Never>?
    private var captureAdmissionService: AdmissionControlledStillCaptureService?
    private var m04QualityRuntime = M04CandidateQualityRuntime(preset: PackagingPresetCatalog.matteHDPE)
    private var m04QualityLogStore: QualityCandidateLogStore?
    private var m04CoverageModel = OrbitCoverageModel()
    private var cameraControlBridge: CameraControlRuntimeBridge?
    #if canImport(AVFoundation)
    let cameraRecoveryOwner = CameraRecoveryOwner()
    private var cameraControlComposition: AVFoundationCameraControlComposition?
    #endif
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
        #if canImport(AVFoundation)
        cameraRecoveryOwner.onStateChange = { [weak self] state, message in self?.updateCameraRecovery(state: state, message: message) }
        #endif
    }

    init(trackingService: any ARTrackingService, motionService: any MotionService, healthMonitor: DeviceHealthMonitor) {
        self.trackingService = trackingService
        self.motionService = motionService
        self.healthMonitor = healthMonitor
        #if canImport(AVFoundation)
        cameraRecoveryOwner.onStateChange = { [weak self] state, message in self?.updateCameraRecovery(state: state, message: message) }
        #endif
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

    func configureM04QualityRuntime(preset: PackagingPreset, layout: SessionStorageLayout? = nil) {
        m04QualityRuntime = M04CandidateQualityRuntime(preset: preset)
        m04QualityLogStore = layout.map { QualityCandidateLogStore(layout: $0) }
        m04CoverageModel = OrbitCoverageModel(configuration: preset.coverage.orbit)
        m04Coverage = m04CoverageModel.snapshot()
        m04CoverageTarget = m04Coverage.missingSectors.first
        m04CoverageActive = true
        m04Evaluation = nil
    }

    @discardableResult
    func recordAcceptedCaptureCoverage(_ record: AcceptedCaptureRecord) -> CoveragePoseObservation {
        let observation = m04CoverageModel.observe(captureID: record.captureID, poseBinding: record.poseBinding)
        m04Coverage = m04CoverageModel.snapshot()
        m04CoverageTarget = m04Coverage.missingSectors.first
        return observation
    }

    @discardableResult
    func analyzeM04Candidate(_ input: M04CandidateFrameInput) async -> M04CandidateQualityEvaluation {
        let evaluation = m04QualityRuntime.evaluate(input)
        m04Evaluation = evaluation
        if let store = m04QualityLogStore {
            try? await store.append(QualityCandidateLog(sessionID: input.sessionID, captureID: input.captureID, sequence: input.sequence, monotonicTimestamp: input.monotonicTimestamp, decision: evaluation.quality))
        }
        return evaluation
    }

    /// Production candidate entry point. Motion is bound in the existing
    /// MotionService timestamp domain before the shared quality runtime runs.
    @discardableResult
    func analyzeM04Candidate(sessionID: String, captureID: String, sequence: Int, monotonicTimestamp: TimeInterval, frame: QualityImageFrame, pose: PoseCaptureBinding? = nil) async -> M04CandidateQualityEvaluation {
        let motionBinding = await motionService.bindCandidateMotion(captureID: captureID, timestamp: monotonicTimestamp)
        return await analyzeM04Candidate(M04CandidateFrameInput(sessionID: sessionID, captureID: captureID, sequence: sequence, monotonicTimestamp: monotonicTimestamp, frame: frame, motion: motionBinding, pose: pose))
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
    func bindProductionCamera(nextLevel: NextLevel, activeLensIdentifier: @escaping () -> String?) async throws {
        let candidates = AVFoundationCameraDiscovery.rearCandidates()
        guard case .selected(let lens) = CameraDeviceSelector.selectMainRearWide(from: candidates),
              let device = AVFoundationCameraDiscovery.rearDevice(for: lens) else { throw CameraServiceError.unavailable }
        let controls = AVFoundationCameraControlComposition(device: device, selectedLens: lens)
        cameraControlComposition = controls
        bindCameraControls(controls.controls)
        let composition = try NextLevelStillCaptureComposition(nextLevel: nextLevel, candidates: candidates, activeLensIdentifier: activeLensIdentifier, recoveryOwner: cameraRecoveryOwner)
        await bindStillCaptureBackend(composition.adapter)
    }
    #endif

    func captureAcceptedStill(captureID: String = UUID().uuidString) async -> StillCaptureResult {
        guard let service = captureAdmissionService else { return .rejected("capture_backend_unavailable") }
        return await service.capture(captureID: captureID)
    }

    func captureAndPersistAcceptedStill(captureID: String = UUID().uuidString, record: AcceptedCaptureRecord, metadata: Data, state: Data, store: ScanSessionStore, poses: PoseBuffer, motion: MotionBuffer, bridge: TimestampDomainBridge? = nil) async throws -> AcceptedStill {
        guard let service = captureAdmissionService else { throw CameraServiceError.failed("capture_backend_unavailable") }
        let result = await service.capture(captureID: captureID)
        guard case .accepted(let still) = result else { throw CameraServiceError.failed("capture_rejected") }
        try await store.storeAcceptedCapture(still: still, record: record, metadata: metadata, state: state, poses: poses, motion: motion, bridge: bridge)
        let evidence = AcceptedStillEvidenceBinder.bind(still: still, poses: poses, motion: motion, bridge: bridge)
        _ = recordAcceptedCaptureCoverage(AcceptedCaptureRecord(captureID: record.captureID, sequence: record.sequence, sourceFilename: record.sourceFilename, metadataFilename: record.metadataFilename, acceptedAt: record.acceptedAt, poseBinding: evidence.pose ?? record.poseBinding, motionBinding: evidence.motion ?? record.motionBinding))
        return still
    }

    func captureAndPersistAcceptedPhoto(captureID: String = UUID().uuidString, filename: String, metadata: PhotoCaptureMetadata, store: AcceptedPhotoMetadataStore) async throws -> PhotoCaptureMetadata {
        guard let service = captureAdmissionService else { throw CameraServiceError.failed("capture_backend_unavailable") }
        let result = await service.capture(captureID: captureID)
        guard case .accepted(let still) = result else { throw CameraServiceError.failed("capture_rejected") }
        let source = try OriginalSourceRecord.fromSource(captureID: still.captureID, filename: filename, dimensions: still.dimensions, orientation: metadata.orientation, bytes: still.sourceBytes)
        #if canImport(AVFoundation)
        let acceptedMetadata = try cameraControlComposition?.acceptedMetadata(metadata) ?? metadata
        #else
        let acceptedMetadata = metadata
        #endif
        try await store.persist(metadata: acceptedMetadata, source: source, bytes: still.sourceBytes)
        return acceptedMetadata
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
                #if canImport(AVFoundation) && canImport(NextLevel)
                NextLevelPreviewBridge(recoveryOwner: runtime.cameraRecoveryOwner) { nextLevel in
                    Task {
                        try? await runtime.bindProductionCamera(nextLevel: nextLevel, activeLensIdentifier: {
                            AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back)?.uniqueID
                        })
                    }
                }.ignoresSafeArea()
                #else
                NextLevelPreviewBridge().ignoresSafeArea()
                #endif
                #endif

                VStack {
                    if let healthMessage = runtime.healthMessage {
                        Text(healthMessage).font(.caption).multilineTextAlignment(.center)
                            .padding(8).background(.black.opacity(0.72), in: Capsule()).foregroundStyle(.white).padding(.top)
                    }
                    Text("Focus: \(runtime.controls.state.focus.rawValue) · Exposure: \(runtime.controls.state.exposure.rawValue) · WB: \(runtime.controls.state.whiteBalance.rawValue)").font(.caption2).foregroundStyle(.white).padding(.top, 4)
                    if let evaluation = runtime.m04Evaluation {
                        let motion = evaluation.quality.metrics.motionBlur
                        VStack(spacing: 2) {
                            Text("Quality: \(evaluation.quality.decision.rawValue) · Motion: \(motion.risk.rawValue)")
                            if !motion.reasons.isEmpty { Text(motion.reasons.joined(separator: ", ")) }
                            let highlight = evaluation.quality.metrics.highlightClipping
                            let shadow = evaluation.quality.metrics.shadowClipping
                            Text("Highlights: \(clippingFractionText(highlight)) · Shadows: \(clippingFractionText(shadow))")
                            let clippingReasons = highlight.reasons + shadow.reasons
                            if !clippingReasons.isEmpty { Text(clippingReasons.joined(separator: ", ")) }
                            let framing = evaluation.quality.metrics.framing
                            Text("Framing: \(framing.band.rawValue) · Object: \(framingObjectFractionText(framing))")
                            if !framing.reasons.isEmpty { Text(framing.reasons.joined(separator: ", ")) }
                            let background = evaluation.quality.metrics.background
                            Text("Background: \(background.band.rawValue) · Score: \(backgroundScoreText(background))")
                            if !background.reasons.isEmpty { Text(background.reasons.joined(separator: ", ")) }
                        }
                        .font(.caption2.monospaced()).foregroundStyle(.white)
                        .padding(6).background(.black.opacity(0.72), in: RoundedRectangle(cornerRadius: 6))
                    }
                    if runtime.m04CoverageActive {
                        CoverageGridView(model: CoverageViewModel(snapshot: runtime.m04Coverage, targeted: runtime.m04CoverageTarget))
                            .padding(8).background(.black.opacity(0.72), in: RoundedRectangle(cornerRadius: 8))
                            .padding(.horizontal, 8)
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
            .sheet(isPresented: $showNewScan) { NavigationStack { NewScanWizard(admission: runtime.admission) { draft in
                Task { do { let layout = SessionStorageLayout(root: ContentView.sessionRoot, sessionID: draft.sessionID); let store = ScanSessionStore(layout: layout); try await store.create(draft); let preset = PackagingPresetCatalog.preset(for: draft.presetID ?? .matteHDPE); runtime.configureM04QualityRuntime(preset: preset, layout: layout); let context = M04ScanContext(preset: preset, preparationAcknowledged: draft.preflight?.preparationAcknowledged ?? false, preflight: draft.preflight); try await M04SessionContextStore(layout: layout).persist(context); await ContentView.sessionRegistry.install(ActiveScanSession(draft: draft, state: PersistedSessionState(sessionID: draft.sessionID, nextSequence: 0, epoch: 0, acceptedIDs: []))) } catch { } }
                showNewScan = false
            } } }
            .sheet(isPresented: $showResume) { NavigationStack { SessionResumeView(root: ContentView.sessionRoot, onResume: { candidate in
                if let draft = candidate.draft, let state = candidate.state { let layout = SessionStorageLayout(root: ContentView.sessionRoot, sessionID: draft.sessionID); runtime.configureM04QualityRuntime(preset: PackagingPresetCatalog.preset(for: draft.presetID ?? .matteHDPE), layout: layout); Task { await ContentView.sessionRegistry.install(ActiveScanSession(draft: draft, state: state)) } }
                showResume = false
            }, onDiscard: { candidate in
                Task { let plan = SessionDeletionPlan(root: ContentView.sessionRoot, candidate: candidate); _ = try? await SafeSessionDeleter().deleteDetailed(plan: plan, confirmed: true) }
                showResume = false
            }) } }
            .task { await runtime.start(); let candidates = await SessionDiscoveryService(root: ContentView.sessionRoot).discover(); showResume = !candidates.isEmpty }
        }
    }

    private func clippingFractionText(_ metric: ClippingMetric) -> String {
        guard let fraction = metric.objectClippedFraction ?? metric.clippedFraction else { return "unavailable" }
        return String(format: "%.1f%% (%@)", fraction * 100, metric.band.rawValue)
    }

    private func framingObjectFractionText(_ metric: FramingMetric) -> String {
        guard let fraction = metric.objectFraction else { return "unavailable" }
        return String(format: "%.1f%%", fraction * 100)
    }

    private func backgroundScoreText(_ metric: BackgroundComplexityMetric) -> String {
        guard let score = metric.score else { return "unavailable" }
        return String(format: "%.3f", score)
    }

    private static var sessionRoot: URL { FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!.appendingPathComponent("PackLabSessions", isDirectory: true) }
    private static let sessionRegistry = ActiveScanSessionRegistry()
}

#Preview { ContentView() }
