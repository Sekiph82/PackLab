import XCTest
@testable import PackLabCapture
#if canImport(CoreGraphics) && canImport(ImageIO) && canImport(UniformTypeIdentifiers)
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers
#endif

@MainActor
private final class SequenceTrackingService: ARTrackingService {
    private var snapshots: [TrackingSnapshot]
    private var stopped = false
    private var index = 0
    init(_ snapshots: [TrackingSnapshot]) { self.snapshots = snapshots }
    func start() async { stopped = false }
    func stop() async { stopped = true }
    func state() async -> ARTrackingServiceState { stopped ? .idle : .tracking }
    func snapshot() async -> TrackingSnapshot {
        guard !stopped else { return TrackingQualityClassifier.classify(state: .unavailable) }
        let value = snapshots[min(index, snapshots.count - 1)]; index += 1; return value
    }
    func latestPose() async -> PoseSample? { PoseSample(timestamp: Double(index), transform: CoordinateTransform.identity.values, tracking: .normal) }
    func localizationEpoch() async -> Int { index }
    func resetDiagnostics() async -> [ResetDiagnosticEvent] { [] }
}

@MainActor
private final class SequenceMotionService: MotionService {
    private var index = 0
    private var stopped = false
    func start() async { stopped = false }
    func stop() async { stopped = true }
    func latestSample() async -> MotionSample? { stopped ? nil : MotionSample(timestamp: Double(index), accelerationX: 0, accelerationY: 0, accelerationZ: 0) }
    func latestRecord() async -> MotionSampleRecord? { stopped ? nil : MotionSampleRecord(monotonicTimestamp: Double(index), attitude: [0, 0, 0, 1], rotationRate: [0, 0, 0]) }
    func state() async -> MotionServiceState { stopped ? .idle : .running }
    func advance() { index += 1 }
}

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

    func testStillCaptureLifecycleCompletesExactlyOnceAndRejectsDuplicates() {
        var lifecycle = StillCaptureLifecycle()
        XCTAssertTrue(lifecycle.begin())
        XCTAssertFalse(lifecycle.begin())
        XCTAssertTrue(lifecycle.complete(success: true))
        XCTAssertFalse(lifecycle.complete(success: false))
        XCTAssertEqual(lifecycle.state, .accepted)
        lifecycle.reset()
        XCTAssertTrue(lifecycle.begin())
        XCTAssertTrue(lifecycle.complete(success: false))
        XCTAssertEqual(lifecycle.state, .failed)
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

    func testOriginalSourceStorePersistsImmutableBytesAndRecord() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let bytes = Data([4, 5, 6])
        let record = OriginalSourceRecord(captureID: "capture-1", filename: "capture-1.heic", dimensions: CaptureDimensions(width: 4, height: 3), orientation: "portrait", sha256: SourceIntegrity.digest(bytes))
        let store = OriginalSourceStore(root: root)
        let url = try await store.persist(record: record, bytes: bytes)
        XCTAssertEqual(try Data(contentsOf: url), bytes)
        XCTAssertEqual(try await store.load(recordID: "capture-1"), record)
        let repeatURL = try await store.persist(record: record, bytes: bytes)
        XCTAssertEqual(repeatURL, url)
        do {
            _ = try await store.persist(record: record, bytes: Data([9]))
            XCTFail("mismatched source must be rejected")
        } catch {
            XCTAssertEqual(error as? SourceIntegrityError, .digestMismatch)
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

    func testExposureCaptureBindingRequiresFiniteReadingAndUsesIntegerISO() throws {
        var binding = try ExposureCaptureBinding(reading: ExposureCaptureReading(exposureSeconds: 0.01, iso: 400, bias: 0))
        XCTAssertEqual(binding.reading.iso, 400)
        XCTAssertEqual(binding.state, .metering)
        binding.lock()
        XCTAssertEqual(binding.state, .locked)
        XCTAssertThrowsError(try ExposureCaptureBinding(reading: ExposureCaptureReading(exposureSeconds: .nan, iso: 400, bias: 0))) { error in
            XCTAssertEqual(error as? ExposureCaptureBindingError, .invalidReading)
        }
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

    func testWhiteBalanceCaptureBindingRequiresObservedTemperature() throws {
        var binding = try WhiteBalanceCaptureBinding(reading: WhiteBalanceCaptureReading(temperatureKelvin: 5200))
        XCTAssertEqual(binding.state, .stabilizing)
        XCTAssertTrue(binding.reading.isValid)
        binding.lock()
        XCTAssertEqual(binding.state, .locked)
        XCTAssertThrowsError(try WhiteBalanceCaptureBinding(reading: WhiteBalanceCaptureReading(temperatureKelvin: .infinity))) { error in
            XCTAssertEqual(error as? WhiteBalanceCaptureBindingError, .invalidReading)
        }
    }

    func testCameraControlModelRetainsSelectedLensAndIndependentStates() {
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle)
        var model = CameraCaptureControlModel(lens: lens)
        model.setFocus(.continuous)
        model.setExposure(.metering)
        model.setWhiteBalance(.stabilizing)
        XCTAssertEqual(model.state.lens, lens)
        XCTAssertEqual(model.state.focus, .continuous)
        XCTAssertEqual(model.state.exposure, .metering)
        XCTAssertEqual(model.state.whiteBalance, .stabilizing)
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

    func testPackScanPhotoWireUsesStrictSnakeCaseAndIntegerISO() throws {
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle)
        let metadata = PhotoCaptureMetadata(photoID: "p1", imagePath: "images/p1.heic", sequence: 0, originalFilename: "p1.heic", pixelDimensions: CaptureDimensions(width: 10, height: 8), orientation: "portrait", lensIdentity: lens, focalLengthMM: SourceMeasurement(status: .available, value: 26, unit: "mm", source: "device_api"), exposureSeconds: SourceMeasurement(status: .estimated, value: 0.01, unit: "s", source: "derived"), iso: SourceMeasurement(status: .available, value: 400, unit: "iso", source: "exif"), whiteBalanceKelvin: SourceMeasurement(status: .unavailable), captureTimestamp: Date(timeIntervalSince1970: 0))
        let wire = try PackScanPhotoMetadataWire.from(metadata)
        let data = try JSONEncoder().encode(PackScanPhotoMetadataDocument(photos: [wire]))
        let object = try XCTUnwrap(try JSONSerialization.jsonObject(with: data) as? [String: Any])
        let photos = try XCTUnwrap(object["photos"] as? [[String: Any]])
        XCTAssertEqual(object["schema_version"] as? String, "1.0.0")
        XCTAssertEqual(photos[0]["photo_id"] as? String, "p1")
        XCTAssertNil(photos[0]["lensIdentity"])
        XCTAssertEqual((photos[0]["iso"] as? [String: Any])?["value"] as? Int, 400)
        XCTAssertEqual((photos[0]["orientation"] as? [String: Any])?["value"] as? String, "portrait")
    }

    func testAcceptedPhotoMetadataStoreAtomicallyBindsSourceAndWireMetadata() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let bytes = Data([7, 8, 9])
        let dimensions = CaptureDimensions(width: 10, height: 8)
        let source = OriginalSourceRecord(captureID: "p1", filename: "p1.heic", dimensions: dimensions, orientation: "portrait", sha256: SourceIntegrity.digest(bytes))
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle)
        let metadata = PhotoCaptureMetadata(photoID: "p1", imagePath: "images/p1.heic", sequence: 0, originalFilename: "p1.heic", pixelDimensions: dimensions, orientation: "portrait", lensIdentity: lens, focalLengthMM: SourceMeasurement(status: .unavailable), exposureSeconds: SourceMeasurement(status: .unavailable), iso: SourceMeasurement(status: .unavailable), whiteBalanceKelvin: SourceMeasurement(status: .unavailable), captureTimestamp: Date(timeIntervalSince1970: 0))
        let store = AcceptedPhotoMetadataStore(sourceRoot: root.appendingPathComponent("images"), metadataURL: root.appendingPathComponent("metadata/photos.json"))
        try await store.persist(metadata: metadata, source: source, bytes: bytes)
        let encoded = try Data(contentsOf: root.appendingPathComponent("metadata/photos.json"))
        let document = try JSONDecoder().decode(PackScanPhotoMetadataDocument.self, from: encoded)
        XCTAssertEqual(document.photos.map(\.photoID), ["p1"])
        do {
            try await store.persist(metadata: metadata, source: source, bytes: bytes)
            XCTFail("duplicate photo must be rejected")
        } catch { XCTAssertEqual(error as? AcceptedPhotoPersistenceError, .duplicatePhoto) }
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

    func testCameraRecoveryCancelsOnlyInFlightAndPreservesAcceptedCaptures() {
        var model = CameraRecoveryIntegrationModel()
        XCTAssertTrue(model.beginCapture(id: "accepted"))
        model.acceptCapture()
        XCTAssertTrue(model.beginCapture(id: "in-flight"))
        model.signal(.interruption)
        XCTAssertEqual(model.acceptedCaptureIDs, ["accepted"])
        XCTAssertNil(model.inFlightCaptureID)
        XCTAssertEqual(model.machine.state, .interrupted)
        XCTAssertFalse(model.beginCapture(id: "next"))
    }

    func testDeviceHealthPolicyUsesConservativeHardStops() {
        let warning = DeviceHealthPolicy.evaluate(DeviceHealthSnapshot(thermal: .fair, availableStorageBytes: 500_000_000, batteryLevel: 0.5, batteryStateAvailable: true))
        XCTAssertEqual(warning.severity, .warning)
        let stop = DeviceHealthPolicy.evaluate(DeviceHealthSnapshot(thermal: .critical, availableStorageBytes: 100, batteryLevel: 0.02, batteryStateAvailable: true))
        XCTAssertEqual(stop.severity, .hardStop)
        let unavailable = DeviceHealthPolicy.evaluate(DeviceHealthSnapshot(thermal: .unavailable, availableStorageBytes: nil, batteryLevel: nil, batteryStateAvailable: false))
        XCTAssertEqual(unavailable.severity, .normal)
    }

    func testDeviceHealthGateDistinguishesWarningHardStopAndUnavailable() {
        let warning = DeviceHealthCaptureGate.evaluate(DeviceHealthSnapshot(thermal: .fair, availableStorageBytes: 500_000_000, batteryLevel: 0.5, batteryStateAvailable: true))
        let stop = DeviceHealthCaptureGate.evaluate(DeviceHealthSnapshot(thermal: .critical, availableStorageBytes: 10, batteryLevel: 0.02, batteryStateAvailable: true))
        let unavailable = DeviceHealthCaptureGate.evaluate(UnavailableDeviceHealthProvider().snapshot())
        XCTAssertTrue(warning.allowsCapture)
        XCTAssertFalse(stop.allowsCapture)
        XCTAssertTrue(unavailable.allowsCapture)
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

    func testPoseBufferSortsOutOfOrderSamplesAndBindsExactBoundaryButRejectsInvalidTransform() {
        var buffer = PoseBuffer(capacity: 3)
        buffer.append(PoseSample(timestamp: 10.1, transform: CoordinateTransform.identity.values, tracking: .normal))
        buffer.append(PoseSample(timestamp: 10.0, transform: CoordinateTransform.identity.values, tracking: .normal))
        XCTAssertEqual(buffer.samples.map(\.timestamp), [10.0, 10.1])
        XCTAssertEqual(buffer.bind(captureID: "p1", timestamp: 10.1, tolerance: 0.1).aligned.status, "available")
        buffer.append(PoseSample(timestamp: 10.2, transform: [1, 2], tracking: .normal))
        XCTAssertEqual(buffer.bind(captureID: "p2", timestamp: 10.2).aligned.status, "invalid_transform")
    }

    func testMotionBufferIsBoundedAndTimestampAligned() {
        var buffer = MotionBuffer(capacity: 2)
        for index in 0..<3 { buffer.append(MotionSampleRecord(monotonicTimestamp: Double(index), attitude: [0,0,0,1], rotationRate: [0,0,0])) }
        XCTAssertEqual(buffer.samples.count, 2)
        XCTAssertNotNil(buffer.nearest(to: 2.05))
        XCTAssertNil(buffer.nearest(to: 0))
    }

    func testMotionCaptureBindingReportsAvailableStaleAndInvalidProviderData() {
        var buffer = MotionBuffer(capacity: 3)
        buffer.append(MotionSampleRecord(monotonicTimestamp: 2, attitude: [0, 0, 0, 1], rotationRate: [0, 0, 0]))
        buffer.append(MotionSampleRecord(monotonicTimestamp: 1, attitude: [0, 0, 0, 1], rotationRate: [0, 0, 0]))
        buffer.append(MotionSampleRecord(monotonicTimestamp: 3, attitude: [0, 0], rotationRate: [0]))
        XCTAssertEqual(MotionAligner.bind(captureID: "p1", timestamp: 2.05, buffer: buffer).status, "available")
        XCTAssertEqual(MotionAligner.bind(captureID: "p2", timestamp: 4, buffer: buffer).status, "stale")
        XCTAssertEqual(MotionAligner.bind(captureID: "p3", timestamp: 2, buffer: MotionBuffer()).status, "unavailable")
    }

    func testCoordinateContractPreservesIdentityAndComposition() {
        XCTAssertEqual(PackScanCoordinateContract.appLocalToPackScan(.identity), .identity)
        XCTAssertEqual(CoordinateTransform.identity.multiplied(by: .identity), .identity)
        XCTAssertTrue(CoordinateTransform.identity.isFinite)
        XCTAssertEqual(PackScanCoordinateContract.units, "metres")
    }

    func testCoordinateMathCoversTranslationRotationsInverseAndFailClosedInvalidInput() throws {
        let translation = CoordinateTransform.translation(x: 2, y: -3, z: 4)
        let composed = try translation.validatedMultiplying(by: CoordinateTransform.rotationZ(.pi / 2))
        let inverse = try composed.inverted()
        let roundTrip = try composed.validatedMultiplying(by: inverse)
        XCTAssertTrue(zip(roundTrip.values, CoordinateTransform.identity.values).allSatisfy { abs($0.0 - $0.1) < 1e-9 })
        XCTAssertEqual(CoordinateTransform.rotationX(.pi / 2).values.count, 16)
        XCTAssertEqual(CoordinateTransform.rotationY(.pi / 2).values.count, 16)
        XCTAssertEqual(CoordinateTransform.rotationZ(.pi / 2).values.count, 16)
        XCTAssertFalse(CoordinateTransform(values: [1, 2]).multiplied(by: .identity).isFinite)
        XCTAssertThrowsError(try CoordinateTransform(values: [1, .infinity]).inverted()) { error in XCTAssertEqual(error as? CoordinateTransformError, .invalidShapeOrValue) }
        XCTAssertNoThrow(try PackScanCoordinateContract.validate(translation))
    }

    func testTrackingClassifierGatesPoseEvidenceDuringFlapping() {
        XCTAssertTrue(TrackingQualityClassifier.classify(state: .normal).poseEvidenceEligible)
        XCTAssertFalse(TrackingQualityClassifier.classify(state: .limited, limitation: .insufficientFeatures).poseEvidenceEligible)
        XCTAssertFalse(TrackingQualityClassifier.classify(state: .recovering).poseEvidenceEligible)
        XCTAssertTrue(TrackingQualityClassifier.classify(state: .normal).poseEvidenceEligible)
    }

    func testTrackingRecoveryRequiresStableNormalFramesAndRetainsDiagnostics() {
        var policy = TrackingRecoveryPolicy(requiredStableNormalFrames: 2)
        XCTAssertFalse(policy.update(state: .normal).poseEvidenceEligible)
        XCTAssertFalse(policy.update(state: .limited, limitation: .insufficientFeatures).poseEvidenceEligible)
        XCTAssertFalse(policy.update(state: .normal).poseEvidenceEligible)
        XCTAssertTrue(policy.update(state: .normal).poseEvidenceEligible)
        XCTAssertEqual(policy.diagnostics.count, 4)
        XCTAssertTrue(TrackingWarningViewModel(snapshot: policy.snapshot).isVisible == false)
        XCTAssertTrue(TrackingWarningViewModel(snapshot: TrackingQualityClassifier.classify(state: .recovering)).isVisible)
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

    func testResetOrchestrationRetainsAcceptedCapturesAndRecordsReasons() {
        var model = ResetOrchestrationModel()
        model.retainAcceptedCapture("accepted")
        model.reset(reason: .trackingDegraded)
        XCTAssertEqual(model.acceptedCaptureIDs, ["accepted"])
        XCTAssertFalse(model.accepts(poseEpoch: 0))
        XCTAssertEqual(model.diagnostics.map(\.reason), [.trackingDegraded])
        model.recovered()
        XCTAssertTrue(model.accepts(poseEpoch: 1))
        model.reset(reason: .userRequested)
        XCTAssertEqual(model.epochCoordinator.epoch, 2)
    }

    func testPoseOverlayLabelsUnavailableDataAndCanBeDisabled() {
        let unavailable = PoseOverlayModel.make(visible: true, tracking: TrackingSnapshot(quality: .unavailable, poseEvidenceEligible: false), epoch: 2, pose: nil)
        XCTAssertTrue(unavailable.lines.contains("Pose: unavailable"))
        XCTAssertFalse(PoseOverlayModel.make(visible: false, tracking: unavailableSnapshot(), epoch: 0, pose: nil).visible)
    }

    func testPoseOverlayFormatsLiveOrientationAndTrackingStatesWithoutInventingData() {
        let pose = PoseSample(timestamp: 4, transform: CoordinateTransform.identity.values, tracking: .normal)
        let motion = MotionSampleRecord(monotonicTimestamp: 4, attitude: [0, 0, 0, 1], rotationRate: [0, 0, 0])
        let normal = PoseOverlayModel.make(visible: true, tracking: TrackingQualityClassifier.classify(state: .normal), epoch: 3, pose: pose, motion: motion)
        XCTAssertTrue(normal.lines.contains("Orientation: ARKit camera-to-world"))
        XCTAssertTrue(normal.lines.contains("Motion t=4.000s"))
        let degraded = PoseOverlayModel.make(visible: true, tracking: TrackingQualityClassifier.classify(state: .recovering), epoch: 3, pose: nil, motion: nil)
        XCTAssertTrue(degraded.lines.contains("Pose: unavailable"))
        XCTAssertTrue(degraded.lines.contains("Motion: unavailable"))
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

    func testPoseDiagnosticsRejectsMalformedSensorShapesAndRedactsIdentifiers() throws {
        let malformedPose = AlignedPose(sample: PoseSample(timestamp: 2, transform: [1, 2], tracking: .normal), delta: 0, status: "available")
        XCTAssertThrowsError(try PoseDiagnosticsExporter.encode(records: [PoseDiagnosticRecord(captureID: "../private", captureTimestamp: 2, pose: malformedPose, motion: nil, epoch: 1)])) { error in
            XCTAssertEqual(error as? PoseDiagnosticsError, .malformedTransform)
        }
        let pose = AlignedPose(sample: PoseSample(timestamp: 2, transform: CoordinateTransform.identity.values, tracking: .normal), delta: 0, status: "available")
        let malformedMotion = MotionSampleRecord(monotonicTimestamp: 2, attitude: [0], rotationRate: [0])
        XCTAssertThrowsError(try PoseDiagnosticsExporter.encode(records: [PoseDiagnosticRecord(captureID: "../private", captureTimestamp: 2, pose: pose, motion: malformedMotion, epoch: 1)])) { error in
            XCTAssertEqual(error as? PoseDiagnosticsError, .malformedMotion)
        }
        let data = try PoseDiagnosticsExporter.encode(records: [PoseDiagnosticRecord(captureID: "../private", captureTimestamp: 2, pose: pose, motion: nil, epoch: 1)])
        XCTAssertTrue(String(decoding: data, as: UTF8.self).contains("_private"))
    }

    func testNewScanDraftNormalizesAndValidatesM02Modes() throws {
        let draft = try NewScanDraftValidator.make(name: "  Kenya Bottle  ", type: .bottle, mode: .guidedOrbit, notes: "  note  ", now: Date(timeIntervalSince1970: 0), sessionID: "s1")
        XCTAssertEqual(draft.packageName, "Kenya Bottle")
        XCTAssertEqual(draft.notes, "note")
        XCTAssertEqual(draft.captureMode, .guidedOrbit)
        XCTAssertThrowsError(try NewScanDraftValidator.make(name: " ", type: .bottle, mode: .freehand)) { XCTAssertEqual($0 as? NewScanDraftError, .emptyName) }
        XCTAssertThrowsError(try NewScanDraftValidator.make(name: String(repeating: "x", count: 121), type: .bottle, mode: .freehand)) { XCTAssertEqual($0 as? NewScanDraftError, .nameTooLong) }
    }

    func testNewScanWorkflowCoversCancelStartFailureAndAllM02Modes() {
        var workflow = NewScanWorkflowModel()
        XCTAssertNil(workflow.start(name: "", type: .bottle, mode: .freehand, sessionID: "s1"))
        if case .validationFailed = workflow.state {} else { XCTFail("invalid start must be visible in workflow state") }
        XCTAssertNotNil(workflow.start(name: "Bottle", type: .bottle, mode: .freehand, sessionID: "s1"))
        XCTAssertNotNil(workflow.start(name: "Bottle", type: .bottle, mode: .guidedOrbit, sessionID: "s2"))
        XCTAssertNotNil(workflow.start(name: "Bottle", type: .bottle, mode: .turntable, sessionID: "s3"))
        workflow.cancel()
        XCTAssertEqual(workflow.state, .cancelled)
    }

    func testSessionStorageLayoutSeparatesSourcesDerivativesAndTemps() {
        let layout = SessionStorageLayout(root: URL(fileURLWithPath: "/tmp/packlab"), sessionID: "s1")
        XCTAssertTrue(layout.images.path.hasSuffix("s1/images"))
        XCTAssertTrue(layout.previews.path.hasSuffix("s1/previews"))
        XCTAssertTrue(layout.temporary.path.hasSuffix("s1/tmp"))
        XCTAssertNotEqual(layout.images, layout.previews)
        XCTAssertTrue(layout.photoRecords.path.hasSuffix("s1/records"))
    }

    func testSessionStoreAcceptedCaptureReopenAndStaleTempRecovery() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "s1")
        let store = ScanSessionStore(layout: layout)
        try await store.create(NewScanDraft(sessionID: "s1", packageName: "Bottle", packageType: .bottle, captureMode: .freehand))
        let record = AcceptedCaptureRecord(captureID: "p1", sequence: 0, sourceFilename: "p1.heic", metadataFilename: "p1.json", acceptedAt: Date(timeIntervalSince1970: 0))
        try await store.storeAcceptedCapture(source: Data([1, 2]), record: record, metadata: Data("{}".utf8), state: try JSONEncoder().encode(PersistedSessionState(sessionID: "s1", nextSequence: 1, epoch: 0, acceptedIDs: ["p1"])))
        FileManager.default.createFile(atPath: layout.temporary.appendingPathComponent(".stale.tmp-1").path, contents: Data([0]))
        if case .resumable(let state) = try await store.reopen(requiredSourceIDs: []) { XCTAssertEqual(state.acceptedIDs, ["p1"]) } else { XCTFail("session should reopen") }
        XCTAssertFalse(FileManager.default.fileExists(atPath: layout.temporary.appendingPathComponent(".stale.tmp-1").path))
        do { try await store.storeAcceptedCapture(source: Data([3]), record: record, metadata: Data("{}".utf8), state: Data()) ; XCTFail("duplicate capture must be rejected") } catch { XCTAssertEqual(error as? SessionStorageError, .duplicateID) }
    }

    func testGalleryDeleteRequiresConfirmationAndRetakeUsesNewIdentity() throws {
        var gallery = GalleryModel(entries: [GalleryEntry(id: "a", previewPath: "previews/a.jpg", sourcePath: "images/a.heic", sequence: 0)])
        XCTAssertThrowsError(try gallery.delete(id: "a", confirmed: false))
        try gallery.retake(replacing: "a", with: GalleryEntry(id: "b", previewPath: "previews/b.jpg", sourcePath: "images/b.heic", sequence: 1))
        XCTAssertEqual(gallery.replacementTrace["a"], "b")
        try gallery.delete(id: "a", confirmed: true)
        XCTAssertEqual(gallery.entries.map(\.id), ["b"])
    }

    func testSessionGalleryDetectsMissingPreviewAndPersistsDeleteRetakeAudit() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "s1")
        let session = ScanSessionStore(layout: layout)
        try await session.create(NewScanDraft(sessionID: "s1", packageName: "Bottle", packageType: .bottle, captureMode: .freehand))
        let record = AcceptedCaptureRecord(captureID: "a", sequence: 0, sourceFilename: "a.heic", metadataFilename: "a.json")
        try await session.storeAcceptedCapture(source: Data([1]), record: record, metadata: Data("{}".utf8), state: try JSONEncoder().encode(PersistedSessionState(sessionID: "s1", nextSequence: 1, epoch: 0, acceptedIDs: ["a"])))
        let gallery = SessionGalleryStore(layout: layout)
        XCTAssertEqual(try await gallery.load().first?.status, "degraded")
        let replacement = AcceptedCaptureRecord(captureID: "b", sequence: 1, sourceFilename: "b.heic", metadataFilename: "b.json")
        try await gallery.retake(replacing: "a", source: Data([2]), record: replacement, metadata: Data("{}".utf8))
        try await gallery.delete(id: "b", confirmed: true)
        XCTAssertTrue(FileManager.default.fileExists(atPath: layout.sessionRoot.appendingPathComponent("gallery-audit.json").path))
    }

    func testSessionResumeBlocksMissingStaleAndVersionMismatchedRecords() {
        let valid = PersistedSessionState(sessionID: "s", nextSequence: 2, epoch: 1, acceptedIDs: ["a", "b"])
        XCTAssertEqual(SessionResumeValidator.disposition(state: valid, requiredSourceIDs: ["a", "b"]), .resumable)
        XCTAssertEqual(SessionResumeValidator.disposition(state: nil, requiredSourceIDs: []), .blocked("missing_state"))
        let mismatch = PersistedSessionState(sessionID: "s", schemaVersion: "2.0.0", nextSequence: 0, epoch: 0, acceptedIDs: [])
        XCTAssertEqual(SessionResumeValidator.disposition(state: mismatch, requiredSourceIDs: []), .blocked("version_mismatch"))
    }

    func testSessionDiscoveryReconstructsHistoryAndBlocksMissingOrVersionMismatch() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "s1")
        try FileManager.default.createDirectory(at: layout.images, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: layout.previews, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: layout.photoRecords, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: layout.temporary, withIntermediateDirectories: true)
        try JSONEncoder().encode(NewScanDraft(sessionID: "s1", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)).write(to: layout.metadata)
        try JSONEncoder().encode(PersistedSessionState(sessionID: "s1", nextSequence: 2, epoch: 3, acceptedIDs: ["a"], rejectedIDs: ["r"], replacementTrace: ["a": "b"])).write(to: layout.state)
        try Data([1]).write(to: layout.images.appendingPathComponent("a.heic"))
        let candidates = await SessionDiscoveryService(root: root).discover()
        XCTAssertEqual(candidates.first?.state?.rejectedIDs, ["r"])
        XCTAssertEqual(candidates.first?.state?.replacementTrace["a"], "b")
        XCTAssertEqual(candidates.first?.disposition, .resumable)
    }

    func testFinalizationGateRequiresPhotoAndMetadataPayloads() throws {
        let input = FinalizationInput(manifest: Data("{}".utf8), payloads: [:], destination: URL(fileURLWithPath: "/tmp/out.packscan"))
        XCTAssertThrowsError(try SessionFinalizer().validate(input)) { error in XCTAssertEqual(error as? FinalizationError, .invalidManifest) }
    }

    func testFinalizationGateDistinguishesBindingAndChecksumFailures() throws {
        let image = Data([1, 2, 3])
        let unavailable = PackScanNumericMeasurement(status: .unavailable)
        let wire = PackScanPhotoMetadataWire(photoID: "p", imagePath: "images/p.heic", sequence: 0, originalFilename: "p.heic", pixelDimensions: CaptureDimensions(width: 1, height: 1), orientation: PackScanOrientation(value: .unknown, source: .unknown), focalLengthMM: unavailable, exposure: unavailable, iso: PackScanISOMeasurement(status: .unavailable), whiteBalanceKelvin: unavailable)
        let validMetadata = try JSONEncoder().encode(PackScanPhotoMetadataDocument(photos: [wire]))
        let manifestObject: [String: Any] = ["schema_version": "1.0.0", "checksums": ["algorithm": "sha256"], "payloads": [["path": "metadata/photos.json", "size_bytes": validMetadata.count, "sha256": SourceIntegrity.digest(validMetadata)], ["path": "images/p.heic", "size_bytes": image.count, "sha256": "bad"]]]
        let manifest = try JSONSerialization.data(withJSONObject: manifestObject)
        let input = FinalizationInput(manifest: manifest, payloads: ["metadata/photos.json": validMetadata, "images/p.heic": image], destination: URL(fileURLWithPath: "/tmp/out.packscan"))
        XCTAssertThrowsError(try SessionFinalizer().validate(input)) { error in XCTAssertEqual(error as? FinalizationError, .checksumFailure) }
        let empty = try JSONEncoder().encode(PackScanPhotoMetadataDocument(photos: []))
        let emptyManifestObject: [String: Any] = ["schema_version": "1.0.0", "checksums": ["algorithm": "sha256"], "payloads": [["path": "metadata/photos.json", "size_bytes": empty.count, "sha256": SourceIntegrity.digest(empty)], ["path": "images/p.heic", "size_bytes": image.count, "sha256": SourceIntegrity.digest(image)]]]
        let emptyInput = FinalizationInput(manifest: try JSONSerialization.data(withJSONObject: emptyManifestObject), payloads: ["metadata/photos.json": empty, "images/p.heic": image], destination: URL(fileURLWithPath: "/tmp/out.packscan"))
        XCTAssertThrowsError(try SessionFinalizer().validate(emptyInput)) { error in XCTAssertEqual(error as? FinalizationError, .invalidMetadataBinding) }
    }

    func testHistoryIndexSortsDeterministicallyAndKeepsDegradedEntries() {
        let index = ScanHistoryIndex()
        let entries = [ScanHistoryEntry(id: "b", packageName: "B", packageType: .bottle, date: Date(timeIntervalSince1970: 1), previewPath: nil, exportState: "in_progress"), ScanHistoryEntry(id: "a", packageName: "A", packageType: .jar, date: Date(timeIntervalSince1970: 2), previewPath: "previews/a.jpg", exportState: "exported")]
        XCTAssertEqual(index.sorted(entries).map(\.id), ["a", "b"])
        XCTAssertEqual(index.degraded(id: "missing", reason: "corrupt_record").exportState, "unavailable")
    }

    func testLocalScanHistoryDerivesEntriesAndRetainsDegradedRows() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "s1")
        try FileManager.default.createDirectory(at: layout.previews, withIntermediateDirectories: true)
        try JSONEncoder().encode(NewScanDraft(sessionID: "s1", packageName: "Bottle", packageType: .bottle, captureMode: .freehand, createdAt: Date(timeIntervalSince1970: 1))).write(to: layout.metadata)
        let entries = await LocalScanHistoryStore(root: root).load()
        XCTAssertEqual(entries.first?.degradedReason, "missing_preview")
        XCTAssertEqual(entries.first?.packageName, "Bottle")
    }

    func testDeletionPlanRequiresConfirmationAndStaysInsideRoot() {
        let root = URL(fileURLWithPath: "/tmp/packlab")
        let session = root.appendingPathComponent("s1")
        XCTAssertThrowsError(try SessionDeletionPlan(root: root, session: session).validate(confirmed: false)) { XCTAssertEqual($0 as? DeletionError, .confirmationRequired) }
        XCTAssertThrowsError(try SessionDeletionPlan(root: root, session: session).validate(confirmed: true)) { XCTAssertEqual($0 as? DeletionError, .nonAuthoritative) }
        XCTAssertThrowsError(try SessionDeletionPlan(root: root, session: URL(fileURLWithPath: "/tmp/other")).validate(confirmed: true)) { XCTAssertEqual($0 as? DeletionError, .outsideRoot) }
    }

    func testAuthoritativeDeletionRemovesSessionAndRejectsTraversal() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "s1")
        try FileManager.default.createDirectory(at: layout.sessionRoot, withIntermediateDirectories: true)
        let candidate = SessionResumeCandidate(id: "s1", draft: nil, disposition: .resumable, state: nil)
        let plan = SessionDeletionPlan(root: root, candidate: candidate)
        let report = try await SafeSessionDeleter().deleteDetailed(plan: plan, confirmed: true)
        XCTAssertEqual(report.sessionID, "s1")
        XCTAssertFalse(FileManager.default.fileExists(atPath: layout.sessionRoot.path))
        let traversal = SessionDeletionPlan(root: root, session: root.appendingPathComponent("../escape"))
        XCTAssertThrowsError(try traversal.validate(confirmed: true)) { XCTAssertEqual($0 as? DeletionError, .outsideRoot) }
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

    func testPL0069AuthorizationMustPrecedeStartedState() {
        var policy = PreviewLifecyclePolicy()
        XCTAssertFalse(policy.beginAuthorizedStart(.denied))
        XCTAssertFalse(policy.isStarted)
        XCTAssertTrue(policy.beginAuthorizedStart(.authorized))
        policy.markStartedAfterSuccessfulStart()
        XCTAssertTrue(policy.isStarted)
    }

    func testPL0071AcceptedStillCarriesMonotonicCaptureEvidence() {
        let still = AcceptedStill(captureID: "p1", sourceBytes: Data([1]), dimensions: CaptureDimensions(width: 1, height: 1), capturedAt: Date(timeIntervalSince1970: 0), monotonicTimestamp: 12.5)
        XCTAssertEqual(still.monotonicTimestamp, 12.5)
        XCTAssertEqual(still.captureID, "p1")
    }

    func testPL0072MetadataExtractorFailsClosedForUnsupportedBytes() {
        XCTAssertThrowsError(try SourceMetadataExtractor.extract(from: Data())) { XCTAssertEqual($0 as? SourceMetadataError, .unsupported) }
        XCTAssertEqual(SourceMetadataExtractor.decodedDimensions(from: Data()), nil)
    }

    func testPL0073FocusCannotLockBeforeObservedStabilization() {
        var focus = FocusPolicy()
        XCTAssertEqual(focus.begin(capabilities: FocusCapabilities(point: true, lock: true)), .focusing)
        XCTAssertEqual(focus.lock(capabilities: FocusCapabilities(point: true, lock: true)), .failed)
        XCTAssertEqual(focus.stabilize(), .continuous)
        XCTAssertEqual(focus.lock(capabilities: FocusCapabilities(point: true, lock: true)), .locked)
    }

    func testPL0074ExposureReadingIsPersistableOnlyWhenValid() throws {
        let reading = try ExposureCaptureBinding(reading: ExposureCaptureReading(exposureSeconds: 0.02, iso: 200, bias: 0), state: .locked)
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle)
        let base = PhotoCaptureMetadata(photoID: "p", imagePath: "images/p.heic", sequence: 0, originalFilename: "p.heic", pixelDimensions: CaptureDimensions(width: 2, height: 2), orientation: "portrait", lensIdentity: lens, focalLengthMM: SourceMeasurement(status: .unavailable), exposureSeconds: SourceMeasurement(status: .unavailable), iso: SourceMeasurement(status: .unavailable), whiteBalanceKelvin: SourceMeasurement(status: .unavailable), captureTimestamp: Date())
        let bound = AcceptedPhotoMetadataFactory.withCaptureReadings(base, exposure: reading, whiteBalance: nil)
        XCTAssertEqual(bound.iso.value, 200)
        XCTAssertEqual(bound.exposureSeconds.source, "device_api")
    }

    func testPL0075WhiteBalanceRequiresObservedReadingBeforeAcceptedMetadata() throws {
        let binding = try WhiteBalanceCaptureBinding(reading: WhiteBalanceCaptureReading(temperatureKelvin: 5000), state: .locked)
        XCTAssertTrue(binding.reading.isValid)
        XCTAssertThrowsError(try WhiteBalanceCaptureBinding(reading: WhiteBalanceCaptureReading(temperatureKelvin: 999)))
    }

    func testPL0076SchemaMapperRejectsStatusValueInconsistency() {
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle)
        let metadata = PhotoCaptureMetadata(photoID: "p", imagePath: "images/p.heic", sequence: 0, originalFilename: "p.heic", pixelDimensions: CaptureDimensions(width: 1, height: 1), orientation: "portrait", lensIdentity: lens, focalLengthMM: SourceMeasurement(status: .unavailable, value: 10), exposureSeconds: SourceMeasurement(status: .unavailable), iso: SourceMeasurement(status: .unavailable), whiteBalanceKelvin: SourceMeasurement(status: .unavailable), captureTimestamp: Date())
        XCTAssertThrowsError(try PackScanPhotoMetadataWire.from(metadata)) { XCTAssertEqual($0 as? PhotoMetadataBindingError, .schemaViolation) }
    }

    func testPL0077RecoveryCancelsOnlyInFlightCaptureAndRetriesRestart() {
        var model = CameraRecoveryIntegrationModel()
        XCTAssertTrue(model.beginCapture(id: "in-flight"))
        model.signal(.runtimeError)
        XCTAssertNil(model.inFlightCaptureID)
        XCTAssertEqual(model.machine.state, .restarting)
        XCTAssertEqual(model.machine.apply(.restartFailed), .restarting)
        XCTAssertEqual(model.machine.apply(.restartFailed), .failed)
    }

    func testPL0078HealthMonitorGateIsTheCaptureAdmissionBoundary() {
        var controller = CaptureAdmissionController()
        controller.update(.warning(DeviceHealthPolicy.evaluate(DeviceHealthSnapshot(thermal: .fair, availableStorageBytes: 500_000_000, batteryLevel: 0.5, batteryStateAvailable: true))))
        XCTAssertTrue(controller.allowsCapture)
        controller.update(.hardStop(DeviceHealthPolicy.evaluate(DeviceHealthSnapshot(thermal: .critical, availableStorageBytes: 1, batteryLevel: 0.01, batteryStateAvailable: true))))
        XCTAssertFalse(controller.allowsCapture)
    }

    func testPL0079FoundationTrackingServiceUsesOneLifecycleContract() async {
        let service = FoundationARTrackingService(isAvailable: true)
        await service.start()
        let runningState = await service.state()
        let runningSnapshot = await service.snapshot()
        XCTAssertEqual(runningState, .tracking)
        XCTAssertTrue(runningSnapshot.poseEvidenceEligible)
        await service.stop()
        let stoppedState = await service.state()
        XCTAssertEqual(stoppedState, .idle)
    }

    func testPL0080AcceptedStillUsesTheARKitMonotonicDomainBridge() {
        let wall = Date(timeIntervalSince1970: 50)
        let bridge = TimestampDomainBridge(wallReference: wall, monotonicReference: 5)
        XCTAssertEqual(bridge.monotonic(for: wall.addingTimeInterval(0.25)), 5.25, accuracy: 0.000001)
    }

    func testPL0081MotionRecordsCarryAttitudeAndRotationRateBehindBoundedBuffer() {
        var buffer = MotionBuffer(capacity: 2)
        buffer.append(MotionSampleRecord(monotonicTimestamp: 1, attitude: [0, 0, 0, 1], rotationRate: [0.1, 0.2, 0.3]))
        buffer.append(MotionSampleRecord(monotonicTimestamp: 2, attitude: [0, 0, 0, 1], rotationRate: [0.4, 0.5, 0.6]))
        buffer.append(MotionSampleRecord(monotonicTimestamp: 3, attitude: [0, 0, 0, 1], rotationRate: [0.7, 0.8, 0.9]))
        XCTAssertEqual(buffer.samples.count, 2)
        XCTAssertEqual(buffer.samples.last?.rotationRate, [0.7, 0.8, 0.9])
    }

    func testPL0082GoldenCoordinateRotationsAndBasisVersion() {
        XCTAssertEqual(CoordinateTransform.rotationX(.pi / 2).values[6], -1, accuracy: 1e-12)
        XCTAssertEqual(CoordinateTransform.rotationY(.pi / 2).values[8], -1, accuracy: 1e-12)
        XCTAssertEqual(CoordinateTransform.rotationZ(.pi / 2).values[4], 1, accuracy: 1e-12)
        XCTAssertEqual(PackScanCoordinateContract.basisConversion, "arkit_to_packscan_identity_shared_right_handed_basis_v1")
    }

    func testPL0083TrackingRecoveryHysteresisRetainsDiagnostics() {
        var recovery = TrackingRecoveryPolicy(requiredStableNormalFrames: 2)
        XCTAssertFalse(recovery.update(state: .normal).poseEvidenceEligible)
        XCTAssertFalse(recovery.update(state: .limited, limitation: .insufficientFeatures).poseEvidenceEligible)
        XCTAssertFalse(recovery.update(state: .normal).poseEvidenceEligible)
        XCTAssertTrue(recovery.update(state: .normal).poseEvidenceEligible)
        XCTAssertEqual(recovery.diagnostics.count, 4)
    }

    func testPL0084ResetEpochSeparatesOldPoseAndRetainsReason() {
        var epochs = SessionEpochCoordinator()
        epochs.reset(reason: .trackingDegraded)
        XCTAssertFalse(epochs.accepts(poseEpoch: 0))
        XCTAssertFalse(epochs.accepts(poseEpoch: 1))
        epochs.recovered()
        XCTAssertTrue(epochs.accepts(poseEpoch: 1))
        XCTAssertEqual(epochs.lastReason, .trackingDegraded)
    }

    func testPL0085OverlayUsesCurrentPoseMotionAndEpoch() {
        let snapshot = TrackingSnapshot(quality: .normal, poseEvidenceEligible: true, message: "Tracking ready")
        let pose = PoseSample(timestamp: 3, transform: CoordinateTransform.identity.values, tracking: .normal)
        let motion = MotionSampleRecord(monotonicTimestamp: 3, attitude: [0, 0, 0, 1], rotationRate: [0, 0, 0])
        let overlay = PoseOverlayModel.make(visible: true, tracking: snapshot, epoch: 4, pose: pose, motion: motion)
        XCTAssertTrue(overlay.lines.contains("Epoch: 4"))
        XCTAssertTrue(overlay.lines.contains { $0.contains("Motion t=") })
    }

    func testPL0086DiagnosticsExportCarriesUnitsAndUsesPrivacyBoundary() throws {
        let pose = AlignedPose(sample: PoseSample(timestamp: 1, transform: CoordinateTransform.identity.values, tracking: .normal), delta: 0, status: "available")
        let data = try PoseDiagnosticsExporter.encode(records: [PoseDiagnosticRecord(captureID: "../private", captureTimestamp: 1, pose: pose, motion: nil, epoch: 0)])
        let json = String(decoding: data, as: UTF8.self)
        XCTAssertTrue(json.contains("basis_conversion")); XCTAssertTrue(json.contains("translation_unit")); XCTAssertFalse(json.contains("../private"))
    }

    func testPL0087WorkflowSeamInvokesStartOnlyForValidDraft() {
        var workflow = NewScanWorkflowModel()
        XCTAssertNil(workflow.start(name: "", type: .bottle, mode: .freehand, sessionID: "bad"))
        XCTAssertNotNil(workflow.start(name: "Bottle", type: .bottle, mode: .guidedOrbit, sessionID: "good"))
        if case .started(let draft) = workflow.state { XCTAssertEqual(draft.captureMode, .guidedOrbit) } else { XCTFail("valid draft must reach started state") }
    }

    func testPL0088CanonicalRecordReopenRequiresSourceAndRecordTogether() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "atomic")
        let store = ScanSessionStore(layout: layout)
        try await store.create(NewScanDraft(sessionID: "atomic", packageName: "Bottle", packageType: .bottle, captureMode: .freehand))
        let record = AcceptedCaptureRecord(captureID: "p1", sequence: 0, sourceFilename: "p1.heic", metadataFilename: "p1.json")
        let state = try JSONEncoder().encode(PersistedSessionState(sessionID: "atomic", nextSequence: 1, epoch: 0, acceptedIDs: ["p1"]))
        try await store.storeAcceptedCapture(source: Data([1]), record: record, metadata: Data("{}".utf8), state: state)
        XCTAssertEqual(try JSONDecoder().decode(AcceptedCaptureRecord.self, from: Data(contentsOf: layout.photoRecords.appendingPathComponent("p1.json"))).captureID, "p1")
    }

    func testPL0089GalleryOrderingAndReplacementTraceRemainDeterministic() throws {
        var gallery = GalleryModel(entries: [GalleryEntry(id: "a", previewPath: nil, sourcePath: "images/a.heic", sequence: 0)])
        try gallery.retake(replacing: "a", with: GalleryEntry(id: "b", previewPath: nil, sourcePath: "images/b.heic", sequence: 1))
        XCTAssertEqual(gallery.replacementTrace["a"], "b")
        XCTAssertEqual(gallery.entries.map(\.id), ["a", "b"])
    }

    func testPL0090ResumeValidatorBlocksMissingCorruptAndVersionMismatchedState() {
        XCTAssertEqual(SessionResumeValidator.disposition(state: nil, requiredSourceIDs: []), .blocked("missing_state"))
        XCTAssertEqual(SessionResumeValidator.disposition(state: PersistedSessionState(sessionID: "s", schemaVersion: "2.0.0", nextSequence: 0, epoch: 0, acceptedIDs: []), requiredSourceIDs: []), .blocked("version_mismatch"))
        XCTAssertEqual(SessionResumeValidator.disposition(state: PersistedSessionState(sessionID: "s", nextSequence: 1, epoch: 0, acceptedIDs: ["missing"]), requiredSourceIDs: []), .blocked("missing_source"))
    }

    func testPL0091FinalizationCanonicalizationConstantMatchesM02() {
        XCTAssertEqual(PackScanWriter.checksumCanonicalization, "sha256_32_bytes_lowercase_hex_64_chars_v1")
    }

    func testPL0092HistoryRetainsDegradedStateInsteadOfDowngradingCorruption() {
        let entry = ScanHistoryIndex().degraded(id: "s1", reason: "corrupt_finalization")
        XCTAssertEqual(entry.exportState, "unavailable")
        XCTAssertEqual(entry.degradedReason, "corrupt_finalization")
    }

    func testPL0093DeletionRequiresAuthoritativeCandidateIdentity() {
        let root = URL(fileURLWithPath: "/tmp/packlab")
        let directPlan = SessionDeletionPlan(root: root, session: root.appendingPathComponent("s1"))
        XCTAssertThrowsError(try directPlan.validate(confirmed: true)) { XCTAssertEqual($0 as? DeletionError, .nonAuthoritative) }
        let blocked = SessionDeletionPlan(root: root, candidate: SessionResumeCandidate(id: "s1", draft: nil, disposition: .blocked("corrupt"), state: nil))
        XCTAssertThrowsError(try blocked.validate(confirmed: true)) { XCTAssertEqual($0 as? DeletionError, .outsideRoot) }
    }

    func testPreviewAuthorizationAndFailureLifecycleRecover() {
        var lifecycle = PreviewLifecyclePolicy()
        XCTAssertFalse(lifecycle.beginAuthorizedStart(.denied))
        XCTAssertFalse(lifecycle.isStarted)
        XCTAssertTrue(lifecycle.beginAuthorizedStart(.authorized))
        lifecycle.markStartedAfterSuccessfulStart()
        XCTAssertTrue(lifecycle.isStarted)
        XCTAssertTrue(lifecycle.stopIfNeeded())
        XCTAssertTrue(lifecycle.beginAuthorizedStart(.authorized))
        lifecycle.markStartedAfterSuccessfulStart()
        XCTAssertTrue(lifecycle.stopIfNeeded())
        XCTAssertEqual(PreviewAuthorizationResolver.state(for: .denied), .denied)
        XCTAssertEqual(PreviewAuthorizationResolver.state(for: CameraServiceError.failed("start")), .error("start"))
    }

    func testStillAdapterBoundaryRejectsDuplicateAndSessionStop() {
        var lifecycle = StillCaptureLifecycle()
        XCTAssertTrue(lifecycle.begin())
        XCTAssertTrue(lifecycle.complete(success: false))
        XCTAssertFalse(lifecycle.complete(success: true))
        lifecycle.reset()
        XCTAssertTrue(lifecycle.begin())
        XCTAssertTrue(lifecycle.complete(success: true))
    }

    func testSourceDerivativeAndSchemaBoundariesAreFailClosed() throws {
        let bytes = Data([1, 2, 3])
        let record = OriginalSourceRecord(captureID: "p1", filename: "p1.heic", dimensions: CaptureDimensions(width: 3, height: 2), orientation: "portrait", sha256: SourceIntegrity.digest(bytes))
        XCTAssertNoThrow(try SourceIntegrity.validateDerivative(URL(fileURLWithPath: "/tmp/p1.jpg"), master: URL(fileURLWithPath: "/tmp/p1.heic")))
        XCTAssertThrowsError(try SourceIntegrity.validateDerivative(URL(fileURLWithPath: "/tmp/p1.heic"), master: URL(fileURLWithPath: "/tmp/p1.heic")))
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle)
        let bad = PhotoCaptureMetadata(photoID: "p1", imagePath: "images/p1.heic", sequence: 0, originalFilename: "p1.heic", pixelDimensions: record.dimensions, orientation: "portrait", lensIdentity: lens, focalLengthMM: SourceMeasurement(status: .available, value: -1, source: "device_api"), exposureSeconds: SourceMeasurement(status: .unavailable), iso: SourceMeasurement(status: .unavailable), whiteBalanceKelvin: SourceMeasurement(status: .unavailable), captureTimestamp: Date())
        XCTAssertThrowsError(try PackScanPhotoMetadataWire.from(bad)) { XCTAssertEqual($0 as? PhotoMetadataBindingError, .schemaViolation) }
    }

    func testActualReadingsBindIntoAcceptedPhotoMetadata() throws {
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle)
        let base = PhotoCaptureMetadata(photoID: "p1", imagePath: "images/p1.heic", sequence: 0, originalFilename: "p1.heic", pixelDimensions: CaptureDimensions(width: 10, height: 8), orientation: "portrait", lensIdentity: lens, focalLengthMM: SourceMeasurement(status: .unavailable), exposureSeconds: SourceMeasurement(status: .unavailable), iso: SourceMeasurement(status: .unavailable), whiteBalanceKelvin: SourceMeasurement(status: .unavailable), captureTimestamp: Date())
        let exposure = try ExposureCaptureBinding(reading: ExposureCaptureReading(exposureSeconds: 0.01, iso: 400, bias: 0), state: .locked)
        let wb = try WhiteBalanceCaptureBinding(reading: WhiteBalanceCaptureReading(temperatureKelvin: 5200), state: .locked)
        let bound = AcceptedPhotoMetadataFactory.withCaptureReadings(base, exposure: exposure, whiteBalance: wb)
        XCTAssertEqual(bound.exposureSeconds.value, 0.01)
        XCTAssertEqual(bound.iso.value, 400)
        XCTAssertEqual(bound.whiteBalanceKelvin.value, 5200)
    }

    func testHealthAdmissionBlocksHardStopButAllowsWarning() {
        var admission = CaptureAdmissionController()
        let warning = DeviceHealthCaptureGate.evaluate(DeviceHealthSnapshot(thermal: .fair, availableStorageBytes: 500_000_000, batteryLevel: 0.5, batteryStateAvailable: true))
        admission.update(warning)
        XCTAssertTrue(admission.allowsCapture)
        admission.update(DeviceHealthCaptureGate.evaluate(DeviceHealthSnapshot(thermal: .critical, availableStorageBytes: 1, batteryLevel: 0.01, batteryStateAvailable: true)))
        XCTAssertFalse(admission.allowsCapture)
        XCTAssertNotNil(admission.rejectReason())
    }

    func testPoseClockBridgeBindsAcceptedStillAndExactBoundaries() {
        let bridge = TimestampDomainBridge(wallReference: Date(timeIntervalSince1970: 100), monotonicReference: 10)
        let still = AcceptedStill(captureID: "p1", sourceBytes: Data([1]), dimensions: CaptureDimensions(width: 1, height: 1), capturedAt: Date(timeIntervalSince1970: 100.1))
        var buffer = PoseBuffer()
        buffer.append(PoseSample(timestamp: 10.2, transform: CoordinateTransform.identity.values, tracking: .normal))
        XCTAssertEqual(AcceptedStillPoseBinder.bind(still: still, buffer: buffer, bridge: bridge)?.aligned.status, "available")
        XCTAssertEqual(PoseAligner.nearest(to: 10.1, samples: [PoseSample(timestamp: 10.2, transform: CoordinateTransform.identity.values, tracking: .normal)], tolerance: 0.1).status, "available")
        XCTAssertEqual(PoseAligner.nearest(to: 10.101, samples: [PoseSample(timestamp: 10.2, transform: CoordinateTransform.identity.values, tracking: .normal)], tolerance: 0.1).status, "stale")
    }

    func testCoordinateGoldensAndBasisContract() {
        let x = CoordinateTransform.rotationX(.pi / 2).values
        let y = CoordinateTransform.rotationY(.pi / 2).values
        let z = CoordinateTransform.rotationZ(.pi / 2).values
        XCTAssertEqual(x[5], 0, accuracy: 1e-12); XCTAssertEqual(x[6], -1, accuracy: 1e-12); XCTAssertEqual(x[9], 1, accuracy: 1e-12)
        XCTAssertEqual(y[0], 0, accuracy: 1e-12); XCTAssertEqual(y[2], 1, accuracy: 1e-12); XCTAssertEqual(y[8], -1, accuracy: 1e-12)
        XCTAssertEqual(z[0], 0, accuracy: 1e-12); XCTAssertEqual(z[1], -1, accuracy: 1e-12); XCTAssertEqual(z[4], 1, accuracy: 1e-12)
        XCTAssertEqual(PackScanCoordinateContract.basisConversion, "arkit_to_packscan_identity_shared_right_handed_basis_v1")
    }

    func testDiagnosticsExportContainsVersionedUnitsAndRejectsBadRecords() throws {
        let pose = AlignedPose(sample: PoseSample(timestamp: 2, transform: CoordinateTransform.identity.values, tracking: .normal), delta: 0, status: "available")
        let data = try PoseDiagnosticsExporter.encode(records: [PoseDiagnosticRecord(captureID: "safe", captureTimestamp: 2, pose: pose, motion: nil, epoch: 1)])
        let json = String(decoding: data, as: UTF8.self)
        XCTAssertTrue(json.contains("basis_conversion")); XCTAssertTrue(json.contains("translation_unit")); XCTAssertTrue(json.contains("attitude_order"))
        XCTAssertThrowsError(try PoseDiagnosticsExporter.encode(records: [PoseDiagnosticRecord(captureID: "", captureTimestamp: 2, pose: pose, motion: nil, epoch: 1)])) { XCTAssertEqual($0 as? PoseDiagnosticsError, .invalidCaptureID) }
    }

    func testTransactionRecordIsCanonicalAndReopenRejectsMissingRecord() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "tx")
        let store = ScanSessionStore(layout: layout)
        try await store.create(NewScanDraft(sessionID: "tx", packageName: "Bottle", packageType: .bottle, captureMode: .freehand))
        let record = AcceptedCaptureRecord(captureID: "p1", sequence: 0, sourceFilename: "p1.heic", metadataFilename: "p1.json")
        let state = try JSONEncoder().encode(PersistedSessionState(sessionID: "tx", nextSequence: 1, epoch: 0, acceptedIDs: ["p1"]))
        try await store.storeAcceptedCapture(source: Data([1]), record: record, metadata: Data("{}".utf8), state: state)
        XCTAssertEqual(try JSONDecoder().decode(AcceptedCaptureRecord.self, from: Data(contentsOf: layout.photoRecords.appendingPathComponent("p1.json"))), record)
        try FileManager.default.removeItem(at: layout.photoRecords.appendingPathComponent("p1.json"))
        if case .blocked(let reason) = try await store.reopen(requiredSourceIDs: []) { XCTAssertEqual(reason, "missing_or_corrupt_record") } else { XCTFail("missing record must block reopen") }
    }

    func testHistoryMarksCorruptFinalizationAsDegraded() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "history")
        try FileManager.default.createDirectory(at: layout.previews, withIntermediateDirectories: true)
        try JSONEncoder().encode(NewScanDraft(sessionID: "history", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)).write(to: layout.metadata)
        try Data("not-json".utf8).write(to: layout.finalization)
        let entries = await LocalScanHistoryStore(root: root).load()
        XCTAssertEqual(entries.first?.exportState, "corrupt")
        XCTAssertEqual(entries.first?.degradedReason, "corrupt_finalization")
    }

    func testFinalizerWritesRealPackageAndKeepsSessionResumableOnDestinationFailure() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        let image = Data([1, 2, 3])
        let unavailable = PackScanNumericMeasurement(status: .unavailable)
        let wire = PackScanPhotoMetadataWire(photoID: "p", imagePath: "images/p.heic", sequence: 0, originalFilename: "p.heic", pixelDimensions: CaptureDimensions(width: 1, height: 1), orientation: PackScanOrientation(value: .unknown, source: .unknown), focalLengthMM: unavailable, exposure: unavailable, iso: PackScanISOMeasurement(status: .unavailable), whiteBalanceKelvin: unavailable)
        let metadata = try JSONEncoder().encode(PackScanPhotoMetadataDocument(photos: [wire]))
        let manifestObject: [String: Any] = ["schema_version": "1.0.0", "capture_id": "session", "checksums": ["algorithm": "sha256", "canonicalization": PackScanWriter.checksumCanonicalization], "payloads": [["path": "metadata/photos.json", "kind": "photo_metadata", "required": true, "authority": "source", "size_bytes": metadata.count, "sha256": SourceIntegrity.digest(metadata)], ["path": "images/p.heic", "kind": "image", "required": true, "authority": "source", "size_bytes": image.count, "sha256": SourceIntegrity.digest(image)]]]
        let manifest = try JSONSerialization.data(withJSONObject: manifestObject)
        let destination = root.appendingPathComponent("out.packscan")
        try SessionFinalizer().finalize(FinalizationInput(manifest: manifest, payloads: ["metadata/photos.json": metadata, "images/p.heic": image], destination: destination, sessionRoot: root))
        XCTAssertTrue(FileManager.default.fileExists(atPath: destination.path))
        XCTAssertTrue(FileManager.default.fileExists(atPath: root.appendingPathComponent("finalization.json").path))
        XCTAssertThrowsError(try SessionFinalizer().finalize(FinalizationInput(manifest: manifest, payloads: ["metadata/photos.json": metadata, "images/p.heic": image], destination: destination, sessionRoot: root))) { XCTAssertEqual($0 as? FinalizationError, .packagingFailed) }
        XCTAssertTrue(FileManager.default.fileExists(atPath: destination.path))
    }

    func testDeletionRejectsNonAuthoritativeAndReportsInjectedPartialFailure() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        try FileManager.default.createDirectory(at: root.appendingPathComponent("s1"), withIntermediateDirectories: true)
        let nonAuthoritative = SessionDeletionPlan(root: root, session: root.appendingPathComponent("s1"))
        XCTAssertThrowsError(try nonAuthoritative.validate(confirmed: true)) { XCTAssertEqual($0 as? DeletionError, .nonAuthoritative) }
        let candidate = SessionResumeCandidate(id: "s1", draft: nil, disposition: .resumable, state: nil)
        let report = try await SafeSessionDeleter(failureInjector: { _ in true }).deleteDetailed(plan: SessionDeletionPlan(root: root, candidate: candidate), confirmed: true)
        XCTAssertEqual(report.failures, [root.appendingPathComponent("s1").path])
    }

    @MainActor
    func testPL0069PreviewBridgeDrivesAuthorizationFailureAndSymmetricLifecycle() {
        final class Driver: PreviewSessionDriver {
            var isAttached = false; var isRunning = false; var attachCount = 0; var startCount = 0; var stopCount = 0; var detachCount = 0; var shouldFail = false
            func attach() throws { attachCount += 1; isAttached = true }
            func detach() { detachCount += 1; isAttached = false }
            func start() throws { startCount += 1; if shouldFail { throw CameraServiceError.failed("injected") }; isRunning = true }
            func stop() { stopCount += 1; isRunning = false }
        }
        let driver = Driver(); let bridge = PreviewBridgeController(driver: driver)
        bridge.appear(authorization: .denied); XCTAssertEqual(bridge.state, .denied); XCTAssertEqual(driver.startCount, 0)
        bridge.appear(authorization: .authorized); XCTAssertEqual(bridge.state, .running); XCTAssertEqual(driver.attachCount, 1); XCTAssertEqual(driver.startCount, 1)
        bridge.disappear(); XCTAssertEqual(driver.stopCount, 1); XCTAssertEqual(driver.detachCount, 1)
        driver.shouldFail = true; bridge.appear(authorization: .authorized); if case .error = bridge.state {} else { XCTFail("start failure must be visible") }; XCTAssertFalse(driver.isRunning)
    }

    @MainActor
    func testPL0071StillPhotoDriverCoreUsesSelectedLensAndExactOnceCallbacks() async throws {
        final class Driver: StillPhotoDriver {
            var canCapturePhoto = true; var delegate: (any StillPhotoDriverDelegate)?; var captures = 0
            func capturePhoto() { captures += 1 }
            func cancelPhotoCapture() {}
            func finish(_ bytes: Data = Data([1, 2]), dimensions: CaptureDimensions = CaptureDimensions(width: 2, height: 1)) { delegate?.stillPhotoDriver(self, didFinish: bytes, dimensions: dimensions); delegate?.stillPhotoDriverDidFinishWithoutData(self) }
        }
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle); let driver = Driver(); let core = StillPhotoAdapterCore(driver: driver, selectedLens: lens, activeLensIdentifier: { "main" })
        let task = Task { try await core.requestOriginalStill() }; await Task.yield(); driver.finish(); let result = try await task.value
        XCTAssertEqual(result.bytes, Data([1, 2])); XCTAssertEqual(driver.captures, 1)
        let wrong = StillPhotoAdapterCore(driver: driver, selectedLens: lens, activeLensIdentifier: { "tele" }); do { _ = try await wrong.requestOriginalStill(); XCTFail("wrong lens must fail") } catch { XCTAssertEqual(error as? CameraServiceError, .failed("selected_lens_mismatch")) }
    }

    func testPL0072AcceptedStillPipelineRequiresImageSourceAndDecodedDimensions() throws {
        #if canImport(ImageIO)
        #if canImport(CoreGraphics) && canImport(UniformTypeIdentifiers)
        func fixture(_ type: UTType) throws -> Data {
            var pixels = [UInt8](repeating: 255, count: 2 * 3 * 4); let space = CGColorSpaceCreateDeviceRGB(); let context = CGContext(data: &pixels, width: 2, height: 3, bitsPerComponent: 8, bytesPerRow: 8, space: space, bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!; let image = context.makeImage()!; let data = NSMutableData(); let destination = CGImageDestinationCreateWithData(data, type.identifier as CFString, 1, nil)!; CGImageDestinationAddImage(destination, image, nil); XCTAssertTrue(CGImageDestinationFinalize(destination)); return data as Data
        }
        for (type, name) in [(UTType.jpeg, "p.jpg"), (UTType.heic, "p.heic")] {
            let bytes = try fixture(type); let record = try OriginalSourceRecord.fromSource(captureID: "p", filename: name, dimensions: CaptureDimensions(width: 2, height: 3), orientation: "landscape", bytes: bytes); XCTAssertEqual(record.sha256, SourceIntegrity.digest(bytes)); XCTAssertFalse(record.metadataBytes.isEmpty); XCTAssertEqual(SourceMetadataExtractor.decodedDimensions(from: bytes), CaptureDimensions(width: 2, height: 3))
        }
        #else
        XCTAssertThrowsError(try OriginalSourceRecord.fromSource(captureID: "p", filename: "p.heic", dimensions: CaptureDimensions(width: 1, height: 1), orientation: "unknown", bytes: Data([1, 2, 3])))
        #endif
        #else
        XCTAssertThrowsError(try SourceMetadataExtractor.extract(from: Data()))
        #endif
    }

    @MainActor
    func testPL0073ToPL0075ControlBridgePublishesObservedStates() {
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle); let bridge = CameraControlRuntimeBridge(lens: lens); var observed: [CameraCaptureControlState] = []; bridge.onStateChange = { observed.append($0) }
        bridge.setFocus(.continuous); bridge.setExposure(.metering); bridge.setWhiteBalance(.stabilizing)
        XCTAssertEqual(observed.last?.focus, .continuous); XCTAssertEqual(observed.last?.exposure, .metering); XCTAssertEqual(observed.last?.whiteBalance, .stabilizing)
    }

    func testPL0076ISORejectsForbiddenStatusValueAndAcceptsSchemaBoundaries() {
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle)
        let base = PhotoCaptureMetadata(photoID: "p", imagePath: "images/p.heic", sequence: 0, originalFilename: "p.heic", pixelDimensions: CaptureDimensions(width: 1, height: 1), orientation: "portrait", lensIdentity: lens, focalLengthMM: SourceMeasurement(status: .unavailable), exposureSeconds: SourceMeasurement(status: .unavailable), iso: SourceMeasurement(status: .unavailable, value: 1, unit: "iso", source: "device_api"), whiteBalanceKelvin: SourceMeasurement(status: .unavailable), captureTimestamp: Date())
        XCTAssertThrowsError(try PackScanPhotoMetadataWire.from(base))
        let valid = PhotoCaptureMetadata(photoID: "p", imagePath: "images/p.heic", sequence: 0, originalFilename: "p.heic", pixelDimensions: base.pixelDimensions, orientation: "portrait", lensIdentity: lens, focalLengthMM: base.focalLengthMM, exposureSeconds: base.exposureSeconds, iso: SourceMeasurement(status: .available, value: 1, unit: "iso", source: "device_api"), whiteBalanceKelvin: base.whiteBalanceKelvin, captureTimestamp: base.captureTimestamp)
        XCTAssertNoThrow(try PackScanPhotoMetadataWire.from(valid))
    }

    func testPL0078AdmissionBoundaryBlocksPhysicalBackendAndRecovers() async {
        final class Backend: StillPhotoBackend, @unchecked Sendable { var calls = 0; func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) { calls += 1; return (Data([1]), CaptureDimensions(width: 1, height: 1)) } }
        let backend = Backend(); let service = AdmissionControlledStillCaptureService(backend: backend); var admission = CaptureAdmissionController(); admission.update(.hardStop(DeviceHealthPolicy.evaluate(DeviceHealthSnapshot(thermal: .critical, availableStorageBytes: 1, batteryLevel: 0, batteryStateAvailable: true)))); await service.updateAdmission(admission); if case .rejected = await service.capture(captureID: "blocked") {} else { XCTFail("hard stop must reject") }; XCTAssertEqual(backend.calls, 0); admission.update(.ready(DeviceHealthPolicy.evaluate(UnavailableDeviceHealthProvider().snapshot()))); await service.updateAdmission(admission); if case .accepted = await service.capture(captureID: "ready") {} else { XCTFail("ready state must capture") }; XCTAssertEqual(backend.calls, 1)
    }

    @MainActor
    func testPL0083AndPL0085RuntimeRefreshUsesInjectedServicesAndStops() async {
        let tracking = SequenceTrackingService([TrackingQualityClassifier.classify(state: .limited), TrackingQualityClassifier.classify(state: .normal), TrackingQualityClassifier.classify(state: .normal)]); let motion = SequenceMotionService(); let vm = CaptureRuntimeViewModel(trackingService: tracking, motionService: motion, healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider())); await vm.start(); await vm.refresh(); XCTAssertFalse(vm.tracking.poseEvidenceEligible); await vm.refresh(); XCTAssertFalse(vm.tracking.poseEvidenceEligible); await vm.refresh(); XCTAssertTrue(vm.tracking.poseEvidenceEligible); let count = vm.trackingDiagnostics.count; await vm.stop(); await vm.refresh(); XCTAssertEqual(vm.trackingDiagnostics.count, count)
    }

    func testPL0086DiagnosticsExactLimitAndRealisticPrivacyBoundary() throws {
        let pose = AlignedPose(sample: PoseSample(timestamp: 1, transform: CoordinateTransform.identity.values, tracking: .normal), delta: 0, status: "available"); let record = PoseDiagnosticRecord(captureID: "C:\\Users\\Alice\\private\\capture", captureTimestamp: 1, pose: pose, motion: nil, epoch: 0); XCTAssertNoThrow(try PoseDiagnosticsExporter.encode(records: [record], maximumRecords: 1)); XCTAssertThrowsError(try PoseDiagnosticsExporter.encode(records: [record, record], maximumRecords: 1)); let text = String(decoding: try PoseDiagnosticsExporter.encode(records: [record]), as: UTF8.self); XCTAssertFalse(text.contains("Alice")); XCTAssertFalse(text.contains("private"))
    }

    func testPL0087NewScanCallbackCoordinatorCallsStartExactlyOnce() {
        var workflow = NewScanWorkflowModel(); var callbacks = 0; XCTAssertFalse(NewScanActionCoordinator.start(workflow: &workflow, name: "", type: .bottle, mode: .freehand, notes: "", onStart: { _ in callbacks += 1 })); XCTAssertEqual(callbacks, 0); XCTAssertTrue(NewScanActionCoordinator.start(workflow: &workflow, name: "Bottle", type: .bottle, mode: .guidedOrbit, notes: "", onStart: { _ in callbacks += 1 })); XCTAssertEqual(callbacks, 1); NewScanActionCoordinator.cancel(workflow: &workflow); XCTAssertEqual(callbacks, 1)
    }

    func testPL0088TransactionRecoveryRollsBackPartialFinalMoves() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let layout = SessionStorageLayout(root: root, sessionID: "tx"); let store = ScanSessionStore(layout: layout); try await store.create(NewScanDraft(sessionID: "tx", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)); let tx = layout.temporary.appendingPathComponent(".txn-crash", isDirectory: true); try FileManager.default.createDirectory(at: tx, withIntermediateDirectories: true); let oldState = try Data(contentsOf: layout.state); try oldState.write(to: tx.appendingPathComponent("previous-state.json")); try Data([1]).write(to: tx.appendingPathComponent("p.heic")); let record = AcceptedCaptureRecord(captureID: "p", sequence: 0, sourceFilename: "p.heic", metadataFilename: "p.json"); try JSONEncoder().encode(record).write(to: tx.appendingPathComponent("p.json")); try JSONEncoder().encode(PersistedSessionState(sessionID: "tx", nextSequence: 1, epoch: 0, acceptedIDs: ["p"])).write(to: tx.appendingPathComponent("state.json")); try JSONEncoder().encode(SessionTransactionMarker(captureID: "p", sourceFilename: "p.heic", recordFilename: "p.json", stage: .recordCommitted)).write(to: tx.appendingPathComponent("marker.json")); try FileManager.default.moveItem(at: tx.appendingPathComponent("p.heic"), to: layout.images.appendingPathComponent("p.heic")); if case .resumable(let recovered) = try await store.reopen(requiredSourceIDs: []) { XCTAssertTrue(recovered.acceptedIDs.isEmpty) } else { XCTFail("rollback should leave a clean resumable session") }; XCTAssertFalse(FileManager.default.fileExists(atPath: layout.images.appendingPathComponent("p.heic").path))
    }

    func testPL0089GalleryFailureRestoresFilesStateAndAudit() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let layout = SessionStorageLayout(root: root, sessionID: "gallery"); let session = ScanSessionStore(layout: layout); try await session.create(NewScanDraft(sessionID: "gallery", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)); let record = AcceptedCaptureRecord(captureID: "a", sequence: 0, sourceFilename: "a.heic", metadataFilename: "a.json"); try await session.storeAcceptedCapture(source: Data([1]), record: record, metadata: Data("{}".utf8), state: try JSONEncoder().encode(PersistedSessionState(sessionID: "gallery", nextSequence: 1, epoch: 0, acceptedIDs: ["a"]))); let failing = SessionGalleryStore(layout: layout, failureInjector: { $0 == "mutation.auditCommit" }); do { try await failing.delete(id: "a", confirmed: true); XCTFail("failed gallery mutation must throw") } catch { XCTAssertEqual(error as? SessionStorageError, .interruptedWrite) }; XCTAssertTrue(FileManager.default.fileExists(atPath: layout.images.appendingPathComponent("a.heic").path)); XCTAssertEqual(try JSONDecoder().decode(PersistedSessionState.self, from: Data(contentsOf: layout.state)).acceptedIDs, ["a"])
    }

    func testPL0091FinalizationFailureLeavesFreshDestinationAbsent() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true); let metadata = try JSONEncoder().encode(PackScanPhotoMetadataDocument(photos: [PackScanPhotoMetadataWire(photoID: "p", imagePath: "images/p.heic", sequence: 0, originalFilename: "p.heic", pixelDimensions: CaptureDimensions(width: 1, height: 1), orientation: PackScanOrientation(value: .unknown, source: .unknown), focalLengthMM: PackScanNumericMeasurement(status: .unavailable), exposure: PackScanNumericMeasurement(status: .unavailable), iso: PackScanISOMeasurement(status: .unavailable), whiteBalanceKelvin: PackScanNumericMeasurement(status: .unavailable))])); let image = Data([1]); let manifest = try JSONSerialization.data(withJSONObject: ["schema_version": "1.0.0", "capture_id": "s", "checksums": ["algorithm": "sha256", "canonicalization": PackScanWriter.checksumCanonicalization], "payloads": [["path": "metadata/photos.json", "kind": "photo_metadata", "required": true, "authority": "source", "size_bytes": metadata.count, "sha256": SourceIntegrity.digest(metadata)], ["path": "images/p.heic", "kind": "image", "required": true, "authority": "source", "size_bytes": image.count, "sha256": SourceIntegrity.digest(image)]]]); let destination = root.appendingPathComponent("fresh.packscan"); XCTAssertThrowsError(try SessionFinalizer(failureInjector: { $0 == "finalization.record" }).finalize(FinalizationInput(manifest: manifest, payloads: ["metadata/photos.json": metadata, "images/p.heic": image], destination: destination, sessionRoot: root))); XCTAssertFalse(FileManager.default.fileExists(atPath: destination.path)); XCTAssertFalse(FileManager.default.fileExists(atPath: root.appendingPathComponent("finalization.json").path))
    }

    func testPL0092HistoryRejectsForeignAndMissingExportedPackage() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let layout = SessionStorageLayout(root: root, sessionID: "history"); try FileManager.default.createDirectory(at: layout.previews, withIntermediateDirectories: true); try Data([1]).write(to: layout.previews.appendingPathComponent("preview.jpg")); try JSONEncoder().encode(NewScanDraft(sessionID: "history", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)).write(to: layout.metadata); try JSONEncoder().encode(SessionFinalizationRecord(sessionID: "foreign", state: "exported", packagePath: root.appendingPathComponent("missing.packscan").path)).write(to: layout.finalization); let entries = await LocalScanHistoryStore(root: root).load(); XCTAssertEqual(entries.first?.degradedReason, "invalid_finalization_identity")
    }

    func testPL0093DeletionAPIThrowsOnPartialFailure() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let session = root.appendingPathComponent("s1"); try FileManager.default.createDirectory(at: session, withIntermediateDirectories: true); let candidate = SessionResumeCandidate(id: "s1", draft: nil, disposition: .resumable, state: nil); let deleter = SafeSessionDeleter(failureInjector: { _ in true }); do { try await deleter.delete(plan: SessionDeletionPlan(root: root, candidate: candidate), confirmed: true); XCTFail("partial delete must throw") } catch { XCTAssertEqual(error as? DeletionError, .partialFailure) }
    }

    func testPL0093RealSymlinkEscapeIsRejectedBeforeDeletion() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let session = root.appendingPathComponent("s1"); let outside = root.deletingLastPathComponent().appendingPathComponent("packlab-outside-\(UUID().uuidString)"); try FileManager.default.createDirectory(at: session, withIntermediateDirectories: true); try FileManager.default.createDirectory(at: outside, withIntermediateDirectories: true); let link = session.appendingPathComponent("linked"); do { try FileManager.default.createSymbolicLink(at: link, withDestinationURL: outside) } catch { throw XCTSkip("symlinks unavailable on this test host") }; let candidate = SessionResumeCandidate(id: "s1", draft: nil, disposition: .resumable, state: nil); XCTAssertThrowsError(try SessionDeletionPlan(root: root, candidate: candidate).validate(confirmed: true)) { XCTAssertEqual($0 as? DeletionError, .symlinkEscape) }
    }
}

// Static verification on Windows covers target wiring, source membership, and privacy settings.
// xcodebuild execution on simulator/macOS CI is intentionally deferred to the authorized M16 runner.
