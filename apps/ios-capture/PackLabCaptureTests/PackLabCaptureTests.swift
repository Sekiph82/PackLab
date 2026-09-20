import XCTest
@testable import PackLabCapture

final class PackLabCaptureTests: XCTestCase {
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
}

// Static verification on Windows covers target wiring, source membership, and privacy settings.
// xcodebuild execution on simulator/macOS CI is intentionally deferred to the authorized M16 runner.
