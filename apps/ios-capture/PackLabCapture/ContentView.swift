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
    @Published private(set) var m04RingCoverage = RingCoverageEvaluation(snapshot: OrbitCoverageModel().snapshot())
    @Published private(set) var m04DetailGuidance: [String] = []
    @Published private(set) var m04BasePass = BasePassEvaluation(snapshot: OrbitCoverageModel().snapshot(), availability: BasePassAvailability(physicallyFeasible: false, reasonCode: "base_pass_unavailable"))
    @Published private(set) var m04Completion = CompletionDiagnostics(rings: RingCoverageEvaluation(snapshot: OrbitCoverageModel().snapshot()))
    @Published private(set) var manualCaptureDecision: ManualCaptureDecision?
    @Published private(set) var m04ActivePreset = PackagingPresetCatalog.matteHDPE
    @Published private(set) var m04ReflectionGuidance: [String] = []
    @Published private(set) var m04AsymmetricCoverage: AsymmetricCoverageEvaluation?
    @Published private(set) var m04TurntableCoverage: TurntableCoverageSnapshot?
    private let trackingService: any ARTrackingService
    private let motionService: any MotionService
    private let healthMonitor: DeviceHealthMonitor
    private let diagnostics = DiagnosticsLogger()
    private var trackingRecoveryPolicy = TrackingRecoveryPolicy(requiredStableNormalFrames: 3)
    private var updateTask: Task<Void, Never>?
    private var captureAdmissionService: AdmissionControlledStillCaptureService?
    private var guidedAutoCaptureService: GuidedAutoCaptureService?
    private var m04QualityRuntime = M04CandidateQualityRuntime(preset: PackagingPresetCatalog.matteHDPE)
    private var m04QualityLogStore: QualityCandidateLogStore?
    private var m04CoverageModel = OrbitCoverageModel()
    private var m04RingPolicy = StandardBottleCoveragePolicy.standard
    private var m04DetailPolicies: [CapturePassID: DetailPassPolicy] = [:]
    private var m04DetailCoverageModels: [CapturePassID: OrbitCoverageModel] = [:]
    private var m04BaseCoverageModel = OrbitCoverageModel(configuration: OrbitCoverageConfiguration(rings: [CoverageRingDefinition(id: "base", minimumElevation: -90, maximumElevation: 90)]))
    private var m04BaseAvailability = BasePassAvailability(physicallyFeasible: false, reasonCode: "base_pass_unavailable")
    private var m04SessionLayout: SessionStorageLayout?
    private var m04AsymmetricPolicy: AsymmetricCoveragePolicy?
    private var m04AsymmetricObservedRegions: [AsymmetricCoverageRegion: Int] = [:]
    private var m04TurntableModel: TurntableCoverageModel?
    private var m04ConsecutiveHighlightBlocks = 0
    private let m04HighlightGuidanceThreshold = 3
    private var m04DetailEvaluations: [CapturePassID: DetailPassEvaluation] = [:]
    private var m04DetailFraming: [CapturePassID: FramingMetric] = [:]
    private var m04AcceptedDuplicateEvidence: [DuplicateEvidence] = []
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
        m04ActivePreset = preset
        m04AsymmetricPolicy = preset.coverage.asymmetricCoverage
        m04AsymmetricObservedRegions = [:]
        m04AsymmetricCoverage = preset.coverage.asymmetricCoverage.map { AsymmetricCoverageEvaluation(observedRegions: [:], policy: $0) }
        m04TurntableModel = preset.id == .turntable ? TurntableCoverageModel(policy: TurntablePolicy(expectedAngleCount: preset.coverage.orbit.azimuthBinCount)) : nil
        m04TurntableCoverage = m04TurntableModel?.snapshot()
        m04ConsecutiveHighlightBlocks = 0
        m04ReflectionGuidance = []
        m04QualityRuntime = M04CandidateQualityRuntime(preset: preset)
        m04QualityLogStore = layout.map { QualityCandidateLogStore(layout: $0) }
        m04SessionLayout = layout
        m04CoverageModel = OrbitCoverageModel(configuration: preset.coverage.orbit)
        m04Coverage = m04CoverageModel.snapshot()
        m04CoverageTarget = m04Coverage.missingSectors.first
        m04RingPolicy = preset.coverage.ringRequirements
        m04RingCoverage = RingCoverageEvaluation(snapshot: m04Coverage, policy: m04RingPolicy)
        if preset.id == .closureCap {
            m04DetailPolicies = [.closure: DetailPassPolicy(passID: .closure, minimumFramingFraction: preset.quality.framing.minimumObjectFraction, minimumSectorCount: 4)]
        } else {
            m04DetailPolicies = [.shoulder: DetailPassPolicy(passID: .shoulder, minimumFramingFraction: 0.18), .neck: DetailPassPolicy(passID: .neck, minimumFramingFraction: 0.20), .closure: DetailPassPolicy(passID: .closure, minimumFramingFraction: 0.22)]
        }
        m04DetailCoverageModels = Dictionary(uniqueKeysWithValues: m04DetailPolicies.keys.map { passID in (passID, OrbitCoverageModel(configuration: detailCoverageConfiguration(for: passID))) })
        m04DetailGuidance = m04DetailPolicies.values.map { "Capture missing \($0.passID.rawValue) detail sectors" }
        m04BaseCoverageModel = OrbitCoverageModel(configuration: OrbitCoverageConfiguration(azimuthBinCount: 4, rings: [CoverageRingDefinition(id: "base", minimumElevation: -90, maximumElevation: 90)]))
        m04BaseAvailability = BasePassAvailability(physicallyFeasible: false, reasonCode: "base_pass_unavailable")
        m04BasePass = BasePassEvaluation(snapshot: m04BaseCoverageModel.snapshot(), availability: m04BaseAvailability)
        m04DetailEvaluations = [:]
        m04DetailFraming = [:]
        recomputeM04Completion()
        m04CoverageActive = true
        m04AcceptedDuplicateEvidence = []
        m04Evaluation = nil
    }

    private func detailCoverageConfiguration(for passID: CapturePassID) -> OrbitCoverageConfiguration {
        OrbitCoverageConfiguration(azimuthBinCount: 4, rings: [CoverageRingDefinition(id: passID.rawValue, minimumElevation: passID == .closure ? 10 : 15, maximumElevation: passID == .shoulder ? 60 : 45)])
    }

    private func defaultDetailFraming(for policy: DetailPassPolicy) -> FramingMetric {
        FramingMetric(availability: .available, objectFraction: policy.minimumFramingFraction, bounds: nil, margins: [:], band: .acceptable, reasons: [])
    }

    private func resetM04DetailPassStateToMissing() {
        m04DetailCoverageModels = Dictionary(uniqueKeysWithValues: m04DetailPolicies.keys.map { passID in (passID, OrbitCoverageModel(configuration: detailCoverageConfiguration(for: passID))) })
        m04DetailEvaluations = [:]
        m04DetailFraming = [:]
        for policy in m04DetailPolicies.values {
            let framing = defaultDetailFraming(for: policy)
            let evaluation = DetailPassEvaluation(snapshot: m04DetailCoverageModels[policy.passID]?.snapshot() ?? OrbitCoverageModel(configuration: detailCoverageConfiguration(for: policy.passID)).snapshot(), framing: framing, policy: policy)
            m04DetailFraming[policy.passID] = framing
            m04DetailEvaluations[policy.passID] = evaluation
        }
        m04DetailGuidance = m04DetailEvaluations.values.flatMap { $0.missingGuidance }
    }

    private func makeM04DetailResumeState() -> [M04DetailPassResumeState] {
        m04DetailPolicies.values.sorted { $0.passID.rawValue < $1.passID.rawValue }.map { policy in
            let snapshot = m04DetailCoverageModels[policy.passID]?.snapshot() ?? OrbitCoverageModel(configuration: detailCoverageConfiguration(for: policy.passID)).snapshot()
            let framing = m04DetailFraming[policy.passID] ?? defaultDetailFraming(for: policy)
            let evaluation = m04DetailEvaluations[policy.passID] ?? DetailPassEvaluation(snapshot: snapshot, framing: framing, policy: policy)
            return M04DetailPassResumeState(passID: policy.passID, policy: policy, coverage: snapshot, framing: framing, evaluation: evaluation)
        }
    }

    private func invalidateM04DetailResumeState() {
        resetM04DetailPassStateToMissing()
        m04DetailGuidance.append("Detail-pass resume evidence unavailable")
        recomputeM04Completion()
    }

    @discardableResult
    func restoreM04DetailPassState(_ states: [M04DetailPassResumeState]?) -> Bool {
        guard let states else {
            resetM04DetailPassStateToMissing()
            recomputeM04Completion()
            return false
        }
        let expectedPasses = Set(m04DetailPolicies.keys)
        guard states.count == expectedPasses.count else {
            invalidateM04DetailResumeState()
            return false
        }
        var seen = Set<CapturePassID>()
        var restoredModels: [CapturePassID: OrbitCoverageModel] = [:]
        var restoredEvaluations: [CapturePassID: DetailPassEvaluation] = [:]
        var restoredFraming: [CapturePassID: FramingMetric] = [:]
        for state in states {
            guard expectedPasses.contains(state.passID), seen.insert(state.passID).inserted,
                  state.passID == state.policy.passID,
                  m04DetailPolicies[state.passID] == state.policy,
                  m04DetailCoverageModels[state.passID]?.configuration == state.coverage.configuration,
                  OrbitCoverageModel(snapshot: state.coverage).snapshot() == state.coverage,
                  state.evaluation == DetailPassEvaluation(snapshot: state.coverage, framing: state.framing, policy: state.policy) else {
                invalidateM04DetailResumeState()
                return false
            }
            restoredModels[state.passID] = OrbitCoverageModel(snapshot: state.coverage)
            restoredEvaluations[state.passID] = state.evaluation
            restoredFraming[state.passID] = state.framing
        }
        guard seen == expectedPasses else {
            invalidateM04DetailResumeState()
            return false
        }
        m04DetailCoverageModels = restoredModels
        m04DetailEvaluations = restoredEvaluations
        m04DetailFraming = restoredFraming
        m04DetailGuidance = restoredEvaluations.values.flatMap { $0.missingGuidance }
        recomputeM04Completion()
        return true
    }

    @discardableResult
    func restoreM04OrbitCoverage(_ snapshot: OrbitCoverageSnapshot?) -> Bool {
        guard let snapshot,
              snapshot.configuration == m04CoverageModel.configuration,
              OrbitCoverageModel(snapshot: snapshot).snapshot() == snapshot else { return false }
        m04CoverageModel = OrbitCoverageModel(snapshot: snapshot)
        m04Coverage = snapshot
        m04CoverageTarget = snapshot.missingSectors.first
        m04RingCoverage = RingCoverageEvaluation(snapshot: snapshot, policy: m04RingPolicy)
        recomputeM04Completion()
        return true
    }

    @discardableResult
    func recordAcceptedCaptureCoverage(_ record: AcceptedCaptureRecord) -> CoveragePoseObservation {
        let observation = m04CoverageModel.observe(captureID: record.captureID, poseBinding: record.poseBinding)
        m04Coverage = m04CoverageModel.snapshot()
        m04CoverageTarget = m04Coverage.missingSectors.first
        m04RingCoverage = RingCoverageEvaluation(snapshot: m04Coverage, policy: m04RingPolicy)
        m04AcceptedDuplicateEvidence.append(DuplicateEvidence(captureID: record.captureID, poseBinding: record.poseBinding))
        if let passID = record.passMetadata?.passID, var detailModel = m04DetailCoverageModels[passID] {
            _ = detailModel.observe(captureID: record.captureID, poseBinding: record.poseBinding)
            m04DetailCoverageModels[passID] = detailModel
            if let policy = m04DetailPolicies[passID] {
                let evaluation = DetailPassEvaluation(snapshot: detailModel.snapshot(), framing: FramingMetric(availability: .available, objectFraction: policy.minimumFramingFraction, bounds: nil, margins: [:], band: .acceptable, reasons: []), policy: policy)
                m04DetailEvaluations[passID] = evaluation
                m04DetailGuidance = m04DetailGuidance.filter { !$0.contains("\(passID.rawValue) detail") } + evaluation.missingGuidance
            }
        }
        if record.passMetadata?.passID == .base {
            _ = m04BaseCoverageModel.observe(captureID: record.captureID, poseBinding: record.poseBinding)
            m04BasePass = BasePassEvaluation(snapshot: m04BaseCoverageModel.snapshot(), availability: m04BaseAvailability)
            recomputeM04Completion()
        }
        recomputeM04Completion()
        return observation
    }

    func setBasePassAvailability(_ availability: BasePassAvailability) {
        m04BaseAvailability = availability
        m04BasePass = BasePassEvaluation(snapshot: m04BaseCoverageModel.snapshot(), availability: availability)
        recomputeM04Completion()
    }

    func skipBasePass(reasonCode: String = "operator_skipped") {
        setBasePassAvailability(BasePassAvailability(physicallyFeasible: false, reasonCode: reasonCode, operatorSkipped: true))
    }

    func restoreBasePass(_ evaluation: BasePassEvaluation) {
        m04BasePass = evaluation
        m04BaseAvailability = BasePassAvailability(physicallyFeasible: evaluation.metadata.required, reasonCode: evaluation.guidance.first ?? "operator_confirmed_feasible", operatorSkipped: evaluation.status == "skipped")
        recomputeM04Completion()
    }

    func restoreCompletion(_ completion: CompletionDiagnostics) { m04Completion = completion }

    func restoreQualityGuidance(_ state: M04QualityGuidanceState?) {
        guard let state, state.presetID == m04ActivePreset.id else { return }
        m04ConsecutiveHighlightBlocks = state.consecutiveHighlightBlocks
        m04ReflectionGuidance = state.guidanceActive ? state.guidance : []
    }

    func observeAsymmetricRegion(_ region: AsymmetricCoverageRegion) {
        guard let policy = m04AsymmetricPolicy else { return }
        m04AsymmetricObservedRegions[region, default: 0] += 1
        m04AsymmetricCoverage = AsymmetricCoverageEvaluation(observedRegions: m04AsymmetricObservedRegions, policy: policy)
        recomputeM04Completion()
    }

    func restoreAsymmetricCoverage(_ evaluation: AsymmetricCoverageEvaluation?) {
        guard m04AsymmetricPolicy != nil else { return }
        m04AsymmetricObservedRegions = evaluation?.observedRegions ?? [:]
        m04AsymmetricCoverage = evaluation
        recomputeM04Completion()
    }

    func restoreTurntableCoverage(_ snapshot: TurntableCoverageSnapshot?) {
        guard snapshot != nil, m04ActivePreset.id == .turntable else { return }
        m04TurntableModel = snapshot.map { TurntableCoverageModel(snapshot: $0) }
        m04TurntableCoverage = m04TurntableModel?.snapshot()
        recomputeM04Completion()
    }

    func evaluateTurntableAngle(_ angleDegrees: Double) -> AutoCaptureDecision {
        guard let model = m04TurntableModel else { return AutoCaptureDecision(allowed: false, reasons: ["turntable_mode_inactive"]) }
        guard angleDegrees.isFinite else { return AutoCaptureDecision(allowed: false, reasons: ["turntable_angle_unavailable"]) }
        return model.isSectorCaptured(angleDegrees: angleDegrees) ? AutoCaptureDecision(allowed: false, reasons: ["repeated_turntable_angle"]) : AutoCaptureDecision(allowed: true, reasons: [])
    }

    @discardableResult
    func observeTurntableAngle(captureID: String, angleDegrees: Double) -> TurntableObservation? {
        guard var model = m04TurntableModel, evaluateTurntableAngle(angleDegrees).allowed else { return nil }
        let observation = model.observe(captureID: captureID, angleDegrees: angleDegrees)
        m04TurntableModel = model
        m04TurntableCoverage = model.snapshot()
        recomputeM04Completion()
        return observation
    }

    func evaluateBasePass(quality: QualityDecision, poseBinding: PoseCaptureBinding?, duplicateDecision: DuplicateDecision?) -> BasePassAcceptanceDecision {
        BasePassAcceptanceDecision(snapshot: m04BaseCoverageModel.snapshot(), availability: m04BaseAvailability, quality: quality, poseBinding: poseBinding, duplicateDecision: duplicateDecision)
    }

    func evaluateDetailPass(passID: CapturePassID, quality: QualityDecision, framing: FramingMetric, poseBinding: PoseCaptureBinding?, duplicateDecision: DuplicateDecision?) -> DetailPassAcceptanceDecision {
        let policy = m04DetailPolicies[passID] ?? DetailPassPolicy(passID: passID)
        let snapshot = m04DetailCoverageModels[passID]?.snapshot() ?? OrbitCoverageModel().snapshot()
        let decision = DetailPassAcceptanceDecision(snapshot: snapshot, policy: policy, quality: quality, framing: framing, poseBinding: poseBinding, duplicateDecision: duplicateDecision)
        m04DetailFraming[passID] = framing
        m04DetailEvaluations[passID] = DetailPassEvaluation(snapshot: snapshot, framing: framing, policy: policy)
        recomputeM04Completion()
        m04DetailGuidance = decision.reasons
        return decision
    }

    func autoCaptureInput(monotonicTimestamp: TimeInterval) -> AutoCaptureInput? {
        guard let evaluation = m04Evaluation else { return nil }
        let target = m04CoverageTarget
        let overlapAllowed = target.map { !m04Coverage.capturedSectors.contains($0) } ?? false
        let candidateEvidence = DuplicateEvidence(captureID: evaluation.input.captureID, poseBinding: evaluation.input.pose)
        let duplicateDecision = NearDuplicateDetector.evaluate(candidate: candidateEvidence, accepted: m04AcceptedDuplicateEvidence, configuration: m04Coverage.configuration)
        return AutoCaptureInput(monotonicTimestamp: monotonicTimestamp, poseEligible: tracking.poseEvidenceEligible, targetSector: target, quality: evaluation.quality, overlapAllowed: overlapAllowed, duplicateDecision: duplicateDecision, admission: admission)
    }

    @discardableResult
    func analyzeM04Candidate(_ input: M04CandidateFrameInput) async -> M04CandidateQualityEvaluation {
        let evaluation = m04QualityRuntime.evaluate(input)
        m04Evaluation = evaluation
        updateM04QualityGuidance(evaluation)
        await persistBasePassContext()
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
        guidedAutoCaptureService = GuidedAutoCaptureService(stillCapture: service)
    }

    func requestAutoCapture(captureID: String = UUID().uuidString, monotonicTimestamp: TimeInterval) async -> (decision: AutoCaptureDecision, result: StillCaptureResult?) {
        guard let service = guidedAutoCaptureService, let input = autoCaptureInput(monotonicTimestamp: monotonicTimestamp) else {
            return (AutoCaptureDecision(allowed: false, reasons: [guidedAutoCaptureService == nil ? "auto_capture_service_unavailable" : "quality_unavailable"]), nil)
        }
        return await service.request(captureID: captureID, input: input)
    }

    func evaluateManualCapture(monotonicTimestamp: TimeInterval, cameraReady: Bool, sessionReady: Bool, sourceIntegrityReady: Bool, metadataReady: Bool, poseEvidenceReady: Bool) -> ManualCaptureDecision {
        guard let evaluation = m04Evaluation else {
            let decision = ManualCaptureDecision(allowed: false, warnings: [], blockingReasons: ["metadata_unavailable", "pose_evidence_unavailable"])
            manualCaptureDecision = decision
            return decision
        }
        let automatic = autoCaptureInput(monotonicTimestamp: monotonicTimestamp).map { AutoCaptureController().evaluate($0) } ?? AutoCaptureDecision(allowed: false, reasons: ["quality_unavailable"])
        let decision = ManualCaptureCoordinator.evaluate(ManualCaptureInput(automaticDecision: automatic, quality: evaluation.quality, admission: admission, cameraReady: cameraReady, sessionReady: sessionReady, sourceIntegrityReady: sourceIntegrityReady, metadataReady: metadataReady, poseEvidenceReady: poseEvidenceReady))
        manualCaptureDecision = decision
        return decision
    }

    func captureAndPersistManual(captureID: String = UUID().uuidString, monotonicTimestamp: TimeInterval, cameraReady: Bool, sessionReady: Bool, sourceIntegrityReady: Bool, metadataReady: Bool, poseEvidenceReady: Bool, record: AcceptedCaptureRecord, metadata: Data, state: Data, store: ScanSessionStore, poses: PoseBuffer, motion: MotionBuffer, bridge: TimestampDomainBridge? = nil) async throws -> (decision: ManualCaptureDecision, still: AcceptedStill?) {
        let decision = evaluateManualCapture(monotonicTimestamp: monotonicTimestamp, cameraReady: cameraReady, sessionReady: sessionReady, sourceIntegrityReady: sourceIntegrityReady, metadataReady: metadataReady, poseEvidenceReady: poseEvidenceReady)
        let audit = ManualCaptureAudit(decision: decision)
        if let evaluation = m04Evaluation, let logStore = m04QualityLogStore {
            try? await logStore.append(QualityCandidateLog(sessionID: evaluation.input.sessionID, captureID: captureID, sequence: record.sequence, monotonicTimestamp: monotonicTimestamp, decision: evaluation.quality, manualAudit: audit))
        }
        guard decision.allowed else { return (decision, nil) }
        guard let service = guidedAutoCaptureService else { throw CameraServiceError.failed("capture_backend_unavailable") }
        let result = await service.requestManual(captureID: captureID, monotonicTimestamp: monotonicTimestamp)
        guard case .accepted(let still) = result else { return (decision, nil) }
        let manualRecord = AcceptedCaptureRecord(captureID: record.captureID, sequence: record.sequence, sourceFilename: record.sourceFilename, metadataFilename: record.metadataFilename, acceptedAt: record.acceptedAt, poseBinding: record.poseBinding, motionBinding: record.motionBinding, passMetadata: record.passMetadata, manualAudit: audit, turntableEvidence: record.turntableEvidence)
        let manualMetadata = (try? JSONEncoder().encode(manualRecord)) ?? metadata
        try await store.storeAcceptedCapture(still: still, record: manualRecord, metadata: manualMetadata, state: state, poses: poses, motion: motion, bridge: bridge)
        recordAcceptedCaptureCoverage(manualRecord)
        return (decision, still)
    }

    func requestManualCapture(captureID: String = UUID().uuidString, monotonicTimestamp: TimeInterval = ProcessInfo.processInfo.systemUptime) async -> (decision: ManualCaptureDecision, still: AcceptedStill?) {
        guard let layout = m04SessionLayout, let stateData = try? Data(contentsOf: layout.state), let state = try? JSONDecoder().decode(PersistedSessionState.self, from: stateData), let evaluation = m04Evaluation else {
            let decision = evaluateManualCapture(monotonicTimestamp: monotonicTimestamp, cameraReady: false, sessionReady: false, sourceIntegrityReady: false, metadataReady: false, poseEvidenceReady: false)
            return (decision, nil)
        }
        let record = AcceptedCaptureRecord(captureID: captureID, sequence: state.nextSequence, sourceFilename: "\(captureID).heic", metadataFilename: "\(captureID).json")
        let poseReady = evaluation.input.pose?.aligned.status == "available" && evaluation.input.pose?.aligned.sample != nil
        let cameraReady = captureAdmissionService != nil && cameraRecoveryState != .denied && cameraRecoveryState != .unavailable && cameraRecoveryState != .failed
        let result = try? await captureAndPersistManual(captureID: captureID, monotonicTimestamp: monotonicTimestamp, cameraReady: cameraReady, sessionReady: state.sessionID == layout.sessionID, sourceIntegrityReady: evaluation.input.frame.isAvailable, metadataReady: true, poseEvidenceReady: poseReady, record: record, metadata: Data(), state: stateData, store: ScanSessionStore(layout: layout), poses: PoseBuffer(), motion: MotionBuffer())
        return result ?? (manualCaptureDecision ?? ManualCaptureDecision(allowed: false, warnings: [], blockingReasons: ["manual_capture_failed"]), nil)
    }

    func captureAndPersistTurntable(captureID: String = UUID().uuidString, angleDegrees: Double, monotonicTimestamp: TimeInterval = ProcessInfo.processInfo.systemUptime, record: AcceptedCaptureRecord, metadata: Data, state: Data, store: ScanSessionStore, poses: PoseBuffer, motion: MotionBuffer, bridge: TimestampDomainBridge? = nil) async throws -> (decision: AutoCaptureDecision, observation: TurntableObservation?, still: AcceptedStill?) {
        let decision = evaluateTurntableAngle(angleDegrees)
        guard decision.allowed else { return (decision, nil, nil) }
        guard let service = guidedAutoCaptureService else { throw CameraServiceError.failed("capture_backend_unavailable") }
        let result = await service.requestManual(captureID: captureID, monotonicTimestamp: monotonicTimestamp)
        guard case .accepted(let still) = result else { return (decision, nil, nil) }
        guard let observation = observeTurntableAngle(captureID: record.captureID, angleDegrees: angleDegrees) else { return (AutoCaptureDecision(allowed: false, reasons: ["turntable_angle_unavailable"]), nil, nil) }
        let enriched = AcceptedCaptureRecord(captureID: record.captureID, sequence: record.sequence, sourceFilename: record.sourceFilename, metadataFilename: record.metadataFilename, acceptedAt: record.acceptedAt, poseBinding: record.poseBinding, motionBinding: record.motionBinding, passMetadata: record.passMetadata, manualAudit: record.manualAudit, turntableEvidence: observation)
        let enrichedMetadata = (try? JSONEncoder().encode(enriched)) ?? metadata
        try await store.storeAcceptedCapture(still: still, record: enriched, metadata: enrichedMetadata, state: state, poses: poses, motion: motion, bridge: bridge)
        recordAcceptedCaptureCoverage(enriched)
        return (decision, observation, still)
    }

    func requestAutoCaptureAndPersist(captureID: String = UUID().uuidString, monotonicTimestamp: TimeInterval, record: AcceptedCaptureRecord, metadata: Data, state: Data, store: ScanSessionStore, poses: PoseBuffer, motion: MotionBuffer, bridge: TimestampDomainBridge? = nil) async throws -> (decision: AutoCaptureDecision, still: AcceptedStill?) {
        let outcome = await requestAutoCapture(captureID: captureID, monotonicTimestamp: monotonicTimestamp)
        guard case .accepted(let still) = outcome.result else { return (outcome.decision, nil) }
        try await store.storeAcceptedCapture(still: still, record: record, metadata: metadata, state: state, poses: poses, motion: motion, bridge: bridge)
        let evidence = AcceptedStillEvidenceBinder.bind(still: still, poses: poses, motion: motion, bridge: bridge)
        _ = recordAcceptedCaptureCoverage(AcceptedCaptureRecord(captureID: record.captureID, sequence: record.sequence, sourceFilename: record.sourceFilename, metadataFilename: record.metadataFilename, acceptedAt: record.acceptedAt, poseBinding: evidence.pose ?? record.poseBinding, motionBinding: evidence.motion ?? record.motionBinding, passMetadata: record.passMetadata, manualAudit: record.manualAudit, turntableEvidence: record.turntableEvidence))
        return (outcome.decision, still)
    }

    func captureAndPersistDetailPass(captureID: String = UUID().uuidString, passID: CapturePassID, quality: QualityDecision, framing: FramingMetric, poseBinding: PoseCaptureBinding?, duplicateDecision: DuplicateDecision?, record: AcceptedCaptureRecord, metadata: Data, state: Data, store: ScanSessionStore, poses: PoseBuffer, motion: MotionBuffer, bridge: TimestampDomainBridge? = nil) async throws -> (decision: DetailPassAcceptanceDecision, still: AcceptedStill?) {
        let decision = evaluateDetailPass(passID: passID, quality: quality, framing: framing, poseBinding: poseBinding, duplicateDecision: duplicateDecision)
        guard decision.allowed else { return (decision, nil) }
        guard let service = captureAdmissionService else { throw CameraServiceError.failed("capture_backend_unavailable") }
        let result = await service.capture(captureID: captureID)
        guard case .accepted(let still) = result else { return (decision, nil) }
        let detailRecord = AcceptedCaptureRecord(captureID: record.captureID, sequence: record.sequence, sourceFilename: record.sourceFilename, metadataFilename: record.metadataFilename, acceptedAt: record.acceptedAt, poseBinding: poseBinding ?? record.poseBinding, motionBinding: record.motionBinding, passMetadata: decision.metadata, manualAudit: record.manualAudit, turntableEvidence: record.turntableEvidence)
        let detailMetadata = (try? JSONEncoder().encode(detailRecord)) ?? metadata
        try await store.storeAcceptedCapture(still: still, record: detailRecord, metadata: detailMetadata, state: state, poses: poses, motion: motion, bridge: bridge)
        recordAcceptedCaptureCoverage(detailRecord)
        return (decision, still)
    }

    func captureAndPersistBasePass(captureID: String = UUID().uuidString, quality: QualityDecision, poseBinding: PoseCaptureBinding?, duplicateDecision: DuplicateDecision?, record: AcceptedCaptureRecord, metadata: Data, state: Data, store: ScanSessionStore, poses: PoseBuffer, motion: MotionBuffer, bridge: TimestampDomainBridge? = nil) async throws -> (decision: BasePassAcceptanceDecision, still: AcceptedStill?) {
        let decision = evaluateBasePass(quality: quality, poseBinding: poseBinding, duplicateDecision: duplicateDecision)
        guard decision.allowed else { return (decision, nil) }
        guard let service = captureAdmissionService else { throw CameraServiceError.failed("capture_backend_unavailable") }
        let result = await service.capture(captureID: captureID)
        guard case .accepted(let still) = result else { return (decision, nil) }
        let baseRecord = AcceptedCaptureRecord(captureID: record.captureID, sequence: record.sequence, sourceFilename: record.sourceFilename, metadataFilename: record.metadataFilename, acceptedAt: record.acceptedAt, poseBinding: poseBinding ?? record.poseBinding, motionBinding: record.motionBinding, passMetadata: CapturePassMetadata(passID: .base, required: false, evidenceStatus: decision.evaluation.status), manualAudit: record.manualAudit, turntableEvidence: record.turntableEvidence)
        let baseMetadata = (try? JSONEncoder().encode(baseRecord)) ?? metadata
        try await store.storeAcceptedCapture(still: still, record: baseRecord, metadata: baseMetadata, state: state, poses: poses, motion: motion, bridge: bridge)
        recordAcceptedCaptureCoverage(baseRecord)
        return (decision, still)
    }

    private func persistBasePassContext() async {
        guard let layout = m04SessionLayout, let existing = try? await M04SessionContextStore(layout: layout).load() else { return }
        let context = M04ScanContext(preset: existing.preset, preparationAcknowledged: existing.preparationAcknowledged, treatmentMode: existing.treatmentMode, preflight: existing.preflight, basePass: m04BasePass, completion: m04Completion, qualityGuidance: m04QualityGuidanceState, asymmetricCoverage: m04AsymmetricCoverage, turntableCoverage: m04TurntableCoverage, orbitCoverage: m04Coverage, detailPasses: makeM04DetailResumeState())
        try? await M04SessionContextStore(layout: layout).persist(context)
    }

    var m04QualityGuidanceState: M04QualityGuidanceState {
        M04QualityGuidanceState(presetID: m04ActivePreset.id, consecutiveHighlightBlocks: m04ConsecutiveHighlightBlocks, triggerThreshold: m04HighlightGuidanceThreshold, guidanceActive: !m04ReflectionGuidance.isEmpty, guidance: m04ReflectionGuidance)
    }

    private func updateM04QualityGuidance(_ evaluation: M04CandidateQualityEvaluation) {
        guard m04ActivePreset.id == .glossyPET else {
            m04ConsecutiveHighlightBlocks = 0
            m04ReflectionGuidance = []
            return
        }
        if evaluation.quality.metrics.highlightClipping.band == .reject {
            m04ConsecutiveHighlightBlocks += 1
        } else {
            m04ConsecutiveHighlightBlocks = 0
        }
        m04ReflectionGuidance = m04ConsecutiveHighlightBlocks >= m04HighlightGuidanceThreshold ? ["Repeated highlight clipping: move or diffuse the light, then reframe before capturing again."] : []
    }

    private func recomputeM04Completion() {
        let asymmetricMissing = m04AsymmetricCoverage?.missingRegions.map { "asymmetric_\($0.rawValue)" } ?? []
        let turntableMissing = m04TurntableCoverage?.missingSectorIndices.map { "turntable_sector_\($0)" } ?? []
        m04Completion = CompletionDiagnostics(rings: m04RingCoverage, detailPasses: Array(m04DetailEvaluations.values), base: m04BasePass, additionalMandatoryMissingAreas: asymmetricMissing + turntableMissing, additionalMandatoryAreaCount: (m04AsymmetricPolicy?.requiredRegions.count ?? 0) + (m04TurntableCoverage?.policy.expectedAngleCount ?? 0))
        Task { await persistBasePassContext() }
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
        _ = recordAcceptedCaptureCoverage(AcceptedCaptureRecord(captureID: record.captureID, sequence: record.sequence, sourceFilename: record.sourceFilename, metadataFilename: record.metadataFilename, acceptedAt: record.acceptedAt, poseBinding: evidence.pose ?? record.poseBinding, motionBinding: evidence.motion ?? record.motionBinding, passMetadata: record.passMetadata, manualAudit: record.manualAudit, turntableEvidence: record.turntableEvidence))
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

    var newScanReadiness: ScanRuntimeReadiness {
        let supportRoot = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first?.appendingPathComponent("PackLabSessions", isDirectory: true)
        let parent = supportRoot?.deletingLastPathComponent()
        let storageAvailable = supportRoot.map { FileManager.default.fileExists(atPath: $0.path) ? FileManager.default.isWritableFile(atPath: $0.path) : (parent.map { FileManager.default.isWritableFile(atPath: $0.path) } ?? false) } ?? false
        return ScanRuntimeReadiness(cameraReady: captureAdmissionService != nil && cameraRecoveryState == .running, sessionReady: isRunning, storageAvailable: storageAvailable, calibration: .ownerRequired)
    }

    deinit { updateTask?.cancel() }
}

struct ContentView: View {
    @State private var showPoseDebug = false
    @State private var showNewScan = false
    @State private var showResume = false
    @State private var showActiveProtocol = false
    @State private var turntableAngleText = "0"
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
                        Text("Preset: \(runtime.m04ActivePreset.displayName) v\(runtime.m04ActivePreset.version)")
                            .font(.caption2.monospaced()).foregroundStyle(.white)
                        ForEach(runtime.m04ReflectionGuidance, id: \.self) { Text($0) }
                        if let turntable = runtime.m04TurntableCoverage {
                            Text("Turntable: \(turntable.capturedSectorIndices.count)/\(turntable.policy.expectedAngleCount) sectors")
                            HStack {
                                TextField("Angle degrees", text: $turntableAngleText).keyboardType(.decimalPad)
                                Button("Record angle evidence") {
                                    if let angle = Double(turntableAngleText) { _ = runtime.observeTurntableAngle(captureID: UUID().uuidString, angleDegrees: angle) }
                                }
                            }
                            ForEach(turntable.missingSectorIndices, id: \.self) { Text("Missing turntable sector \($0)") }
                        }
                        CoverageGridView(model: CoverageViewModel(snapshot: runtime.m04Coverage, targeted: runtime.m04CoverageTarget))
                            .padding(8).background(.black.opacity(0.72), in: RoundedRectangle(cornerRadius: 8))
                            .padding(.horizontal, 8)
                        VStack(alignment: .leading, spacing: 2) {
                            ForEach(runtime.m04RingCoverage.statuses) { status in
                                Text("\(status.ringID): \(status.capturedSectorCount)/\(status.minimumSectorCount)\(status.missing ? " · missing" : " · ready")")
                            }
                            ForEach(runtime.m04RingCoverage.guidance, id: \.self) { Text($0) }
                            ForEach(runtime.m04DetailGuidance, id: \.self) { Text($0) }
                            Text("Base: \(runtime.m04BasePass.status)")
                            ForEach(runtime.m04BasePass.guidance, id: \.self) { Text($0) }
                            if let asymmetric = runtime.m04AsymmetricCoverage {
                                Text("Asymmetric: \(asymmetric.isComplete ? "complete" : "missing")")
                                ForEach(asymmetric.guidance, id: \.self) { Text($0) }
                            }
                            Text("Completion: \(Int(runtime.m04Completion.score * 100))% · \(runtime.m04Completion.status.rawValue)")
                            ForEach(runtime.m04Completion.mandatoryMissingAreas, id: \.self) { Text("Missing: \($0)") }
                            ForEach(runtime.m04Completion.optionalUnavailableAreas, id: \.self) { Text("Optional unavailable: \($0)") }
                            ForEach(runtime.m04Completion.guidance, id: \.self) { Text($0) }
                        }
                        .font(.caption2.monospaced()).foregroundStyle(.white)
                            .padding(.horizontal, 12)
                        Button("Manual Capture") {
                            Task { _ = await runtime.requestManualCapture() }
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(!runtime.admitCapture())
                        if let manual = runtime.manualCaptureDecision {
                            ForEach(manual.warnings, id: \.self) { Text("Manual warning: \($0)") }
                            ForEach(manual.blockingReasons, id: \.self) { Text("Manual blocked: \($0)") }
                        }
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
                ToolbarItem(placement: .topBarTrailing) { Button("Protocol") { showActiveProtocol = true } }
                ToolbarItem(placement: .topBarTrailing) { Button(showPoseDebug ? "Hide Debug" : "Show Debug") { showPoseDebug.toggle() } }
            }
            .sheet(isPresented: $showNewScan) { NavigationStack { NewScanWizard(admission: runtime.admission, readiness: runtime.newScanReadiness) { draft in
                Task { do { let layout = SessionStorageLayout(root: ContentView.sessionRoot, sessionID: draft.sessionID); let store = ScanSessionStore(layout: layout); try await store.create(draft); let preset = PackagingPresetCatalog.preset(for: draft.presetID ?? .matteHDPE); runtime.configureM04QualityRuntime(preset: preset, layout: layout); let context = M04ScanContext(preset: preset, preparationAcknowledged: draft.preflight?.preparationAcknowledged ?? false, treatmentMode: draft.treatmentMode?.rawValue, preflight: draft.preflight, basePass: runtime.m04BasePass, completion: runtime.m04Completion, qualityGuidance: runtime.m04QualityGuidanceState, asymmetricCoverage: runtime.m04AsymmetricCoverage, turntableCoverage: runtime.m04TurntableCoverage); try await M04SessionContextStore(layout: layout).persist(context); await ContentView.sessionRegistry.install(ActiveScanSession(draft: draft, state: PersistedSessionState(sessionID: draft.sessionID, nextSequence: 0, epoch: 0, acceptedIDs: []))) } catch { } }
                showNewScan = false
            } } }
            .sheet(isPresented: $showResume) { NavigationStack { SessionResumeView(root: ContentView.sessionRoot, onResume: { candidate in
                if let draft = candidate.draft, let state = candidate.state { let layout = SessionStorageLayout(root: ContentView.sessionRoot, sessionID: draft.sessionID); runtime.configureM04QualityRuntime(preset: PackagingPresetCatalog.preset(for: draft.presetID ?? .matteHDPE), layout: layout); Task { if let context = try? await M04SessionContextStore(layout: layout).load() { if let basePass = context.basePass { runtime.restoreBasePass(basePass) }; _ = runtime.restoreM04OrbitCoverage(context.orbitCoverage); _ = runtime.restoreM04DetailPassState(context.detailPasses); runtime.restoreQualityGuidance(context.qualityGuidance); runtime.restoreAsymmetricCoverage(context.asymmetricCoverage); runtime.restoreTurntableCoverage(context.turntableCoverage) }; await ContentView.sessionRegistry.install(ActiveScanSession(draft: draft, state: state)) } }
                showResume = false
            }, onDiscard: { candidate in
                Task { let plan = SessionDeletionPlan(root: ContentView.sessionRoot, candidate: candidate); _ = try? await SafeSessionDeleter().deleteDetailed(plan: plan, confirmed: true) }
                showResume = false
            }) } }
            .sheet(isPresented: $showActiveProtocol) {
                NavigationStack {
                    CaptureProtocolView(preset: runtime.m04ActivePreset) { _ in showActiveProtocol = false }
                }
            }
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
