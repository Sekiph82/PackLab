import Foundation

public struct CaptureQualitySample: Sendable, Equatable {
    public let motionMagnitude: Double
    public let trackingAvailable: Bool

    public init(motionMagnitude: Double, trackingAvailable: Bool) {
        self.motionMagnitude = motionMagnitude
        self.trackingAvailable = trackingAvailable
    }
}

public struct CaptureQualityResult: Sendable, Equatable {
    public let isAcceptable: Bool
    public let reason: String

    public init(isAcceptable: Bool, reason: String) {
        self.isAcceptable = isAcceptable
        self.reason = reason
    }
}

public protocol CaptureQualityService: Sendable {
    func evaluate(_ sample: CaptureQualitySample) async -> CaptureQualityResult
}

/// Small deterministic policy seam; capture policy belongs in later milestones.
public struct FoundationCaptureQualityService: CaptureQualityService {
    public let maximumMotionMagnitude: Double

    public init(maximumMotionMagnitude: Double = 1.0) {
        self.maximumMotionMagnitude = maximumMotionMagnitude
    }

    public func evaluate(_ sample: CaptureQualitySample) async -> CaptureQualityResult {
        guard sample.trackingAvailable else {
            return CaptureQualityResult(isAcceptable: false, reason: "tracking-unavailable")
        }
        guard sample.motionMagnitude <= maximumMotionMagnitude else {
            return CaptureQualityResult(isAcceptable: false, reason: "motion-too-high")
        }
        return CaptureQualityResult(isAcceptable: true, reason: "acceptable")
    }
}
