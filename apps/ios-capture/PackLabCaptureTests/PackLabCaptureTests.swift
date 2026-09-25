import XCTest
@testable import PackLabCapture
#if canImport(CoreGraphics) && canImport(ImageIO) && canImport(UniformTypeIdentifiers)
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers
#endif
#if canImport(ARKit) && canImport(UIKit)
import ARKit
import UIKit
#endif
#if canImport(AVFoundation)
import AVFoundation
#endif
#if canImport(AVFoundation) && canImport(CoreGraphics)
import CoreGraphics

@MainActor
private final class FakeCameraDeviceControlDriver: CameraDeviceControlDriver {
    let uniqueID: String
    let position: AVCaptureDevice.Position
    var supportsContinuousFocus = true
    var supportsLockedFocus = true
    var supportsFocusPoint = true
    var isAdjustingFocus = false
    var focusMode: CameraDeviceFocusMode?
    var focusPoint: CGPoint?
    var supportsContinuousExposure = true
    var supportsLockedExposure = true
    var minExposureTargetBias: Float = -2
    var maxExposureTargetBias: Float = 2
    var exposureDurationSeconds = 0.008
    var iso: Float = 200
    var exposureTargetBias: Float = 0
    var exposureMode: CameraDeviceExposureMode?
    var supportsContinuousWhiteBalance = true
    var supportsLockedWhiteBalance = true
    var isAdjustingWhiteBalance = false
    var temperatureKelvin: Double? = 4500
    var whiteBalanceMode: CameraDeviceWhiteBalanceMode?
    private(set) var configurationCount = 0
    private(set) var configurationDepth = 0
    private(set) var maximumConfigurationDepth = 0

    init(uniqueID: String, position: AVCaptureDevice.Position = .back) { self.uniqueID = uniqueID; self.position = position }
    func setFocusPoint(_ point: CGPoint) { focusPoint = point }
    func setFocusMode(_ mode: CameraDeviceFocusMode) { focusMode = mode }
    func setExposureTargetBias(_ bias: Float) { exposureTargetBias = bias }
    func setExposureMode(_ mode: CameraDeviceExposureMode) { exposureMode = mode }
    func observedTemperatureKelvin() -> Double? { temperatureKelvin }
    func setWhiteBalanceMode(_ mode: CameraDeviceWhiteBalanceMode) { whiteBalanceMode = mode }
    func lockForConfiguration() throws { configurationCount += 1; configurationDepth += 1; maximumConfigurationDepth = max(maximumConfigurationDepth, configurationDepth) }
    func unlockForConfiguration() { configurationDepth -= 1 }
}

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

private func acceptedPoseBinding(captureID: String, pose: PoseSample?) -> PoseCaptureBinding? {
    guard let pose else { return nil }
    let status = pose.tracking == .normal && pose.hasValidTransform ? "available" : "unavailable"
    return PoseCaptureBinding(captureID: captureID, captureTimestamp: pose.timestamp, aligned: AlignedPose(sample: status == "available" ? pose : nil, delta: 0, status: status))
}

private actor CountingStillPhotoBackend: StillPhotoBackend {
    private(set) var requestCount = 0
    func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) {
        requestCount += 1
        return (Data([9, 8, 7]), CaptureDimensions(width: 2, height: 1))
    }
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

    func testPL0090DiscoveryUsesRecoveredStateBlocksCorruptionAndDiscardsOnlyResumableSessions() async throws {
        let stages = ["transaction.prepare", "transaction.sourceStage", "transaction.recordStage", "transaction.stateStage", "transaction.sourceCommit", "transaction.recordCommit", "transaction.stateCommit"]
        for stage in stages {
            let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let layout = SessionStorageLayout(root: root, sessionID: "resume"); let store = ScanSessionStore(layout: layout, failureInjector: { $0 == stage }); try await store.create(NewScanDraft(sessionID: "resume", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)); let record = AcceptedCaptureRecord(captureID: "capture", sequence: 0, sourceFilename: "capture.heic", metadataFilename: "capture.json"); do { try await store.storeAcceptedCapture(source: Data([1]), record: record, metadata: try JSONEncoder().encode(record), state: try JSONEncoder().encode(PersistedSessionState(sessionID: "resume", nextSequence: 1, epoch: 0, acceptedIDs: ["capture"]))) } catch { }; let candidates = await SessionDiscoveryService(root: root).discover(); XCTAssertEqual(candidates.first?.disposition, .resumable, stage); XCTAssertEqual(candidates.first?.state?.acceptedIDs, [], stage)
        }
        let staleRoot = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: staleRoot) }; let staleLayout = SessionStorageLayout(root: staleRoot, sessionID: "stale"); let staleStore = ScanSessionStore(layout: staleLayout); try await staleStore.create(NewScanDraft(sessionID: "stale", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)); try FileManager.default.createDirectory(at: staleLayout.temporary.appendingPathComponent(".txn-stale"), withIntermediateDirectories: true); let stale = await SessionDiscoveryService(root: staleRoot).discover(); XCTAssertEqual(stale.first?.disposition, .blocked("corrupt_transaction"))
        let corruptRoot = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: corruptRoot) }; let corruptLayout = SessionStorageLayout(root: corruptRoot, sessionID: "corrupt"); let corruptStore = ScanSessionStore(layout: corruptLayout); try await corruptStore.create(NewScanDraft(sessionID: "corrupt", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)); let corruptRecord = AcceptedCaptureRecord(captureID: "capture", sequence: 0, sourceFilename: "capture.heic", metadataFilename: "capture.json"); try await corruptStore.storeAcceptedCapture(source: Data([1]), record: corruptRecord, metadata: try JSONEncoder().encode(corruptRecord), state: try JSONEncoder().encode(PersistedSessionState(sessionID: "corrupt", nextSequence: 1, epoch: 0, acceptedIDs: ["capture"]))); try FileManager.default.removeItem(at: corruptLayout.images.appendingPathComponent("capture.heic")); let missingSource = await SessionDiscoveryService(root: corruptRoot).discover(); XCTAssertEqual(missingSource.first?.disposition, .blocked("missing_or_corrupt_record"))
        let versionRoot = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: versionRoot) }; let versionLayout = SessionStorageLayout(root: versionRoot, sessionID: "version"); let versionStore = ScanSessionStore(layout: versionLayout); try await versionStore.create(NewScanDraft(sessionID: "version", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)); try JSONEncoder().encode(PersistedSessionState(sessionID: "version", schemaVersion: "9", nextSequence: 0, epoch: 0, acceptedIDs: [])).write(to: versionLayout.state); let versionCandidate = await SessionDiscoveryService(root: versionRoot).discover(); XCTAssertEqual(versionCandidate.first?.disposition, .blocked("version_mismatch"))
        let discardRoot = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: discardRoot) }; let discardLayout = SessionStorageLayout(root: discardRoot, sessionID: "discard"); let discardStore = ScanSessionStore(layout: discardLayout); try await discardStore.create(NewScanDraft(sessionID: "discard", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)); let discovered = await SessionDiscoveryService(root: discardRoot).discover(); guard let candidate = discovered.first else { return XCTFail("resumable candidate missing") }; XCTAssertEqual(candidate.disposition, .resumable); try await SafeSessionDeleter().delete(plan: SessionDeletionPlan(root: discardRoot, candidate: candidate), confirmed: true); XCTAssertFalse(FileManager.default.fileExists(atPath: discardLayout.sessionRoot.path)); let blocked = SessionResumeCandidate(id: "blocked", draft: nil, disposition: .blocked("corrupt_transaction"), state: nil); XCTAssertThrowsError(try SessionDeletionPlan(root: discardRoot, candidate: blocked).validate(confirmed: true))
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
            var canCapturePhoto = true; var delegate: (any StillPhotoDriverDelegate)?; var captures = 0; var cancellations = 0
            func capturePhoto() { captures += 1 }
            func cancelPhotoCapture() { cancellations += 1 }
            func finish(_ bytes: Data = Data([1, 2]), dimensions: CaptureDimensions = CaptureDimensions(width: 2, height: 1)) { delegate?.stillPhotoDriver(self, didFinish: bytes, dimensions: dimensions); delegate?.stillPhotoDriverDidFinishWithoutData(self) }
        }
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle); let driver = Driver(); let core = StillPhotoAdapterCore(driver: driver, selectedLens: lens, activeLensIdentifier: { "main" })
        let task = Task { try await core.requestOriginalStill() }; await Task.yield(); driver.finish(); let result = try await task.value
        XCTAssertEqual(result.bytes, Data([1, 2])); XCTAssertEqual(driver.captures, 1)
        let wrong = StillPhotoAdapterCore(driver: driver, selectedLens: lens, activeLensIdentifier: { "tele" }); do { _ = try await wrong.requestOriginalStill(); XCTFail("wrong lens must fail") } catch { XCTAssertEqual(error as? CameraServiceError, .failed("selected_lens_mismatch")) }
    }

    @MainActor
    func testPL0071StillPhotoAdapterTerminalPathsResumeOnceAndCancelAppropriately() async throws {
        final class Driver: StillPhotoDriver {
            var canCapturePhoto = true; var delegate: (any StillPhotoDriverDelegate)?; var captures = 0; var cancellations = 0
            func capturePhoto() { captures += 1 }
            func cancelPhotoCapture() { cancellations += 1 }
            func finishWithoutData() { delegate?.stillPhotoDriverDidFinishWithoutData(self) }
            func finish(_ bytes: Data = Data([7, 8])) { delegate?.stillPhotoDriver(self, didFinish: bytes, dimensions: CaptureDimensions(width: 2, height: 1)) }
        }
        let lens = CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle)
        let missingDriver = Driver(); let missing = StillPhotoAdapterCore(driver: missingDriver, selectedLens: lens, activeLensIdentifier: { "main" })
        let missingTask = Task { try await missing.requestOriginalStill() }; await Task.yield(); missingDriver.finishWithoutData(); missingDriver.finish();
        do { _ = try await missingTask.value; XCTFail("missing data must fail") } catch { XCTAssertEqual(error as? CameraServiceError, .failed("photo_capture_completed_without_data")) }
        XCTAssertEqual(missingDriver.cancellations, 0)

        let overlapDriver = Driver(); let overlap = StillPhotoAdapterCore(driver: overlapDriver, selectedLens: lens, activeLensIdentifier: { "main" })
        let first = Task { try await overlap.requestOriginalStill() }; await Task.yield()
        do { _ = try await overlap.requestOriginalStill(); XCTFail("overlap must fail") } catch { XCTAssertEqual(error as? CameraServiceError, .failed("capture_in_flight")) }
        overlapDriver.finish(); _ = try await first.value; XCTAssertEqual(overlapDriver.cancellations, 0)

        let cancelledDriver = Driver(); let cancelled = StillPhotoAdapterCore(driver: cancelledDriver, selectedLens: lens, activeLensIdentifier: { "main" })
        let cancelledTask = Task { try await cancelled.requestOriginalStill() }; await Task.yield(); cancelledTask.cancel()
        do { _ = try await cancelledTask.value; XCTFail("task cancellation must fail") } catch { XCTAssertEqual(error as? CameraServiceError, .failed("capture_cancelled")) }
        XCTAssertEqual(cancelledDriver.cancellations, 1)

        let stoppedDriver = Driver(); let stopped = StillPhotoAdapterCore(driver: stoppedDriver, selectedLens: lens, activeLensIdentifier: { "main" })
        let stoppedTask = Task { try await stopped.requestOriginalStill() }; await Task.yield(); stopped.cancel()
        do { _ = try await stoppedTask.value; XCTFail("session stop must fail") } catch { XCTAssertEqual(error as? CameraServiceError, .failed("session_stopped")) }
        stoppedDriver.finish(); XCTAssertEqual(stoppedDriver.cancellations, 1)
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

    @MainActor
    func testPL0073ToPL0075ViewModelPublishesTheBoundControlRuntimeState() {
        let tracking = SequenceTrackingService([]); let motion = SequenceMotionService(); let vm = CaptureRuntimeViewModel(trackingService: tracking, motionService: motion, healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        let bridge = CameraControlRuntimeBridge(lens: CameraLensIdentity(identifier: "main", position: .back, kind: .wideAngle)); vm.bindCameraControls(bridge)
        bridge.setFocus(.locked); bridge.setExposure(.locked); bridge.setWhiteBalance(.locked)
        XCTAssertEqual(vm.controls.state.focus, .locked); XCTAssertEqual(vm.controls.state.exposure, .locked); XCTAssertEqual(vm.controls.state.whiteBalance, .locked)
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

    @MainActor
    func testPL0085OverlayPropagatesNewestPoseMotionAndEpochThenStops() async {
        let tracking = SequenceTrackingService([TrackingQualityClassifier.classify(state: .normal), TrackingQualityClassifier.classify(state: .normal), TrackingQualityClassifier.classify(state: .normal)])
        let motion = SequenceMotionService()
        let vm = CaptureRuntimeViewModel(trackingService: tracking, motionService: motion, healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        await vm.start(); await vm.refresh(); let firstPose = vm.pose; let firstMotion = vm.motion; let firstEpoch = vm.epoch
        await vm.refresh(); XCTAssertNotEqual(vm.pose?.timestamp, firstPose?.timestamp); XCTAssertNotEqual(vm.motion?.monotonicTimestamp, firstMotion?.monotonicTimestamp); XCTAssertGreaterThan(vm.epoch, firstEpoch); XCTAssertTrue(vm.overlay.lines.contains { $0.contains("Epoch: \(vm.epoch)") }); XCTAssertTrue(vm.overlay.lines.contains { $0.contains(String(format: "Pose t=%.3fs", vm.pose?.timestamp ?? -1)) }); XCTAssertTrue(vm.overlay.lines.contains { $0.contains(String(format: "Motion t=%.3fs", vm.motion?.monotonicTimestamp ?? -1)) })
        let stoppedPose = vm.pose; let stoppedMotion = vm.motion; let stoppedEpoch = vm.epoch; await vm.stop(); await vm.refresh(); XCTAssertEqual(vm.pose, stoppedPose); XCTAssertEqual(vm.motion, stoppedMotion); XCTAssertEqual(vm.epoch, stoppedEpoch)
    }

    @MainActor
    func testPL0080AndPL0081AcceptedStillOrchestrationPersistsPoseMotionAndReopens() async throws {
        struct Backend: TimestampedStillPhotoBackend, Sendable {
            func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) { (Data([1, 2, 3]), CaptureDimensions(width: 2, height: 1)) }
            func lastCaptureMonotonicTimestamp() async -> TimeInterval? { 10 }
        }
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        await vm.bindStillCaptureBackend(Backend())
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "evidence"); let store = ScanSessionStore(layout: layout); try await store.create(NewScanDraft(sessionID: "evidence", packageName: "Bottle", packageType: .bottle, captureMode: .freehand))
        var poses = PoseBuffer(); poses.append(PoseSample(timestamp: 11, transform: CoordinateTransform.identity.values, tracking: .normal)); poses.append(PoseSample(timestamp: 9, transform: CoordinateTransform.identity.values, tracking: .normal))
        var motion = MotionBuffer(); motion.append(MotionSampleRecord(monotonicTimestamp: 10.05, attitude: [0, 0, 0, 1], rotationRate: [1, 2, 3]))
        let record = AcceptedCaptureRecord(captureID: "capture", sequence: 0, sourceFilename: "capture.heic", metadataFilename: "capture.json")
        let state = try JSONEncoder().encode(PersistedSessionState(sessionID: "evidence", nextSequence: 1, epoch: 0, acceptedIDs: ["capture"]))
        let metadata = try JSONEncoder().encode(record)
        _ = try await vm.captureAndPersistAcceptedStill(captureID: "capture", record: record, metadata: metadata, state: state, store: store, poses: poses, motion: motion)
        let persisted = try JSONDecoder().decode(AcceptedCaptureRecord.self, from: Data(contentsOf: layout.photoRecords.appendingPathComponent("capture.json")))
        XCTAssertEqual(persisted.poseBinding?.aligned.status, "available"); XCTAssertEqual(persisted.motionBinding?.status, "available")
        if case .resumable(let recovered) = try await store.reopen(requiredSourceIDs: []) { XCTAssertEqual(recovered.acceptedIDs, ["capture"]) } else { XCTFail("accepted capture should reopen") }
        XCTAssertEqual(PoseBuffer().bind(captureID: "missing", timestamp: 10).aligned.status, "unavailable")
        XCTAssertEqual(poses.bind(captureID: "stale", timestamp: 20).aligned.status, "stale")
        XCTAssertEqual(MotionCaptureBinder.bind(captureID: "stale", timestamp: 20, records: motion.samples).status, "stale")
    }

    #if canImport(ARKit) && canImport(UIKit)
    @MainActor
    func testPL0079AndPL0084InjectedAROwnerLifecycleResetAndServiceMapping() async {
        @MainActor final class Driver: ARSessionLifecycleDriver {
            let session = ARSession(); let isSupported: Bool; var runs: [Bool] = []; var pauses = 0
            init(isSupported: Bool) { self.isSupported = isSupported }
            func run(resetTracking: Bool) { runs.append(resetTracking) }
            func pause() { pauses += 1 }
        }
        let unsupportedDriver = Driver(isSupported: false); let unsupportedOwner = SharedARSessionOwner(injectedDriver: unsupportedDriver); unsupportedOwner.start(); XCTAssertEqual(unsupportedOwner.policy.snapshot.quality, .limited); XCTAssertEqual(unsupportedDriver.runs.count, 0)
        let driver = Driver(isSupported: true); let owner = SharedARSessionOwner(injectedDriver: driver); owner.start(); owner.start(); XCTAssertEqual(driver.runs.count, 1); owner.stop(); owner.stop(); XCTAssertEqual(driver.pauses, 1)
        owner.start(); owner.applyTrackingEvent(.limited(.insufficientFeatures)); owner.applyTrackingEvent(.limited(.insufficientFeatures)); owner.applyTrackingEvent(.limited(.insufficientFeatures)); XCTAssertEqual(owner.epochCoordinator.lastReason, .trackingDegraded); XCTAssertTrue(owner.resetDiagnostics.contains { $0.reason == .trackingDegraded && $0.state == .relocalizing }); owner.applyTrackingEvent(.normal); XCTAssertEqual(owner.epochCoordinator.state, .recovered); XCTAssertTrue(owner.resetDiagnostics.contains { $0.state == .recovered })
        owner.reset(reason: .userRequested); let resetEpoch = owner.epochCoordinator.epoch; owner.reset(reason: .runtimeError); XCTAssertEqual(owner.epochCoordinator.epoch, resetEpoch + 1); XCTAssertEqual(Array(driver.runs.suffix(2)), [true, true])
        owner.sessionWasInterrupted(owner.session); XCTAssertEqual(owner.policy.snapshot.quality, .recovering); owner.sessionInterruptionEnded(owner.session); XCTAssertEqual(owner.policy.snapshot.quality, .recovering); owner.session(owner.session, didFailWithError: NSError(domain: "test", code: 1)); XCTAssertEqual(owner.epochCoordinator.state, .failed)
        let service = ARKitTrackingService(owner: owner); let state = await service.state(); XCTAssertEqual(state, .limited)
    }
    #endif

    #if canImport(AVFoundation)
    @MainActor
    func testPL0077UnifiedRecoveryOwnerUsesOneObserverSetCancellationRestartAndRuntimeUI() async {
        let center = NotificationCenter(); let session = AVCaptureSession(); let owner = CameraRecoveryOwner(); var cancellations = 0; var restarts = 0; var observed: [CameraRecoveryState] = []
        owner.onStateChange = { state, _ in observed.append(state) }; _ = owner.addStateObserver { state, _ in observed.append(state) }; owner.setInFlightCancellation { cancellations += 1 }; owner.setSessionRestart { restarts += 1 }; owner.register(session: session, notificationCenter: center); owner.register(session: session, notificationCenter: center); XCTAssertEqual(owner.registrationCount, 1)
        owner.handle(.permission(.denied)); XCTAssertEqual(owner.machine.state, .denied); owner.handle(.permission(.authorized)); owner.handle(.started); owner.handle(.interruption); XCTAssertEqual(cancellations, 1); owner.handle(.interruptionEnded); XCTAssertEqual(restarts, 1); owner.handle(.restartSucceeded); owner.handle(.runtimeError); XCTAssertEqual(cancellations, 2); XCTAssertEqual(restarts, 2); XCTAssertTrue(observed.contains(.running)); owner.unregister(notificationCenter: center)
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider())); vm.cameraRecoveryOwner.handle(.permission(.denied)); XCTAssertEqual(vm.cameraRecoveryState, .denied)
    }

    @MainActor
    func testPL0073PhysicalFocusAdapterSeamCoversDeviceSelectionStabilityLockAndRuntime() throws {
        let lens = CameraLensIdentity(identifier: "selected", position: .back, kind: .wideAngle); let selected = FakeCameraDeviceControlDriver(uniqueID: "selected"); let wrong = FakeCameraDeviceControlDriver(uniqueID: "other"); let coordinator = CameraDeviceConfigurationCoordinator(driver: selected, selectedLens: lens)
        XCTAssertThrowsError(try AVFoundationFocusAdapter.configure(driver: wrong, point: nil, coordinator: coordinator)) { XCTAssertEqual($0 as? CameraConfigurationError, .nonSelectedDevice) }
        XCTAssertEqual(try AVFoundationFocusAdapter.configure(driver: selected, point: CGPoint(x: 0.5, y: 0.5), coordinator: coordinator), .focusing); XCTAssertEqual(selected.focusMode, .continuousAutoFocus); XCTAssertEqual(selected.maximumConfigurationDepth, 1)
        selected.isAdjustingFocus = true; XCTAssertEqual(try AVFoundationFocusAdapter.observe(driver: selected, coordinator: coordinator), .focusing); XCTAssertThrowsError(try AVFoundationFocusAdapter.lock(driver: selected, coordinator: coordinator)) { XCTAssertEqual($0 as? CameraConfigurationError, .stabilizationRequired) }
        selected.isAdjustingFocus = false; XCTAssertEqual(try AVFoundationFocusAdapter.observe(driver: selected, coordinator: coordinator), .continuous); XCTAssertEqual(try AVFoundationFocusAdapter.lock(driver: selected, coordinator: coordinator), .locked); XCTAssertEqual(selected.focusMode, .locked)
        let composition = AVFoundationCameraControlComposition(driver: selected, selectedLens: lens); let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider())); vm.bindCameraControls(composition.controls); composition.configureFocus(); XCTAssertEqual(vm.controls.state.focus, .focusing); composition.observeFocus(); XCTAssertEqual(vm.controls.state.focus, .continuous)
    }

    @MainActor
    func testPL0074PhysicalExposureAdapterSeamClampsSerializesPropagatesAndPersists() throws {
        let lens = CameraLensIdentity(identifier: "selected", position: .back, kind: .wideAngle); let selected = FakeCameraDeviceControlDriver(uniqueID: "selected"); let wrong = FakeCameraDeviceControlDriver(uniqueID: "other"); let coordinator = CameraDeviceConfigurationCoordinator(driver: selected, selectedLens: lens)
        XCTAssertThrowsError(try AVFoundationExposureAdapter.configure(driver: wrong, bias: 0, coordinator: coordinator)) { XCTAssertEqual($0 as? CameraConfigurationError, .nonSelectedDevice) }
        XCTAssertEqual(try AVFoundationExposureAdapter.configure(driver: selected, bias: 99, coordinator: coordinator), .metering); XCTAssertEqual(selected.exposureTargetBias, selected.maxExposureTargetBias); XCTAssertEqual(selected.exposureMode, .continuousAutoExposure); XCTAssertEqual(selected.maximumConfigurationDepth, 1); XCTAssertEqual(try AVFoundationExposureAdapter.lock(driver: selected, coordinator: coordinator), .locked); XCTAssertEqual(selected.exposureMode, .locked)
        let composition = AVFoundationCameraControlComposition(driver: selected, selectedLens: lens); let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider())); vm.bindCameraControls(composition.controls); composition.configureExposure(bias: -99); XCTAssertEqual(vm.controls.state.exposure, .metering); XCTAssertEqual(selected.exposureTargetBias, selected.minExposureTargetBias)
        let base = PhotoCaptureMetadata(photoID: "p", imagePath: "images/p.heic", sequence: 0, originalFilename: "p.heic", pixelDimensions: CaptureDimensions(width: 1, height: 1), orientation: "portrait", lensIdentity: lens, focalLengthMM: SourceMeasurement(status: .unavailable), exposureSeconds: SourceMeasurement(status: .unavailable), iso: SourceMeasurement(status: .unavailable), whiteBalanceKelvin: SourceMeasurement(status: .unavailable), captureTimestamp: Date()); let accepted = try composition.acceptedMetadata(base); XCTAssertEqual(accepted.exposureSeconds.status, .available); XCTAssertEqual(accepted.exposureSeconds.value, selected.exposureDurationSeconds); XCTAssertEqual(accepted.iso.value, Double(selected.iso)); XCTAssertEqual(accepted.exposureSeconds.source, "device_api")
    }

    @MainActor
    func testPL0075PhysicalWhiteBalanceAdapterSeamStabilizesLocksObservesAndPersists() throws {
        let lens = CameraLensIdentity(identifier: "selected", position: .back, kind: .wideAngle); let selected = FakeCameraDeviceControlDriver(uniqueID: "selected"); let wrong = FakeCameraDeviceControlDriver(uniqueID: "other"); let coordinator = CameraDeviceConfigurationCoordinator(driver: selected, selectedLens: lens)
        XCTAssertThrowsError(try AVFoundationWhiteBalanceAdapter.configure(driver: wrong, coordinator: coordinator)) { XCTAssertEqual($0 as? CameraConfigurationError, .nonSelectedDevice) }
        XCTAssertEqual(try AVFoundationWhiteBalanceAdapter.configure(driver: selected, coordinator: coordinator), .stabilizing); XCTAssertEqual(selected.whiteBalanceMode, .continuousAutoWhiteBalance); selected.isAdjustingWhiteBalance = true; XCTAssertEqual(try AVFoundationWhiteBalanceAdapter.observe(driver: selected, coordinator: coordinator), .stabilizing); XCTAssertThrowsError(try AVFoundationWhiteBalanceAdapter.lock(driver: selected, coordinator: coordinator)) { XCTAssertEqual($0 as? CameraConfigurationError, .stabilizationRequired) }
        selected.isAdjustingWhiteBalance = false; XCTAssertEqual(try AVFoundationWhiteBalanceAdapter.observe(driver: selected, coordinator: coordinator), .stabilizing); XCTAssertEqual(try AVFoundationWhiteBalanceAdapter.lock(driver: selected, coordinator: coordinator), .locked); XCTAssertEqual(selected.whiteBalanceMode, .locked); XCTAssertEqual(AVFoundationWhiteBalanceAdapter.observedTemperatureKelvin(driver: selected)?.temperatureKelvin, 4500)
        let composition = AVFoundationCameraControlComposition(driver: selected, selectedLens: lens); let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider())); vm.bindCameraControls(composition.controls); composition.configureWhiteBalance(); XCTAssertEqual(vm.controls.state.whiteBalance, .stabilizing); composition.observeWhiteBalance(); XCTAssertEqual(vm.controls.state.whiteBalance, .stabilizing); composition.lockWhiteBalance(); XCTAssertEqual(vm.controls.state.whiteBalance, .locked)
        let base = PhotoCaptureMetadata(photoID: "p", imagePath: "images/p.heic", sequence: 0, originalFilename: "p.heic", pixelDimensions: CaptureDimensions(width: 1, height: 1), orientation: "portrait", lensIdentity: lens, focalLengthMM: SourceMeasurement(status: .unavailable), exposureSeconds: SourceMeasurement(status: .unavailable), iso: SourceMeasurement(status: .unavailable), whiteBalanceKelvin: SourceMeasurement(status: .unavailable), captureTimestamp: Date()); let accepted = try composition.acceptedMetadata(base); XCTAssertEqual(accepted.whiteBalanceKelvin.status, .available); XCTAssertEqual(accepted.whiteBalanceKelvin.value, 4500); XCTAssertEqual(accepted.whiteBalanceKelvin.unit, "K"); XCTAssertEqual(accepted.whiteBalanceKelvin.source, "device_api")
    }
    #endif

    func testPL0086DiagnosticsExactLimitAndRealisticPrivacyBoundary() throws {
        let pose = AlignedPose(sample: PoseSample(timestamp: 1, transform: CoordinateTransform.identity.values, tracking: .normal), delta: 0, status: "available"); let record = PoseDiagnosticRecord(captureID: "C:\\Users\\Alice\\private\\capture", captureTimestamp: 1, pose: pose, motion: nil, epoch: 0); XCTAssertNoThrow(try PoseDiagnosticsExporter.encode(records: [record], maximumRecords: 1)); XCTAssertThrowsError(try PoseDiagnosticsExporter.encode(records: [record, record], maximumRecords: 1)); let text = String(decoding: try PoseDiagnosticsExporter.encode(records: [record]), as: UTF8.self); XCTAssertFalse(text.contains("Alice")); XCTAssertFalse(text.contains("private"))
    }

    func testPL0087NewScanCallbackCoordinatorCallsStartExactlyOnce() {
        var workflow = NewScanWorkflowModel(); var callbacks = 0; XCTAssertFalse(NewScanActionCoordinator.start(workflow: &workflow, name: "", type: .bottle, mode: .freehand, notes: "", onStart: { _ in callbacks += 1 })); XCTAssertEqual(callbacks, 0); XCTAssertTrue(NewScanActionCoordinator.start(workflow: &workflow, name: "Bottle", type: .bottle, mode: .guidedOrbit, notes: "", onStart: { _ in callbacks += 1 })); XCTAssertEqual(callbacks, 1); NewScanActionCoordinator.cancel(workflow: &workflow); XCTAssertEqual(callbacks, 1)
    }

    func testPL0088TransactionRecoveryRollsBackPartialFinalMoves() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let layout = SessionStorageLayout(root: root, sessionID: "tx"); let store = ScanSessionStore(layout: layout); try await store.create(NewScanDraft(sessionID: "tx", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)); let tx = layout.temporary.appendingPathComponent(".txn-crash", isDirectory: true); try FileManager.default.createDirectory(at: tx, withIntermediateDirectories: true); let oldState = try Data(contentsOf: layout.state); try oldState.write(to: tx.appendingPathComponent("previous-state.json")); try Data([1]).write(to: tx.appendingPathComponent("p.heic")); let record = AcceptedCaptureRecord(captureID: "p", sequence: 0, sourceFilename: "p.heic", metadataFilename: "p.json"); try JSONEncoder().encode(record).write(to: tx.appendingPathComponent("p.json")); try JSONEncoder().encode(PersistedSessionState(sessionID: "tx", nextSequence: 1, epoch: 0, acceptedIDs: ["p"])).write(to: tx.appendingPathComponent("state.json")); try JSONEncoder().encode(SessionTransactionMarker(captureID: "p", sourceFilename: "p.heic", recordFilename: "p.json", stage: .recordCommitted)).write(to: tx.appendingPathComponent("marker.json")); try FileManager.default.moveItem(at: tx.appendingPathComponent("p.heic"), to: layout.images.appendingPathComponent("p.heic")); if case .resumable(let recovered) = try await store.reopen(requiredSourceIDs: []) { XCTAssertTrue(recovered.acceptedIDs.isEmpty) } else { XCTFail("rollback should leave a clean resumable session") }; XCTAssertFalse(FileManager.default.fileExists(atPath: layout.images.appendingPathComponent("p.heic").path))
    }

    func testPL0088EveryTransactionFailureStageRecoversCleanPreCaptureState() async throws {
        let stages = ["transaction.prepare", "transaction.sourceStage", "transaction.recordStage", "transaction.stateStage", "transaction.sourceCommit", "transaction.recordCommit", "transaction.stateCommit"]
        for stage in stages {
            let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }
            let layout = SessionStorageLayout(root: root, sessionID: "stage"); let store = ScanSessionStore(layout: layout, failureInjector: { $0 == stage }); try await store.create(NewScanDraft(sessionID: "stage", packageName: "Bottle", packageType: .bottle, captureMode: .freehand))
            let record = AcceptedCaptureRecord(captureID: "capture", sequence: 0, sourceFilename: "capture.heic", metadataFilename: "capture.json"); let state = try JSONEncoder().encode(PersistedSessionState(sessionID: "stage", nextSequence: 1, epoch: 0, acceptedIDs: ["capture"]))
            do { try await store.storeAcceptedCapture(source: Data([1, 2]), record: record, metadata: try JSONEncoder().encode(record), state: state); XCTFail("injected stage must fail: \(stage)") } catch { }
            if case .resumable(let recovered) = try await store.reopen(requiredSourceIDs: []) { XCTAssertTrue(recovered.acceptedIDs.isEmpty, stage); XCTAssertFalse(FileManager.default.fileExists(atPath: layout.images.appendingPathComponent("capture.heic").path)); XCTAssertFalse(FileManager.default.fileExists(atPath: layout.photoRecords.appendingPathComponent("capture.json").path)) } else { XCTFail("stage must recover cleanly: \(stage)") }
        }
        let malformedRoot = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: malformedRoot) }; let malformedLayout = SessionStorageLayout(root: malformedRoot, sessionID: "malformed"); let malformedStore = ScanSessionStore(layout: malformedLayout); try await malformedStore.create(NewScanDraft(sessionID: "malformed", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)); let malformedTxn = malformedLayout.temporary.appendingPathComponent(".txn-malformed", isDirectory: true); try FileManager.default.createDirectory(at: malformedTxn, withIntermediateDirectories: true); try Data("not-json".utf8).write(to: malformedTxn.appendingPathComponent("marker.json")); do { _ = try await malformedStore.reopen(requiredSourceIDs: []); XCTFail("malformed marker must surface") } catch { XCTAssertEqual(error as? SessionStorageError, .interruptedWrite) }
    }

    func testPL0089GalleryFailureRestoresFilesStateAndAudit() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let layout = SessionStorageLayout(root: root, sessionID: "gallery"); let session = ScanSessionStore(layout: layout); try await session.create(NewScanDraft(sessionID: "gallery", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)); let record = AcceptedCaptureRecord(captureID: "a", sequence: 0, sourceFilename: "a.heic", metadataFilename: "a.json"); try await session.storeAcceptedCapture(source: Data([1]), record: record, metadata: Data("{}".utf8), state: try JSONEncoder().encode(PersistedSessionState(sessionID: "gallery", nextSequence: 1, epoch: 0, acceptedIDs: ["a"]))); let failing = SessionGalleryStore(layout: layout, failureInjector: { $0 == "mutation.auditCommit" }); do { try await failing.delete(id: "a", confirmed: true); XCTFail("failed gallery mutation must throw") } catch { XCTAssertEqual(error as? SessionStorageError, .interruptedWrite) }; XCTAssertTrue(FileManager.default.fileExists(atPath: layout.images.appendingPathComponent("a.heic").path)); XCTAssertEqual(try JSONDecoder().decode(PersistedSessionState.self, from: Data(contentsOf: layout.state)).acceptedIDs, ["a"])
    }

    func testPL0089RetakeCallbackAndDeleteRetakeFailureStagesRollbackCoherently() async throws {
        let stages = ["retake.source", "retake.record", "mutation.stateStage", "mutation.auditStage", "mutation.stateCommit", "mutation.auditCommit", "retake.remove.a.heic"]
        for stage in stages {
            let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let layout = SessionStorageLayout(root: root, sessionID: "gallery"); let session = ScanSessionStore(layout: layout); try await session.create(NewScanDraft(sessionID: "gallery", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)); let old = AcceptedCaptureRecord(captureID: "a", sequence: 0, sourceFilename: "a.heic", metadataFilename: "a.json"); try await session.storeAcceptedCapture(source: Data([1]), record: old, metadata: try JSONEncoder().encode(old), state: try JSONEncoder().encode(PersistedSessionState(sessionID: "gallery", nextSequence: 1, epoch: 0, acceptedIDs: ["a"]))); try Data([9]).write(to: layout.previews.appendingPathComponent("a-thumbnail.jpg")); let failing = SessionGalleryStore(layout: layout, failureInjector: { $0 == stage }); let entry = try await failing.load().first!; let replacement = AcceptedCaptureRecord(captureID: "b", sequence: 1, sourceFilename: "b.heic", metadataFilename: "b.json"); let callback: (GalleryEntry) async throws -> RetakeCapturePayload = { _ in RetakeCapturePayload(source: Data([2]), record: replacement, metadata: try JSONEncoder().encode(replacement)) }; let payload = try await callback(entry); do { try await failing.retake(replacing: entry.id, source: payload.source, record: payload.record, metadata: payload.metadata); XCTFail("injected retake stage must fail: \(stage)") } catch { }; XCTAssertTrue(FileManager.default.fileExists(atPath: layout.images.appendingPathComponent("a.heic").path)); XCTAssertFalse(FileManager.default.fileExists(atPath: layout.images.appendingPathComponent("b.heic").path)); XCTAssertEqual(try JSONDecoder().decode(PersistedSessionState.self, from: Data(contentsOf: layout.state)).acceptedIDs, ["a"])
        }
        let missingRoot = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: missingRoot) }; try FileManager.default.createDirectory(at: missingRoot, withIntermediateDirectories: true); let missingCandidate = SessionResumeCandidate(id: "missing", draft: nil, disposition: .resumable, state: nil); let missingReport = try await SafeSessionDeleter().deleteDetailed(plan: SessionDeletionPlan(root: missingRoot, candidate: missingCandidate), confirmed: true); XCTAssertEqual(missingReport.failures, ["missing_session"])
    }

    func testPL0091FinalizationFailureLeavesFreshDestinationAbsent() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true); let metadata = try JSONEncoder().encode(PackScanPhotoMetadataDocument(photos: [PackScanPhotoMetadataWire(photoID: "p", imagePath: "images/p.heic", sequence: 0, originalFilename: "p.heic", pixelDimensions: CaptureDimensions(width: 1, height: 1), orientation: PackScanOrientation(value: .unknown, source: .unknown), focalLengthMM: PackScanNumericMeasurement(status: .unavailable), exposure: PackScanNumericMeasurement(status: .unavailable), iso: PackScanISOMeasurement(status: .unavailable), whiteBalanceKelvin: PackScanNumericMeasurement(status: .unavailable))])); let image = Data([1]); let manifest = try JSONSerialization.data(withJSONObject: ["schema_version": "1.0.0", "capture_id": "s", "checksums": ["algorithm": "sha256", "canonicalization": PackScanWriter.checksumCanonicalization], "payloads": [["path": "metadata/photos.json", "kind": "photo_metadata", "required": true, "authority": "source", "size_bytes": metadata.count, "sha256": SourceIntegrity.digest(metadata)], ["path": "images/p.heic", "kind": "image", "required": true, "authority": "source", "size_bytes": image.count, "sha256": SourceIntegrity.digest(image)]]]); let destination = root.appendingPathComponent("fresh.packscan"); XCTAssertThrowsError(try SessionFinalizer(failureInjector: { $0 == "finalization.record" }).finalize(FinalizationInput(manifest: manifest, payloads: ["metadata/photos.json": metadata, "images/p.heic": image], destination: destination, sessionRoot: root))); XCTAssertFalse(FileManager.default.fileExists(atPath: destination.path)); XCTAssertFalse(FileManager.default.fileExists(atPath: root.appendingPathComponent("finalization.json").path))
    }

    func testPL0092HistoryRejectsForeignAndMissingExportedPackage() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let layout = SessionStorageLayout(root: root, sessionID: "history"); try FileManager.default.createDirectory(at: layout.previews, withIntermediateDirectories: true); try Data([1]).write(to: layout.previews.appendingPathComponent("preview.jpg")); try JSONEncoder().encode(NewScanDraft(sessionID: "history", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)).write(to: layout.metadata); try JSONEncoder().encode(SessionFinalizationRecord(sessionID: "foreign", state: .exported, packagePath: root.appendingPathComponent("missing.packscan").path)).write(to: layout.finalization); let entries = await LocalScanHistoryStore(root: root).load(); XCTAssertEqual(entries.first?.degradedReason, "invalid_finalization_identity")
    }

    func testPL0092ClosedFinalizationStateAndRealFinalizerTransition() async throws {
        let unknown = Data("{\"sessionID\":\"s\",\"state\":\"unknown\"}".utf8); XCTAssertNil(try? JSONDecoder().decode(SessionFinalizationRecord.self, from: unknown))
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let sessionRoot = root.appendingPathComponent("real"); try FileManager.default.createDirectory(at: sessionRoot.appendingPathComponent("previews"), withIntermediateDirectories: true); try Data([1]).write(to: sessionRoot.appendingPathComponent("previews/preview.jpg")); try JSONEncoder().encode(NewScanDraft(sessionID: "real", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)).write(to: sessionRoot.appendingPathComponent("metadata.json")); try JSONEncoder().encode(SessionFinalizationRecord(sessionID: "real", state: .inProgress)).write(to: sessionRoot.appendingPathComponent("finalization.json"))
        let metadata = try JSONEncoder().encode(PackScanPhotoMetadataDocument(photos: [PackScanPhotoMetadataWire(photoID: "p", imagePath: "images/p.heic", sequence: 0, originalFilename: "p.heic", pixelDimensions: CaptureDimensions(width: 1, height: 1), orientation: PackScanOrientation(value: .unknown, source: .unknown), focalLengthMM: PackScanNumericMeasurement(status: .unavailable), exposure: PackScanNumericMeasurement(status: .unavailable), iso: PackScanISOMeasurement(status: .unavailable), whiteBalanceKelvin: PackScanNumericMeasurement(status: .unavailable))])); let image = Data([1]); let payloads = ["metadata/photos.json": metadata, "images/p.heic": image]; let manifest = try JSONSerialization.data(withJSONObject: ["schema_version": "1.0.0", "capture_id": "real", "checksums": ["algorithm": "sha256", "canonicalization": PackScanWriter.checksumCanonicalization], "payloads": [["path": "metadata/photos.json", "kind": "photo_metadata", "required": true, "authority": "source", "size_bytes": metadata.count, "sha256": SourceIntegrity.digest(metadata)], ["path": "images/p.heic", "kind": "image", "required": true, "authority": "source", "size_bytes": image.count, "sha256": SourceIntegrity.digest(image)]]]); let destination = root.appendingPathComponent("real.packscan"); try SessionFinalizer().finalize(FinalizationInput(manifest: manifest, payloads: payloads, destination: destination, sessionRoot: sessionRoot)); let history = await LocalScanHistoryStore(root: root).load(); XCTAssertEqual(history.first?.exportState, "exported"); XCTAssertEqual(history.first?.degradedReason, nil); XCTAssertTrue(FileManager.default.fileExists(atPath: destination.path))
        let corruptRoot = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: corruptRoot) }; let corruptSession = corruptRoot.appendingPathComponent("corrupt"); try FileManager.default.createDirectory(at: corruptSession.appendingPathComponent("previews"), withIntermediateDirectories: true); try Data([1]).write(to: corruptSession.appendingPathComponent("previews/preview.jpg")); try JSONEncoder().encode(NewScanDraft(sessionID: "corrupt", packageName: "Bottle", packageType: .bottle, captureMode: .freehand)).write(to: corruptSession.appendingPathComponent("metadata.json")); try Data("{\"state\":\"unknown\"}".utf8).write(to: corruptSession.appendingPathComponent("finalization.json")); XCTAssertEqual((await LocalScanHistoryStore(root: corruptRoot).load()).first?.degradedReason, "corrupt_finalization")
    }

    func testPL0093DeletionAPIThrowsOnPartialFailure() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let session = root.appendingPathComponent("s1"); try FileManager.default.createDirectory(at: session, withIntermediateDirectories: true); let candidate = SessionResumeCandidate(id: "s1", draft: nil, disposition: .resumable, state: nil); let deleter = SafeSessionDeleter(failureInjector: { _ in true }); do { try await deleter.delete(plan: SessionDeletionPlan(root: root, candidate: candidate), confirmed: true); XCTFail("partial delete must throw") } catch { XCTAssertEqual(error as? DeletionError, .partialFailure) }
    }

    func testPL0093MissingSessionAndHistoryIndexFailuresNeverReportSuccess() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }
        let missing = SessionResumeCandidate(id: "missing", draft: nil, disposition: .resumable, state: nil); do { try await SafeSessionDeleter().delete(plan: SessionDeletionPlan(root: root, candidate: missing), confirmed: true); XCTFail("missing session must not report success") } catch { XCTAssertEqual(error as? DeletionError, .partialFailure) }
        let session = root.appendingPathComponent("s2"); try FileManager.default.createDirectory(at: session, withIntermediateDirectories: true); let history = root.appendingPathComponent("history.json"); let entry = ScanHistoryEntry(id: "s2", packageName: "Bottle", packageType: .bottle, date: Date(), previewPath: nil, exportState: "in_progress"); try JSONEncoder().encode([entry]).write(to: history); let candidate = SessionResumeCandidate(id: "s2", draft: nil, disposition: .resumable, state: nil); let failing = SafeSessionDeleter(failureInjector: { $0 == history.path }); let report = try await failing.deleteDetailed(plan: SessionDeletionPlan(root: root, candidate: candidate), confirmed: true, historyIndex: history); XCTAssertEqual(report.failures, [history.path]); XCTAssertFalse(FileManager.default.fileExists(atPath: session.path)); do { try await failing.delete(plan: SessionDeletionPlan(root: root, candidate: candidate), confirmed: true); XCTFail("history failure must not report success") } catch { XCTAssertEqual(error as? DeletionError, .partialFailure) }
    }

    func testPL0093RealSymlinkEscapeIsRejectedBeforeDeletion() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }; let session = root.appendingPathComponent("s1"); let outside = root.deletingLastPathComponent().appendingPathComponent("packlab-outside-\(UUID().uuidString)"); try FileManager.default.createDirectory(at: session, withIntermediateDirectories: true); try FileManager.default.createDirectory(at: outside, withIntermediateDirectories: true); let link = session.appendingPathComponent("linked"); do { try FileManager.default.createSymbolicLink(at: link, withDestinationURL: outside) } catch { throw XCTSkip("symlinks unavailable on this test host") }; let candidate = SessionResumeCandidate(id: "s1", draft: nil, disposition: .resumable, state: nil); XCTAssertThrowsError(try SessionDeletionPlan(root: root, candidate: candidate).validate(confirmed: true)) { XCTAssertEqual($0 as? DeletionError, .symlinkEscape) }
    }

    func testPL0094SharpnessIsDimensionStableAndHasExplicitBands() {
        let sharpPixels = (0..<64).flatMap { y in (0..<64).map { x in ((x + y) % 2 == 0) ? 1.0 : 0.0 } }
        let resizedPixels = (0..<128).flatMap { y in (0..<128).map { x in ((x / 2 + y / 2) % 2 == 0) ? 1.0 : 0.0 } }
        let sharp = SharpnessAnalyzer.analyze(QualityImageFrame(width: 64, height: 64, luminance: sharpPixels))
        let resized = SharpnessAnalyzer.analyze(QualityImageFrame(width: 128, height: 128, luminance: resizedPixels))
        XCTAssertEqual(sharp.band, .accept)
        XCTAssertEqual(resized.band, sharp.band)
        XCTAssertNotNil(sharp.normalizedLaplacianVariance)
        XCTAssertEqual(SharpnessAnalyzer.analyze(.unavailable).band, .unavailable)
    }

    func testPL0094SharpnessBoundariesAndProvisionalCalibration() {
        let thresholds = SharpnessThresholds(acceptMinimum: 0.018, warnMinimum: 0.006)
        XCTAssertEqual(SharpnessCalibrationHarness.suggestThresholds(from: [SharpnessCalibrationSample(label: .blurred, metric: 0.002), SharpnessCalibrationSample(label: .usable, metric: 0.008), SharpnessCalibrationSample(label: .sharp, metric: 0.02)]).calibrationStatus, "provisional_test_calibrated")
        XCTAssertEqual(thresholds.warnMinimum, 0.006)
        XCTAssertEqual(SharpnessThresholds(acceptMinimum: 0.01, warnMinimum: 0.2).warnMinimum, 0.01)

        XCTAssertEqual(SharpnessAnalyzer.analyze(normalizedLaplacianVariance: thresholds.acceptMinimum, sampleCount: 10, thresholds: thresholds).band, .accept)
        XCTAssertEqual(SharpnessAnalyzer.analyze(normalizedLaplacianVariance: thresholds.warnMinimum, sampleCount: 10, thresholds: thresholds).band, .warn)
        XCTAssertEqual(SharpnessAnalyzer.analyze(normalizedLaplacianVariance: thresholds.warnMinimum.nextDown, sampleCount: 10, thresholds: thresholds).band, .reject)
        XCTAssertEqual(SharpnessAnalyzer.analyze(normalizedLaplacianVariance: thresholds.acceptMinimum.nextDown, sampleCount: 10, thresholds: thresholds).band, .warn)
    }

    func testPL0094SharpnessFrameFixturesProduceWarnAndRejectBands() {
        let warnPixels = (0..<48).flatMap { y in
            (0..<48).map { x in 0.5 + 0.5 * sin(2 * Double.pi * Double(x) / 6.0) }
        }
        let warn = SharpnessAnalyzer.analyze(QualityImageFrame(width: 48, height: 48, luminance: warnPixels))
        let reject = SharpnessAnalyzer.analyze(QualityImageFrame(width: 48, height: 48, luminance: [Double](repeating: 0.5, count: 48 * 48)))
        XCTAssertEqual(warn.band, .warn)
        XCTAssertEqual(warn.reasonCode, "sharpness_warn")
        XCTAssertEqual(reject.band, .reject)
        XCTAssertEqual(reject.reasonCode, "sharpness_reject")
    }

    func testPL0094CandidateRuntimeUsesSelectedPresetAndPropagatesAllQualityMetrics() {
        let frame = QualityImageFrame(width: 8, height: 8, luminance: (0..<64).map { (($0 / 8 + $0 % 8) % 2 == 0) ? 0.2 : 0.8 }, objectMask: (0..<64).map { index in let x = index % 8; let y = index / 8; return (2...5).contains(x) && (2...5).contains(y) })
        let input = M04CandidateFrameInput(sessionID: "session", captureID: "candidate", sequence: 3, monotonicTimestamp: 10, frame: frame)
        let evaluation = M04CandidateQualityRuntime(preset: PackagingPresetCatalog.glossyPET).evaluate(input)
        XCTAssertEqual(evaluation.input.captureID, "candidate")
        XCTAssertEqual(evaluation.quality.metrics.highlightClipping, LuminanceClippingAnalyzer.highlight(frame, thresholds: PackagingPresetCatalog.glossyPET.quality.highlight))
        XCTAssertNotEqual(evaluation.quality.metrics.sharpness.reasonCode, "sharpness_(band.rawValue)")
        XCTAssertTrue(["sharpness_accept", "sharpness_warn", "sharpness_reject"].contains(evaluation.quality.metrics.sharpness.reasonCode))
    }

    func testPL0095MotionBlurUsesMonotonicBindingAndExplainsUnavailableMotion() {
        let blurred = SharpnessMetric(availability: .available, normalizedLaplacianVariance: 0.001, sampleCount: 10, band: .reject, reasonCode: "sharpness_reject")
        let lowMotion = MotionCaptureBinding(captureID: "c1", captureTimestamp: 10, sample: MotionSampleRecord(monotonicTimestamp: 10, attitude: [0, 0, 0, 1], rotationRate: [0.1, 0, 0]), delta: 0, status: "available")
        let highMotion = MotionCaptureBinding(captureID: "c2", captureTimestamp: 20, sample: MotionSampleRecord(monotonicTimestamp: 20, attitude: [0, 0, 0, 1], rotationRate: [2, 0, 0]), delta: 0, status: "available")
        XCTAssertEqual(MotionBlurAnalyzer.analyze(sharpness: blurred, motion: lowMotion).reasons, ["image_blur_low_motion"])
        XCTAssertEqual(MotionBlurAnalyzer.analyze(sharpness: blurred, motion: highMotion).risk, .highRisk)
        XCTAssertEqual(MotionBlurAnalyzer.analyze(sharpness: blurred, motion: nil).reasons, ["image_blur_motion_unavailable"])
        let stale = MotionCaptureBinding(captureID: "c3", captureTimestamp: 30, sample: nil, delta: 1, status: "stale")
        XCTAssertEqual(MotionBlurAnalyzer.analyze(sharpness: SharpnessMetric(availability: .available, normalizedLaplacianVariance: 0.03, sampleCount: 10, band: .accept, reasonCode: "sharpness_accept"), motion: stale).availability, .stale)
    }

    func testPL0095CandidateRuntimePublishesAlignedMotionWarningsAndHighRisk() {
        let sharpFrame = QualityImageFrame(width: 64, height: 64, luminance: (0..<64).flatMap { y in (0..<64).map { x in ((x + y) % 2 == 0) ? 1.0 : 0.0 } }, objectMask: (0..<64).flatMap { y in (0..<64).map { x in (16..<48).contains(x) && (16..<48).contains(y) } })
        let blurredFrame = QualityImageFrame(width: 8, height: 8, luminance: [Double](repeating: 0.5, count: 64))
        let sharpRuntime = M04CandidateQualityRuntime(preset: PackagingPresetCatalog.matteHDPE)
        let missing = sharpRuntime.evaluate(M04CandidateFrameInput(sessionID: "s", captureID: "missing", sequence: 0, monotonicTimestamp: 10, frame: sharpFrame))
        XCTAssertEqual(missing.quality.decision, .accept)
        XCTAssertEqual(missing.quality.metrics.motionBlur.risk, .unavailable)
        XCTAssertTrue(missing.quality.warnings.contains("motion_unavailable"))

        let low = MotionCaptureBinding(captureID: "low", captureTimestamp: 10, sample: MotionSampleRecord(monotonicTimestamp: 10, attitude: [0, 0, 0, 1], rotationRate: [0.35, 0, 0]), delta: 0, status: "available")
        let high = MotionCaptureBinding(captureID: "high", captureTimestamp: 10, sample: MotionSampleRecord(monotonicTimestamp: 10, attitude: [0, 0, 0, 1], rotationRate: [1.2, 0, 0]), delta: 0, status: "available")
        let stale = MotionCaptureBinding(captureID: "stale", captureTimestamp: 10, sample: nil, delta: 1, status: "stale")
        let lowResult = sharpRuntime.evaluate(M04CandidateFrameInput(sessionID: "s", captureID: "low", sequence: 1, monotonicTimestamp: 10, frame: blurredFrame, motion: low))
        let highResult = sharpRuntime.evaluate(M04CandidateFrameInput(sessionID: "s", captureID: "high", sequence: 2, monotonicTimestamp: 10, frame: blurredFrame, motion: high))
        let staleResult = sharpRuntime.evaluate(M04CandidateFrameInput(sessionID: "s", captureID: "stale", sequence: 3, monotonicTimestamp: 10, frame: sharpFrame, motion: stale))
        XCTAssertEqual(lowResult.quality.metrics.motionBlur.reasons, ["image_blur_low_motion"])
        XCTAssertEqual(highResult.quality.metrics.motionBlur.risk, .highRisk)
        XCTAssertEqual(highResult.quality.decision, .reject)
        XCTAssertTrue(staleResult.quality.warnings.contains("image_blur_motion_stale") == false)
        XCTAssertTrue(staleResult.quality.warnings.contains("motion_stale"))
    }

    func testPL0096HighlightClippingToleratesLocalizedSpecularPixelsAndRejectsBroadClipping() {
        let localized = [Double](repeating: 0.5, count: 99) + [1.0]
        let localizedMetric = LuminanceClippingAnalyzer.highlight(QualityImageFrame(width: 10, height: 10, luminance: localized, objectMask: [Bool](repeating: true, count: 100)))
        XCTAssertEqual(localizedMetric.band, .pass)
        XCTAssertEqual(localizedMetric.clippedPixelCount, 1)
        let broad = [Double](repeating: 1.0, count: 25) + [Double](repeating: 0.5, count: 75)
        let broadMetric = LuminanceClippingAnalyzer.highlight(QualityImageFrame(width: 10, height: 10, luminance: broad, objectMask: [Bool](repeating: true, count: 100)))
        XCTAssertEqual(broadMetric.band, .reject)
        XCTAssertEqual(LuminanceClippingAnalyzer.highlight(.unavailable).band, .unavailable)
    }

    func testPL0096HighlightThresholdBoundaryIsDeterministic() {
        let thresholds = ClippingThresholds(luminanceCutoff: 0.98, toleratedFraction: 0.10, warningFraction: 0.20, rejectFraction: 0.30)
        let zero = LuminanceClippingAnalyzer.highlight(QualityImageFrame(width: 10, height: 1, luminance: [Double](repeating: 0.5, count: 10), objectMask: [Bool](repeating: true, count: 10)), thresholds: thresholds)
        XCTAssertEqual(zero.band, .pass)
        XCTAssertTrue(zero.reasons.contains("highlight_clipping_within_tolerance"))
        let atWarning = [Double](repeating: 1.0, count: 2) + [Double](repeating: 0.5, count: 8)
        let warning = LuminanceClippingAnalyzer.highlight(QualityImageFrame(width: 10, height: 1, luminance: atWarning, objectMask: [Bool](repeating: true, count: 10)), thresholds: thresholds)
        XCTAssertEqual(warning.band, .warn)
        XCTAssertTrue(warning.reasons.contains("highlight_clipping_warn"))
        let atReject = [Double](repeating: 1.0, count: 3) + [Double](repeating: 0.5, count: 7)
        XCTAssertEqual(LuminanceClippingAnalyzer.highlight(QualityImageFrame(width: 10, height: 1, luminance: atReject, objectMask: [Bool](repeating: true, count: 10)), thresholds: thresholds).band, .reject)
    }

    func testPL0096CandidateRuntimeUsesGlossyPETHighlightPolicyAndRawFraction() {
        let frame = QualityImageFrame(width: 10, height: 10, luminance: [Double](repeating: 1.0, count: 3) + [Double](repeating: 0.5, count: 97), objectMask: [Bool](repeating: true, count: 100))
        let glossy = M04CandidateQualityRuntime(preset: PackagingPresetCatalog.glossyPET).evaluate(M04CandidateFrameInput(sessionID: "s", captureID: "glossy", sequence: 1, monotonicTimestamp: 1, frame: frame))
        let matte = M04CandidateQualityRuntime(preset: PackagingPresetCatalog.matteHDPE).evaluate(M04CandidateFrameInput(sessionID: "s", captureID: "matte", sequence: 1, monotonicTimestamp: 1, frame: frame))
        XCTAssertEqual(glossy.quality.metrics.highlightClipping.clippedFraction, 0.03)
        XCTAssertEqual(glossy.quality.metrics.highlightClipping.band, .warn)
        XCTAssertEqual(matte.quality.metrics.highlightClipping.band, .pass)
        XCTAssertTrue(glossy.quality.warnings.contains("highlight_clipping_warn"))
    }

    func testPL0097ShadowClippingUsesObjectRegionAndExplainsMissingMask() {
        let objectMask = [Bool](repeating: true, count: 20) + [Bool](repeating: false, count: 80)
        let pixels = [Double](repeating: 0.01, count: 20) + [Double](repeating: 0.5, count: 80)
        let objectMetric = LuminanceClippingAnalyzer.shadow(QualityImageFrame(width: 10, height: 10, luminance: pixels, objectMask: objectMask))
        XCTAssertEqual(objectMetric.band, .reject)
        XCTAssertEqual(objectMetric.objectClippedFraction, 1.0)
        let noMask = LuminanceClippingAnalyzer.shadow(QualityImageFrame(width: 10, height: 10, luminance: pixels))
        XCTAssertTrue(noMask.reasons.contains("shadow_object_region_unavailable"))
    }

    func testPL0097CandidateRuntimePublishesShadowBandsAndRawObjectFraction() {
        let mask = (0..<100).map { index in
            let x = index % 10; let y = index / 10
            return (1...8).contains(x) && (1...8).contains(y)
        }
        let normal = [Double](repeating: 0.5, count: 100)
        let objectIndices = mask.indices.filter { mask[$0] }
        func withClippedObjectPixels(_ count: Int) -> [Double] {
            var pixels = normal
            objectIndices.prefix(count).forEach { pixels[$0] = 0.01 }
            return pixels
        }
        let localized = withClippedObjectPixels(1)
        let warning = withClippedObjectPixels(6)
        let broad = withClippedObjectPixels(16)
        let runtime = M04CandidateQualityRuntime(preset: PackagingPresetCatalog.matteHDPE)
        func evaluate(_ luminance: [Double], id: String) -> ClippingMetric {
            let frame = QualityImageFrame(width: 10, height: 10, luminance: luminance, objectMask: mask)
            return runtime.evaluate(M04CandidateFrameInput(sessionID: "s", captureID: id, sequence: 1, monotonicTimestamp: 1, frame: frame)).quality.metrics.shadowClipping
        }
        XCTAssertEqual(evaluate(normal, id: "normal").band, .pass)
        XCTAssertEqual(evaluate(localized, id: "localized").band, .pass)
        XCTAssertEqual(evaluate(warning, id: "warning").band, .warn)
        XCTAssertEqual(evaluate(warning, id: "warning").objectClippedFraction, 0.125)
        XCTAssertEqual(evaluate(broad, id: "broad").band, .reject)
        let noMask = runtime.evaluate(M04CandidateFrameInput(sessionID: "s", captureID: "no-mask", sequence: 1, monotonicTimestamp: 1, frame: QualityImageFrame(width: 10, height: 10, luminance: normal))).quality.metrics.shadowClipping
        XCTAssertNil(noMask.objectClippedFraction)
        XCTAssertTrue(noMask.reasons.contains("shadow_object_region_unavailable"))
    }

    func testPL0098FramingDistinguishesSmallAcceptableAndCroppedObjects() {
        let pixels = [Double](repeating: 0.5, count: 100)
        let smallMask = (0..<100).map { $0 == 44 }
        XCTAssertEqual(FramingAnalyzer.analyze(QualityImageFrame(width: 10, height: 10, luminance: pixels, objectMask: smallMask)).band, .tooSmall)
        let goodMask = (0..<100).map { index in
            let x = index % 10; let y = index / 10
            return (2...7).contains(x) && (2...7).contains(y)
        }
        XCTAssertEqual(FramingAnalyzer.analyze(QualityImageFrame(width: 10, height: 10, luminance: pixels, objectMask: goodMask)).band, .acceptable)
        let edgeMask = (0..<100).map { index in index % 10 < 9 && index / 10 > 0 && index / 10 < 9 }
        XCTAssertEqual(FramingAnalyzer.analyze(QualityImageFrame(width: 10, height: 10, luminance: pixels, objectMask: edgeMask)).band, .cropped)
        XCTAssertEqual(FramingAnalyzer.analyze(.unavailable).band, .unavailable)
    }

    func testPL0098CandidateRuntimePublishesFramingStateAtSizeAndMarginBoundaries() {
        let pixels = [Double](repeating: 0.5, count: 100)
        let smallMask = (0..<100).map { $0 == 44 }
        let centeredMask = (0..<100).map { index in
            let x = index % 10; let y = index / 10
            return (2...7).contains(x) && (2...7).contains(y)
        }
        let edgeMask = (0..<100).map { index in index % 10 < 9 && index / 10 > 0 && index / 10 < 9 }
        let oversizedMask = (0..<100).map { index in index % 10 != 0 }
        let runtime = M04CandidateQualityRuntime(preset: PackagingPresetCatalog.matteHDPE)
        func framing(_ mask: [Bool]?, id: String) -> FramingMetric {
            let frame = QualityImageFrame(width: 10, height: 10, luminance: pixels, objectMask: mask)
            return runtime.evaluate(M04CandidateFrameInput(sessionID: "s", captureID: id, sequence: 1, monotonicTimestamp: 1, frame: frame)).quality.metrics.framing
        }
        XCTAssertEqual(framing(smallMask, id: "small").band, .tooSmall)
        XCTAssertEqual(framing(centeredMask, id: "centered").band, .acceptable)
        XCTAssertEqual(framing(edgeMask, id: "edge").band, .cropped)
        XCTAssertEqual(framing(oversizedMask, id: "oversized").band, .cropped)
        XCTAssertEqual(framing(nil, id: "unavailable").band, .unavailable)
        XCTAssertEqual(framing(centeredMask, id: "centered").objectFraction, 0.36)

        let exactSizePreset = PackagingPreset(id: .matteHDPE, version: "test", displayName: "Test", quality: QualityPolicyConfiguration(framing: FramingThresholds(minimumObjectFraction: 0.36, maximumObjectFraction: 0.82, minimumMargin: 0.19)), coverage: PackagingPresetCatalog.matteHDPE.coverage, lightingGuidance: [], preparationGuidance: [], requiresPreparationAcknowledgement: false)
        let exactSize = M04CandidateQualityRuntime(preset: exactSizePreset).evaluate(M04CandidateFrameInput(sessionID: "s", captureID: "exact-size", sequence: 1, monotonicTimestamp: 1, frame: QualityImageFrame(width: 10, height: 10, luminance: pixels, objectMask: centeredMask))).quality.metrics.framing
        XCTAssertEqual(exactSize.band, .acceptable)
        let exactMarginPreset = PackagingPreset(id: .matteHDPE, version: "test", displayName: "Test", quality: QualityPolicyConfiguration(framing: FramingThresholds(minimumObjectFraction: 0.36, maximumObjectFraction: 0.82, minimumMargin: 0.2)), coverage: PackagingPresetCatalog.matteHDPE.coverage, lightingGuidance: [], preparationGuidance: [], requiresPreparationAcknowledgement: false)
        let exactMargin = M04CandidateQualityRuntime(preset: exactMarginPreset).evaluate(M04CandidateFrameInput(sessionID: "s", captureID: "exact-margin", sequence: 1, monotonicTimestamp: 1, frame: QualityImageFrame(width: 10, height: 10, luminance: pixels, objectMask: centeredMask))).quality.metrics.framing
        XCTAssertEqual(exactMargin.band, .cropped)
    }

    func testPL0099BackgroundComplexityExcludesObjectAndWarnsOnClutter() {
        let cleanPixels = [Double](repeating: 0.5, count: 100)
        let mask = (0..<100).map { index in (3...6).contains(index % 10) && (3...6).contains(index / 10) }
        XCTAssertEqual(BackgroundComplexityAnalyzer.analyze(QualityImageFrame(width: 10, height: 10, luminance: cleanPixels, objectMask: mask)).band, .clean)
        let clutter = (0..<100).map { index in mask[index] ? 0.5 : ((index % 2 == 0) ? 0.0 : 1.0) }
        let clutterMetric = BackgroundComplexityAnalyzer.analyze(QualityImageFrame(width: 10, height: 10, luminance: clutter, objectMask: mask))
        XCTAssertEqual(clutterMetric.band, .warning)
        XCTAssertGreaterThan(clutterMetric.edgeDensity ?? 0, 0)
        XCTAssertEqual(BackgroundComplexityAnalyzer.analyze(QualityImageFrame(width: 10, height: 10, luminance: cleanPixels)).band, .unavailable)
    }

    func testPL0099CandidateRuntimePublishesBoundedBackgroundMetricAndFallback() {
        let mask = (0..<100).map { index in (3...6).contains(index % 10) && (3...6).contains(index / 10) }
        let cleanPixels = [Double](repeating: 0.5, count: 100)
        let moderatePixels = (0..<100).map { index in mask[index] ? 0.5 : ((index % 5 == 0) ? 0.4 : 0.5) }
        let clutterPixels = (0..<100).map { index in mask[index] ? 0.5 : ((index % 2 == 0) ? 0.0 : 1.0) }
        let runtime = M04CandidateQualityRuntime(preset: PackagingPresetCatalog.matteHDPE)
        func background(_ luminance: [Double], mask: [Bool]?, id: String) -> BackgroundComplexityMetric {
            let frame = QualityImageFrame(width: 10, height: 10, luminance: luminance, objectMask: mask)
            return runtime.evaluate(M04CandidateFrameInput(sessionID: "s", captureID: id, sequence: 1, monotonicTimestamp: 1, frame: frame)).quality.metrics.background
        }
        XCTAssertEqual(background(cleanPixels, mask: mask, id: "clean").band, .clean)
        XCTAssertEqual(background(moderatePixels, mask: mask, id: "moderate").band, .clean)
        let clutter = background(clutterPixels, mask: mask, id: "clutter")
        XCTAssertEqual(clutter.band, .warning)
        XCTAssertGreaterThan(clutter.edgeDensity ?? 0, 0)
        let unavailable = background(cleanPixels, mask: nil, id: "unavailable")
        XCTAssertEqual(unavailable.band, .unavailable)
        XCTAssertTrue(unavailable.reasons.contains("background_object_region_unavailable"))
    }

    func testPL0100QualityDecisionHasStablePrecedenceAndRetainsWarnings() {
        let sharp = SharpnessMetric(availability: .available, normalizedLaplacianVariance: 0.03, sampleCount: 10, band: .accept, reasonCode: "sharpness_accept")
        let motion = MotionBlurAssessment(risk: .none, availability: .available, rotationRateMagnitude: 0, reasons: [])
        let passClip = ClippingMetric(availability: .available, clippedFraction: 0, objectClippedFraction: 0, clippedPixelCount: 0, analyzedPixelCount: 10, band: .pass, reasons: [])
        let frame = FramingMetric(availability: .available, objectFraction: 0.3, bounds: NormalizedBounds(minX: 0.2, minY: 0.2, maxX: 0.8, maxY: 0.8), margins: ["left": 0.2], band: .acceptable, reasons: [])
        let background = BackgroundComplexityMetric(availability: .available, score: 0.3, luminanceVariance: 0.01, edgeDensity: 0.2, sampledPixelCount: 10, band: .warning, reasons: ["background_complexity_warning"])
        let warningDecision = QualityDecisionEngine.evaluate(CandidateQualityMetrics(sharpness: sharp, motionBlur: motion, highlightClipping: passClip, shadowClipping: passClip, framing: frame, background: background))
        XCTAssertEqual(warningDecision.decision, .accept)
        XCTAssertTrue(warningDecision.warnings.contains("background_complexity_warning"))
        let rejected = QualityDecisionEngine.evaluate(CandidateQualityMetrics(sharpness: sharp, motionBlur: motion, highlightClipping: passClip, shadowClipping: passClip, framing: FramingMetric(availability: .available, objectFraction: 0.01, bounds: nil, margins: [:], band: .tooSmall, reasons: ["framing_too_small"]), background: background))
        XCTAssertEqual(rejected.decision, .reject)
        XCTAssertEqual(rejected.reasons, ["framing_too_small"])
    }

    func testPL0100UnavailableClippingPolicyTableAndRuntimePrecedence() {
        let sharp = SharpnessMetric(availability: .available, normalizedLaplacianVariance: 0.03, sampleCount: 10, band: .accept, reasonCode: "sharpness_accept")
        let motion = MotionBlurAssessment(risk: .none, availability: .available, rotationRateMagnitude: 0, reasons: [])
        let unavailableHighlight = ClippingMetric(availability: .unavailable, clippedFraction: nil, objectClippedFraction: nil, clippedPixelCount: 0, analyzedPixelCount: 0, band: .unavailable, reasons: ["highlight_clipping_unavailable"])
        let unavailableShadow = ClippingMetric(availability: .unavailable, clippedFraction: nil, objectClippedFraction: nil, clippedPixelCount: 0, analyzedPixelCount: 0, band: .unavailable, reasons: ["shadow_clipping_unavailable"])
        let frame = FramingMetric(availability: .available, objectFraction: 0.3, bounds: nil, margins: [:], band: .acceptable, reasons: [])
        let background = BackgroundComplexityMetric(availability: .available, score: 0, luminanceVariance: 0, edgeDensity: 0, sampledPixelCount: 10, band: .clean, reasons: [])
        let metrics = CandidateQualityMetrics(sharpness: sharp, motionBlur: motion, highlightClipping: unavailableHighlight, shadowClipping: unavailableShadow, framing: frame, background: background)
        let cases: [(QualityDecisionPolicy, CandidateQualityDecision, [String], [String])] = [
            (.provisional, .accept, [], ["highlight_clipping_unavailable", "shadow_clipping_unavailable"]),
            (QualityDecisionPolicy(rejectUnavailableClipping: true), .reject, ["highlight_clipping_unavailable", "shadow_clipping_unavailable"], [])
        ]
        for (policy, expectedDecision, expectedReasons, expectedWarnings) in cases {
            let decision = QualityDecisionEngine.evaluate(metrics, policy: policy)
            XCTAssertEqual(decision.decision, expectedDecision)
            XCTAssertEqual(decision.reasons, expectedReasons)
            XCTAssertEqual(decision.warnings, expectedWarnings)
        }
        let defaultRuntime = M04CandidateQualityRuntime(preset: PackagingPresetCatalog.matteHDPE)
        let strictRuntime = M04CandidateQualityRuntime(preset: PackagingPresetCatalog.matteHDPE, decisionPolicy: QualityDecisionPolicy(rejectUnavailableClipping: true))
        let defaultQuality = defaultRuntime.evaluateQuality(frame: .unavailable, motion: nil)
        let strictQuality = strictRuntime.evaluateQuality(frame: .unavailable, motion: nil)
        XCTAssertTrue(defaultQuality.warnings.contains("highlight_clipping_unavailable"))
        XCTAssertTrue(strictQuality.reasons.contains("highlight_clipping_unavailable"))
    }

    func testPL0101QualityCandidateLogIsBoundedOrderedAndSanitized() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "session")
        let store = QualityCandidateLogStore(layout: layout, maximumRecords: 2)
        let sharp = SharpnessMetric(availability: .available, normalizedLaplacianVariance: 0.03, sampleCount: 10, band: .accept, reasonCode: "sharpness_accept")
        let motion = MotionBlurAssessment(risk: .none, availability: .available, rotationRateMagnitude: 0, reasons: [])
        let clip = ClippingMetric(availability: .available, clippedFraction: 0, objectClippedFraction: 0, clippedPixelCount: 0, analyzedPixelCount: 10, band: .pass, reasons: [])
        let frame = FramingMetric(availability: .available, objectFraction: 0.3, bounds: nil, margins: [:], band: .acceptable, reasons: [])
        let background = BackgroundComplexityMetric(availability: .available, score: 0, luminanceVariance: 0, edgeDensity: 0, sampledPixelCount: 10, band: .clean, reasons: [])
        let decision = QualityDecisionEngine.evaluate(CandidateQualityMetrics(sharpness: sharp, motionBlur: motion, highlightClipping: clip, shadowClipping: clip, framing: frame, background: background))
        for sequence in 0..<3 { try await store.append(QualityCandidateLog(sessionID: "C:/private/session", captureID: "capture/\(sequence)", sequence: sequence, monotonicTimestamp: Double(sequence), decision: decision)) }
        let entries = try await store.snapshot()
        XCTAssertEqual(entries.map(\.sequence), [1, 2])
        XCTAssertFalse(entries[0].sessionID.contains("/"))
        XCTAssertFalse(entries[0].captureID.contains("/"))
        XCTAssertTrue(FileManager.default.fileExists(atPath: layout.qualityLog.path))
    }

    @MainActor
    func testPL0101CandidateRuntimeLogsAcceptedAndRejectedEntriesAndReopens() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "runtime-session")
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        vm.configureM04QualityRuntime(preset: PackagingPresetCatalog.matteHDPE, layout: layout)
        let acceptedFrame = QualityImageFrame(width: 10, height: 10, luminance: (0..<100).map { (($0 / 10 + $0 % 10) % 2 == 0) ? 0.2 : 0.8 }, objectMask: (0..<100).map { index in let x = index % 10; let y = index / 10; return (2...7).contains(x) && (2...7).contains(y) })
        let rejectedFrame = QualityImageFrame(width: 10, height: 10, luminance: [Double](repeating: 0.5, count: 100), objectMask: (0..<100).map { $0 == 44 })
        let accepted = await vm.analyzeM04Candidate(M04CandidateFrameInput(sessionID: "runtime-session", captureID: "accepted", sequence: 0, monotonicTimestamp: 10, frame: acceptedFrame))
        let rejected = await vm.analyzeM04Candidate(M04CandidateFrameInput(sessionID: "runtime-session", captureID: "rejected", sequence: 1, monotonicTimestamp: 11, frame: rejectedFrame))
        XCTAssertEqual(accepted.quality.decision, .accept)
        XCTAssertEqual(rejected.quality.decision, .reject)
        let reopened = try await QualityCandidateLogStore(layout: layout).snapshot()
        XCTAssertEqual(reopened.map(\.captureID), ["accepted", "rejected"])
        XCTAssertEqual(reopened.map(\.sequence), [0, 1])
        XCTAssertEqual(reopened.map(\.monotonicTimestamp), [10, 11])
    }

    func testPL0101CorruptQualityLogFailsClosedWithoutMutatingCanonicalSessionFiles() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "corrupt-runtime")
        let sessionStore = ScanSessionStore(layout: layout)
        try await sessionStore.create(NewScanDraft(sessionID: "corrupt-runtime", packageName: "Bottle", packageType: .bottle, captureMode: .guided))
        let record = AcceptedCaptureRecord(captureID: "accepted", sequence: 0, sourceFilename: "accepted.heic", metadataFilename: "accepted.json")
        let recordData = try JSONEncoder().encode(record)
        let stateData = try Data(contentsOf: layout.state)
        try await sessionStore.storeAcceptedCapture(source: Data([1, 2, 3]), record: record, metadata: recordData, state: stateData)
        let canonicalPaths = [layout.metadata, layout.state, layout.images.appendingPathComponent("accepted.heic"), layout.photoRecords.appendingPathComponent("accepted.json")]
        let canonicalBefore = try canonicalPaths.map { try Data(contentsOf: $0) }

        try Data("{malformed quality jsonl".utf8).write(to: layout.qualityLog, options: .atomic)
        do {
            _ = try await QualityCandidateLogStore(layout: layout).snapshot()
            XCTFail("corrupt quality log must fail closed")
        } catch {
            XCTAssertEqual(error as? QualityLogStoreError, .corruptLog)
        }
        XCTAssertEqual(try canonicalPaths.map { try Data(contentsOf: $0) }, canonicalBefore)
    }

    func testPL0102CoverageMapsWrapAroundAndRejectsUnavailablePose() {
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 4, rings: [CoverageRingDefinition(id: "middle", minimumElevation: -10, maximumElevation: 10)])
        var model = OrbitCoverageModel(configuration: configuration)
        let zero = PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: 0, z: -1).values, tracking: .normal)
        let wrap = PoseSample(timestamp: 2, transform: CoordinateTransform.translation(x: -0.01, y: 0, z: -1).values, tracking: .normal)
        XCTAssertEqual(model.observe(captureID: "zero", poseBinding: acceptedPoseBinding(captureID: "zero", pose: zero)).sector?.azimuthIndex, 0)
        XCTAssertEqual(model.observe(captureID: "wrap", poseBinding: acceptedPoseBinding(captureID: "wrap", pose: wrap)).sector?.azimuthIndex, 3)
        XCTAssertEqual(model.observe(captureID: "duplicate", poseBinding: acceptedPoseBinding(captureID: "duplicate", pose: zero)).status, "available")
        XCTAssertEqual(model.observe(captureID: "missing", poseBinding: nil).status, "pose_unavailable")
        XCTAssertEqual(model.snapshot().duplicateCaptureIDs, ["duplicate"])
        XCTAssertEqual(model.snapshot().invalidCaptureIDs, ["missing"])
        XCTAssertFalse(model.snapshot().isComplete)
    }

    @MainActor
    func testPL0102CoverageAcceptsOnlyAuthoritativeAlignedBindingAndUpdatesActiveRuntime() {
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 4, rings: [CoverageRingDefinition(id: "middle", minimumElevation: -10, maximumElevation: 10)])
        var model = OrbitCoverageModel(configuration: configuration)
        let availablePose = PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: 0, z: -1).values, tracking: .normal)
        let stale = PoseCaptureBinding(captureID: "stale", captureTimestamp: 1, aligned: AlignedPose(sample: nil, delta: 1, status: "stale"))
        let invalid = PoseCaptureBinding(captureID: "invalid", captureTimestamp: 1, aligned: AlignedPose(sample: nil, delta: 0, status: "invalid_transform"))
        XCTAssertEqual(model.observe(captureID: "stale", poseBinding: stale).status, "pose_stale")
        XCTAssertEqual(model.observe(captureID: "invalid", poseBinding: invalid).status, "pose_invalid_transform")
        XCTAssertEqual(model.observe(captureID: "mismatch", poseBinding: acceptedPoseBinding(captureID: "other", pose: availablePose)).status, "pose_capture_mismatch")
        XCTAssertEqual(model.snapshot().capturedSectors.count, 0)

        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        let preset = PackagingPreset(id: .matteHDPE, version: "test", displayName: "Test", quality: QualityPolicyConfiguration(), coverage: CoveragePolicyConfiguration(orbit: configuration), lightingGuidance: [], preparationGuidance: [], requiresPreparationAcknowledgement: false)
        vm.configureM04QualityRuntime(preset: preset)
        let record = AcceptedCaptureRecord(captureID: "accepted", sequence: 0, sourceFilename: "accepted.heic", metadataFilename: "accepted.json", poseBinding: acceptedPoseBinding(captureID: "accepted", pose: availablePose))
        XCTAssertEqual(vm.recordAcceptedCaptureCoverage(record).status, "available")
        XCTAssertEqual(vm.m04Coverage.capturedSectors.count, 1)
        XCTAssertEqual(vm.m04Coverage.invalidCaptureIDs, [])
    }

    func testPL0102CoverageUsesExactElevationBoundariesAndAdjacentValuesDeterministically() {
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 4, rings: [
            CoverageRingDefinition(id: "lower", minimumElevation: -30, maximumElevation: -5),
            CoverageRingDefinition(id: "middle", minimumElevation: -5, maximumElevation: 5),
            CoverageRingDefinition(id: "upper", minimumElevation: 5, maximumElevation: 30)
        ])
        func binding(_ captureID: String, elevation: Double) -> PoseCaptureBinding? {
            let radians = elevation * Double.pi / 180
            let pose = PoseSample(timestamp: Double(captureID.count), transform: CoordinateTransform.translation(x: 0, y: tan(radians), z: -1).values, tracking: .normal)
            return acceptedPoseBinding(captureID: captureID, pose: pose)
        }
        var model = OrbitCoverageModel(configuration: configuration)
        XCTAssertEqual(model.observe(captureID: "lower-min", poseBinding: binding("lower-min", elevation: -30)).sector?.ringID, "lower")
        XCTAssertNil(model.observe(captureID: "below-lower-min", poseBinding: binding("below-lower-min", elevation: -30.0001)).sector)
        XCTAssertEqual(model.observe(captureID: "lower-max", poseBinding: binding("lower-max", elevation: -5)).sector?.ringID, "middle")
        XCTAssertEqual(model.observe(captureID: "middle-min", poseBinding: binding("middle-min", elevation: -5)).sector?.ringID, "middle")
        XCTAssertEqual(model.observe(captureID: "middle-max", poseBinding: binding("middle-max", elevation: 5)).sector?.ringID, "upper")
        XCTAssertEqual(model.observe(captureID: "upper-min", poseBinding: binding("upper-min", elevation: 5)).sector?.ringID, "upper")
        XCTAssertEqual(model.observe(captureID: "upper-inside", poseBinding: binding("upper-inside", elevation: 5.0001)).sector?.ringID, "upper")
        XCTAssertNil(model.observe(captureID: "above-upper-max", poseBinding: binding("above-upper-max", elevation: 30)).sector)

        let snapshot = model.snapshot()
        XCTAssertEqual(snapshot.capturedSectors.map(\.id), ["lower-a0", "middle-a0", "upper-a0"])
        XCTAssertEqual(snapshot.invalidCaptureIDs, ["below-lower-min", "above-upper-max"])
        XCTAssertEqual(snapshot.missingSectors.count, 9)
    }

    func testPL0103CoverageViewModelLabelsEmptyPartialCompleteAndUnavailableStates() {
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 2, rings: [CoverageRingDefinition(id: "middle", minimumElevation: -10, maximumElevation: 10)])
        let emptyModel = CoverageViewModel(snapshot: OrbitCoverageModel(configuration: configuration).snapshot())
        XCTAssertTrue(emptyModel.statusText.contains("missing"))
        var unavailable = OrbitCoverageModel(configuration: configuration)
        _ = unavailable.observe(captureID: "unavailable", poseBinding: nil)
        XCTAssertEqual(CoverageViewModel(snapshot: unavailable.snapshot()).statusText, "Coverage evidence unavailable")
        var partial = OrbitCoverageModel(configuration: configuration)
        _ = partial.observe(captureID: "one", poseBinding: acceptedPoseBinding(captureID: "one", pose: PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: 0, z: -1).values, tracking: .normal)))
        let partialModel = CoverageViewModel(snapshot: partial.snapshot(), targeted: CoverageSector(ringID: "middle", azimuthIndex: 1))
        XCTAssertTrue(partialModel.items.contains { $0.status == .targeted })
        var complete = OrbitCoverageModel(configuration: configuration)
        _ = complete.observe(captureID: "one", poseBinding: acceptedPoseBinding(captureID: "one", pose: PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: 0, z: -1).values, tracking: .normal)))
        _ = complete.observe(captureID: "two", poseBinding: acceptedPoseBinding(captureID: "two", pose: PoseSample(timestamp: 2, transform: CoordinateTransform.translation(x: -1, y: 0, z: 0).values, tracking: .normal)))
        XCTAssertEqual(CoverageViewModel(snapshot: complete.snapshot()).statusText, "Coverage complete")
    }

    @MainActor
    func testPL0103ActiveRuntimeCoverageTargetAdvancesAfterAcceptedEvidence() {
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 2, rings: [CoverageRingDefinition(id: "middle", minimumElevation: -10, maximumElevation: 10)])
        let preset = PackagingPreset(id: .matteHDPE, version: "test", displayName: "Test", quality: QualityPolicyConfiguration(), coverage: CoveragePolicyConfiguration(orbit: configuration), lightingGuidance: [], preparationGuidance: [], requiresPreparationAcknowledgement: false)
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        vm.configureM04QualityRuntime(preset: preset)
        XCTAssertTrue(vm.m04CoverageActive)
        XCTAssertEqual(vm.m04CoverageTarget, CoverageSector(ringID: "middle", azimuthIndex: 0))
        let pose = PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: 0, z: -1).values, tracking: .normal)
        _ = vm.recordAcceptedCaptureCoverage(AcceptedCaptureRecord(captureID: "accepted", sequence: 0, sourceFilename: "a.heic", metadataFilename: "a.json", poseBinding: acceptedPoseBinding(captureID: "accepted", pose: pose)))
        XCTAssertEqual(vm.m04CoverageTarget, CoverageSector(ringID: "middle", azimuthIndex: 1))
        XCTAssertTrue(CoverageViewModel(snapshot: vm.m04Coverage, targeted: vm.m04CoverageTarget).accessibilityText.contains("middle sector 2 targeted"))
    }

    func testPL0104AutoCaptureRequiresAllGatesAndRearmsAfterCooldown() {
        let sharp = SharpnessMetric(availability: .available, normalizedLaplacianVariance: 0.03, sampleCount: 10, band: .accept, reasonCode: "sharpness_accept")
        let motion = MotionBlurAssessment(risk: .none, availability: .available, rotationRateMagnitude: 0, reasons: [])
        let clip = ClippingMetric(availability: .available, clippedFraction: 0, objectClippedFraction: 0, clippedPixelCount: 0, analyzedPixelCount: 10, band: .pass, reasons: [])
        let frame = FramingMetric(availability: .available, objectFraction: 0.3, bounds: nil, margins: [:], band: .acceptable, reasons: [])
        let background = BackgroundComplexityMetric(availability: .available, score: 0, luminanceVariance: 0, edgeDensity: 0, sampledPixelCount: 10, band: .clean, reasons: [])
        let quality = QualityDecisionEngine.evaluate(CandidateQualityMetrics(sharpness: sharp, motionBlur: motion, highlightClipping: clip, shadowClipping: clip, framing: frame, background: background))
        let admission = CaptureAdmissionController()
        let target = CoverageSector(ringID: "middle", azimuthIndex: 0)
        let input = AutoCaptureInput(monotonicTimestamp: 10, poseEligible: true, targetSector: target, quality: quality, overlapAllowed: true, admission: admission)
        var controller = AutoCaptureController(cooldownSeconds: 1)
        XCTAssertTrue(controller.begin(input).allowed)
        XCTAssertFalse(controller.begin(input).allowed)
        controller.complete(success: true, monotonicTimestamp: 10)
        XCTAssertFalse(controller.evaluate(input).allowed)
        XCTAssertTrue(controller.evaluate(AutoCaptureInput(monotonicTimestamp: 11.1, poseEligible: true, targetSector: target, quality: quality, overlapAllowed: true, admission: admission)).allowed)
        XCTAssertTrue(controller.evaluate(AutoCaptureInput(monotonicTimestamp: 11.1, poseEligible: false, targetSector: target, quality: quality, overlapAllowed: true, admission: admission)).reasons.contains("pose_ineligible"))
    }

    func testPL0104ProductionGateMatrixNeverInvokesBackendWhenBlocked() async {
        let sharp = SharpnessMetric(availability: .available, normalizedLaplacianVariance: 0.03, sampleCount: 10, band: .accept, reasonCode: "sharpness_accept")
        let motion = MotionBlurAssessment(risk: .none, availability: .available, rotationRateMagnitude: 0, reasons: [])
        let clip = ClippingMetric(availability: .available, clippedFraction: 0, objectClippedFraction: 0, clippedPixelCount: 0, analyzedPixelCount: 10, band: .pass, reasons: [])
        let frame = FramingMetric(availability: .available, objectFraction: 0.3, bounds: nil, margins: [:], band: .acceptable, reasons: [])
        let background = BackgroundComplexityMetric(availability: .available, score: 0, luminanceVariance: 0, edgeDensity: 0, sampledPixelCount: 10, band: .clean, reasons: [])
        let metrics = CandidateQualityMetrics(sharpness: sharp, motionBlur: motion, highlightClipping: clip, shadowClipping: clip, framing: frame, background: background)
        let acceptedQuality = QualityDecisionEngine.evaluate(metrics)
        let rejectedQuality = QualityDecision(decision: .reject, reasons: ["sharpness_reject"], warnings: [], metrics: metrics)
        let target = CoverageSector(ringID: "middle", azimuthIndex: 0)
        let ready = CaptureAdmissionController()
        let backend = CountingStillPhotoBackend()
        let gated = AdmissionControlledStillCaptureService(backend: backend)
        await gated.updateAdmission(ready)
        let guided = GuidedAutoCaptureService(stillCapture: gated, cooldownSeconds: 0.75)
        func input(_ timestamp: TimeInterval, poseEligible: Bool, targetSector: CoverageSector?, quality: QualityDecision, overlapAllowed: Bool, admission: CaptureAdmissionController) -> AutoCaptureInput {
            AutoCaptureInput(monotonicTimestamp: timestamp, poseEligible: poseEligible, targetSector: targetSector, quality: quality, overlapAllowed: overlapAllowed, duplicateDecision: DuplicateDecision(isDuplicate: false, reasonCode: "useful_candidate"), admission: admission)
        }

        let qualityBlocked = await guided.request(captureID: "quality-blocked", input: input(1, poseEligible: true, targetSector: target, quality: rejectedQuality, overlapAllowed: true, admission: ready))
        XCTAssertFalse(qualityBlocked.decision.allowed)
        XCTAssertTrue(qualityBlocked.decision.reasons.contains("sharpness_reject"))
        let targetBlocked = await guided.request(captureID: "target-blocked", input: input(2, poseEligible: true, targetSector: nil, quality: acceptedQuality, overlapAllowed: false, admission: ready))
        XCTAssertFalse(targetBlocked.decision.allowed)
        XCTAssertTrue(targetBlocked.decision.reasons.contains("coverage_target_missing"))
        let poseBlocked = await guided.request(captureID: "pose-blocked", input: input(3, poseEligible: false, targetSector: target, quality: acceptedQuality, overlapAllowed: true, admission: ready))
        XCTAssertFalse(poseBlocked.decision.allowed)
        XCTAssertTrue(poseBlocked.decision.reasons.contains("pose_ineligible"))
        let overlapBlocked = await guided.request(captureID: "overlap-blocked", input: input(4, poseEligible: true, targetSector: target, quality: acceptedQuality, overlapAllowed: false, admission: ready))
        XCTAssertFalse(overlapBlocked.decision.allowed)
        XCTAssertTrue(overlapBlocked.decision.reasons.contains("overlap_not_allowed"))
        var hardStop = CaptureAdmissionController()
        hardStop.update(.hardStop(HealthDecision(severity: .hardStop, messages: ["test health hard stop"])))
        let healthBlocked = await guided.request(captureID: "health-blocked", input: input(5, poseEligible: true, targetSector: target, quality: acceptedQuality, overlapAllowed: true, admission: hardStop))
        XCTAssertFalse(healthBlocked.decision.allowed)
        XCTAssertTrue(healthBlocked.decision.reasons.contains("test health hard stop"))
        let blockedCount = await backend.requestCount
        XCTAssertEqual(blockedCount, 0)

        var controller = AutoCaptureController(cooldownSeconds: 1)
        let controllerInput = input(10, poseEligible: true, targetSector: target, quality: acceptedQuality, overlapAllowed: true, admission: ready)
        XCTAssertTrue(controller.begin(controllerInput).allowed)
        XCTAssertFalse(controller.begin(controllerInput).allowed)
        controller.complete(success: false, monotonicTimestamp: 10)
        XCTAssertTrue(controller.evaluate(controllerInput).allowed)

        let accepted = await guided.request(captureID: "accepted", input: input(20, poseEligible: true, targetSector: target, quality: acceptedQuality, overlapAllowed: true, admission: ready))
        XCTAssertTrue(accepted.decision.allowed)
        XCTAssertNotNil(accepted.result)
        let acceptedCount = await backend.requestCount
        XCTAssertEqual(acceptedCount, 1)
        let cooldownBlocked = await guided.request(captureID: "cooldown-blocked", input: input(20.74, poseEligible: true, targetSector: target, quality: acceptedQuality, overlapAllowed: true, admission: ready))
        XCTAssertFalse(cooldownBlocked.decision.allowed)
        XCTAssertTrue(cooldownBlocked.decision.reasons.contains("auto_capture_cooldown"))
        let cooldownCount = await backend.requestCount
        XCTAssertEqual(cooldownCount, 1)
        let cooldownBoundary = await guided.request(captureID: "cooldown-boundary", input: input(20.75, poseEligible: true, targetSector: target, quality: acceptedQuality, overlapAllowed: true, admission: ready))
        XCTAssertTrue(cooldownBoundary.decision.allowed)
        let boundaryCount = await backend.requestCount
        XCTAssertEqual(boundaryCount, 2)
    }

    @MainActor
    func testPL0104ProductionAutoCaptureUsesHealthGatedBackendAndAcceptedTransaction() async throws {
        struct Backend: StillPhotoBackend, Sendable {
            func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) { (Data([1, 2, 3]), CaptureDimensions(width: 2, height: 1)) }
        }
        let vm = CaptureRuntimeViewModel(trackingService: SequenceTrackingService([TrackingQualityClassifier.classify(state: .normal)]), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 2, rings: [CoverageRingDefinition(id: "middle", minimumElevation: -10, maximumElevation: 10)])
        let preset = PackagingPreset(id: .matteHDPE, version: "test", displayName: "Test", quality: QualityPolicyConfiguration(), coverage: CoveragePolicyConfiguration(orbit: configuration), lightingGuidance: [], preparationGuidance: [], requiresPreparationAcknowledgement: false)
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "auto")
        let store = ScanSessionStore(layout: layout)
        try await store.create(NewScanDraft(sessionID: "auto", packageName: "Bottle", packageType: .bottle, captureMode: .guided))
        vm.configureM04QualityRuntime(preset: preset, layout: layout)
        await vm.bindStillCaptureBackend(Backend())
        await vm.start(); await vm.refresh()
        let frame = QualityImageFrame(width: 10, height: 10, luminance: (0..<100).map { (($0 / 10 + $0 % 10) % 2 == 0) ? 0.2 : 0.8 }, objectMask: (0..<100).map { index in let x = index % 10; let y = index / 10; return (2...7).contains(x) && (2...7).contains(y) })
        _ = await vm.analyzeM04Candidate(M04CandidateFrameInput(sessionID: "auto", captureID: "candidate", sequence: 0, monotonicTimestamp: 10, frame: frame))
        var poses = PoseBuffer(); poses.append(PoseSample(timestamp: 10, transform: CoordinateTransform.translation(x: 0, y: 0, z: -1).values, tracking: .normal))
        let record = AcceptedCaptureRecord(captureID: "auto-capture", sequence: 0, sourceFilename: "auto-capture.heic", metadataFilename: "auto-capture.json")
        let state = try JSONEncoder().encode(PersistedSessionState(sessionID: "auto", nextSequence: 1, epoch: 0, acceptedIDs: ["auto-capture"]))
        let metadata = try JSONEncoder().encode(record)
        let outcome = try await vm.requestAutoCaptureAndPersist(captureID: "auto-capture", monotonicTimestamp: 10, record: record, metadata: metadata, state: state, store: store, poses: poses, motion: MotionBuffer())
        XCTAssertTrue(outcome.decision.allowed)
        XCTAssertNotNil(outcome.still)
        XCTAssertEqual(vm.m04Coverage.capturedSectors.count, 1)
        let cooldown = await vm.requestAutoCapture(captureID: "cooldown", monotonicTimestamp: 10.1)
        XCTAssertTrue(cooldown.decision.reasons.contains("auto_capture_cooldown"))
        await vm.stop()
    }

    func testPL0105NearDuplicateDetectionPreservesUsefulParallaxAndFailsSafeWithoutPose() {
        let base = PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: 0, z: -1).values, tracking: .normal)
        let accepted = DuplicateEvidence(captureID: "accepted", pose: base, visualSignature: [1, 2, 3])
        let duplicate = NearDuplicateDetector.evaluate(candidate: DuplicateEvidence(captureID: "candidate", pose: base, visualSignature: [1, 2, 3]), accepted: [accepted])
        XCTAssertTrue(duplicate.isDuplicate)
        let parallax = PoseSample(timestamp: 2, transform: CoordinateTransform.translation(x: 0.2, y: 0, z: -1).values, tracking: .normal)
        XCTAssertFalse(NearDuplicateDetector.evaluate(candidate: DuplicateEvidence(captureID: "parallax", pose: parallax), accepted: [accepted]).isDuplicate)
        let stale = PoseSample(timestamp: 3, transform: base.transform, tracking: .limited)
        XCTAssertEqual(NearDuplicateDetector.evaluate(candidate: DuplicateEvidence(captureID: "stale", pose: stale), accepted: [accepted]).reasonCode, "duplicate_pose_unavailable")
    }

    func testPL0105AcceptedPoseBindingDuplicateDecisionFeedsAutoGate() {
        let base = PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: 0, z: -1).values, tracking: .normal)
        let binding = acceptedPoseBinding(captureID: "accepted", pose: base)
        let duplicate = NearDuplicateDetector.evaluate(candidate: DuplicateEvidence(captureID: "candidate", poseBinding: acceptedPoseBinding(captureID: "candidate", pose: base), visualSignature: [1, 2, 3]), accepted: [DuplicateEvidence(captureID: "accepted", poseBinding: binding, visualSignature: [1, 2, 3])])
        XCTAssertTrue(duplicate.isDuplicate)
        XCTAssertEqual(duplicate.reasonCode, "near_duplicate_candidate")
        let stale = PoseCaptureBinding(captureID: "candidate", captureTimestamp: 1, aligned: AlignedPose(sample: nil, delta: 1, status: "stale"))
        let useful = NearDuplicateDetector.evaluate(candidate: DuplicateEvidence(captureID: "candidate", poseBinding: stale), accepted: [DuplicateEvidence(captureID: "accepted", poseBinding: binding)])
        XCTAssertFalse(useful.isDuplicate)
        XCTAssertEqual(useful.reasonCode, "duplicate_pose_unavailable")
        let sharp = SharpnessMetric(availability: .available, normalizedLaplacianVariance: 0.03, sampleCount: 10, band: .accept, reasonCode: "sharpness_accept")
        let motion = MotionBlurAssessment(risk: .none, availability: .available, rotationRateMagnitude: 0, reasons: [])
        let clip = ClippingMetric(availability: .available, clippedFraction: 0, objectClippedFraction: 0, clippedPixelCount: 0, analyzedPixelCount: 10, band: .pass, reasons: [])
        let frame = FramingMetric(availability: .available, objectFraction: 0.3, bounds: nil, margins: [:], band: .acceptable, reasons: [])
        let background = BackgroundComplexityMetric(availability: .available, score: 0, luminanceVariance: 0, edgeDensity: 0, sampledPixelCount: 10, band: .clean, reasons: [])
        let quality = QualityDecisionEngine.evaluate(CandidateQualityMetrics(sharpness: sharp, motionBlur: motion, highlightClipping: clip, shadowClipping: clip, framing: frame, background: background))
        let input = AutoCaptureInput(monotonicTimestamp: 1, poseEligible: true, targetSector: CoverageSector(ringID: "middle", azimuthIndex: 0), quality: quality, overlapAllowed: true, duplicateDecision: duplicate, admission: CaptureAdmissionController())
        XCTAssertTrue(AutoCaptureController().evaluate(input).reasons.contains("near_duplicate_candidate"))
    }

    func testPL0105DuplicateDetectorProvesTranslationElevationAndSignatureBoundaries() {
        let basePose = PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: 0, z: -1).values, tracking: .normal)
        let accepted = DuplicateEvidence(captureID: "accepted", pose: basePose, visualSignature: [0, 0, 0, 0])

        let translationPolicy = DuplicatePolicy(maximumTranslationMeters: 0.04, maximumElevationDifference: 0, maximumSignatureDistance: 0)
        let atTranslation = PoseSample(timestamp: 2, transform: CoordinateTransform.translation(x: 0.04, y: 0, z: -1).values, tracking: .normal)
        let pastTranslation = PoseSample(timestamp: 3, transform: CoordinateTransform.translation(x: 0.040001, y: 0, z: -1).values, tracking: .normal)
        XCTAssertTrue(NearDuplicateDetector.evaluate(candidate: DuplicateEvidence(captureID: "translation-at", pose: atTranslation), accepted: [accepted], policy: translationPolicy).isDuplicate)
        XCTAssertFalse(NearDuplicateDetector.evaluate(candidate: DuplicateEvidence(captureID: "translation-past", pose: pastTranslation), accepted: [accepted], policy: translationPolicy).isDuplicate)

        let elevationPolicy = DuplicatePolicy(maximumTranslationMeters: 1, maximumElevationDifference: 4, maximumSignatureDistance: 0)
        let atElevation = PoseSample(timestamp: 4, transform: CoordinateTransform.translation(x: 0, y: tan(4 * Double.pi / 180), z: -1).values, tracking: .normal)
        let pastElevation = PoseSample(timestamp: 5, transform: CoordinateTransform.translation(x: 0, y: tan(4.0001 * Double.pi / 180), z: -1).values, tracking: .normal)
        XCTAssertTrue(NearDuplicateDetector.evaluate(candidate: DuplicateEvidence(captureID: "elevation-at", pose: atElevation), accepted: [accepted], policy: elevationPolicy).isDuplicate)
        XCTAssertFalse(NearDuplicateDetector.evaluate(candidate: DuplicateEvidence(captureID: "elevation-past", pose: pastElevation), accepted: [accepted], policy: elevationPolicy).isDuplicate)

        let sameAzimuthUseful = PoseSample(timestamp: 6, transform: CoordinateTransform.translation(x: 0, y: tan(5 * Double.pi / 180), z: -1).values, tracking: .normal)
        XCTAssertFalse(NearDuplicateDetector.evaluate(candidate: DuplicateEvidence(captureID: "elevation-useful", pose: sameAzimuthUseful), accepted: [accepted], policy: translationPolicy).isDuplicate)

        let signaturePolicy = DuplicatePolicy(maximumTranslationMeters: 0, maximumElevationDifference: 0, maximumSignatureDistance: 2)
        let signatureAt = DuplicateEvidence(captureID: "signature-at", pose: basePose, visualSignature: [0, 0, 1, 1])
        let signaturePast = DuplicateEvidence(captureID: "signature-past", pose: basePose, visualSignature: [0, 1, 1, 1])
        XCTAssertTrue(NearDuplicateDetector.evaluate(candidate: signatureAt, accepted: [accepted], policy: signaturePolicy).isDuplicate)
        XCTAssertFalse(NearDuplicateDetector.evaluate(candidate: signaturePast, accepted: [accepted], policy: signaturePolicy).isDuplicate)
    }

    func testPL0106StandardBottleCompletionRequiresEveryConfiguredRing() {
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 2, rings: [CoverageRingDefinition(id: "lower", minimumElevation: -30, maximumElevation: -5), CoverageRingDefinition(id: "middle", minimumElevation: -5, maximumElevation: 5), CoverageRingDefinition(id: "upper", minimumElevation: 5, maximumElevation: 30)])
        let policy = StandardBottleCoveragePolicy(requirements: [RingCoverageRequirement(ringID: "lower", minimumSectorCount: 1), RingCoverageRequirement(ringID: "middle", minimumSectorCount: 1), RingCoverageRequirement(ringID: "upper", minimumSectorCount: 1)])
        var model = OrbitCoverageModel(configuration: configuration)
        _ = model.observe(captureID: "lower", poseBinding: acceptedPoseBinding(captureID: "lower", pose: PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: -0.2, z: -1).values, tracking: .normal)))
        _ = model.observe(captureID: "middle", poseBinding: acceptedPoseBinding(captureID: "middle", pose: PoseSample(timestamp: 2, transform: CoordinateTransform.translation(x: 0, y: 0, z: -1).values, tracking: .normal)))
        XCTAssertFalse(RingCoverageEvaluation(snapshot: model.snapshot(), policy: policy).isComplete)
        XCTAssertEqual(RingCoverageEvaluation(snapshot: model.snapshot(), policy: policy).missingRingIDs, ["upper"])
        _ = model.observe(captureID: "upper", poseBinding: acceptedPoseBinding(captureID: "upper", pose: PoseSample(timestamp: 3, transform: CoordinateTransform.translation(x: 0, y: 0.2, z: -1).values, tracking: .normal)))
        XCTAssertTrue(RingCoverageEvaluation(snapshot: model.snapshot(), policy: policy).isComplete)
    }

    @MainActor
    func testPL0106ActivePresetRingPolicyPublishesUnevenGuidance() {
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 2, rings: [CoverageRingDefinition(id: "lower", minimumElevation: -30, maximumElevation: -5), CoverageRingDefinition(id: "middle", minimumElevation: -5, maximumElevation: 5), CoverageRingDefinition(id: "upper", minimumElevation: 5, maximumElevation: 30)])
        let policy = StandardBottleCoveragePolicy(requirements: [RingCoverageRequirement(ringID: "lower", minimumSectorCount: 1), RingCoverageRequirement(ringID: "middle", minimumSectorCount: 1), RingCoverageRequirement(ringID: "upper", minimumSectorCount: 1)])
        let preset = PackagingPreset(id: .matteHDPE, version: "test", displayName: "Test", quality: QualityPolicyConfiguration(), coverage: CoveragePolicyConfiguration(orbit: configuration, ringRequirements: policy), lightingGuidance: [], preparationGuidance: [], requiresPreparationAcknowledgement: false)
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        vm.configureM04QualityRuntime(preset: preset)
        XCTAssertEqual(vm.m04RingCoverage.missingRingIDs, ["lower", "middle", "upper"])
        let lower = PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: -0.2, z: -1).values, tracking: .normal)
        _ = vm.recordAcceptedCaptureCoverage(AcceptedCaptureRecord(captureID: "lower", sequence: 0, sourceFilename: "l.heic", metadataFilename: "l.json", poseBinding: acceptedPoseBinding(captureID: "lower", pose: lower)))
        XCTAssertEqual(vm.m04RingCoverage.missingRingIDs, ["middle", "upper"])
        XCTAssertTrue(vm.m04RingCoverage.guidance.contains("Capture more middle ring sectors"))
        XCTAssertFalse(vm.m04RingCoverage.isComplete)
    }

    @MainActor
    func testPL0106RingAndSectorBoundariesAreDeterministicInLiveGuidance() {
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 4, rings: [
            CoverageRingDefinition(id: "lower", minimumElevation: -30, maximumElevation: -5),
            CoverageRingDefinition(id: "middle", minimumElevation: -5, maximumElevation: 5),
            CoverageRingDefinition(id: "upper", minimumElevation: 5, maximumElevation: 30)
        ])
        let policy = StandardBottleCoveragePolicy(requirements: [
            RingCoverageRequirement(ringID: "lower", minimumSectorCount: 1),
            RingCoverageRequirement(ringID: "middle", minimumSectorCount: 1),
            RingCoverageRequirement(ringID: "upper", minimumSectorCount: 1)
        ])
        func binding(_ captureID: String, elevation: Double, azimuth: Double = 0) -> PoseCaptureBinding? {
            let elevationRadians = elevation * Double.pi / 180
            let azimuthRadians = azimuth * Double.pi / 180
            let pose = PoseSample(timestamp: Double(captureID.count), transform: CoordinateTransform.translation(x: sin(azimuthRadians), y: tan(elevationRadians), z: -cos(azimuthRadians)).values, tracking: .normal)
            return acceptedPoseBinding(captureID: captureID, pose: pose)
        }
        var model = OrbitCoverageModel(configuration: configuration)
        XCTAssertEqual(model.observe(captureID: "lower", poseBinding: binding("lower", elevation: -30)).sector, CoverageSector(ringID: "lower", azimuthIndex: 0))
        XCTAssertEqual(model.observe(captureID: "middle", poseBinding: binding("middle", elevation: -5)).sector, CoverageSector(ringID: "middle", azimuthIndex: 0))
        XCTAssertEqual(model.observe(captureID: "upper", poseBinding: binding("upper", elevation: 5)).sector, CoverageSector(ringID: "upper", azimuthIndex: 0))
        XCTAssertNil(model.observe(captureID: "outside", poseBinding: binding("outside", elevation: 30)).sector)
        XCTAssertEqual(model.observe(captureID: "azimuth-before", poseBinding: binding("azimuth-before", elevation: 0, azimuth: 89.999)).sector?.azimuthIndex, 0)
        XCTAssertEqual(model.observe(captureID: "azimuth-at", poseBinding: binding("azimuth-at", elevation: 0, azimuth: 90)).sector?.azimuthIndex, 1)
        XCTAssertEqual(model.observe(captureID: "azimuth-next", poseBinding: binding("azimuth-next", elevation: 0, azimuth: 180)).sector?.azimuthIndex, 2)
        XCTAssertEqual(model.observe(captureID: "azimuth-last", poseBinding: binding("azimuth-last", elevation: 0, azimuth: 359.999)).sector?.azimuthIndex, 3)

        let preset = PackagingPreset(id: .matteHDPE, version: "boundary-test", displayName: "Boundary Test", quality: QualityPolicyConfiguration(), coverage: CoveragePolicyConfiguration(orbit: configuration, ringRequirements: policy), lightingGuidance: [], preparationGuidance: [], requiresPreparationAcknowledgement: false)
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        vm.configureM04QualityRuntime(preset: preset)
        XCTAssertEqual(vm.m04RingCoverage.missingRingIDs, ["lower", "middle", "upper"])
        _ = vm.recordAcceptedCaptureCoverage(AcceptedCaptureRecord(captureID: "live-lower", sequence: 0, sourceFilename: "l.heic", metadataFilename: "l.json", poseBinding: binding("live-lower", elevation: -30)))
        XCTAssertEqual(vm.m04RingCoverage.missingRingIDs, ["middle", "upper"])
        _ = vm.recordAcceptedCaptureCoverage(AcceptedCaptureRecord(captureID: "live-middle", sequence: 1, sourceFilename: "m.heic", metadataFilename: "m.json", poseBinding: binding("live-middle", elevation: -5)))
        XCTAssertEqual(vm.m04RingCoverage.missingRingIDs, ["upper"])
        _ = vm.recordAcceptedCaptureCoverage(AcceptedCaptureRecord(captureID: "live-upper", sequence: 2, sourceFilename: "u.heic", metadataFilename: "u.json", poseBinding: binding("live-upper", elevation: 5)))
        XCTAssertTrue(vm.m04RingCoverage.isComplete)
        XCTAssertTrue(vm.m04RingCoverage.guidance.isEmpty)
    }

    func testPL0107DetailPassRequiresCoverageQualityAndExplicitMetadata() {
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 2, rings: [CoverageRingDefinition(id: "neck", minimumElevation: 15, maximumElevation: 45)])
        let policy = DetailPassPolicy(passID: .neck, minimumFramingFraction: 0.2, minimumSectorCount: 1)
        var model = OrbitCoverageModel(configuration: configuration)
        _ = model.observe(captureID: "neck", poseBinding: acceptedPoseBinding(captureID: "neck", pose: PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: 0.4, z: -1).values, tracking: .normal)))
        let framing = FramingMetric(availability: .available, objectFraction: 0.25, bounds: nil, margins: ["left": 0.2], band: .acceptable, reasons: [])
        let evaluation = DetailPassEvaluation(snapshot: model.snapshot(), framing: framing, policy: policy)
        XCTAssertTrue(evaluation.isComplete)
        XCTAssertEqual(evaluation.metadata.passID, .neck)
        let unavailable = DetailPassEvaluation(snapshot: OrbitCoverageSnapshot(configuration: configuration, capturedSectors: [], missingSectors: [CoverageSector(ringID: "neck", azimuthIndex: 0)], duplicateCaptureIDs: [], invalidCaptureIDs: ["missing"], observations: []), framing: framing, policy: policy)
        XCTAssertEqual(unavailable.metadata.evidenceStatus, "pose_evidence_unavailable")
    }

    @MainActor
    func testPL0107DetailPassRuntimeGatesAndPersistsPassMetadata() async throws {
        struct Backend: StillPhotoBackend, Sendable {
            func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) { (Data([7, 8, 9]), CaptureDimensions(width: 2, height: 1)) }
        }
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        vm.configureM04QualityRuntime(preset: PackagingPresetCatalog.matteHDPE)
        let sharp = SharpnessMetric(availability: .available, normalizedLaplacianVariance: 0.03, sampleCount: 10, band: .accept, reasonCode: "sharpness_accept")
        let motion = MotionBlurAssessment(risk: .none, availability: .available, rotationRateMagnitude: 0, reasons: [])
        let clip = ClippingMetric(availability: .available, clippedFraction: 0, objectClippedFraction: 0, clippedPixelCount: 0, analyzedPixelCount: 10, band: .pass, reasons: [])
        let framing = FramingMetric(availability: .available, objectFraction: 0.25, bounds: nil, margins: ["left": 0.2], band: .acceptable, reasons: [])
        let background = BackgroundComplexityMetric(availability: .available, score: 0, luminanceVariance: 0, edgeDensity: 0, sampledPixelCount: 10, band: .clean, reasons: [])
        let quality = QualityDecisionEngine.evaluate(CandidateQualityMetrics(sharpness: sharp, motionBlur: motion, highlightClipping: clip, shadowClipping: clip, framing: framing, background: background))
        let pose = PoseSample(timestamp: 10, transform: CoordinateTransform.translation(x: 0, y: 0.3, z: -1).values, tracking: .normal)
        let binding = acceptedPoseBinding(captureID: "detail", pose: pose)
        let useful = DuplicateDecision(isDuplicate: false, reasonCode: "useful_candidate")
        let accepted = vm.evaluateDetailPass(passID: .neck, quality: quality, framing: framing, poseBinding: binding, duplicateDecision: useful)
        XCTAssertTrue(accepted.allowed)
        XCTAssertEqual(accepted.metadata.passID, .neck)
        let rejected = vm.evaluateDetailPass(passID: .neck, quality: QualityDecision(decision: .reject, reasons: ["sharpness_reject"], warnings: [], metrics: quality.metrics), framing: framing, poseBinding: binding, duplicateDecision: useful)
        XCTAssertFalse(rejected.allowed)
        XCTAssertTrue(rejected.reasons.contains("sharpness_reject"))
        let duplicate = vm.evaluateDetailPass(passID: .neck, quality: quality, framing: framing, poseBinding: binding, duplicateDecision: DuplicateDecision(isDuplicate: true, reasonCode: "near_duplicate_candidate", matchedCaptureID: "old"))
        XCTAssertFalse(duplicate.allowed)
        let unavailable = vm.evaluateDetailPass(passID: .neck, quality: quality, framing: framing, poseBinding: nil, duplicateDecision: useful)
        XCTAssertTrue(unavailable.reasons.contains("pose_evidence_unavailable"))

        await vm.bindStillCaptureBackend(Backend())
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "detail")
        let store = ScanSessionStore(layout: layout); try await store.create(NewScanDraft(sessionID: "detail", packageName: "Bottle", packageType: .bottle, captureMode: .guided))
        let record = AcceptedCaptureRecord(captureID: "detail", sequence: 0, sourceFilename: "detail.heic", metadataFilename: "detail.json")
        let state = try JSONEncoder().encode(PersistedSessionState(sessionID: "detail", nextSequence: 1, epoch: 0, acceptedIDs: ["detail"]))
        let outcome = try await vm.captureAndPersistDetailPass(passID: .neck, quality: quality, framing: framing, poseBinding: binding, duplicateDecision: useful, record: record, metadata: Data(), state: state, store: store, poses: PoseBuffer(), motion: MotionBuffer())
        XCTAssertNotNil(outcome.still)
        let persisted = try JSONDecoder().decode(AcceptedCaptureRecord.self, from: Data(contentsOf: layout.photoRecords.appendingPathComponent("detail.json")))
        XCTAssertEqual(persisted.passMetadata?.passID, .neck)
        XCTAssertEqual(persisted.passMetadata?.evidenceStatus, "accepted")
    }

    @MainActor
    func testPL0108BasePassHonorsSafetyStateAndPersistsAcceptedStatus() async throws {
        struct Backend: StillPhotoBackend, Sendable {
            func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) { (Data([4, 5, 6]), CaptureDimensions(width: 2, height: 1)) }
        }
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 2, rings: [CoverageRingDefinition(id: "base", minimumElevation: -90, maximumElevation: 90)])
        var model = OrbitCoverageModel(configuration: configuration)
        let first = PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: 0, z: -1).values, tracking: .normal)
        let second = PoseSample(timestamp: 2, transform: CoordinateTransform.translation(x: -1, y: 0, z: 0).values, tracking: .normal)
        _ = model.observe(captureID: "one", poseBinding: acceptedPoseBinding(captureID: "one", pose: first))
        _ = model.observe(captureID: "two", poseBinding: acceptedPoseBinding(captureID: "two", pose: second))
        let quality = QualityDecisionEngine.evaluate(CandidateQualityMetrics(sharpness: SharpnessMetric(availability: .available, normalizedLaplacianVariance: 0.03, sampleCount: 10, band: .accept, reasonCode: "sharpness_accept"), motionBlur: MotionBlurAssessment(risk: .none, availability: .available, rotationRateMagnitude: 0, reasons: []), highlightClipping: ClippingMetric(availability: .available, clippedFraction: 0, objectClippedFraction: 0, clippedPixelCount: 0, analyzedPixelCount: 10, band: .pass, reasons: []), shadowClipping: ClippingMetric(availability: .available, clippedFraction: 0, objectClippedFraction: 0, clippedPixelCount: 0, analyzedPixelCount: 10, band: .pass, reasons: []), framing: FramingMetric(availability: .available, objectFraction: 0.3, bounds: nil, margins: [:], band: .acceptable, reasons: []), background: BackgroundComplexityMetric(availability: .available, score: 0, luminanceVariance: 0, edgeDensity: 0, sampledPixelCount: 10, band: .clean, reasons: [])))
        let useful = DuplicateDecision(isDuplicate: false, reasonCode: "useful_candidate")
        let complete = BasePassEvaluation(snapshot: model.snapshot(), availability: BasePassAvailability(physicallyFeasible: true, reasonCode: "operator_confirmed_feasible"))
        XCTAssertEqual(complete.status, "complete")
        let incomplete = BasePassEvaluation(snapshot: OrbitCoverageModel(configuration: configuration).snapshot(), availability: BasePassAvailability(physicallyFeasible: true, reasonCode: "operator_confirmed_feasible"))
        XCTAssertEqual(incomplete.status, "incomplete")
        let unavailable = BasePassAcceptanceDecision(snapshot: model.snapshot(), availability: BasePassAvailability(physicallyFeasible: false, reasonCode: "object_cannot_be_safely_tilted"), quality: quality, poseBinding: acceptedPoseBinding(captureID: "base", pose: first), duplicateDecision: useful)
        XCTAssertFalse(unavailable.allowed)
        XCTAssertTrue(unavailable.reasons.contains("object_cannot_be_safely_tilted"))
        let rejectedPose = BasePassAcceptanceDecision(snapshot: model.snapshot(), availability: BasePassAvailability(physicallyFeasible: true, reasonCode: "operator_confirmed_feasible"), quality: quality, poseBinding: nil, duplicateDecision: useful)
        XCTAssertTrue(rejectedPose.reasons.contains("pose_evidence_unavailable"))

        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        let preset = PackagingPreset(id: .matteHDPE, version: "test", displayName: "Test", quality: QualityPolicyConfiguration(), coverage: CoveragePolicyConfiguration(orbit: configuration), lightingGuidance: [], preparationGuidance: [], requiresPreparationAcknowledgement: false)
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "base")
        let store = ScanSessionStore(layout: layout); try await store.create(NewScanDraft(sessionID: "base", packageName: "Bottle", packageType: .bottle, captureMode: .guided)); try await M04SessionContextStore(layout: layout).persist(M04ScanContext(preset: preset))
        vm.configureM04QualityRuntime(preset: preset, layout: layout); vm.setBasePassAvailability(BasePassAvailability(physicallyFeasible: true, reasonCode: "operator_confirmed_feasible")); await vm.bindStillCaptureBackend(Backend())
        let binding = acceptedPoseBinding(captureID: "base", pose: first)
        let record = AcceptedCaptureRecord(captureID: "base", sequence: 0, sourceFilename: "base.heic", metadataFilename: "base.json")
        let state = try JSONEncoder().encode(PersistedSessionState(sessionID: "base", nextSequence: 1, epoch: 0, acceptedIDs: ["base"]))
        let outcome = try await vm.captureAndPersistBasePass(quality: quality, poseBinding: binding, duplicateDecision: useful, record: record, metadata: Data(), state: state, store: store, poses: PoseBuffer(), motion: MotionBuffer())
        XCTAssertNotNil(outcome.still)
        XCTAssertEqual(vm.m04BasePass.status, "incomplete")
        let persisted = try JSONDecoder().decode(AcceptedCaptureRecord.self, from: Data(contentsOf: layout.photoRecords.appendingPathComponent("base.json")))
        XCTAssertEqual(persisted.passMetadata?.passID, .base)
        await Task.yield()
        let persistedContext = try await M04SessionContextStore(layout: layout).load()
        XCTAssertEqual(persistedContext.basePass?.status, "incomplete")
    }

    func testPL0108BasePassSeparatesFeasibleIncompleteAndUnavailableStates() {
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 2, rings: [CoverageRingDefinition(id: "base", minimumElevation: -60, maximumElevation: -35)])
        var model = OrbitCoverageModel(configuration: configuration)
        _ = model.observe(captureID: "base-1", poseBinding: acceptedPoseBinding(captureID: "base-1", pose: PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: -1, z: -1).values, tracking: .normal)))
        let incomplete = BasePassEvaluation(snapshot: model.snapshot(), availability: BasePassAvailability(physicallyFeasible: true, reasonCode: "operator_confirmed_feasible"), minimumSectorCount: 2)
        XCTAssertEqual(incomplete.status, "incomplete")
        let unavailable = BasePassEvaluation(snapshot: model.snapshot(), availability: BasePassAvailability(physicallyFeasible: false, reasonCode: "object_cannot_be_safely_tilted"))
        XCTAssertEqual(unavailable.status, "unavailable")
        XCTAssertFalse(unavailable.isComplete)
    }

    func testPL0109CompletionDiagnosticsNeverHidesMandatoryMissingAreas() {
        let ring = RingCoverageEvaluation(snapshot: OrbitCoverageSnapshot(configuration: OrbitCoverageConfiguration(), capturedSectors: [CoverageSector(ringID: "lower", azimuthIndex: 0)], missingSectors: [CoverageSector(ringID: "middle", azimuthIndex: 0)], duplicateCaptureIDs: [], invalidCaptureIDs: [], observations: []), policy: StandardBottleCoveragePolicy(requirements: [RingCoverageRequirement(ringID: "lower", minimumSectorCount: 1), RingCoverageRequirement(ringID: "middle", minimumSectorCount: 1)]))
        let base = BasePassEvaluation(snapshot: OrbitCoverageSnapshot(configuration: OrbitCoverageConfiguration(), capturedSectors: [], missingSectors: [], duplicateCaptureIDs: [], invalidCaptureIDs: [], observations: []), availability: BasePassAvailability(physicallyFeasible: false, reasonCode: "base_view_unavailable"))
        let diagnostics = CompletionDiagnostics(rings: ring, base: base)
        XCTAssertEqual(diagnostics.status, .incomplete)
        XCTAssertTrue(diagnostics.mandatoryMissingAreas.contains("middle"))
        XCTAssertTrue(diagnostics.optionalUnavailableAreas.contains("base"))
        XCTAssertLessThan(diagnostics.score, 1)
    }

    func testPL0109CompletionDiagnosticsDistinguishesCompleteAndUnavailableEvidence() {
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 1, rings: [CoverageRingDefinition(id: "lower", minimumElevation: -90, maximumElevation: 90)])
        let policy = StandardBottleCoveragePolicy(requirements: [RingCoverageRequirement(ringID: "lower", minimumSectorCount: 1)])
        let completeSnapshot = OrbitCoverageSnapshot(configuration: configuration, capturedSectors: [CoverageSector(ringID: "lower", azimuthIndex: 0)], missingSectors: [], duplicateCaptureIDs: [], invalidCaptureIDs: [], observations: [])
        let complete = CompletionDiagnostics(rings: RingCoverageEvaluation(snapshot: completeSnapshot, policy: policy))
        XCTAssertEqual(complete.status, .complete)
        XCTAssertEqual(complete.score, 1)
        let unavailable = CompletionDiagnostics(rings: RingCoverageEvaluation(snapshot: OrbitCoverageModel().snapshot()))
        XCTAssertEqual(unavailable.status, .unavailable)
        XCTAssertEqual(unavailable.score, 0)
    }

    @MainActor
    func testPL0109ActiveCompletionPropagatesAndPersistsWithOptionalBaseState() async throws {
        let configuration = OrbitCoverageConfiguration(azimuthBinCount: 2, rings: [CoverageRingDefinition(id: "middle", minimumElevation: -10, maximumElevation: 10)])
        let policy = StandardBottleCoveragePolicy(requirements: [RingCoverageRequirement(ringID: "middle", minimumSectorCount: 1)])
        let preset = PackagingPreset(id: .matteHDPE, version: "test", displayName: "Test", quality: QualityPolicyConfiguration(), coverage: CoveragePolicyConfiguration(orbit: configuration, ringRequirements: policy), lightingGuidance: [], preparationGuidance: [], requiresPreparationAcknowledgement: false)
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "completion")
        try await M04SessionContextStore(layout: layout).persist(M04ScanContext(preset: preset))
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        vm.configureM04QualityRuntime(preset: preset, layout: layout)
        XCTAssertEqual(vm.m04Completion.status, .incomplete)
        XCTAssertTrue(vm.m04Completion.mandatoryMissingAreas.contains("middle"))
        vm.setBasePassAvailability(BasePassAvailability(physicallyFeasible: false, reasonCode: "base_unavailable"))
        for _ in 0..<3 { await Task.yield() }
        let loaded = try await M04SessionContextStore(layout: layout).load()
        XCTAssertEqual(loaded.completion, vm.m04Completion)
        XCTAssertTrue(loaded.completion?.mandatoryMissingAreas.contains("middle") == true)
        let optionalBase = BasePassEvaluation(snapshot: vm.m04Coverage, availability: BasePassAvailability(physicallyFeasible: false, reasonCode: "base_unavailable"))
        let optionalDiagnostics = CompletionDiagnostics(rings: vm.m04RingCoverage, base: optionalBase)
        XCTAssertTrue(optionalDiagnostics.optionalUnavailableAreas.contains("base"))
    }

    func testPL0110ManualCaptureAllowsQualityWarningButNeverSafetyOrEvidenceBypass() {
        let sharp = SharpnessMetric(availability: .available, normalizedLaplacianVariance: 0.001, sampleCount: 10, band: .reject, reasonCode: "sharpness_reject")
        let motion = MotionBlurAssessment(risk: .warning, availability: .available, rotationRateMagnitude: 0.5, reasons: ["image_blur_with_motion"])
        let clip = ClippingMetric(availability: .available, clippedFraction: 0, objectClippedFraction: 0, clippedPixelCount: 0, analyzedPixelCount: 10, band: .pass, reasons: [])
        let frame = FramingMetric(availability: .available, objectFraction: 0.3, bounds: nil, margins: [:], band: .acceptable, reasons: [])
        let background = BackgroundComplexityMetric(availability: .available, score: 0, luminanceVariance: 0, edgeDensity: 0, sampledPixelCount: 10, band: .clean, reasons: [])
        let quality = QualityDecisionEngine.evaluate(CandidateQualityMetrics(sharpness: sharp, motionBlur: motion, highlightClipping: clip, shadowClipping: clip, framing: frame, background: background))
        let admission = CaptureAdmissionController()
        let automatic = AutoCaptureDecision(allowed: false, reasons: ["auto_capture_quality_reject"])
        let input = ManualCaptureInput(automaticDecision: automatic, quality: quality, admission: admission, cameraReady: true, sessionReady: true, sourceIntegrityReady: true, metadataReady: true, poseEvidenceReady: true)
        let allowed = ManualCaptureCoordinator.evaluate(input)
        XCTAssertTrue(allowed.allowed)
        XCTAssertTrue(allowed.warnings.contains("manual_capture_override"))
        XCTAssertFalse(ManualCaptureCoordinator.evaluate(ManualCaptureInput(automaticDecision: automatic, quality: quality, admission: admission, cameraReady: false, sessionReady: true, sourceIntegrityReady: true, metadataReady: true, poseEvidenceReady: true)).allowed)
        XCTAssertTrue(ManualCaptureCoordinator.evaluate(ManualCaptureInput(automaticDecision: automatic, quality: quality, admission: admission, cameraReady: true, sessionReady: true, sourceIntegrityReady: true, metadataReady: true, poseEvidenceReady: false)).blockingReasons.contains("pose_evidence_unavailable"))
    }

    @MainActor
    func testPL0110ManualCaptureUsesSharedTransactionPersistsOverrideAndRearmsAutoCooldown() async throws {
        struct Backend: StillPhotoBackend, Sendable {
            func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) { (Data([4, 5, 6]), CaptureDimensions(width: 2, height: 1)) }
        }
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "manual")
        let store = ScanSessionStore(layout: layout)
        try await store.create(NewScanDraft(sessionID: "manual", packageName: "Bottle", packageType: .bottle, captureMode: .guided))
        let vm = CaptureRuntimeViewModel(trackingService: SequenceTrackingService([TrackingQualityClassifier.classify(state: .normal)]), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        vm.configureM04QualityRuntime(preset: PackagingPresetCatalog.matteHDPE, layout: layout)
        await vm.bindStillCaptureBackend(Backend())
        let frame = QualityImageFrame(width: 10, height: 10, luminance: (0..<100).map { (($0 / 10 + $0 % 10) % 2 == 0) ? 0.2 : 0.8 }, objectMask: (0..<100).map { index in let x = index % 10; let y = index / 10; return (2...7).contains(x) && (2...7).contains(y) })
        let evaluation = await vm.analyzeM04Candidate(M04CandidateFrameInput(sessionID: "manual", captureID: "candidate", sequence: 0, monotonicTimestamp: 10, frame: frame))
        XCTAssertEqual(evaluation.quality.decision, .accept)
        let record = AcceptedCaptureRecord(captureID: "manual-capture", sequence: 0, sourceFilename: "manual-capture.heic", metadataFilename: "manual-capture.json")
        let state = try JSONEncoder().encode(PersistedSessionState(sessionID: "manual", nextSequence: 1, epoch: 0, acceptedIDs: ["manual-capture"]))
        let outcome = try await vm.captureAndPersistManual(captureID: "manual-capture", monotonicTimestamp: 10, cameraReady: true, sessionReady: true, sourceIntegrityReady: true, metadataReady: true, poseEvidenceReady: true, record: record, metadata: Data(), state: state, store: store, poses: PoseBuffer(), motion: MotionBuffer())
        XCTAssertTrue(outcome.decision.allowed)
        XCTAssertTrue(outcome.decision.warnings.contains("manual_capture_override"))
        XCTAssertNotNil(outcome.still)
        let persisted = try JSONDecoder().decode(AcceptedCaptureRecord.self, from: Data(contentsOf: layout.photoRecords.appendingPathComponent("manual-capture.json")))
        XCTAssertEqual(persisted.manualAudit?.warnings, outcome.decision.warnings)
        let logs = try await QualityCandidateLogStore(layout: layout).snapshot()
        XCTAssertTrue(logs.contains { $0.manualAudit?.warnings.contains("manual_capture_override") == true })
        let cooldown = await vm.requestAutoCapture(captureID: "auto-after-manual", monotonicTimestamp: 10.1)
        XCTAssertTrue(cooldown.decision.reasons.contains("auto_capture_cooldown") || cooldown.decision.reasons.contains("pose_ineligible"))
    }

    @MainActor
    func testPL0110ManualCaptureRejectedHardBlockIsLoggedWithoutWritingAcceptedRecord() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "manual-block")
        let store = ScanSessionStore(layout: layout)
        try await store.create(NewScanDraft(sessionID: "manual-block", packageName: "Bottle", packageType: .bottle, captureMode: .guided))
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        vm.configureM04QualityRuntime(preset: PackagingPresetCatalog.matteHDPE, layout: layout)
        let frame = QualityImageFrame(width: 10, height: 10, luminance: [Double](repeating: 0.5, count: 100), objectMask: (0..<100).map { $0 == 44 })
        _ = await vm.analyzeM04Candidate(M04CandidateFrameInput(sessionID: "manual-block", captureID: "candidate", sequence: 0, monotonicTimestamp: 10, frame: frame))
        let record = AcceptedCaptureRecord(captureID: "blocked", sequence: 0, sourceFilename: "blocked.heic", metadataFilename: "blocked.json")
        let state = try JSONEncoder().encode(PersistedSessionState(sessionID: "manual-block", nextSequence: 1, epoch: 0, acceptedIDs: ["blocked"]))
        let outcome = try await vm.captureAndPersistManual(captureID: "blocked", monotonicTimestamp: 10, cameraReady: false, sessionReady: true, sourceIntegrityReady: true, metadataReady: true, poseEvidenceReady: true, record: record, metadata: Data(), state: state, store: store, poses: PoseBuffer(), motion: MotionBuffer())
        XCTAssertFalse(outcome.decision.allowed)
        XCTAssertTrue(outcome.decision.blockingReasons.contains("camera_not_ready"))
        XCTAssertFalse(FileManager.default.fileExists(atPath: layout.photoRecords.appendingPathComponent("blocked.json").path))
        XCTAssertTrue((try await QualityCandidateLogStore(layout: layout).snapshot()).contains { $0.manualAudit?.blockingReasons.contains("camera_not_ready") == true })
    }

    func testPL0111MattePresetIsVersionedConfigDrivenAndPersisted() async throws {
        let preset = PackagingPresetCatalog.preset(for: .matteHDPE)
        XCTAssertEqual(preset.id, .matteHDPE)
        XCTAssertFalse(preset.version.isEmpty)
        XCTAssertFalse(preset.lightingGuidance.isEmpty)
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "preset-session")
        let store = M04SessionContextStore(layout: layout)
        try await store.persist(M04ScanContext(preset: preset))
        let loaded = try await store.load()
        XCTAssertEqual(loaded, M04ScanContext(preset: preset))
        XCTAssertEqual(PackagingPresetCatalog.preset(for: .matteHDPE).quality, preset.quality)
    }

    func testPL0112GlossyPresetTightensHighlightsAndCoverage() {
        let matte = PackagingPresetCatalog.preset(for: .matteHDPE)
        let glossy = PackagingPresetCatalog.preset(for: .glossyPET)
        XCTAssertEqual(glossy.id, .glossyPET)
        XCTAssertLessThan(glossy.quality.highlight.rejectFraction, matte.quality.highlight.rejectFraction)
        XCTAssertGreaterThan(glossy.coverage.orbit.azimuthBinCount, matte.coverage.orbit.azimuthBinCount)
        XCTAssertTrue(glossy.lightingGuidance.contains { $0.localizedCaseInsensitiveContains("reflection") })
    }

    @MainActor
    func testPL0112GlossyPresetDrivesLiveRuntimeRepeatedBlockGuidanceAndPersistence() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "glossy")
        let store = M04SessionContextStore(layout: layout)
        try await store.persist(M04ScanContext(preset: PackagingPresetCatalog.glossyPET))
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        vm.configureM04QualityRuntime(preset: PackagingPresetCatalog.glossyPET, layout: layout)
        XCTAssertEqual(vm.m04ActivePreset.id, .glossyPET)
        XCTAssertEqual(vm.m04ActivePreset.quality, PackagingPresetCatalog.glossyPET.quality)
        let blockedFrame = QualityImageFrame(width: 10, height: 1, luminance: [Double](repeating: 1, count: 10), objectMask: [Bool](repeating: true, count: 10))
        for sequence in 0..<3 {
            let evaluation = await vm.analyzeM04Candidate(M04CandidateFrameInput(sessionID: "glossy", captureID: "blocked-\(sequence)", sequence: sequence, monotonicTimestamp: Double(sequence), frame: blockedFrame))
            XCTAssertEqual(evaluation.quality.metrics.highlightClipping.band, .reject)
        }
        XCTAssertEqual(vm.m04QualityGuidanceState.consecutiveHighlightBlocks, 3)
        XCTAssertTrue(vm.m04ReflectionGuidance.first?.localizedCaseInsensitiveContains("reframe") == true)
        let recoveryFrame = QualityImageFrame(width: 10, height: 1, luminance: [Double](repeating: 0.5, count: 10), objectMask: [Bool](repeating: true, count: 10))
        _ = await vm.analyzeM04Candidate(M04CandidateFrameInput(sessionID: "glossy", captureID: "recovery", sequence: 3, monotonicTimestamp: 3, frame: recoveryFrame))
        XCTAssertTrue(vm.m04ReflectionGuidance.isEmpty)
        for _ in 0..<3 { await Task.yield() }
        let loaded = try await store.load()
        XCTAssertEqual(loaded.preset.id, .glossyPET)
        XCTAssertEqual(loaded.qualityGuidance?.consecutiveHighlightBlocks, 0)
        XCTAssertEqual(loaded.qualityGuidance?.presetID, .glossyPET)
    }

    func testPL0113TransparentModeRequiresAcknowledgementWithoutFalseSuitability() {
        let preset = PackagingPresetCatalog.preset(for: .transparent)
        XCTAssertTrue(preset.requiresPreparationAcknowledgement)
        let notAcknowledged = TransparentPreparationEvaluation(acknowledged: false, treatment: .none)
        XCTAssertFalse(notAcknowledged.mayStart)
        XCTAssertEqual(notAcknowledged.suitability, "warning_only_not_physically_verified")
        let acknowledged = TransparentPreparationEvaluation(acknowledged: true, treatment: .temporaryMatte)
        XCTAssertTrue(acknowledged.mayStart)
        XCTAssertTrue(acknowledged.warningCodes.contains("transparent_reconstruction_unproven"))
        XCTAssertEqual(M04ScanContext(preset: preset, preparationAcknowledged: true, treatmentMode: TransparentTreatmentMode.temporaryMatte.rawValue).treatmentMode, "temporaryMatte")
    }

    func testPL0113TransparentTreatmentOptionsAreExplicitAndNoneIsNotTreated() async throws {
        for treatment in TransparentTreatmentMode.allCases {
            let evaluation = TransparentPreparationEvaluation(acknowledged: true, treatment: treatment)
            XCTAssertEqual(evaluation.mayStart, treatment != .none)
        }
        let preset = PackagingPresetCatalog.preset(for: .transparent)
        let blocked = ScanSuitabilityPreflight.evaluate(ScanPreflightInput(preset: preset, cameraReady: true, sessionReady: true, storageAvailable: true, calibration: .ownerRequired, preparationAcknowledged: true, environmentGuidanceAcknowledged: true, transparentTreatment: .none))
        XCTAssertFalse(blocked.canStart)
        XCTAssertTrue(blocked.issues.contains { $0.code == "transparent_treatment_required" && $0.severity == .blocker })
        let selected = try NewScanDraftValidator.make(name: "Transparent", type: .bottle, mode: .guidedOrbit, sessionID: "transparent", presetID: .transparent, preflight: ScanSuitabilityPreflight.evaluate(ScanPreflightInput(preset: preset, cameraReady: true, sessionReady: true, storageAvailable: true, calibration: .ownerRequired, preparationAcknowledged: true, environmentGuidanceAcknowledged: true, transparentTreatment: .temporaryMatte)), treatmentMode: .temporaryMatte)
        let roundTrip = try JSONDecoder().decode(NewScanDraft.self, from: JSONEncoder().encode(selected))
        XCTAssertEqual(roundTrip.treatmentMode, .temporaryMatte)
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "transparent")
        try await M04SessionContextStore(layout: layout).persist(M04ScanContext(preset: preset, preparationAcknowledged: true, treatmentMode: selected.treatmentMode?.rawValue, preflight: selected.preflight))
        let loaded = try await M04SessionContextStore(layout: layout).load()
        XCTAssertEqual(loaded.treatmentMode, "temporaryMatte")
    }

    func testPL0114AsymmetricCoverageRequiresHandleAndAllMajorRegions() {
        let policy = AsymmetricCoveragePolicy()
        let incomplete = AsymmetricCoverageEvaluation(observedRegions: [.front: 4, .back: 4, .left: 2, .right: 2], policy: policy)
        XCTAssertFalse(incomplete.isComplete)
        XCTAssertEqual(incomplete.missingRegions, [.handle])
        let complete = AsymmetricCoverageEvaluation(observedRegions: [.front: 1, .back: 1, .left: 1, .right: 1, .handle: 1], policy: policy)
        XCTAssertTrue(complete.isComplete)
        XCTAssertEqual(PackagingPresetCatalog.preset(for: .asymmetricJerrycan).coverage.orbit.azimuthBinCount, 12)
    }

    @MainActor
    func testPL0114AsymmetricPresetDrivesActiveGuidanceAndPersistsObservedRegions() async throws {
        let preset = PackagingPresetCatalog.preset(for: .asymmetricJerrycan)
        XCTAssertEqual(preset.coverage.asymmetricCoverage?.requiredRegions, AsymmetricCoveragePolicy().requiredRegions)
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "jerrycan")
        try await M04SessionContextStore(layout: layout).persist(M04ScanContext(preset: preset))
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        vm.configureM04QualityRuntime(preset: preset, layout: layout)
        XCTAssertTrue(vm.m04AsymmetricCoverage?.missingRegions.contains(.handle) == true)
        for region in [AsymmetricCoverageRegion.front, .back, .left, .right] {
            for _ in 0..<12 { vm.observeAsymmetricRegion(region) }
        }
        XCTAssertFalse(vm.m04AsymmetricCoverage?.isComplete == true)
        XCTAssertTrue(vm.m04Completion.mandatoryMissingAreas.contains("asymmetric_handle"))
        vm.observeAsymmetricRegion(.handle)
        XCTAssertTrue(vm.m04AsymmetricCoverage?.isComplete == true)
        XCTAssertFalse(vm.m04Completion.mandatoryMissingAreas.contains("asymmetric_handle"))
        for _ in 0..<3 { await Task.yield() }
        let loaded = try await M04SessionContextStore(layout: layout).load()
        XCTAssertEqual(loaded.preset.coverage.asymmetricCoverage, preset.coverage.asymmetricCoverage)
        XCTAssertEqual(loaded.asymmetricCoverage?.observedRegions[.handle], 1)
        XCTAssertTrue(loaded.asymmetricCoverage?.isComplete == true)
    }

    func testPL0115ClosurePresetUsesMainLensInvariantAndTighterFraming() {
        let preset = PackagingPresetCatalog.preset(for: .closureCap)
        XCTAssertEqual(preset.supportedLensRule, "selected_rear_main_wide_only")
        XCTAssertEqual(preset.coverage.orbit.rings.first?.id, "closure")
        XCTAssertGreaterThan(preset.quality.framing.minimumObjectFraction, PackagingPresetCatalog.preset(for: .matteHDPE).quality.framing.minimumObjectFraction)
        XCTAssertTrue(preset.preparationGuidance.contains { $0.localizedCaseInsensitiveContains("working distance") })
    }

    @MainActor
    func testPL0115ClosurePresetDrivesRuntimeFramingDetailAndRingPersistence() async throws {
        let preset = PackagingPresetCatalog.preset(for: .closureCap)
        XCTAssertEqual(preset.coverage.ringRequirements.requirements, [RingCoverageRequirement(ringID: "closure", minimumSectorCount: 8)])
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        vm.configureM04QualityRuntime(preset: preset)
        XCTAssertEqual(vm.m04ActivePreset.id, .closureCap)
        XCTAssertEqual(vm.m04RingCoverage.statuses.map(\.ringID), ["closure"])
        let quality = QualityDecisionEngine.evaluate(CandidateQualityMetrics(sharpness: SharpnessMetric(availability: .available, normalizedLaplacianVariance: 0.03, sampleCount: 10, band: .accept, reasonCode: "sharpness_accept"), motionBlur: MotionBlurAssessment(risk: .none, availability: .available, rotationRateMagnitude: 0, reasons: []), highlightClipping: ClippingMetric(availability: .available, clippedFraction: 0, objectClippedFraction: 0, clippedPixelCount: 0, analyzedPixelCount: 10, band: .pass, reasons: []), shadowClipping: ClippingMetric(availability: .available, clippedFraction: 0, objectClippedFraction: 0, clippedPixelCount: 0, analyzedPixelCount: 10, band: .pass, reasons: []), framing: FramingMetric(availability: .available, objectFraction: 0.2, bounds: nil, margins: [:], band: .acceptable, reasons: []), background: BackgroundComplexityMetric(availability: .available, score: 0, luminanceVariance: 0, edgeDensity: 0, sampledPixelCount: 10, band: .clean, reasons: [])))
        let pose = acceptedPoseBinding(captureID: "closure", pose: PoseSample(timestamp: 1, transform: CoordinateTransform.translation(x: 0, y: 0.3, z: -1).values, tracking: .normal))
        let useful = DuplicateDecision(isDuplicate: false, reasonCode: "useful_candidate")
        let tightRejected = vm.evaluateDetailPass(passID: .closure, quality: quality, framing: FramingMetric(availability: .available, objectFraction: 0.13, bounds: nil, margins: [:], band: .acceptable, reasons: []), poseBinding: pose, duplicateDecision: useful)
        XCTAssertFalse(tightRejected.allowed)
        let accepted = vm.evaluateDetailPass(passID: .closure, quality: quality, framing: FramingMetric(availability: .available, objectFraction: 0.20, bounds: nil, margins: [:], band: .acceptable, reasons: []), poseBinding: pose, duplicateDecision: useful)
        XCTAssertTrue(accepted.allowed)
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "closure")
        try await M04SessionContextStore(layout: layout).persist(M04ScanContext(preset: preset))
        let loaded = try await M04SessionContextStore(layout: layout).load()
        XCTAssertEqual(loaded.preset.supportedLensRule, "selected_rear_main_wide_only")
        XCTAssertEqual(loaded.preset.coverage.ringRequirements, preset.coverage.ringRequirements)
    }

    func testPL0116TurntableCoverageNormalizesAnglesAndLabelsEvidenceSource() {
        var model = TurntableCoverageModel(policy: TurntablePolicy(expectedAngleCount: 4))
        let first = model.observe(captureID: "zero", angleDegrees: 0)
        let wrap = model.observe(captureID: "wrap", angleDegrees: 360)
        XCTAssertEqual(first.source, .turntableAngle)
        XCTAssertEqual(first.sectorIndex, 0)
        XCTAssertEqual(wrap.status, "repeated_angle")
        XCTAssertEqual(model.snapshot().repeatedCaptureIDs, ["wrap"])
        XCTAssertEqual(model.snapshot().missingSectorIndices, [1, 2, 3])
        XCTAssertFalse(model.snapshot().isComplete)
    }

    @MainActor
    func testPL0116TurntableRuntimeBlocksRepeatedAnglesPersistsEvidenceAndKeepsPoseSeparate() async throws {
        struct Backend: StillPhotoBackend, Sendable {
            func requestOriginalStill() async throws -> (bytes: Data, dimensions: CaptureDimensions) { (Data([7, 8]), CaptureDimensions(width: 2, height: 1)) }
        }
        let orbit = OrbitCoverageConfiguration(azimuthBinCount: 2)
        let preset = PackagingPreset(id: .turntable, version: "test", displayName: "Turntable", quality: QualityPolicyConfiguration(), coverage: CoveragePolicyConfiguration(orbit: orbit), lightingGuidance: [], preparationGuidance: [], requiresPreparationAcknowledgement: false)
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "turntable")
        let store = ScanSessionStore(layout: layout)
        try await store.create(NewScanDraft(sessionID: "turntable", packageName: "Bottle", packageType: .bottle, captureMode: .turntable))
        try await M04SessionContextStore(layout: layout).persist(M04ScanContext(preset: preset))
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        vm.configureM04QualityRuntime(preset: preset, layout: layout)
        await vm.bindStillCaptureBackend(Backend())
        XCTAssertTrue(vm.evaluateTurntableAngle(0).allowed)
        let first = vm.observeTurntableAngle(captureID: "angle-0", angleDegrees: 0)
        XCTAssertEqual(first?.source, .turntableAngle)
        XCTAssertFalse(vm.evaluateTurntableAngle(360).allowed)
        XCTAssertNil(vm.observeTurntableAngle(captureID: "repeat", angleDegrees: 360))
        let record = AcceptedCaptureRecord(captureID: "captured-angle", sequence: 0, sourceFilename: "captured-angle.heic", metadataFilename: "captured-angle.json")
        let state = try JSONEncoder().encode(PersistedSessionState(sessionID: "turntable", nextSequence: 1, epoch: 0, acceptedIDs: ["captured-angle"]))
        let outcome = try await vm.captureAndPersistTurntable(captureID: "captured-angle", angleDegrees: 180, record: record, metadata: Data(), state: state, store: store, poses: PoseBuffer(), motion: MotionBuffer())
        XCTAssertTrue(outcome.decision.allowed)
        XCTAssertEqual(outcome.observation?.source, .turntableAngle)
        let persisted = try JSONDecoder().decode(AcceptedCaptureRecord.self, from: Data(contentsOf: layout.photoRecords.appendingPathComponent("captured-angle.json")))
        XCTAssertEqual(persisted.turntableEvidence?.source, .turntableAngle)
        XCTAssertNil(persisted.poseBinding)
        for _ in 0..<3 { await Task.yield() }
        let loaded = try await M04SessionContextStore(layout: layout).load()
        XCTAssertEqual(loaded.turntableCoverage?.capturedSectorIndices, [0, 1])
        XCTAssertTrue(loaded.turntableCoverage?.isComplete == true)
    }

    func testPL0117CaptureProtocolIsPresetDrivenAndAcknowledgementScoped() {
        for id in PackagingPresetID.allCases {
            let model = CaptureProtocolViewModel(preset: PackagingPresetCatalog.preset(for: id))
            XCTAssertFalse(model.sections.isEmpty)
            XCTAssertFalse(model.sections.flatMap { $0.lines }.isEmpty)
        }
        let transparent = PackagingPresetCatalog.preset(for: .transparent)
        var required = CaptureProtocolViewModel(preset: transparent)
        XCTAssertTrue(required.acknowledgementRequired)
        XCTAssertFalse(required.canContinue)
        required.acknowledgePreparation()
        XCTAssertTrue(required.canContinue)
        XCTAssertTrue(CaptureProtocolViewModel(preset: PackagingPresetCatalog.preset(for: .matteHDPE)).canContinue)
    }

    func testPL0117ProtocolContinueFeedsNewScanDraftAndPersistedAcknowledgement() async throws {
        let preset = PackagingPresetCatalog.preset(for: .transparent)
        var protocolModel = CaptureProtocolViewModel(preset: preset)
        XCTAssertFalse(protocolModel.canContinue)
        protocolModel.acknowledgePreparation()
        XCTAssertTrue(protocolModel.canContinue)
        let preflight = ScanSuitabilityPreflight.evaluate(ScanPreflightInput(preset: preset, cameraReady: true, sessionReady: true, storageAvailable: true, calibration: .ownerRequired, preparationAcknowledged: true, environmentGuidanceAcknowledged: true, transparentTreatment: .texturedInsert))
        var workflow = NewScanWorkflowModel()
        var draft: NewScanDraft?
        XCTAssertTrue(NewScanActionCoordinator.start(workflow: &workflow, name: "Transparent", type: .bottle, mode: .guidedOrbit, notes: "", presetID: .transparent, preflight: preflight, treatmentMode: .texturedInsert) { draft = $0 })
        XCTAssertEqual(draft?.preflight?.preparationAcknowledged, true)
        XCTAssertEqual(draft?.treatmentMode, .texturedInsert)
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); defer { try? FileManager.default.removeItem(at: root) }
        let layout = SessionStorageLayout(root: root, sessionID: "protocol")
        try await M04SessionContextStore(layout: layout).persist(M04ScanContext(preset: preset, preparationAcknowledged: draft?.preflight?.preparationAcknowledged ?? false, treatmentMode: draft?.treatmentMode?.rawValue, preflight: draft?.preflight))
        let loaded = try await M04SessionContextStore(layout: layout).load()
        XCTAssertTrue(loaded.preparationAcknowledged)
    }

    func testPL0118PreflightBlocksMissingGuidanceAndPreservesCalibrationWarning() {
        let preset = PackagingPresetCatalog.preset(for: .transparent)
        let result = ScanSuitabilityPreflight.evaluate(ScanPreflightInput(preset: preset, cameraReady: true, sessionReady: true, storageAvailable: true, calibration: .ownerRequired, preparationAcknowledged: false, environmentGuidanceAcknowledged: false))
        XCTAssertFalse(result.canStart)
        XCTAssertEqual(result.calibration, .ownerRequired)
        XCTAssertTrue(result.issues.contains { $0.code == "preparation_acknowledgement_required" && $0.severity == .blocker })
        XCTAssertTrue(result.issues.contains { $0.code == "environment_guidance_required" && $0.severity == .blocker })
        XCTAssertTrue(result.issues.contains { $0.code == "calibration_owner_required" && $0.severity == .warning })
        XCTAssertTrue(result.issues.contains { $0.code == "transparent_reconstruction_unproven" && $0.severity == .warning })
    }

    func testPL0118PreflightAllowsAdmittedSessionWithExplicitOwnerRequiredCalibration() {
        let preset = PackagingPresetCatalog.preset(for: .matteHDPE)
        let result = ScanSuitabilityPreflight.evaluate(ScanPreflightInput(preset: preset, cameraReady: true, sessionReady: true, storageAvailable: true, calibration: .ownerRequired, preparationAcknowledged: true, environmentGuidanceAcknowledged: true))
        XCTAssertTrue(result.canStart)
        XCTAssertEqual(result.issues.map(\.code), ["calibration_owner_required", "environment_guidance_acknowledged"])
        let draft = try? NewScanDraftValidator.make(name: "Bottle", type: .bottle, mode: .guidedOrbit, sessionID: "preflight-session", presetID: .matteHDPE, preflight: result)
        XCTAssertEqual(draft?.presetID, .matteHDPE)
        XCTAssertEqual(draft?.preflight, result)
    }

    func testPL0118PreflightBlocksCameraAndStorageFailures() {
        let preset = PackagingPresetCatalog.preset(for: .matteHDPE)
        let result = ScanSuitabilityPreflight.evaluate(ScanPreflightInput(preset: preset, cameraReady: false, sessionReady: true, storageAvailable: false, calibration: .provisionalTestCalibrated, preparationAcknowledged: true, environmentGuidanceAcknowledged: true))
        XCTAssertFalse(result.canStart)
        XCTAssertTrue(result.issues.contains { $0.code == "camera_unavailable" && $0.severity == .blocker })
        XCTAssertTrue(result.issues.contains { $0.code == "storage_unavailable" && $0.severity == .blocker })
        XCTAssertTrue(result.issues.contains { $0.code == "calibration_owner_required" && $0.severity == .warning })
    }

    func testPL0118PreflightIsTableDrivenAcrossPresetsAndHealthConditions() {
        for id in PackagingPresetID.allCases {
            let result = ScanSuitabilityPreflight.evaluate(ScanPreflightInput(preset: PackagingPresetCatalog.preset(for: id), cameraReady: true, sessionReady: true, storageAvailable: true, calibration: .ownerVerified, preparationAcknowledged: true, environmentGuidanceAcknowledged: true))
            XCTAssertTrue(result.canStart, id.rawValue)
            XCTAssertTrue(result.issues.contains { $0.severity == .information && $0.code == "environment_guidance_acknowledged" })
            if id == .transparent { XCTAssertTrue(result.issues.contains { $0.code == "transparent_reconstruction_unproven" && $0.severity == .warning }) }
        }

        var admission = CaptureAdmissionController()
        admission.update(.warning(HealthDecision(severity: .warning, messages: ["battery_low"])))
        let warning = ScanSuitabilityPreflight.evaluate(ScanPreflightInput(preset: PackagingPresetCatalog.matteHDPE, admission: admission, cameraReady: true, sessionReady: true, storageAvailable: true, calibration: .ownerVerified, preparationAcknowledged: true, environmentGuidanceAcknowledged: true))
        XCTAssertTrue(warning.canStart)
        XCTAssertTrue(warning.issues.contains { $0.code == "health_warning" && $0.severity == .warning })

        admission.update(.hardStop(HealthDecision(severity: .hardStop, messages: ["thermal_critical", "storage_critical"])))
        let hardStop = ScanSuitabilityPreflight.evaluate(ScanPreflightInput(preset: PackagingPresetCatalog.matteHDPE, admission: admission, cameraReady: true, sessionReady: true, storageAvailable: true, calibration: .ownerVerified, preparationAcknowledged: true, environmentGuidanceAcknowledged: true))
        XCTAssertFalse(hardStop.canStart)
        XCTAssertTrue(hardStop.issues.contains { $0.code == "health_hard_stop" && $0.severity == .blocker })
    }

    @MainActor
    func testPL0118RuntimeReadinessTransitionsFeedExactPreflightEligibility() async {
        let vm = CaptureRuntimeViewModel(trackingService: FoundationARTrackingService(isAvailable: false), motionService: FoundationMotionService(), healthMonitor: DeviceHealthMonitor(provider: UnavailableDeviceHealthProvider()))
        XCTAssertFalse(vm.newScanReadiness.sessionReady)
        await vm.start()
        XCTAssertTrue(vm.newScanReadiness.sessionReady)
        let unavailable = ScanSuitabilityPreflight.evaluate(ScanPreflightInput(preset: PackagingPresetCatalog.matteHDPE, admission: vm.admission, cameraReady: vm.newScanReadiness.cameraReady, sessionReady: vm.newScanReadiness.sessionReady, storageAvailable: vm.newScanReadiness.storageAvailable, calibration: vm.newScanReadiness.calibration, preparationAcknowledged: true, environmentGuidanceAcknowledged: true))
        XCTAssertFalse(unavailable.canStart)
        XCTAssertTrue(unavailable.issues.contains { $0.code == "camera_unavailable" && $0.severity == .blocker })
        let admitted = ScanSuitabilityPreflight.evaluate(ScanPreflightInput(preset: PackagingPresetCatalog.matteHDPE, cameraReady: true, sessionReady: true, storageAvailable: true, calibration: .ownerRequired, preparationAcknowledged: true, environmentGuidanceAcknowledged: true))
        XCTAssertTrue(admitted.canStart)
        await vm.stop()
        XCTAssertFalse(vm.newScanReadiness.sessionReady)
    }

}

// Static verification on Windows covers target wiring, source membership, and privacy settings.
// xcodebuild execution on simulator/macOS CI is intentionally deferred to the authorized M16 runner.
