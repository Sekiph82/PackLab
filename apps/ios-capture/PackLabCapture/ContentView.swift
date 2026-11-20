import SwiftUI
import Foundation
#if canImport(AVFoundation)
import AVFoundation
#endif
#if canImport(ARKit) && canImport(UIKit)
import ARKit
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
    /// True while one manual capture (shutter + session transaction + photo metadata) runs.
    @Published private(set) var manualCaptureInFlight = false
    /// Object the orbit is measured around; nil until the operator sets it (or after an AR reset).
    @Published private(set) var m04ObjectCenter: ObjectCenter?
    @Published private(set) var objectCenterMessage: String?
    /// Live camera position relative to the object (100 ms tracking poll), for the dial.
    @Published private(set) var m04LiveObservation: CoveragePoseObservation?
    @Published private(set) var m04Instruction: OrbitGuidanceInstruction = .setObjectCenter
    @Published private(set) var captureToast: CaptureToastMessage?
    @Published private(set) var m04ActivePreset = PackagingPresetCatalog.matteHDPE
    @Published private(set) var m04ReflectionGuidance: [String] = []
    @Published private(set) var m04AsymmetricCoverage: AsymmetricCoverageEvaluation?
    @Published private(set) var m04TurntableCoverage: TurntableCoverageSnapshot?
    private let trackingService: any ARTrackingService
    private let motionService: any MotionService
    private let healthMonitor: DeviceHealthMonitor
    private let automaticallyPoll: Bool
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
    private var m04PersistenceTask: Task<Void, Never>?
    private var m04AsymmetricPolicy: AsymmetricCoveragePolicy?
    private var m04AsymmetricObservedRegions: [AsymmetricCoverageRegion: Int] = [:]
    private var m04TurntableModel: TurntableCoverageModel?
    private var m04ConsecutiveHighlightBlocks = 0
    private let m04HighlightGuidanceThreshold = 3
    private var m04DetailEvaluations: [CapturePassID: DetailPassEvaluation] = [:]
    private var m04SortedDetailEvaluations: [DetailPassEvaluation] {
        m04DetailEvaluations.values.sorted { $0.metadata.passID.rawValue < $1.metadata.passID.rawValue }
    }
    private var m04DetailFraming: [CapturePassID: FramingMetric] = [:]
    private var m04AcceptedDuplicateEvidence: [DuplicateEvidence] = []
    private var cameraControlBridge: CameraControlRuntimeBridge?
    #if canImport(AVFoundation)
    let cameraRecoveryOwner = CameraRecoveryOwner()
    private var cameraControlComposition: AVFoundationCameraControlComposition?
    #endif
    private var isRunning = false
    private var controlObservationTick = 0
    /// Live candidate-quality loop (production camera only; nil in Simulator/tests).
    private var liveCandidateTask: Task<Void, Never>?
    private var liveFrameSource: (@MainActor () -> (frame: QualityImageFrame, timestamp: TimeInterval)?)?
    /// Shared AR pose buffer; binds candidate frames and accepted stills to their poses.
    private var capturePoseSource: (@MainActor () -> PoseBuffer)?
    /// Raycast from the screen centre into the AR world (production camera only).
    private var objectCenterSource: (@MainActor () -> ObjectCenter?)?
    /// Identity of the current AR world; a different value invalidates the object center.
    private var worldIdentitySource: (@MainActor () -> String?)?
    static let liveCandidateIntervalNanoseconds: UInt64 = 500_000_000
    /// Manual capture refuses quality/pose evidence older than this (seconds, uptime domain).
    static let maximumLiveEvidenceAge: TimeInterval = 2.0
    /// Candidate sequence for the quality log; never reset, so loop restarts cannot collide.
    private var liveCandidateSequence = 0

    init() {
        automaticallyPoll = true
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

    init(trackingService: any ARTrackingService, motionService: any MotionService, healthMonitor: DeviceHealthMonitor, automaticallyPoll: Bool = true) {
        self.trackingService = trackingService
        self.motionService = motionService
        self.healthMonitor = healthMonitor
        self.automaticallyPoll = automaticallyPoll
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
            await self?.applyHealthUpdate(gate)
        }
        updateTask?.cancel()
        if automaticallyPoll {
            updateTask = Task { [weak self] in
                while !Task.isCancelled {
                    await self?.refresh()
                    try? await Task.sleep(nanoseconds: 100_000_000)
                }
            }
        }
        if m04CoverageActive { startLiveCandidateLoop() }
        await refresh()
    }

    func stop() async {
        isRunning = false
        updateTask?.cancel()
        updateTask = nil
        stopLiveCandidateLoop()
        await healthMonitor.stop()
        await trackingService.stop()
        await motionService.stop()
    }

    func refresh() async {
        guard isRunning else { return }
        let raw = await trackingService.snapshot()
        _ = trackingRecoveryPolicy.update(state: raw.quality, limitation: raw.limitation)
        trackingDiagnostics = trackingRecoveryPolicy.diagnostics
        tracking = trackingRecoveryPolicy.snapshot
        pose = await trackingService.latestPose()
        motion = await motionService.latestRecord()
        updateOrbitGuidance()
        epoch = await trackingService.localizationEpoch()
        resetDiagnostics = await trackingService.resetDiagnostics()
        #if canImport(AVFoundation)
        observeCameraControlsIfDue()
        #endif
        await diagnostics.record(category: "tracking", code: raw.quality.rawValue, message: raw.message)
    }

    private func applyHealthUpdate(_ gate: DeviceHealthCaptureGate) async {
        health = gate
        admission.update(gate)
        if let captureAdmissionService { await captureAdmissionService.updateAdmission(admission) }
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
        m04DetailGuidance = m04DetailPolicies.values.sorted { $0.passID.rawValue < $1.passID.rawValue }.map { "Capture missing \($0.passID.rawValue) detail sectors" }
        m04BaseCoverageModel = OrbitCoverageModel(configuration: OrbitCoverageConfiguration(azimuthBinCount: 4, rings: [CoverageRingDefinition(id: "base", minimumElevation: -90, maximumElevation: 90)]))
        m04BaseAvailability = BasePassAvailability(physicallyFeasible: false, reasonCode: "base_pass_unavailable")
        m04BasePass = BasePassEvaluation(snapshot: m04BaseCoverageModel.snapshot(), availability: m04BaseAvailability)
        m04DetailEvaluations = [:]
        m04DetailFraming = [:]
        recomputeM04Completion()
        m04CoverageActive = true
        m04AcceptedDuplicateEvidence = []
        m04Evaluation = nil
        m04ObjectCenter = nil
        objectCenterMessage = nil
        m04LiveObservation = nil
        updateOrbitGuidance()
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
        for policy in m04DetailPolicies.values.sorted(by: { $0.passID.rawValue < $1.passID.rawValue }) {
            let framing = defaultDetailFraming(for: policy)
            let evaluation = DetailPassEvaluation(snapshot: m04DetailCoverageModels[policy.passID]?.snapshot() ?? OrbitCoverageModel(configuration: detailCoverageConfiguration(for: policy.passID)).snapshot(), framing: framing, policy: policy)
            m04DetailFraming[policy.passID] = framing
            m04DetailEvaluations[policy.passID] = evaluation
        }
        m04DetailGuidance = m04SortedDetailEvaluations.flatMap { $0.missingGuidance }
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
        m04DetailGuidance = restoredEvaluations.values.sorted { $0.metadata.passID.rawValue < $1.metadata.passID.rawValue }.flatMap { $0.missingGuidance }
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
        let center = m04ObjectCenter?.position
        let observation = m04CoverageModel.observe(captureID: record.captureID, poseBinding: record.poseBinding, center: center)
        m04Coverage = m04CoverageModel.snapshot()
        m04CoverageTarget = m04Coverage.missingSectors.first
        m04RingCoverage = RingCoverageEvaluation(snapshot: m04Coverage, policy: m04RingPolicy)
        m04AcceptedDuplicateEvidence.append(DuplicateEvidence(captureID: record.captureID, poseBinding: record.poseBinding))
        updateOrbitGuidance()
        if let passID = record.passMetadata?.passID, var detailModel = m04DetailCoverageModels[passID] {
            _ = detailModel.observe(captureID: record.captureID, poseBinding: record.poseBinding, center: center)
            m04DetailCoverageModels[passID] = detailModel
            if let policy = m04DetailPolicies[passID] {
                let evaluation = DetailPassEvaluation(snapshot: detailModel.snapshot(), framing: FramingMetric(availability: .available, objectFraction: policy.minimumFramingFraction, bounds: nil, margins: [:], band: .acceptable, reasons: []), policy: policy)
                m04DetailEvaluations[passID] = evaluation
                m04DetailGuidance = m04SortedDetailEvaluations.flatMap { $0.missingGuidance }
            }
        }
        if record.passMetadata?.passID == .base {
            _ = m04BaseCoverageModel.observe(captureID: record.captureID, poseBinding: record.poseBinding, center: center)
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
        let duplicateDecision = NearDuplicateDetector.evaluate(candidate: candidateEvidence, accepted: m04AcceptedDuplicateEvidence, configuration: m04Coverage.configuration, center: m04ObjectCenter?.position)
        return AutoCaptureInput(monotonicTimestamp: monotonicTimestamp, poseEligible: tracking.poseEvidenceEligible, targetSector: target, quality: evaluation.quality, overlapAllowed: overlapAllowed, duplicateDecision: duplicateDecision, admission: admission)
    }

    /// `recordDiagnostics: false` (the 2 Hz live loop) skips the candidate log and only
    /// persists the context when the quality-guidance state actually changed.
    @discardableResult
    func analyzeM04Candidate(_ input: M04CandidateFrameInput, recordDiagnostics: Bool = true) async -> M04CandidateQualityEvaluation {
        let evaluation = m04QualityRuntime.evaluate(input)
        m04Evaluation = evaluation
        let guidanceBefore = m04QualityGuidanceState
        updateM04QualityGuidance(evaluation)
        guard recordDiagnostics else {
            if m04QualityGuidanceState != guidanceBefore { await persistBasePassContext() }
            return evaluation
        }
        await persistBasePassContext()
        if let store = m04QualityLogStore {
            try? await store.append(QualityCandidateLog(sessionID: input.sessionID, captureID: input.captureID, sequence: input.sequence, monotonicTimestamp: input.monotonicTimestamp, decision: evaluation.quality))
        }
        return evaluation
    }

    /// Production candidate entry point. Motion is bound in the existing
    /// MotionService timestamp domain before the shared quality runtime runs.
    @discardableResult
    func analyzeM04Candidate(sessionID: String, captureID: String, sequence: Int, monotonicTimestamp: TimeInterval, frame: QualityImageFrame, pose: PoseCaptureBinding? = nil, recordDiagnostics: Bool = true) async -> M04CandidateQualityEvaluation {
        let motionBinding = await motionService.bindCandidateMotion(captureID: captureID, timestamp: monotonicTimestamp)
        return await analyzeM04Candidate(M04CandidateFrameInput(sessionID: sessionID, captureID: captureID, sequence: sequence, monotonicTimestamp: monotonicTimestamp, frame: frame, motion: motionBinding, pose: pose), recordDiagnostics: recordDiagnostics)
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
            // No live camera frame has been analyzed yet, so there is no quality or pose evidence.
            let decision = ManualCaptureDecision(allowed: false, warnings: [], blockingReasons: ["live_frame_unavailable", "pose_evidence_unavailable"])
            manualCaptureDecision = decision
            return decision
        }
        let automatic = autoCaptureInput(monotonicTimestamp: monotonicTimestamp).map { AutoCaptureController().evaluate($0) } ?? AutoCaptureDecision(allowed: false, reasons: ["quality_unavailable"])
        let decision = ManualCaptureCoordinator.evaluate(ManualCaptureInput(automaticDecision: automatic, quality: evaluation.quality, admission: admission, cameraReady: cameraReady, sessionReady: sessionReady, sourceIntegrityReady: sourceIntegrityReady, metadataReady: metadataReady, poseEvidenceReady: poseEvidenceReady))
        manualCaptureDecision = decision
        return decision
    }

    /// `photoLayout`, when given, also appends the accepted still to the session's PackScan
    /// `metadata/photos.json` contract that finalization requires. The binding is validated
    /// before the session transaction so an unbindable still commits nothing, and a failed
    /// append rolls the committed capture back so no record exists without its metadata.
    /// Empty `poses`/`motion` buffers fall back to the live AR pose buffer and CoreMotion
    /// records read after the shutter, so the still binds to its own frame's pose.
    func captureAndPersistManual(captureID: String = UUID().uuidString, monotonicTimestamp: TimeInterval, cameraReady: Bool, sessionReady: Bool, sourceIntegrityReady: Bool, metadataReady: Bool, poseEvidenceReady: Bool, record: AcceptedCaptureRecord, metadata: Data, state: Data, store: ScanSessionStore, poses: PoseBuffer, motion: MotionBuffer, bridge: TimestampDomainBridge? = nil, photoLayout: SessionStorageLayout? = nil) async throws -> (decision: ManualCaptureDecision, still: AcceptedStill?) {
        let decision = evaluateManualCapture(monotonicTimestamp: monotonicTimestamp, cameraReady: cameraReady, sessionReady: sessionReady, sourceIntegrityReady: sourceIntegrityReady, metadataReady: metadataReady, poseEvidenceReady: poseEvidenceReady)
        let audit = ManualCaptureAudit(decision: decision)
        if let evaluation = m04Evaluation, let logStore = m04QualityLogStore {
            try? await logStore.append(QualityCandidateLog(sessionID: evaluation.input.sessionID, captureID: captureID, sequence: record.sequence, monotonicTimestamp: monotonicTimestamp, decision: evaluation.quality, manualAudit: audit))
        }
        guard decision.allowed else { return (decision, nil) }
        guard let service = guidedAutoCaptureService else { throw CameraServiceError.failed("capture_backend_unavailable") }
        let result = await service.requestManual(captureID: captureID, monotonicTimestamp: monotonicTimestamp)
        guard case .accepted(let still) = result else { return (decision, nil) }
        var pendingPhoto: (metadata: PhotoCaptureMetadata, source: OriginalSourceRecord)?
        if photoLayout != nil { pendingPhoto = try manualPhotoMetadata(still: still, record: record) }
        let posesAtCapture = poses.samples.isEmpty ? (capturePoseSource?() ?? poses) : poses
        var motionAtCapture = motion
        if motionAtCapture.samples.isEmpty { for sample in await motionService.records() { motionAtCapture.append(sample) } }
        let evidence = AcceptedStillEvidenceBinder.bind(still: still, poses: posesAtCapture, motion: motionAtCapture, bridge: bridge)
        let manualRecord = AcceptedCaptureRecord(captureID: record.captureID, sequence: record.sequence, sourceFilename: record.sourceFilename, metadataFilename: record.metadataFilename, acceptedAt: record.acceptedAt, poseBinding: evidence.pose ?? record.poseBinding, motionBinding: evidence.motion ?? record.motionBinding, passMetadata: record.passMetadata, manualAudit: audit, turntableEvidence: record.turntableEvidence)
        let manualMetadata = (try? JSONEncoder().encode(manualRecord)) ?? metadata
        try await store.storeAcceptedCapture(still: still, record: manualRecord, metadata: manualMetadata, state: state, poses: posesAtCapture, motion: motionAtCapture, bridge: bridge)
        if let photoLayout, let pendingPhoto {
            do {
                try await AcceptedPhotoMetadataStore(sourceRoot: photoLayout.images, metadataURL: photoLayout.photoMetadata).appendForCommittedSource(metadata: pendingPhoto.metadata, source: pendingPhoto.source, bytes: still.sourceBytes)
            } catch {
                // ponytail: rollback, not one transaction; a crash between commit and append still
                // leaves a record without photo metadata (finalize then refuses the session).
                try? await SessionGalleryStore(layout: photoLayout).delete(id: record.captureID, confirmed: true)
                throw error
            }
        }
        recordAcceptedCaptureCoverage(manualRecord)
        return (decision, still)
    }

    /// PackScan photo metadata for a manual still. Orientation is derived from the stored
    /// pixel dimensions (AR stills are written with EXIF orientation 1); focal length is not
    /// claimed, and exposure/white balance are recorded only when the device reports them.
    private func manualPhotoMetadata(still: AcceptedStill, record: AcceptedCaptureRecord) throws -> (metadata: PhotoCaptureMetadata, source: OriginalSourceRecord) {
        let width = still.dimensions.width, height = still.dimensions.height
        let orientation = width > height ? "landscape" : (width < height ? "portrait" : "square")
        let source = try OriginalSourceRecord.fromSource(captureID: still.captureID, filename: record.sourceFilename, dimensions: still.dimensions, orientation: orientation, bytes: still.sourceBytes)
        let lens = controls.state.lens ?? CameraLensIdentity(identifier: "unavailable", position: .unspecified, kind: .other)
        let base = PhotoCaptureMetadata(photoID: still.captureID, imagePath: "images/\(record.sourceFilename)", sequence: record.sequence, originalFilename: record.sourceFilename, pixelDimensions: still.dimensions, orientation: orientation, lensIdentity: lens, focalLengthMM: SourceMeasurement(status: .unavailable), exposureSeconds: SourceMeasurement(status: .unavailable), iso: SourceMeasurement(status: .unavailable), whiteBalanceKelvin: SourceMeasurement(status: .unavailable), captureTimestamp: still.capturedAt)
        #if canImport(AVFoundation)
        // Readings are optional evidence: an unreadable exposure/WB keeps the honest "unavailable".
        let photo = cameraControlComposition.flatMap { try? $0.acceptedMetadata(base) } ?? base
        #else
        let photo = base
        #endif
        try PhotoMetadataBinding.validate(metadata: photo, source: source, bytes: still.sourceBytes)
        _ = try PackScanPhotoMetadataWire.from(photo)
        return (photo, source)
    }

    func requestManualCapture(captureID: String = UUID().uuidString, monotonicTimestamp: TimeInterval = ProcessInfo.processInfo.systemUptime) async -> (decision: ManualCaptureDecision, still: AcceptedStill?) {
        // One capture at a time: the next one must read the state the previous one committed.
        guard !manualCaptureInFlight else { return (ManualCaptureDecision(allowed: false, warnings: [], blockingReasons: ["capture_in_flight"]), nil) }
        manualCaptureInFlight = true
        defer { manualCaptureInFlight = false }
        let coveredBefore = m04Coverage.capturedSectors.count
        let outcome = await performManualCapture(captureID: captureID, monotonicTimestamp: monotonicTimestamp)
        let coveredAfter = m04Coverage.capturedSectors.count
        let observation = m04Coverage.observations.last { $0.captureID == captureID }
        let hint = outcome.decision.blockingReasons.first.map { ContentView.manualBlockHint($0) }
        showCaptureToast(CaptureToast.text(decision: outcome.decision, saved: outcome.still != nil, observation: observation, newlyCovered: coveredAfter > coveredBefore, capturedCount: coveredAfter, totalCount: coveredAfter + m04Coverage.missingSectors.count, blockHint: hint))
        return outcome
    }

    private func performManualCapture(captureID: String, monotonicTimestamp: TimeInterval) async -> (decision: ManualCaptureDecision, still: AcceptedStill?) {
        guard let layout = m04SessionLayout, let stateData = try? Data(contentsOf: layout.state), let state = try? JSONDecoder().decode(PersistedSessionState.self, from: stateData) else {
            return (publishManualBlock(["session_not_ready"]), nil)
        }
        // Orbit coverage is measured around the object, so it must be set first (not for turntable).
        validateObjectCenterWorld()
        if m04ObjectCenter == nil && m04ActivePreset.id != .turntable {
            return (publishManualBlock(["object_center_unset"] + (m04Evaluation == nil ? ["live_frame_unavailable"] : [])), nil)
        }
        guard let evaluation = m04Evaluation else {
            return (evaluateManualCapture(monotonicTimestamp: monotonicTimestamp, cameraReady: false, sessionReady: false, sourceIntegrityReady: false, metadataReady: false, poseEvidenceReady: false), nil)
        }
        let evidenceAge = monotonicTimestamp - evaluation.input.monotonicTimestamp
        guard evidenceAge.isFinite, evidenceAge <= CaptureRuntimeViewModel.maximumLiveEvidenceAge else {
            return (publishManualBlock(["live_frame_stale"]), nil)
        }
        let record = AcceptedCaptureRecord(captureID: captureID, sequence: state.nextSequence, sourceFilename: "\(captureID).heic", metadataFilename: "\(captureID).json")
        // The committed state advances with the accepted capture (same transaction).
        let next = PersistedSessionState(sessionID: state.sessionID, schemaVersion: state.schemaVersion, nextSequence: state.nextSequence + 1, epoch: state.epoch, acceptedIDs: state.acceptedIDs + [captureID], rejectedIDs: state.rejectedIDs, replacementTrace: state.replacementTrace)
        let poseReady = evaluation.input.pose?.aligned.status == "available" && evaluation.input.pose?.aligned.sample != nil
        let cameraReady = captureAdmissionService != nil && cameraRecoveryState != .denied && cameraRecoveryState != .unavailable && cameraRecoveryState != .failed && cameraRecoveryState != .blocked
        do {
            let nextData = try JSONEncoder().encode(next)
            return try await captureAndPersistManual(captureID: captureID, monotonicTimestamp: monotonicTimestamp, cameraReady: cameraReady, sessionReady: state.sessionID == layout.sessionID, sourceIntegrityReady: evaluation.input.frame.isAvailable, metadataReady: true, poseEvidenceReady: poseReady, record: record, metadata: Data(), state: nextData, store: ScanSessionStore(layout: layout), poses: PoseBuffer(), motion: MotionBuffer(), photoLayout: layout)
        } catch {
            return (publishManualBlock(["capture_persist_failed"]), nil)
        }
    }

    private func showCaptureToast(_ text: String) {
        let message = CaptureToastMessage(text: text)
        captureToast = message
        Task { [weak self] in
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            if self?.captureToast == message { self?.captureToast = nil }
        }
    }

    // MARK: Object center and live orbit guidance

    /// Injection seam: production binds the shared ARSession raycast and world identity.
    func bindObjectCenterSources(center: (@MainActor () -> ObjectCenter?)?, worldIdentity: (@MainActor () -> String?)?) {
        objectCenterSource = center
        worldIdentitySource = worldIdentity
    }

    /// Raycasts from the crosshair (screen centre) and, on a hit, makes it the object center.
    @discardableResult
    func setObjectCenterFromScreenCenter() async -> Bool {
        guard let source = objectCenterSource else {
            objectCenterMessage = "Object center needs the camera (not available here)"
            return false
        }
        guard let center = source() else {
            objectCenterMessage = "No surface found at the crosshair — move a little closer, keep the package in good light and try again"
            return false
        }
        return await setObjectCenter(center)
    }

    @discardableResult
    func setObjectCenter(_ center: ObjectCenter) async -> Bool {
        guard center.isValid else { objectCenterMessage = "Object center was not measurable — try again"; return false }
        m04ObjectCenter = center
        objectCenterMessage = "Object center set"
        updateOrbitGuidance()
        await persistBasePassContext()
        return true
    }

    /// Resume: a stored center is only valid inside the same AR world.
    func restoreObjectCenter(_ center: ObjectCenter?) {
        guard let center else { return }
        if center.isValid, let current = worldIdentitySource?(), current == center.worldIdentity {
            m04ObjectCenter = center
            objectCenterMessage = nil
        } else {
            m04ObjectCenter = nil
            objectCenterMessage = "The AR session restarted — set the object center again"
        }
        updateOrbitGuidance()
    }

    /// Drops the center once the AR world it was measured in is gone (tracking reset, new session).
    private func validateObjectCenterWorld() {
        guard let center = m04ObjectCenter, let current = worldIdentitySource?(), current != center.worldIdentity else { return }
        m04ObjectCenter = nil
        objectCenterMessage = "AR tracking was reset — set the object center again"
    }

    private func updateOrbitGuidance() {
        validateObjectCenterWorld()
        let configuration = m04Coverage.configuration
        let live: CoveragePoseObservation? = m04ObjectCenter.map { CoveragePoseMapper.map(captureID: "live", pose: pose, configuration: configuration, center: $0.position) }
        if live != m04LiveObservation { m04LiveObservation = live }
        if m04ObjectCenter != nil, live?.azimuthDegrees != nil {
            let target = OrbitGuidance.nextTarget(snapshot: m04Coverage, current: live)
            if target != m04CoverageTarget { m04CoverageTarget = target }
        }
        let instruction = OrbitGuidance.instruction(current: live, target: m04CoverageTarget, configuration: configuration, centerSet: m04ObjectCenter != nil)
        if instruction != m04Instruction { m04Instruction = instruction }
    }

    private func publishManualBlock(_ reasons: [String]) -> ManualCaptureDecision {
        let decision = ManualCaptureDecision(allowed: false, warnings: [], blockingReasons: reasons)
        manualCaptureDecision = decision
        return decision
    }

    /// Ends live capture for a session that was finalized or discarded: no further candidate
    /// logs, context writes or captures may land in it.
    func endActiveSession(sessionID: String) {
        guard m04SessionLayout?.sessionID == sessionID else { return }
        stopLiveCandidateLoop()
        m04CoverageActive = false
        m04SessionLayout = nil
        m04QualityLogStore = nil
        m04Evaluation = nil
        manualCaptureDecision = nil
        m04ObjectCenter = nil
        m04LiveObservation = nil
    }

    // MARK: Live candidate loop

    /// Starts the ~2 Hz live candidate-quality loop. A no-op without a production camera
    /// frame source (Simulator, tests). Ticks run sequentially, never overlapping.
    func startLiveCandidateLoop() {
        stopLiveCandidateLoop()
        guard liveFrameSource != nil else { return }
        liveCandidateTask = Task { [weak self] in
            while !Task.isCancelled {
                guard let model = self else { return }
                await model.analyzeLiveCandidateFrame()
                try? await Task.sleep(nanoseconds: CaptureRuntimeViewModel.liveCandidateIntervalNanoseconds)
            }
        }
    }

    func stopLiveCandidateLoop() {
        liveCandidateTask?.cancel()
        liveCandidateTask = nil
    }

    /// Injection seam shared by production (bindProductionARCamera) and tests.
    func bindLiveCandidateSources(frame: (@MainActor () -> (frame: QualityImageFrame, timestamp: TimeInterval)?)?, poses: (@MainActor () -> PoseBuffer)?) {
        liveFrameSource = frame
        capturePoseSource = poses
    }

    /// One live-loop tick: the current camera frame, bound to its AR pose in the
    /// ARFrame timestamp domain, goes through the production analyzeM04Candidate entry.
    @discardableResult
    func analyzeLiveCandidateFrame() async -> M04CandidateQualityEvaluation? {
        guard m04CoverageActive, let layout = m04SessionLayout, let live = liveFrameSource?() else { return nil }
        let sequence = liveCandidateSequence
        liveCandidateSequence += 1
        let candidateID = UUID().uuidString
        let pose = capturePoseSource?().bind(captureID: candidateID, timestamp: live.timestamp)
        return await analyzeM04Candidate(sessionID: layout.sessionID, captureID: candidateID, sequence: sequence, monotonicTimestamp: live.timestamp, frame: live.frame, pose: pose, recordDiagnostics: false)
    }

    func captureAndPersistTurntable(captureID: String = UUID().uuidString, angleDegrees: Double, monotonicTimestamp: TimeInterval = ProcessInfo.processInfo.systemUptime, record: AcceptedCaptureRecord, metadata: Data, state: Data, store: ScanSessionStore, poses: PoseBuffer, motion: MotionBuffer, bridge: TimestampDomainBridge? = nil) async throws -> (decision: AutoCaptureDecision, observation: TurntableObservation?, still: AcceptedStill?) {
        let decision = evaluateTurntableAngle(angleDegrees)
        guard decision.allowed else { return (decision, nil, nil) }
        guard let service = guidedAutoCaptureService else { throw CameraServiceError.failed("capture_backend_unavailable") }
        let result = await service.requestManual(captureID: captureID, monotonicTimestamp: monotonicTimestamp)
        guard case .accepted(let still) = result else { return (decision, nil, nil) }
        guard let observation = observeTurntableAngle(captureID: record.captureID, angleDegrees: angleDegrees) else { return (AutoCaptureDecision(allowed: false, reasons: ["turntable_angle_unavailable"]), nil, nil) }
        let evidence = AcceptedStillEvidenceBinder.bind(still: still, poses: poses, motion: motion, bridge: bridge)
        let motionBinding = evidence.motion?.status == "available" ? evidence.motion : (record.motionBinding ?? evidence.motion)
        let enriched = AcceptedCaptureRecord(captureID: record.captureID, sequence: record.sequence, sourceFilename: record.sourceFilename, metadataFilename: record.metadataFilename, acceptedAt: record.acceptedAt, poseBinding: record.poseBinding, motionBinding: motionBinding, passMetadata: record.passMetadata, manualAudit: record.manualAudit, turntableEvidence: observation)
        let enrichedMetadata = (try? JSONEncoder().encode(enriched)) ?? metadata
        // Turntable angle evidence is an independent coverage source. Preserve
        // caller-provided pose evidence without synthesizing an unavailable AR
        // pose binding from the shutter timestamp.
        try await store.storeAcceptedCapture(source: still.sourceBytes, record: enriched, metadata: enrichedMetadata, state: state)
        recordAcceptedCaptureCoverage(enriched)
        await waitForM04ContextPersistence()
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
        await waitForM04ContextPersistence()
        return (decision, still)
    }

    private func persistBasePassContext() async {
        guard let layout = m04SessionLayout, let existing = try? await M04SessionContextStore(layout: layout).load() else { return }
        let context = M04ScanContext(preset: existing.preset, preparationAcknowledged: existing.preparationAcknowledged, treatmentMode: existing.treatmentMode, preflight: existing.preflight, basePass: m04BasePass, completion: m04Completion, qualityGuidance: m04QualityGuidanceState, asymmetricCoverage: m04AsymmetricCoverage, turntableCoverage: m04TurntableCoverage, orbitCoverage: m04Coverage, detailPasses: makeM04DetailResumeState(), objectCenter: m04ObjectCenter)
        try? await M04SessionContextStore(layout: layout).persist(context)
    }

    private func scheduleM04ContextPersistence() {
        let previous = m04PersistenceTask
        m04PersistenceTask = Task { [weak self] in
            await previous?.value
            await self?.persistBasePassContext()
        }
    }

    func waitForM04ContextPersistence() async {
        await m04PersistenceTask?.value
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
        m04Completion = CompletionDiagnostics(rings: m04RingCoverage, detailPasses: m04SortedDetailEvaluations, base: m04BasePass, additionalMandatoryMissingAreas: asymmetricMissing + turntableMissing, additionalMandatoryAreaCount: (m04AsymmetricPolicy?.requiredRegions.count ?? 0) + (m04TurntableCoverage?.policy.expectedAngleCount ?? 0))
        scheduleM04ContextPersistence()
    }

    #if canImport(ARKit) && canImport(UIKit) && canImport(AVFoundation)
    /// Production camera composition: the shared ARSession is the only camera client.
    /// Preview, tracking, still capture, recovery and pairing hand-off all go through it.
    func bindProductionARCamera(owner: SharedARSessionOwner = .shared) async {
        let recovery = cameraRecoveryOwner
        owner.onCameraSignal = { [weak self] signal in
            recovery.handle(signal)
            if signal == .started || signal == .restartSucceeded { self?.configureARCameraControls() }
        }
        // An operator Retry is logged as user-requested; other restarts follow a runtime error.
        recovery.setSessionRestart { [weak owner, weak recovery] in
            owner?.restartCamera(reason: recovery?.restartTrigger == .retry ? .userRequested : .runtimeError)
        }
        // QR pairing opens its own AVCaptureSession, so it must pause the AR session first.
        ProductionCaptureCameraLifecycle.shared.install(stop: { [weak owner] in
            guard let owner else { return false }
            owner.stop()
            return true
        }, restore: { [weak owner] in owner?.start() })
        await bindStillCaptureBackend(ARSessionStillCaptureBackend(source: owner, recordPose: { [weak owner] sample in owner?.recordCapturePose(sample) }))
        #if !targetEnvironment(simulator)
        // Live candidate frames and pose evidence come from the same shared ARSession.
        bindLiveCandidateSources(frame: { [weak owner] in owner?.currentCandidateFrame() }, poses: { [weak owner] in owner?.poseBuffer ?? PoseBuffer() })
        bindObjectCenterSources(center: { [weak owner] in owner?.raycastObjectCenter() }, worldIdentity: { [weak owner] in owner?.worldIdentity })
        #endif
    }

    /// Focus/exposure/WB are reported from the AVCaptureDevice ARKit itself drives
    /// (configurableCaptureDeviceForPrimaryCamera). They stay in continuous auto mode:
    /// ARKit manages them for tracking, so no lock is applied while AR runs.
    private func configureARCameraControls() {
        #if !targetEnvironment(simulator)
        guard let device = ARWorldTrackingConfiguration.configurableCaptureDeviceForPrimaryCamera,
              case .selected(let lens) = CameraDeviceSelector.selectMainRearWide(from: AVFoundationCameraDiscovery.rearCandidates()),
              lens.identifier == device.uniqueID else {
            updateControlState(lens: nil, focus: .unavailable, exposure: .unavailable, whiteBalance: .unavailable, message: "ARKit does not expose this camera's controls; focus, exposure and white balance are automatic.")
            return
        }
        if cameraControlComposition == nil {
            let controls = AVFoundationCameraControlComposition(device: device, selectedLens: lens)
            cameraControlComposition = controls
            bindCameraControls(controls.controls)
        }
        guard let composition = cameraControlComposition else { return }
        composition.configureFocus()
        composition.configureExposure(bias: 0)
        composition.configureWhiteBalance()
        composition.controls.setMessage("ARKit-managed auto focus, exposure and white balance (locks not applied during AR tracking)")
        #endif
    }
    #endif

    #if canImport(AVFoundation)
    /// Focus readout from the ARKit-driven device, polled about once a second (every 10th
    /// 100 ms refresh) and published only when it changes. A failed read keeps the last
    /// state and the ARKit-managed note instead of overwriting them. White balance has no
    /// settled observable state (the adapter always reports stabilizing), so it is not polled.
    private func observeCameraControlsIfDue() {
        controlObservationTick += 1
        guard controlObservationTick % 10 == 0, let composition = cameraControlComposition,
              let focus = try? AVFoundationFocusAdapter.observe(driver: composition.coordinator.driver, coordinator: composition.coordinator),
              focus != composition.controls.state.focus else { return }
        composition.controls.setFocus(focus)
    }
    #endif

    func retryCamera() {
        #if canImport(AVFoundation)
        cameraRecoveryOwner.retry()
        #endif
    }

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
        // Application Support does not exist on a fresh install; create the session root so a
        // first launch is not misreported as unwritable storage.
        let fm = FileManager.default
        let storageAvailable: Bool = {
            guard let root = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask).first?.appendingPathComponent("PackLabSessions", isDirectory: true) else { return false }
            try? fm.createDirectory(at: root, withIntermediateDirectories: true)
            return fm.isWritableFile(atPath: root.path)
        }()
        return ScanRuntimeReadiness(cameraReady: captureAdmissionService != nil && cameraRecoveryState == .running, sessionReady: isRunning, storageAvailable: storageAvailable, calibration: .ownerRequired)
    }

    deinit { updateTask?.cancel(); liveCandidateTask?.cancel() }
}

struct ContentView: View {
    @State private var showPoseDebug = false
    @State private var showNewScan = false
    @State private var scanStartError: String?
    @State private var showResume = false
    @State private var showActiveProtocol = false
    @State private var showHistory = false
    @State private var showARPreview = false
    @State private var turntableAngleText = "0"
    @StateObject private var runtime: CaptureRuntimeViewModel
    /// Layout-test seam: receives named element frames ("manualCapture", "guidanceDial") in
    /// window coordinates.
    private let onLayoutFrame: (@MainActor (String, CGRect) -> Void)?

    init() {
        _runtime = StateObject(wrappedValue: CaptureRuntimeViewModel())
        onLayoutFrame = nil
    }

    /// Hosts an already-configured runtime (layout tests); production uses `init()`.
    init(runtime: CaptureRuntimeViewModel, onLayoutFrame: (@MainActor (String, CGRect) -> Void)? = nil) {
        _runtime = StateObject(wrappedValue: runtime)
        self.onLayoutFrame = onLayoutFrame
    }

    private var orbitGuidanceActive: Bool { runtime.m04CoverageActive && runtime.m04ActivePreset.id != .turntable }

    private func frameReporter(_ key: String) -> some View {
        GeometryReader { proxy in
            Color.clear
                .onAppear { onLayoutFrame?(key, proxy.frame(in: .global)) }
                .onChange(of: proxy.frame(in: .global)) { _, frame in onLayoutFrame?(key, frame) }
        }
    }

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
                #elseif canImport(RealityKit) && canImport(ARKit)
                SharedARCameraPreview().ignoresSafeArea()
                #endif

                if orbitGuidanceActive {
                    // Crosshair at the image centre: "Set object center" raycasts through this point.
                    Image(systemName: "plus").font(.system(size: 34, weight: .light)).foregroundStyle(.yellow)
                        .frame(maxWidth: .infinity, maxHeight: .infinity).ignoresSafeArea()
                        .allowsHitTesting(false).accessibilityHidden(true)
                }

                VStack {
                    if let healthMessage = runtime.healthMessage {
                        Text(healthMessage).font(.caption).multilineTextAlignment(.center)
                            .padding(8).background(.black.opacity(0.72), in: Capsule()).foregroundStyle(.white).padding(.top)
                    }
                    if let scanStartError {
                        Text(scanStartError).font(.caption).multilineTextAlignment(.center)
                            .padding(8).background(.red.opacity(0.8), in: RoundedRectangle(cornerRadius: 8)).foregroundStyle(.white).padding(.horizontal)
                            .onTapGesture { self.scanStartError = nil }
                            .accessibilityHint("Tap to dismiss")
                    }
                    if !runtime.cameraRecoveryMessage.isEmpty {
                        VStack(spacing: 6) {
                            Text(runtime.cameraRecoveryMessage).font(.caption).multilineTextAlignment(.center)
                            if runtime.cameraRecoveryState == .blocked || runtime.cameraRecoveryState == .failed {
                                Button("Retry camera") { runtime.retryCamera() }.buttonStyle(.borderedProminent)
                            }
                        }
                        .padding(8).background(.black.opacity(0.72), in: RoundedRectangle(cornerRadius: 8)).foregroundStyle(.white).padding(.horizontal)
                    }
                    Text("Focus: \(runtime.controls.state.focus.rawValue) · Exposure: \(runtime.controls.state.exposure.rawValue) · WB: \(runtime.controls.state.whiteBalance.rawValue)").font(.caption2).foregroundStyle(.white).padding(.top, 4)
                    if let controlNote = runtime.controls.state.message {
                        Text(controlNote).font(.caption2).foregroundStyle(.white.opacity(0.8)).multilineTextAlignment(.center).padding(.horizontal)
                    }
                    if orbitGuidanceActive {
                        // Primary guidance: where to stand and what to do next.
                        VStack(spacing: 6) {
                            OrbitGuidanceDial(snapshot: runtime.m04Coverage, target: runtime.m04CoverageTarget, current: runtime.m04LiveObservation)
                            Text(runtime.m04Instruction.text).font(.callout.weight(.semibold)).multilineTextAlignment(.center)
                            if let message = runtime.objectCenterMessage { Text(message).font(.caption2).multilineTextAlignment(.center) }
                        }
                        .foregroundStyle(.white)
                        .padding(8).background(.black.opacity(0.72), in: RoundedRectangle(cornerRadius: 10)).padding(.horizontal)
                        .background(frameReporter("guidanceDial"))
                    }
                    if runtime.m04CoverageActive {
                        // Coverage detail can exceed the screen height; keep it in a bounded scroll
                        // area so the Manual Capture button below stays visible on an iPhone. The grid
                        // the operator walks by comes first; diagnostic readouts follow.
                        ScrollView {
                        VStack(spacing: 4) {
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
                        if let manual = runtime.manualCaptureDecision, !manual.warnings.isEmpty {
                            VStack(alignment: .leading, spacing: 2) {
                                ForEach(manual.warnings, id: \.self) { Text("Manual warning: \($0)") }
                            }
                            .font(.caption2.monospaced()).foregroundStyle(.white).padding(.horizontal, 12)
                        }
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
                        }
                        }
                        .frame(maxHeight: 200)
                        HStack(spacing: 12) {
                            if orbitGuidanceActive {
                                Button(runtime.m04ObjectCenter == nil ? "Set object center" : "Reset center") {
                                    Task { await runtime.setObjectCenterFromScreenCenter() }
                                }
                                .buttonStyle(.bordered).tint(.white)
                                .accessibilityIdentifier("setObjectCenterButton")
                            }
                            Button("Manual Capture") {
                                Task { _ = await runtime.requestManualCapture() }
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(!runtime.admitCapture() || runtime.manualCaptureInFlight)
                            .accessibilityIdentifier("manualCaptureButton")
                            .background(frameReporter("manualCapture"))
                        }
                        // Only blocking reasons stay under the button, on a dark plate readable over the camera.
                        if let manual = runtime.manualCaptureDecision, !manual.blockingReasons.isEmpty {
                            VStack(alignment: .leading, spacing: 2) {
                                ForEach(manual.blockingReasons, id: \.self) { Text("Manual blocked: \(ContentView.manualBlockHint($0))") }
                            }
                            .font(.caption).foregroundStyle(.white)
                            .padding(8).background(.black.opacity(0.72), in: RoundedRectangle(cornerRadius: 8)).padding(.horizontal)
                        }
                        if let toast = runtime.captureToast {
                            Text(toast.text).font(.callout).foregroundStyle(.white).multilineTextAlignment(.center)
                                .padding(10).background(.black.opacity(0.85), in: RoundedRectangle(cornerRadius: 10)).padding(.horizontal)
                                .accessibilityIdentifier("captureToast")
                        }
                    }
                    Spacer()
                    if runtime.tracking.poseEvidenceEligible == false {
                        Text(runtime.tracking.message).font(.caption)
                            .padding(8).background(.black.opacity(0.65), in: Capsule()).foregroundStyle(.white).padding()
                    } else {
                        Text(runtime.m04CoverageActive ? "Use Manual Capture to take photos" : "Tap New Scan to start a scan").font(.headline)
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
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                // Only the primary action stays in the bar; the rest share one menu so the
                // toolbar fits an iPhone portrait width.
                ToolbarItem(placement: .topBarLeading) { Button("New Scan") { showNewScan = true } }
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button("History", systemImage: "clock") { showHistory = true }
                        Button("Protocol", systemImage: "list.bullet.rectangle") { showActiveProtocol = true }
                        if ARPreviewFeatureFlag.isEnabled() {
                            Button("AR Preview", systemImage: "arkit") { showARPreview = true }
                        }
                        Button(showPoseDebug ? "Hide Debug" : "Show Debug", systemImage: "ladybug") { showPoseDebug.toggle() }
                    } label: {
                        Label("More", systemImage: "ellipsis.circle")
                    }
                    .accessibilityLabel("More actions")
                    .accessibilityHint(ARPreviewFeatureFlag.isEnabled() ? "History, protocol, AR preview and debug overlay" : "History, protocol and debug overlay")
                }
            }
            .sheet(isPresented: $showNewScan) { NavigationStack { NewScanWizard(admission: runtime.admission, readiness: runtime.newScanReadiness) { draft in
                Task { do { let layout = SessionStorageLayout(root: ContentView.sessionRoot, sessionID: draft.sessionID); let store = ScanSessionStore(layout: layout); try await store.create(draft); let preset = PackagingPresetCatalog.preset(for: draft.presetID ?? .matteHDPE); runtime.configureM04QualityRuntime(preset: preset, layout: layout); runtime.startLiveCandidateLoop(); let context = M04ScanContext(preset: preset, preparationAcknowledged: draft.preflight?.preparationAcknowledged ?? false, treatmentMode: draft.treatmentMode?.rawValue, preflight: draft.preflight, basePass: runtime.m04BasePass, completion: runtime.m04Completion, qualityGuidance: runtime.m04QualityGuidanceState, asymmetricCoverage: runtime.m04AsymmetricCoverage, turntableCoverage: runtime.m04TurntableCoverage); try await M04SessionContextStore(layout: layout).persist(context); await ContentView.sessionRegistry.install(ActiveScanSession(draft: draft, state: PersistedSessionState(sessionID: draft.sessionID, nextSequence: 0, epoch: 0, acceptedIDs: []))); scanStartError = nil } catch { scanStartError = "Scan could not start: \(error.localizedDescription)" } }
                showNewScan = false
            } } }
            .sheet(isPresented: $showHistory) { NavigationStack { LocalScanHistoryView(root: ContentView.sessionRoot, onFinalized: { sessionID in runtime.endActiveSession(sessionID: sessionID) }) } }
            .sheet(isPresented: $showARPreview) { NavigationStack { ARPreviewEntryView() } }
            .sheet(isPresented: $showResume) { NavigationStack { SessionResumeView(root: ContentView.sessionRoot, onResume: { candidate in
                if let draft = candidate.draft, let state = candidate.state { let layout = SessionStorageLayout(root: ContentView.sessionRoot, sessionID: draft.sessionID); runtime.configureM04QualityRuntime(preset: PackagingPresetCatalog.preset(for: draft.presetID ?? .matteHDPE), layout: layout); runtime.startLiveCandidateLoop(); Task { if let context = try? await M04SessionContextStore(layout: layout).load() { if let basePass = context.basePass { runtime.restoreBasePass(basePass) }; _ = runtime.restoreM04OrbitCoverage(context.orbitCoverage); _ = runtime.restoreM04DetailPassState(context.detailPasses); runtime.restoreQualityGuidance(context.qualityGuidance); runtime.restoreAsymmetricCoverage(context.asymmetricCoverage); runtime.restoreTurntableCoverage(context.turntableCoverage); runtime.restoreObjectCenter(context.objectCenter) }; await ContentView.sessionRegistry.install(ActiveScanSession(draft: draft, state: state)) } }
                showResume = false
            }, onDiscard: { candidate in
                runtime.endActiveSession(sessionID: candidate.id)
                Task { let plan = SessionDeletionPlan(root: ContentView.sessionRoot, candidate: candidate); _ = try? await SafeSessionDeleter().deleteDetailed(plan: plan, confirmed: true) }
                showResume = false
            }) } }
            .sheet(isPresented: $showActiveProtocol) {
                NavigationStack {
                    CaptureProtocolView(preset: runtime.m04ActivePreset) { _ in showActiveProtocol = false }
                }
            }
            .task {
                #if !targetEnvironment(simulator) && canImport(ARKit) && canImport(UIKit) && canImport(AVFoundation)
                await runtime.bindProductionARCamera()
                #endif
                await runtime.start(); let candidates = await SessionDiscoveryService(root: ContentView.sessionRoot).discover(); showResume = !candidates.isEmpty }
        }
    }

    static func manualBlockHint(_ reason: String) -> String {
        switch reason {
        case "live_frame_unavailable": return "no camera frame analyzed yet — point the camera at the package and wait a moment (live_frame_unavailable)"
        case "pose_evidence_unavailable": return "AR tracking has no pose for this frame — move slowly until tracking is ready (pose_evidence_unavailable)"
        case "camera_not_ready": return "camera is not running (camera_not_ready)"
        case "session_not_ready": return "no active scan — tap New Scan first (session_not_ready)"
        case "health_hard_stop": return "device health stop (thermal/battery/storage) (health_hard_stop)"
        case "capture_persist_failed": return "photo could not be saved to the scan (capture_persist_failed)"
        case "live_frame_stale": return "camera evidence is out of date — keep the camera on the package for a moment and try again (live_frame_stale)"
        case "object_center_unset": return "aim the crosshair at the middle of the package and tap Set object center (object_center_unset)"
        case "capture_in_flight": return "previous photo is still being saved — wait for it to finish (capture_in_flight)"
        default: return reason
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
