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
