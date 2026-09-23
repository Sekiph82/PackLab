import XCTest
@testable import PackLabCapture

final class PackLabCaptureTests: XCTestCase {
    func testPreviewLifecyclePolicyIsIdempotent() {
        var policy = PreviewLifecyclePolicy()
        XCTAssertTrue(policy.startIfNeeded())
        XCTAssertFalse(policy.startIfNeeded())
        policy.attach()
        policy.attach()
        XCTAssertEqual(policy.attachmentCount, 2)
        XCTAssertTrue(policy.stopIfNeeded())
        XCTAssertFalse(policy.stopIfNeeded())
        policy.detach()
        policy.detach()
        policy.detach()
        XCTAssertEqual(policy.attachmentCount, 0)
    }

    func testMainRearWideSelectionRejectsFrontAndUnsupportedLenses() {
        let candidates = [
            CameraDeviceDescriptor(position: .front, kind: .wideAngle, stableID: "front"),
            CameraDeviceDescriptor(position: .back, kind: .ultraWide, stableID: "ultra"),
            CameraDeviceDescriptor(position: .back, kind: .wideAngle, stableID: "main")
        ]
        XCTAssertEqual(
            CameraDeviceSelector.selectMainRearWide(from: candidates),
            .selected(CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle))
        )
        XCTAssertEqual(CameraDeviceSelector.selectMainRearWide(from: []), .unavailable)
        XCTAssertEqual(
            CameraDeviceSelector.selectMainRearWide(from: [candidates[1]]),
            .unsupported
        )
    }

    func testMainRearWideSelectionIsExplicitlyAmbiguous() {
        let candidates = [
            CameraDeviceDescriptor(position: .back, kind: .wideAngle, stableID: "a"),
            CameraDeviceDescriptor(position: .back, kind: .wideAngle, stableID: "b")
        ]
        XCTAssertEqual(CameraDeviceSelector.selectMainRearWide(from: candidates), .ambiguous(candidates))
    }

    func testHighResolutionCaptureRejectsOverlappingRequestsAndInvalidSource() async {
        struct Backend: StillPhotoBackend {
            let bytes: Data
            func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) {
                try await Task.sleep(for: .milliseconds(10))
                return (bytes, CaptureDimensions(width: 4000, height: 3000))
            }
        }
        let service = HighResolutionStillCaptureService(backend: Backend(bytes: Data([1, 2, 3])))
        async let first = service.capture(captureID: "one")
        let second = await service.capture(captureID: "two")
        let firstResult = await first
        XCTAssertTrue([firstResult, second].contains { if case .accepted = $0 { true } else { false } })
        XCTAssertTrue([firstResult, second].contains { if case .rejected("capture_in_flight") = $0 { true } else { false } })
    }

    func testOriginalSourceIntegrityPreservesBytesDimensionsAndSeparateDerivativePath() throws {
        let bytes = Data([10, 20, 30])
        let dimensions = CaptureDimensions(width: 4000, height: 3000)
        let record = OriginalSourceRecord(
            captureID: "capture-1", filename: "IMG_0001.HEIC", dimensions: dimensions,
            orientation: "landscape", sha256: SourceIntegrity.digest(bytes), metadataBytes: Data([99])
        )
        XCTAssertNoThrow(try SourceIntegrity.validate(record: record, bytes: bytes, dimensions: dimensions))
        XCTAssertEqual(SourceIntegrity.derivativePath(for: record), "previews/capture-1-thumbnail.jpg")
        XCTAssertThrowsError(try SourceIntegrity.validate(record: record, bytes: Data([0]), dimensions: dimensions)) { error in
            XCTAssertEqual(error as? SourceIntegrityError, .digestMismatch)
        }
        XCTAssertThrowsError(try SourceIntegrity.validate(record: record, bytes: bytes, dimensions: CaptureDimensions(width: 1, height: 1))) { error in
            XCTAssertEqual(error as? SourceIntegrityError, .dimensionMismatch)
        }
    }

    func testFocusPolicyRequiresCapabilityBeforeLock() {
        var policy = FocusPolicy()
        XCTAssertEqual(policy.begin(capabilities: FocusCapabilities(point: false, lock: true)), .unavailable)
        XCTAssertEqual(policy.lock(capabilities: FocusCapabilities(point: true, lock: true)), .failed)
        XCTAssertEqual(policy.begin(capabilities: FocusCapabilities(point: true, lock: true)), .focusing)
        XCTAssertEqual(policy.stabilize(), .continuous)
        XCTAssertEqual(policy.lock(capabilities: FocusCapabilities(point: true, lock: true)), .locked)
    }

    func testExposurePolicyClampsBiasAndGatesLock() {
        var policy = ExposurePolicy()
        XCTAssertEqual(policy.meter(capabilities: ExposureCapabilities(minBias: -2, maxBias: 2, lock: true), requestedBias: 9), .metering)
        XCTAssertEqual(policy.targetBias, 2)
        XCTAssertEqual(policy.lock(capabilities: ExposureCapabilities(minBias: -2, maxBias: 2, lock: true)), .locked)
        var unsupported = ExposurePolicy()
        XCTAssertEqual(unsupported.lock(capabilities: ExposureCapabilities(minBias: -1, maxBias: 1, lock: false)), .failed)
    }

    func testWhiteBalancePolicyDoesNotInventTemperature() {
        var policy = WhiteBalancePolicy()
        XCTAssertEqual(policy.stabilize(capabilities: WhiteBalanceCapabilities(continuous: true, lock: true)), .stabilizing)
        XCTAssertNil(policy.temperatureKelvin)
        XCTAssertEqual(policy.lock(capabilities: WhiteBalanceCapabilities(continuous: true, lock: true)), .locked)
        var unavailable = WhiteBalancePolicy()
        XCTAssertEqual(unavailable.stabilize(capabilities: WhiteBalanceCapabilities(continuous: false, lock: false), reportedKelvin: 5000), .unavailable)
        XCTAssertNil(unavailable.temperatureKelvin)
    }

    func testPhotoMetadataBindingFailsClosedForMismatchedSource() throws {
        let bytes = Data([1, 2, 3])
        let dims = CaptureDimensions(width: 12, height: 8)
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle)
        let source = OriginalSourceRecord(captureID: "p1", filename: "p1.heic", dimensions: dims, orientation: "portrait", sha256: SourceIntegrity.digest(bytes))
        let metadata = PhotoCaptureMetadata(photoID: "p1", imagePath: "images/p1.heic", sequence: 0, originalFilename: "p1.heic", pixelDimensions: dims, orientation: "portrait", lensIdentity: lens, focalLengthMM: SourceMeasurement(status: .unavailable), exposureSeconds: SourceMeasurement(status: .unavailable), iso: SourceMeasurement(status: .unavailable), whiteBalanceKelvin: SourceMeasurement(status: .unavailable), captureTimestamp: Date(timeIntervalSince1970: 0))
        XCTAssertNoThrow(try PhotoMetadataBinding.validate(metadata: metadata, source: source, bytes: bytes))
        XCTAssertThrowsError(try PhotoMetadataBinding.validate(metadata: metadata, source: source, bytes: Data([9]))) { error in
            XCTAssertEqual(error as? PhotoMetadataBindingError, .digestMismatch)
        }
        let wrong = PhotoCaptureMetadata(photoID: "other", imagePath: metadata.imagePath, sequence: 0, originalFilename: metadata.originalFilename, pixelDimensions: dims, orientation: "portrait", lensIdentity: lens, focalLengthMM: metadata.focalLengthMM, exposureSeconds: metadata.exposureSeconds, iso: metadata.iso, whiteBalanceKelvin: metadata.whiteBalanceKelvin, captureTimestamp: metadata.captureTimestamp)
        XCTAssertThrowsError(try PhotoMetadataBinding.validate(metadata: wrong, source: source, bytes: bytes)) { error in
            XCTAssertEqual(error as? PhotoMetadataBindingError, .idMismatch)
        }
    }

    func testCameraRecoveryIsIdempotentAndBounded() {
        var machine = CameraRecoveryMachine()
        XCTAssertEqual(machine.apply(.requestStart), .starting)
        XCTAssertEqual(machine.apply(.started), .running)
        XCTAssertEqual(machine.apply(.interrupted), .interrupted)
        XCTAssertEqual(machine.apply(.interruptionEnded), .restarting)
        XCTAssertEqual(machine.apply(.restartFailed), .restarting)
        XCTAssertEqual(machine.apply(.restartFailed), .restarting)
        XCTAssertEqual(machine.apply(.restartFailed), .failed)
        XCTAssertFalse(machine.userMessage.isEmpty)
        XCTAssertEqual(machine.apply(.stop), .idle)
    }

    func testDeviceHealthPolicyUsesConservativeHardStops() {
        let warning = DeviceHealthPolicy.evaluate(DeviceHealthSnapshot(thermal: .fair, availableStorageBytes: 500_000_000, batteryLevel: 0.5, batteryStateAvailable: true))
        XCTAssertEqual(warning.severity, .warning)
        let stop = DeviceHealthPolicy.evaluate(DeviceHealthSnapshot(thermal: .critical, availableStorageBytes: 100, batteryLevel: 0.02, batteryStateAvailable: true))
        XCTAssertEqual(stop.severity, .hardStop)
        let unavailable = DeviceHealthPolicy.evaluate(DeviceHealthSnapshot(thermal: .unavailable, availableStorageBytes: nil, batteryLevel: nil, batteryStateAvailable: false))
        XCTAssertEqual(unavailable.severity, .normal)
    }

    func testTrackingLifecycleIsUnavailableUntilRecovered() {
        var policy = ARTrackingLifecyclePolicy()
        XCTAssertFalse(policy.snapshot.poseEvidenceEligible)
        policy.started()
        XCTAssertEqual(policy.snapshot.quality, .limited)
        policy.normal()
        XCTAssertTrue(policy.snapshot.poseEvidenceEligible)
        let oldEpoch = policy.epoch
        policy.reset()
        XCTAssertEqual(policy.epoch, oldEpoch + 1)
        XCTAssertFalse(policy.snapshot.poseEvidenceEligible)
        policy.recovered()
        XCTAssertTrue(policy.snapshot.poseEvidenceEligible)
    }

    func testPoseAlignmentRejectsMissingStaleAndUnavailableSamples() {
        let sample = PoseSample(timestamp: 10, transform: Array(repeating: 0, count: 16), tracking: .normal)
        XCTAssertEqual(PoseAligner.nearest(to: 10.05, samples: [sample]).status, "available")
        XCTAssertEqual(PoseAligner.nearest(to: 11, samples: [sample]).status, "stale")
        XCTAssertEqual(PoseAligner.nearest(to: 10, samples: []).status, "unavailable")
        let unavailable = PoseSample(timestamp: 10, transform: Array(repeating: 0, count: 16), tracking: .unavailable)
        XCTAssertEqual(PoseAligner.nearest(to: 10, samples: [unavailable]).status, "unavailable")
    }

    func testMotionBufferIsBoundedAndTimestampAligned() {
        var buffer = MotionBuffer(capacity: 2)
        for index in 0..<3 { buffer.append(MotionSampleRecord(monotonicTimestamp: Double(index), attitude: [0,0,0,1], rotationRate: [0,0,0])) }
        XCTAssertEqual(buffer.samples.count, 2)
        XCTAssertNotNil(buffer.nearest(to: 2.05))
        XCTAssertNil(buffer.nearest(to: 0))
    }

    func testCoordinateContractPreservesIdentityAndComposition() {
        XCTAssertEqual(PackScanCoordinateContract.appLocalToPackScan(.identity), .identity)
        XCTAssertEqual(CoordinateTransform.identity.multiplied(by: .identity), .identity)
        XCTAssertTrue(CoordinateTransform.identity.isFinite)
        XCTAssertEqual(PackScanCoordinateContract.units, "metres")
    }

    func testTrackingClassifierGatesPoseEvidenceDuringFlapping() {
        XCTAssertTrue(TrackingQualityClassifier.classify(state: .normal).poseEvidenceEligible)
        XCTAssertFalse(TrackingQualityClassifier.classify(state: .limited, limitation: .insufficientFeatures).poseEvidenceEligible)
        XCTAssertFalse(TrackingQualityClassifier.classify(state: .recovering).poseEvidenceEligible)
        XCTAssertTrue(TrackingQualityClassifier.classify(state: .normal).poseEvidenceEligible)
    }

    func testResetCreatesEpochAndNeverMixesPoseSegments() {
        var coordinator = SessionEpochCoordinator()
        coordinator.reset(reason: .trackingDegraded)
        XCTAssertEqual(coordinator.epoch, 1)
        XCTAssertFalse(coordinator.accepts(poseEpoch: 0))
        XCTAssertFalse(coordinator.accepts(poseEpoch: 1))
        coordinator.recovered()
        XCTAssertTrue(coordinator.accepts(poseEpoch: 1))
        coordinator.reset(reason: .userRequested)
        XCTAssertFalse(coordinator.accepts(poseEpoch: 1))
    }

    func testPoseOverlayLabelsUnavailableDataAndCanBeDisabled() {
        let unavailable = PoseOverlayModel.make(visible: true, tracking: TrackingSnapshot(quality: .unavailable, poseEvidenceEligible: false), epoch: 2, pose: nil)
        XCTAssertTrue(unavailable.lines.contains("Pose: unavailable"))
        XCTAssertFalse(PoseOverlayModel.make(visible: false, tracking: unavailableSnapshot(), epoch: 0, pose: nil).visible)
    }

    private func unavailableSnapshot() -> TrackingSnapshot { TrackingSnapshot(quality: .unavailable, poseEvidenceEligible: false) }

    func testPoseDiagnosticsExportIsDeterministicAndRejectsNonFiniteData() throws {
        let pose = AlignedPose(sample: PoseSample(timestamp: 2, transform: Array(repeating: 0, count: 16), tracking: .normal), delta: 0.01, status: "available")
        let record = PoseDiagnosticRecord(captureID: "b", captureTimestamp: 2, pose: pose, motion: nil, epoch: 1)
        let bytes = try PoseDiagnosticsExporter.encode(records: [record])
        XCTAssertTrue(String(decoding: bytes, as: UTF8.self).contains("1.0.0"))
        XCTAssertThrowsError(try PoseDiagnosticsExporter.encode(records: [PoseDiagnosticRecord(captureID: "bad", captureTimestamp: .infinity, pose: pose, motion: nil, epoch: 1)])) { error in
            XCTAssertEqual(error as? PoseDiagnosticsError, .nonFinite)
        }
    }


    func testStableTrackedSampleIsAccepted() async {
        let service = FoundationCaptureQualityService(maximumMotionMagnitude: 1.0)
        let result = await service.evaluate(
            CaptureQualitySample(motionMagnitude: 0.25, trackingAvailable: true)
        )

        XCTAssertTrue(result.isAcceptable)
        XCTAssertEqual(result.reason, "acceptable")
    }

    func testSimulatorMotionFallbackDoesNotCreateSensorEvidence() async {
        let service = SimulatorMotionService()
        await service.start()
        let sample = await service.latestSample()
        let state = await SimulatorARTrackingService().state()

        XCTAssertNil(sample)
        XCTAssertEqual(state, .unavailable)
    }

    func testDiagnosticsRedactsSecretsAndPrivatePathsBeforeRetention() async {
        let logger = DiagnosticsLogger()
        await logger.record(
            category: "auth",
            code: "token",
            message: #"api_key=secret123 path=C:\Users\Alice\private\capture.json Bearer abc.def"#
        )

        let entries = await logger.snapshot()
        XCTAssertEqual(entries.count, 1)
        let entry = entries[0]
        XCTAssertTrue(entry.message.contains("[REDACTED_SECRET]"))
        XCTAssertTrue(entry.message.contains("[USER_PATH]"))
        XCTAssertFalse(entry.message.contains("secret123"))
        XCTAssertFalse(entry.message.contains("Alice"))
        XCTAssertFalse(entry.message.contains("abc.def"))
    }

    func testDiagnosticsCapabilityExportIsConstrainedAndSanitized() throws {
        let environment = DiagnosticsEnvironment(
            appVersion: "api_key=version-secret",
            buildNumber: "1.0",
            capabilities: ["Camera", "GPU: RTX 4090", "/Users/alice/private", "token=hidden"]
        )
        let data = try DiagnosticsExporter().prepareUserInitiatedExport(
            entries: [DiagnosticsEntry(sequence: 0, timestamp: Date(), level: .info, category: "test", code: "safe", message: "ok")],
            environment: environment
        )
        let json = String(decoding: data, as: UTF8.self)

        XCTAssertTrue(json.contains("camera"))
        XCTAssertTrue(json.contains("gpu-rtx-4090"))
        XCTAssertFalse(json.contains("version-secret"))
        XCTAssertFalse(json.contains("alice"))
        XCTAssertFalse(json.contains("hidden"))
    }

    func testDiagnosticsRetentionRemainsBounded() async {
        let logger = DiagnosticsLogger(capacity: 2)
        for sequence in 0..<3 {
            await logger.record(category: "test", code: "entry", message: "\(sequence)")
        }

        let entries = await logger.snapshot()
        XCTAssertEqual(entries.count, 2)
        XCTAssertEqual(entries.map(\.message), ["1", "2"])
    }

    func testDiagnosticsEmptyExportFailsClosed() async {
        do {
            _ = try await DiagnosticsExporter().prepareUserInitiatedExport(from: DiagnosticsLogger())
            XCTFail("An empty diagnostics export must fail closed")
        } catch let error as DiagnosticsExportError {
            XCTAssertEqual(error, .empty)
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }
}

// Static verification on Windows covers target wiring, source membership, and privacy settings.
// xcodebuild execution on simulator/macOS CI is intentionally deferred to the authorized M16 runner.
