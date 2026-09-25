import Foundation
#if canImport(SwiftUI)
import SwiftUI
#endif

/// The quality engine consumes normalized luminance samples produced by the
/// camera adapter.  Keeping this value type independent of UIKit/Core Image
/// makes the production seam deterministic and keeps the algorithm testable on
/// the Windows builder.  Luminance values are expected in the closed interval
/// [0, 1]; invalid samples make the frame unavailable rather than being
/// silently clamped into evidence.
public struct QualityImageFrame: Sendable, Equatable {
    public let width: Int
    public let height: Int
    public let luminance: [Double]
    public let objectMask: [Bool]?

    public init(width: Int, height: Int, luminance: [Double], objectMask: [Bool]? = nil) {
        self.width = width
        self.height = height
        self.luminance = luminance
        self.objectMask = objectMask
    }

    public var isAvailable: Bool {
        width > 0 && height > 0 && luminance.count == width * height && luminance.allSatisfy { $0.isFinite && (0...1).contains($0) } && (objectMask == nil || objectMask?.count == luminance.count)
    }

    public var objectMaskIsUsable: Bool {
        isAvailable && objectMask?.contains(true) == true
    }

    public static let unavailable = QualityImageFrame(width: 0, height: 0, luminance: [])
}

public enum QualityMetricAvailability: String, Codable, Sendable, Equatable {
    case available
    case unavailable
    case stale
    case invalid
}

public enum SharpnessBand: String, Codable, Sendable, Equatable {
    case accept
    case warn
    case reject
    case unavailable
}

/// Sharpness units are normalized Laplacian variance over a fixed 48x48 grid.
/// The fixed analysis grid prevents a larger still from receiving a larger
/// score solely because it contains more pixels.  Values are provisional until
/// owner/device-labelled captures are supplied through the calibration harness.
public struct SharpnessThresholds: Codable, Sendable, Equatable {
    public let acceptMinimum: Double
    public let warnMinimum: Double
    public init(acceptMinimum: Double = 0.018, warnMinimum: Double = 0.006) {
        self.acceptMinimum = max(0, acceptMinimum)
        self.warnMinimum = max(0, min(warnMinimum, self.acceptMinimum))
    }
    public static let provisional = SharpnessThresholds()
}

public struct SharpnessMetric: Codable, Sendable, Equatable {
    public let availability: QualityMetricAvailability
    public let normalizedLaplacianVariance: Double?
    public let sampleCount: Int
    public let band: SharpnessBand
    public let reasonCode: String
    public init(availability: QualityMetricAvailability, normalizedLaplacianVariance: Double?, sampleCount: Int, band: SharpnessBand, reasonCode: String) {
        self.availability = availability
        self.normalizedLaplacianVariance = normalizedLaplacianVariance
        self.sampleCount = sampleCount
        self.band = band
        self.reasonCode = reasonCode
    }
}

public enum SharpnessAnalyzer {
    public static let analysisSide = 48

    public static func analyze(_ frame: QualityImageFrame, thresholds: SharpnessThresholds = .provisional) -> SharpnessMetric {
        guard frame.isAvailable else {
            return SharpnessMetric(availability: .unavailable, normalizedLaplacianVariance: nil, sampleCount: 0, band: .unavailable, reasonCode: "sharpness_unavailable")
        }
        let grid = normalizedGrid(frame, side: analysisSide)
        guard grid.count >= 9 else {
            return SharpnessMetric(availability: .invalid, normalizedLaplacianVariance: nil, sampleCount: grid.count, band: .unavailable, reasonCode: "sharpness_grid_invalid")
        }
        var responses: [Double] = []
        responses.reserveCapacity((analysisSide - 2) * (analysisSide - 2))
        for y in 1..<(analysisSide - 1) {
            for x in 1..<(analysisSide - 1) {
                let center = grid[y * analysisSide + x]
                let neighbours = grid[(y - 1) * analysisSide + x] + grid[(y + 1) * analysisSide + x] + grid[y * analysisSide + x - 1] + grid[y * analysisSide + x + 1]
                responses.append((4 * center - neighbours) / 4)
            }
        }
        let mean = responses.reduce(0, +) / Double(responses.count)
        let variance = responses.reduce(0) { $0 + ($1 - mean) * ($1 - mean) } / Double(responses.count)
        return analyze(normalizedLaplacianVariance: variance, sampleCount: responses.count, thresholds: thresholds)
    }

    /// Classifies a measured metric through the same production threshold
    /// seam used by frame analysis.  The injectable metric form keeps exact
    /// threshold behavior testable without pretending that synthetic pixels
    /// are an owner/device calibration capture.
    public static func analyze(normalizedLaplacianVariance: Double, sampleCount: Int, thresholds: SharpnessThresholds = .provisional) -> SharpnessMetric {
        guard normalizedLaplacianVariance.isFinite, sampleCount > 0 else {
            return SharpnessMetric(availability: .invalid, normalizedLaplacianVariance: nil, sampleCount: max(0, sampleCount), band: .unavailable, reasonCode: "sharpness_metric_invalid")
        }
        let band: SharpnessBand = normalizedLaplacianVariance >= thresholds.acceptMinimum ? .accept : (normalizedLaplacianVariance >= thresholds.warnMinimum ? .warn : .reject)
        return SharpnessMetric(availability: .available, normalizedLaplacianVariance: normalizedLaplacianVariance, sampleCount: sampleCount, band: band, reasonCode: "sharpness_\(band.rawValue)")
    }

    private static func normalizedGrid(_ frame: QualityImageFrame, side: Int) -> [Double] {
        (0..<side).flatMap { y in
            (0..<side).map { x in
                let sourceX = min(frame.width - 1, Int((Double(x) + 0.5) * Double(frame.width) / Double(side)))
                let sourceY = min(frame.height - 1, Int((Double(y) + 0.5) * Double(frame.height) / Double(side)))
                return frame.luminance[sourceY * frame.width + sourceX]
            }
        }
    }
}

public enum SharpnessCalibrationLabel: String, Codable, Sendable, Equatable { case sharp, usable, blurred }

public struct SharpnessCalibrationSample: Codable, Sendable, Equatable {
    public let label: SharpnessCalibrationLabel
    public let metric: Double
    public init(label: SharpnessCalibrationLabel, metric: Double) { self.label = label; self.metric = metric }
}

public struct SharpnessCalibrationResult: Codable, Sendable, Equatable {
    public let thresholds: SharpnessThresholds
    public let sampleCount: Int
    public let calibrationStatus: String
    public init(thresholds: SharpnessThresholds, sampleCount: Int, calibrationStatus: String) { self.thresholds = thresholds; self.sampleCount = sampleCount; self.calibrationStatus = calibrationStatus }
}

/// Fixture/label harness. It suggests thresholds from labelled samples but
/// never changes the metric contract and explicitly records its provisional
/// status when samples are synthetic or not owner/device verified.
public enum SharpnessCalibrationHarness {
    public static func suggestThresholds(from samples: [SharpnessCalibrationSample], ownerDeviceVerified: Bool = false) -> SharpnessCalibrationResult {
        let finite = samples.filter { $0.metric.isFinite }
        let sharp = finite.filter { $0.label == .sharp }.map(\.metric).min()
        let usable = finite.filter { $0.label == .usable }.map(\.metric).min()
        let blurred = finite.filter { $0.label == .blurred }.map(\.metric).max()
        let accept = max(0, sharp ?? usable ?? SharpnessThresholds.provisional.acceptMinimum)
        let warn = max(0, min(accept, blurred ?? usable ?? SharpnessThresholds.provisional.warnMinimum))
        return SharpnessCalibrationResult(thresholds: SharpnessThresholds(acceptMinimum: accept, warnMinimum: warn), sampleCount: finite.count, calibrationStatus: ownerDeviceVerified ? "owner_device_labelled" : "provisional_test_calibrated")
    }
}

public enum MotionBlurRisk: String, Codable, Sendable, Equatable {
    case none
    case warning
    case highRisk = "high_risk"
    case unavailable
}

public struct MotionBlurThresholds: Codable, Sendable, Equatable {
    public let warningRotationRate: Double
    public let highRotationRate: Double
    public init(warningRotationRate: Double = 0.35, highRotationRate: Double = 1.2) {
        self.warningRotationRate = max(0, warningRotationRate)
        self.highRotationRate = max(self.warningRotationRate, highRotationRate)
    }
    public static let provisional = MotionBlurThresholds()
}

public struct MotionBlurAssessment: Codable, Sendable, Equatable {
    public let risk: MotionBlurRisk
    public let availability: QualityMetricAvailability
    public let rotationRateMagnitude: Double?
    public let reasons: [String]
    public init(risk: MotionBlurRisk, availability: QualityMetricAvailability, rotationRateMagnitude: Double?, reasons: [String]) {
        self.risk = risk
        self.availability = availability
        self.rotationRateMagnitude = rotationRateMagnitude
        self.reasons = reasons
    }
}

/// Motion blur is an explainable warning layer, not a second capture gate.
/// The input binding is the M03 timestamp-domain binding; no wall-clock value
/// is compared with a CoreMotion timestamp here.
public enum MotionBlurAnalyzer {
    public static func analyze(sharpness: SharpnessMetric, motion: MotionCaptureBinding?, thresholds: MotionBlurThresholds = .provisional) -> MotionBlurAssessment {
        let imageBlurred = sharpness.band == .reject
        guard let motion else {
            return MotionBlurAssessment(risk: imageBlurred ? .warning : .unavailable, availability: .unavailable, rotationRateMagnitude: nil, reasons: imageBlurred ? ["image_blur_motion_unavailable"] : ["motion_unavailable"])
        }
        guard motion.status == "available", let sample = motion.sample, sample.isValid else {
            return MotionBlurAssessment(risk: imageBlurred ? .warning : .unavailable, availability: motion.status == "stale" ? .stale : .unavailable, rotationRateMagnitude: nil, reasons: imageBlurred ? ["image_blur_motion_stale"] : ["motion_\(motion.status)"])
        }
        let magnitude = sqrt(sample.rotationRate.reduce(0) { $0 + $1 * $1 })
        if imageBlurred && magnitude >= thresholds.highRotationRate {
            return MotionBlurAssessment(risk: .highRisk, availability: .available, rotationRateMagnitude: magnitude, reasons: ["combined_blur_and_high_motion"])
        }
        if imageBlurred {
            return MotionBlurAssessment(risk: .warning, availability: .available, rotationRateMagnitude: magnitude, reasons: [magnitude <= thresholds.warningRotationRate ? "image_blur_low_motion" : "image_blur_with_motion"])
        }
        if magnitude >= thresholds.highRotationRate {
            return MotionBlurAssessment(risk: .warning, availability: .available, rotationRateMagnitude: magnitude, reasons: ["high_motion_sharp_frame"])
        }
        return MotionBlurAssessment(risk: .none, availability: .available, rotationRateMagnitude: magnitude, reasons: [])
    }
}

public enum ClippingBand: String, Codable, Sendable, Equatable { case pass, warn, reject, unavailable }

public struct ClippingThresholds: Codable, Sendable, Equatable {
    public let luminanceCutoff: Double
    public let toleratedFraction: Double
    public let warningFraction: Double
    public let rejectFraction: Double
    public init(luminanceCutoff: Double, toleratedFraction: Double = 0.01, warningFraction: Double = 0.05, rejectFraction: Double = 0.20) {
        self.luminanceCutoff = min(1, max(0, luminanceCutoff))
        self.toleratedFraction = min(1, max(0, toleratedFraction))
        self.warningFraction = min(1, max(self.toleratedFraction, warningFraction))
        self.rejectFraction = min(1, max(self.warningFraction, rejectFraction))
    }
    public static let highlightProvisional = ClippingThresholds(luminanceCutoff: 0.98, toleratedFraction: 0.01, warningFraction: 0.05, rejectFraction: 0.20)
    public static let shadowProvisional = ClippingThresholds(luminanceCutoff: 0.05, toleratedFraction: 0.01, warningFraction: 0.08, rejectFraction: 0.25)
}

public struct ClippingMetric: Codable, Sendable, Equatable {
    public let availability: QualityMetricAvailability
    public let clippedFraction: Double?
    public let objectClippedFraction: Double?
    public let clippedPixelCount: Int
    public let analyzedPixelCount: Int
    public let band: ClippingBand
    public let reasons: [String]
    public init(availability: QualityMetricAvailability, clippedFraction: Double?, objectClippedFraction: Double?, clippedPixelCount: Int, analyzedPixelCount: Int, band: ClippingBand, reasons: [String]) {
        self.availability = availability
        self.clippedFraction = clippedFraction
        self.objectClippedFraction = objectClippedFraction
        self.clippedPixelCount = clippedPixelCount
        self.analyzedPixelCount = analyzedPixelCount
        self.band = band
        self.reasons = reasons
    }
}

public enum LuminanceClippingAnalyzer {
    /// Highlight and shadow measurements share one explicit fraction policy:
    /// tolerated fractions pass within tolerance, the configured warning
    /// fraction starts a warning, and the reject fraction is hard failure.
    public static func highlight(_ frame: QualityImageFrame, thresholds: ClippingThresholds = .highlightProvisional) -> ClippingMetric {
        analyze(frame, thresholds: thresholds, predicate: { $0 >= thresholds.luminanceCutoff }, reasonPrefix: "highlight")
    }

    public static func shadow(_ frame: QualityImageFrame, thresholds: ClippingThresholds = .shadowProvisional) -> ClippingMetric {
        analyze(frame, thresholds: thresholds, predicate: { $0 <= thresholds.luminanceCutoff }, reasonPrefix: "shadow")
    }

    private static func analyze(_ frame: QualityImageFrame, thresholds: ClippingThresholds, predicate: (Double) -> Bool, reasonPrefix: String) -> ClippingMetric {
        guard frame.isAvailable, !frame.luminance.isEmpty else {
            return ClippingMetric(availability: .unavailable, clippedFraction: nil, objectClippedFraction: nil, clippedPixelCount: 0, analyzedPixelCount: 0, band: .unavailable, reasons: ["\(reasonPrefix)_clipping_unavailable"])
        }
        let clipped = frame.luminance.map(predicate)
        let allCount = clipped.count
        let allClipped = clipped.filter { $0 }.count
        let overall = Double(allClipped) / Double(allCount)
        var selectedFraction: Double = overall
        var objectFraction: Double?
        var reasons: [String] = []
        if let mask = frame.objectMask, mask.count == clipped.count, mask.contains(true) {
            let objectIndices = clipped.indices.filter { mask[$0] }
            let objectClipped = objectIndices.filter { clipped[$0] }.count
            objectFraction = Double(objectClipped) / Double(objectIndices.count)
            selectedFraction = objectFraction ?? overall
        } else {
            reasons.append("\(reasonPrefix)_object_region_unavailable")
        }
        let band: ClippingBand
        if selectedFraction >= thresholds.rejectFraction {
            band = .reject
        } else if selectedFraction >= thresholds.warningFraction {
            band = .warn
        } else {
            band = .pass
            reasons.append(selectedFraction > thresholds.toleratedFraction ? "\(reasonPrefix)_clipping_within_warning_threshold" : "\(reasonPrefix)_clipping_within_tolerance")
        }
        reasons.append("\(reasonPrefix)_clipping_\(band.rawValue)")
        return ClippingMetric(availability: .available, clippedFraction: overall, objectClippedFraction: objectFraction, clippedPixelCount: allClipped, analyzedPixelCount: allCount, band: band, reasons: reasons)
    }
}

public struct NormalizedBounds: Codable, Sendable, Equatable {
    public let minX: Double
    public let minY: Double
    public let maxX: Double
    public let maxY: Double
    public init(minX: Double, minY: Double, maxX: Double, maxY: Double) { self.minX = minX; self.minY = minY; self.maxX = maxX; self.maxY = maxY }
    public var width: Double { max(0, maxX - minX) }
    public var height: Double { max(0, maxY - minY) }
    public var area: Double { width * height }
}

public enum FramingBand: String, Codable, Sendable, Equatable { case tooSmall = "too_small", acceptable, cropped, unavailable }

public struct FramingThresholds: Codable, Sendable, Equatable {
    public let minimumObjectFraction: Double
    public let maximumObjectFraction: Double
    public let minimumMargin: Double
    public init(minimumObjectFraction: Double = 0.08, maximumObjectFraction: Double = 0.82, minimumMargin: Double = 0.03) {
        self.minimumObjectFraction = max(0, min(1, minimumObjectFraction))
        self.maximumObjectFraction = max(self.minimumObjectFraction, min(1, maximumObjectFraction))
        self.minimumMargin = max(0, min(0.5, minimumMargin))
    }
    public static let provisional = FramingThresholds()
}

public struct FramingMetric: Codable, Sendable, Equatable {
    public let availability: QualityMetricAvailability
    public let objectFraction: Double?
    public let bounds: NormalizedBounds?
    public let margins: [String: Double]
    public let band: FramingBand
    public let reasons: [String]
    public init(availability: QualityMetricAvailability, objectFraction: Double?, bounds: NormalizedBounds?, margins: [String: Double], band: FramingBand, reasons: [String]) { self.availability = availability; self.objectFraction = objectFraction; self.bounds = bounds; self.margins = margins; self.band = band; self.reasons = reasons }
}

public enum FramingAnalyzer {
    public static func analyze(_ frame: QualityImageFrame, thresholds: FramingThresholds = .provisional) -> FramingMetric {
        guard frame.isAvailable, let mask = frame.objectMask, mask.count == frame.luminance.count, mask.contains(true) else {
            return FramingMetric(availability: .unavailable, objectFraction: nil, bounds: nil, margins: [:], band: .unavailable, reasons: ["framing_object_region_unavailable"])
        }
        let objectIndices = mask.indices.filter { mask[$0] }
        let minX = objectIndices.map { $0 % frame.width }.min() ?? 0
        let maxX = objectIndices.map { $0 % frame.width }.max() ?? 0
        let minY = objectIndices.map { $0 / frame.width }.min() ?? 0
        let maxY = objectIndices.map { $0 / frame.width }.max() ?? 0
        let bounds = NormalizedBounds(minX: Double(minX) / Double(frame.width), minY: Double(minY) / Double(frame.height), maxX: Double(maxX + 1) / Double(frame.width), maxY: Double(maxY + 1) / Double(frame.height))
        let objectFraction = Double(objectIndices.count) / Double(mask.count)
        let margins = ["left": bounds.minX, "top": bounds.minY, "right": 1 - bounds.maxX, "bottom": 1 - bounds.maxY]
        let touchesEdge = margins.values.contains { $0 <= thresholds.minimumMargin }
        let band: FramingBand = objectFraction < thresholds.minimumObjectFraction ? .tooSmall : (objectFraction > thresholds.maximumObjectFraction || touchesEdge ? .cropped : .acceptable)
        var reasons = ["framing_\(band.rawValue)"]
        if touchesEdge { reasons.append("framing_edge_margin") }
        return FramingMetric(availability: .available, objectFraction: objectFraction, bounds: bounds, margins: margins, band: band, reasons: reasons)
    }
}

public enum BackgroundComplexityBand: String, Codable, Sendable, Equatable { case clean, warning, unavailable }

public struct BackgroundComplexityThresholds: Codable, Sendable, Equatable {
    public let warningScore: Double
    public init(warningScore: Double = 0.18) { self.warningScore = max(0, min(1, warningScore)) }
    public static let provisional = BackgroundComplexityThresholds()
}

public struct BackgroundComplexityMetric: Codable, Sendable, Equatable {
    public let availability: QualityMetricAvailability
    public let score: Double?
    public let luminanceVariance: Double?
    public let edgeDensity: Double?
    public let sampledPixelCount: Int
    public let band: BackgroundComplexityBand
    public let reasons: [String]
    public init(availability: QualityMetricAvailability, score: Double?, luminanceVariance: Double?, edgeDensity: Double?, sampledPixelCount: Int, band: BackgroundComplexityBand, reasons: [String]) { self.availability = availability; self.score = score; self.luminanceVariance = luminanceVariance; self.edgeDensity = edgeDensity; self.sampledPixelCount = sampledPixelCount; self.band = band; self.reasons = reasons }
}

/// Bounded background analysis. The object mask is an input contract, not an
/// inferred second segmentation pipeline; object pixels are excluded and only
/// a 32x32 deterministic sample grid is evaluated.
public enum BackgroundComplexityAnalyzer {
    public static let maximumSamples = 1024
    public static func analyze(_ frame: QualityImageFrame, thresholds: BackgroundComplexityThresholds = .provisional) -> BackgroundComplexityMetric {
        guard frame.isAvailable, let mask = frame.objectMask, mask.count == frame.luminance.count else {
            return BackgroundComplexityMetric(availability: .unavailable, score: nil, luminanceVariance: nil, edgeDensity: nil, sampledPixelCount: 0, band: .unavailable, reasons: ["background_object_region_unavailable"])
        }
        let side = min(32, max(1, min(frame.width, frame.height)))
        var samples: [(x: Int, y: Int, value: Double)] = []
        for y in 0..<side {
            for x in 0..<side {
                let sourceX = min(frame.width - 1, Int((Double(x) + 0.5) * Double(frame.width) / Double(side)))
                let sourceY = min(frame.height - 1, Int((Double(y) + 0.5) * Double(frame.height) / Double(side)))
                let index = sourceY * frame.width + sourceX
                if !mask[index] { samples.append((x, y, frame.luminance[index])) }
            }
        }
        guard !samples.isEmpty else {
            return BackgroundComplexityMetric(availability: .unavailable, score: nil, luminanceVariance: nil, edgeDensity: nil, sampledPixelCount: 0, band: .unavailable, reasons: ["background_pixels_unavailable"])
        }
        let mean = samples.reduce(0) { $0 + $1.value } / Double(samples.count)
        let variance = samples.reduce(0) { $0 + ($1.value - mean) * ($1.value - mean) } / Double(samples.count)
        let sampled = Dictionary(uniqueKeysWithValues: samples.map { ("\($0.x):\($0.y)", $0.value) })
        var edgeCount = 0
        var edgePairs = 0
        for sample in samples {
            for neighbour in [(sample.x + 1, sample.y), (sample.x, sample.y + 1)] {
                if let value = sampled["\(neighbour.0):\(neighbour.1)"] {
                    edgePairs += 1
                    if abs(sample.value - value) >= 0.12 { edgeCount += 1 }
                }
            }
        }
        let edgeDensity = edgePairs == 0 ? 0 : Double(edgeCount) / Double(edgePairs)
        let score = min(1, variance * 4 + edgeDensity)
        let band: BackgroundComplexityBand = score >= thresholds.warningScore ? .warning : .clean
        return BackgroundComplexityMetric(availability: .available, score: score, luminanceVariance: variance, edgeDensity: edgeDensity, sampledPixelCount: min(samples.count, maximumSamples), band: band, reasons: ["background_complexity_\(band.rawValue)"])
    }
}

public enum CandidateQualityDecision: String, Codable, Sendable, Equatable { case accept, reject }

public struct CandidateQualityMetrics: Codable, Sendable, Equatable {
    public let sharpness: SharpnessMetric
    public let motionBlur: MotionBlurAssessment
    public let highlightClipping: ClippingMetric
    public let shadowClipping: ClippingMetric
    public let framing: FramingMetric
    public let background: BackgroundComplexityMetric
    public init(sharpness: SharpnessMetric, motionBlur: MotionBlurAssessment, highlightClipping: ClippingMetric, shadowClipping: ClippingMetric, framing: FramingMetric, background: BackgroundComplexityMetric) { self.sharpness = sharpness; self.motionBlur = motionBlur; self.highlightClipping = highlightClipping; self.shadowClipping = shadowClipping; self.framing = framing; self.background = background }
}

public struct QualityDecisionPolicy: Codable, Sendable, Equatable {
    public let rejectUnavailableSharpness: Bool
    public let rejectUnavailableFraming: Bool
    public let rejectUnavailableClipping: Bool
    public init(rejectUnavailableSharpness: Bool = true, rejectUnavailableFraming: Bool = true, rejectUnavailableClipping: Bool = false) { self.rejectUnavailableSharpness = rejectUnavailableSharpness; self.rejectUnavailableFraming = rejectUnavailableFraming; self.rejectUnavailableClipping = rejectUnavailableClipping }
    public static let provisional = QualityDecisionPolicy()
}

public struct QualityDecision: Codable, Sendable, Equatable {
    public let decision: CandidateQualityDecision
    public let reasons: [String]
    public let warnings: [String]
    public let metrics: CandidateQualityMetrics
    public init(decision: CandidateQualityDecision, reasons: [String], warnings: [String], metrics: CandidateQualityMetrics) { self.decision = decision; self.reasons = reasons; self.warnings = warnings; self.metrics = metrics }
    public var isAcceptable: Bool { decision == .accept }
}

/// Authoritative M04 candidate decision. Reason ordering is fixed so logs and
/// later Windows analysis are stable across platforms and repeated runs.
public enum QualityDecisionEngine {
    public static func evaluate(_ metrics: CandidateQualityMetrics, policy: QualityDecisionPolicy = .provisional) -> QualityDecision {
        var hard: [String] = []
        var warnings: [String] = []
        if metrics.sharpness.band == .reject || (metrics.sharpness.band == .unavailable && policy.rejectUnavailableSharpness) { hard.append(metrics.sharpness.band == .unavailable ? "sharpness_unavailable" : metrics.sharpness.reasonCode) }
        else if metrics.sharpness.band == .warn { warnings.append(metrics.sharpness.reasonCode) }
        if metrics.motionBlur.risk == .highRisk { hard.append(contentsOf: metrics.motionBlur.reasons) }
        else if metrics.motionBlur.risk == .warning || metrics.motionBlur.risk == .unavailable { warnings.append(contentsOf: metrics.motionBlur.reasons) }
        if metrics.highlightClipping.band == .reject { hard.append(contentsOf: metrics.highlightClipping.reasons.filter { $0.hasSuffix("_reject") }) }
        else if metrics.highlightClipping.band == .unavailable {
            if policy.rejectUnavailableClipping { hard.append(contentsOf: metrics.highlightClipping.reasons) } else { warnings.append(contentsOf: metrics.highlightClipping.reasons) }
        }
        else if metrics.highlightClipping.band == .warn { warnings.append(contentsOf: metrics.highlightClipping.reasons) }
        if metrics.shadowClipping.band == .reject { hard.append(contentsOf: metrics.shadowClipping.reasons.filter { $0.hasSuffix("_reject") }) }
        else if metrics.shadowClipping.band == .unavailable {
            if policy.rejectUnavailableClipping { hard.append(contentsOf: metrics.shadowClipping.reasons) } else { warnings.append(contentsOf: metrics.shadowClipping.reasons) }
        }
        else if metrics.shadowClipping.band == .warn { warnings.append(contentsOf: metrics.shadowClipping.reasons) }
        if metrics.framing.band == .tooSmall || metrics.framing.band == .cropped || (metrics.framing.band == .unavailable && policy.rejectUnavailableFraming) { hard.append(contentsOf: metrics.framing.reasons) }
        if metrics.background.band == .warning || metrics.background.band == .unavailable { warnings.append(contentsOf: metrics.background.reasons) }
        func unique(_ values: [String]) -> [String] { var seen = Set<String>(); return values.filter { seen.insert($0).inserted } }
        let uniqueHard = unique(hard)
        let uniqueWarnings = unique(warnings)
        return QualityDecision(decision: uniqueHard.isEmpty ? .accept : .reject, reasons: uniqueHard, warnings: uniqueWarnings, metrics: metrics)
    }
}

/// The single production-used quality seam. Camera/preview adapters provide a
/// normalized candidate frame and the already-owned M03 motion binding; every
/// M04 metric is evaluated from the selected versioned preset here.
public struct M04CandidateFrameInput: Sendable, Equatable {
    public let sessionID: String
    public let captureID: String
    public let sequence: Int
    public let monotonicTimestamp: TimeInterval
    public let frame: QualityImageFrame
    public let motion: MotionCaptureBinding?
    public let pose: PoseCaptureBinding?
    public init(sessionID: String, captureID: String = UUID().uuidString, sequence: Int, monotonicTimestamp: TimeInterval, frame: QualityImageFrame, motion: MotionCaptureBinding? = nil, pose: PoseCaptureBinding? = nil) {
        self.sessionID = sessionID; self.captureID = captureID; self.sequence = sequence; self.monotonicTimestamp = monotonicTimestamp; self.frame = frame; self.motion = motion; self.pose = pose
    }
}

public struct M04CandidateQualityEvaluation: Sendable, Equatable {
    public let input: M04CandidateFrameInput
    public let quality: QualityDecision
    public init(input: M04CandidateFrameInput, quality: QualityDecision) { self.input = input; self.quality = quality }
}

public struct M04CandidateQualityRuntime: Sendable, Equatable {
    public let preset: PackagingPreset
    public let decisionPolicy: QualityDecisionPolicy
    public init(preset: PackagingPreset, decisionPolicy: QualityDecisionPolicy = .provisional) { self.preset = preset; self.decisionPolicy = decisionPolicy }
    public func evaluate(_ input: M04CandidateFrameInput) -> M04CandidateQualityEvaluation {
        let quality = evaluateQuality(frame: input.frame, motion: input.motion)
        return M04CandidateQualityEvaluation(input: input, quality: quality)
    }
    public func evaluateQuality(frame: QualityImageFrame, motion: MotionCaptureBinding?) -> QualityDecision {
        let sharpness = SharpnessAnalyzer.analyze(frame, thresholds: preset.quality.sharpness)
        let motionBlur = MotionBlurAnalyzer.analyze(sharpness: sharpness, motion: motion)
        let highlight = LuminanceClippingAnalyzer.highlight(frame, thresholds: preset.quality.highlight)
        let shadow = LuminanceClippingAnalyzer.shadow(frame, thresholds: preset.quality.shadow)
        let framing = FramingAnalyzer.analyze(frame, thresholds: preset.quality.framing)
        let background = BackgroundComplexityAnalyzer.analyze(frame, thresholds: preset.quality.background)
        return QualityDecisionEngine.evaluate(CandidateQualityMetrics(sharpness: sharpness, motionBlur: motionBlur, highlightClipping: highlight, shadowClipping: shadow, framing: framing, background: background), policy: decisionPolicy)
    }
}

public struct QualityCandidateLog: Codable, Sendable, Equatable, Identifiable {
    public let id: String
    public let sessionID: String
    public let captureID: String
    public let sequence: Int
    public let monotonicTimestamp: TimeInterval
    public let decision: CandidateQualityDecision
    public let reasons: [String]
    public let warnings: [String]
    public let metrics: CandidateQualityMetrics
    public let manualAudit: ManualCaptureAudit?
    public init(sessionID: String, captureID: String, sequence: Int, monotonicTimestamp: TimeInterval, decision: QualityDecision, manualAudit: ManualCaptureAudit? = nil) {
        self.sessionID = QualityLogSanitizer.identifier(sessionID)
        self.captureID = QualityLogSanitizer.identifier(captureID)
        self.sequence = max(0, sequence)
        self.monotonicTimestamp = monotonicTimestamp.isFinite ? monotonicTimestamp : 0
        self.decision = decision.decision
        self.reasons = Array(decision.reasons.prefix(32)).map(QualityLogSanitizer.reason)
        self.warnings = Array(decision.warnings.prefix(32)).map(QualityLogSanitizer.reason)
        self.metrics = decision.metrics
        self.manualAudit = manualAudit
        self.id = "\(self.sessionID):\(self.captureID):\(self.sequence)"
    }
}

public enum QualityLogSanitizer {
    public static func identifier(_ value: String) -> String {
        let filtered = value.map { $0.isLetter || $0.isNumber || $0 == "-" || $0 == "_" ? $0 : "_" }
        return String(filtered.prefix(96)).isEmpty ? "unavailable" : String(filtered.prefix(96))
    }
    public static func reason(_ value: String) -> String { String(value.filter { $0.isLetter || $0.isNumber || $0 == "_" || $0 == "-" }.prefix(96)) }
}

public enum QualityLogStoreError: Error, Sendable, Equatable { case invalidEntry, corruptLog }

public extension SessionStorageLayout {
    var qualityLog: URL { sessionRoot.appendingPathComponent("quality-candidates.jsonl") }
}

/// Rejected candidates are diagnostics, not accepted-session records. This
/// actor writes a bounded JSONL sidecar atomically so a crash during a rejected
/// candidate cannot corrupt source images or the canonical session state.
public actor QualityCandidateLogStore {
    private let url: URL
    private let fileManager: FileManager
    private let maximumRecords: Int
    public init(layout: SessionStorageLayout, maximumRecords: Int = 2048, fileManager: FileManager = .default) { self.url = layout.qualityLog; self.maximumRecords = max(1, maximumRecords); self.fileManager = fileManager }

    public func append(_ entry: QualityCandidateLog) throws {
        guard entry.sequence >= 0, entry.monotonicTimestamp.isFinite else { throw QualityLogStoreError.invalidEntry }
        var entries = try load()
        entries.append(entry)
        if entries.count > maximumRecords { entries.removeFirst(entries.count - maximumRecords) }
        try write(entries)
    }

    public func snapshot() throws -> [QualityCandidateLog] { try load() }

    private func load() throws -> [QualityCandidateLog] {
        guard fileManager.fileExists(atPath: url.path) else { return [] }
        do {
            let data = try Data(contentsOf: url)
            return try data.split(separator: 10).filter { !$0.isEmpty }.map { try JSONDecoder().decode(QualityCandidateLog.self, from: Data($0)) }
        } catch { throw QualityLogStoreError.corruptLog }
    }

    private func write(_ entries: [QualityCandidateLog]) throws {
        try fileManager.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        let encoder = JSONEncoder()
        var data = Data()
        for entry in entries { data.append(try encoder.encode(entry)); data.append(10) }
        try data.write(to: url, options: .atomic)
    }
}

public struct CoverageRingDefinition: Codable, Sendable, Equatable, Identifiable {
    public let id: String
    public let minimumElevation: Double
    public let maximumElevation: Double
    public let required: Bool
    public init(id: String, minimumElevation: Double, maximumElevation: Double, required: Bool = true) { self.id = id; self.minimumElevation = minimumElevation; self.maximumElevation = max(minimumElevation, maximumElevation); self.required = required }
}

public struct OrbitCoverageConfiguration: Codable, Sendable, Equatable {
    public let azimuthBinCount: Int
    public let rings: [CoverageRingDefinition]
    public init(azimuthBinCount: Int = 8, rings: [CoverageRingDefinition] = OrbitCoverageConfiguration.standardRings) { self.azimuthBinCount = max(1, azimuthBinCount); self.rings = rings }
    public static let standardRings = [CoverageRingDefinition(id: "lower", minimumElevation: -35, maximumElevation: -10), CoverageRingDefinition(id: "middle", minimumElevation: -10, maximumElevation: 15), CoverageRingDefinition(id: "upper", minimumElevation: 15, maximumElevation: 40)]
}

public struct CoverageSector: Codable, Sendable, Equatable, Hashable, Identifiable {
    public let ringID: String
    public let azimuthIndex: Int
    public let id: String
    public init(ringID: String, azimuthIndex: Int) { self.ringID = ringID; self.azimuthIndex = azimuthIndex; self.id = "\(ringID)-a\(azimuthIndex)" }
}

public struct CoveragePoseObservation: Codable, Sendable, Equatable {
    public let captureID: String
    public let sector: CoverageSector?
    public let azimuthDegrees: Double?
    public let elevationDegrees: Double?
    public let status: String
    public init(captureID: String, sector: CoverageSector?, azimuthDegrees: Double?, elevationDegrees: Double?, status: String) { self.captureID = captureID; self.sector = sector; self.azimuthDegrees = azimuthDegrees; self.elevationDegrees = elevationDegrees; self.status = status }
}

public struct OrbitCoverageSnapshot: Codable, Sendable, Equatable {
    public let configuration: OrbitCoverageConfiguration
    public let capturedSectors: [CoverageSector]
    public let missingSectors: [CoverageSector]
    public let duplicateCaptureIDs: [String]
    public let invalidCaptureIDs: [String]
    public let observations: [CoveragePoseObservation]
    public let completionFraction: Double
    public let isComplete: Bool
    public init(configuration: OrbitCoverageConfiguration, capturedSectors: [CoverageSector], missingSectors: [CoverageSector], duplicateCaptureIDs: [String], invalidCaptureIDs: [String], observations: [CoveragePoseObservation]) {
        self.configuration = configuration; self.capturedSectors = capturedSectors; self.missingSectors = missingSectors; self.duplicateCaptureIDs = duplicateCaptureIDs; self.invalidCaptureIDs = invalidCaptureIDs; self.completionFraction = missingSectors.isEmpty && !capturedSectors.isEmpty ? 1 : Double(capturedSectors.count) / Double(max(1, capturedSectors.count + missingSectors.count)); self.isComplete = missingSectors.isEmpty && !capturedSectors.isEmpty
    }
}

public enum CoveragePoseMapper {
    public static func map(captureID: String, pose: PoseSample?, configuration: OrbitCoverageConfiguration) -> CoveragePoseObservation {
        guard let pose, pose.tracking == .normal, pose.hasValidTransform, pose.transform.count == 16 else { return CoveragePoseObservation(captureID: captureID, sector: nil, azimuthDegrees: nil, elevationDegrees: nil, status: "pose_unavailable") }
        let x = pose.transform[3], y = pose.transform[7], z = pose.transform[11]
        let radius = sqrt(x * x + z * z)
        guard radius > 1e-9 else { return CoveragePoseObservation(captureID: captureID, sector: nil, azimuthDegrees: nil, elevationDegrees: nil, status: "pose_radius_unavailable") }
        let azimuth = (atan2(x, -z) * 180 / Double.pi + 360).truncatingRemainder(dividingBy: 360)
        let elevation = atan2(y, radius) * 180 / Double.pi
        guard let ring = configuration.rings.first(where: { elevation >= $0.minimumElevation && elevation < $0.maximumElevation }) else { return CoveragePoseObservation(captureID: captureID, sector: nil, azimuthDegrees: azimuth, elevationDegrees: elevation, status: "elevation_out_of_range") }
        let index = min(configuration.azimuthBinCount - 1, max(0, Int(azimuth / 360 * Double(configuration.azimuthBinCount))))
        return CoveragePoseObservation(captureID: captureID, sector: CoverageSector(ringID: ring.id, azimuthIndex: index), azimuthDegrees: azimuth, elevationDegrees: elevation, status: "available")
    }
}

public struct OrbitCoverageModel: Sendable, Equatable {
    public let configuration: OrbitCoverageConfiguration
    private var captured: Set<CoverageSector> = []
    private var duplicateIDs: [String] = []
    private var invalidIDs: [String] = []
    private var recordedObservations: [CoveragePoseObservation] = []
    public init(configuration: OrbitCoverageConfiguration = OrbitCoverageConfiguration()) { self.configuration = configuration }
    public init(snapshot: OrbitCoverageSnapshot) {
        self.configuration = snapshot.configuration
        self.captured = Set(snapshot.capturedSectors)
        self.duplicateIDs = snapshot.duplicateCaptureIDs
        self.invalidIDs = snapshot.invalidCaptureIDs
        self.recordedObservations = snapshot.observations
    }
    /// Coverage is admitted only from the accepted-capture pose binding. Raw
    /// preview poses cannot create coverage evidence.
    public mutating func observe(captureID: String, poseBinding: PoseCaptureBinding?) -> CoveragePoseObservation {
        let observation: CoveragePoseObservation
        guard let poseBinding, poseBinding.captureID == captureID else {
            observation = CoveragePoseObservation(captureID: captureID, sector: nil, azimuthDegrees: nil, elevationDegrees: nil, status: poseBinding == nil ? "pose_unavailable" : "pose_capture_mismatch")
            recordedObservations.append(observation); invalidIDs.append(captureID); return observation
        }
        guard poseBinding.aligned.status == "available", let pose = poseBinding.aligned.sample else {
            observation = CoveragePoseObservation(captureID: captureID, sector: nil, azimuthDegrees: nil, elevationDegrees: nil, status: "pose_\(poseBinding.aligned.status)")
            recordedObservations.append(observation); invalidIDs.append(captureID); return observation
        }
        observation = CoveragePoseMapper.map(captureID: captureID, pose: pose, configuration: configuration)
        recordedObservations.append(observation)
        guard let sector = observation.sector, observation.status == "available" else { invalidIDs.append(captureID); return observation }
        if captured.contains(sector) { duplicateIDs.append(captureID) } else { captured.insert(sector) }
        return observation
    }
    public func snapshot() -> OrbitCoverageSnapshot {
        let all = configuration.rings.flatMap { ring in (0..<configuration.azimuthBinCount).map { CoverageSector(ringID: ring.id, azimuthIndex: $0) } }
        return OrbitCoverageSnapshot(configuration: configuration, capturedSectors: all.filter { captured.contains($0) }, missingSectors: all.filter { !captured.contains($0) }, duplicateCaptureIDs: duplicateIDs, invalidCaptureIDs: invalidIDs, observations: recordedObservations)
    }
}

public enum CoverageDisplayStatus: String, Codable, Sendable, Equatable { case captured, targeted, missing, unavailable }

public struct CoverageDisplayItem: Sendable, Equatable, Identifiable {
    public let sector: CoverageSector
    public let status: CoverageDisplayStatus
    public let label: String
    public init(sector: CoverageSector, status: CoverageDisplayStatus) { self.sector = sector; self.status = status; self.label = "\(sector.ringID) sector \(sector.azimuthIndex + 1) \(status.rawValue)" }
    public var id: String { sector.id }
}

public struct CoverageViewModel: Sendable, Equatable {
    public let items: [CoverageDisplayItem]
    public let statusText: String
    public let accessibilityText: String
    public init(snapshot: OrbitCoverageSnapshot, targeted: CoverageSector? = nil) {
        let unavailable = snapshot.configuration.rings.isEmpty || (!snapshot.invalidCaptureIDs.isEmpty && snapshot.capturedSectors.isEmpty)
        items = snapshot.missingSectors.sorted { $0.id < $1.id }.map { CoverageDisplayItem(sector: $0, status: $0 == targeted ? .targeted : (unavailable ? .unavailable : .missing)) } + snapshot.capturedSectors.sorted { $0.id < $1.id }.map { CoverageDisplayItem(sector: $0, status: .captured) }
        if unavailable { statusText = "Coverage evidence unavailable" }
        else if snapshot.isComplete { statusText = "Coverage complete" }
        else { statusText = "Coverage \(Int(snapshot.completionFraction * 100)) percent; \(snapshot.missingSectors.count) sectors missing" }
        accessibilityText = items.map { $0.label }.joined(separator: ", ")
    }
}

public struct AutoCaptureInput: Sendable, Equatable {
    public let monotonicTimestamp: TimeInterval
    public let poseEligible: Bool
    public let targetSector: CoverageSector?
    public let quality: QualityDecision
    public let overlapAllowed: Bool
    public let duplicateDecision: DuplicateDecision?
    public let admission: CaptureAdmissionController
    public init(monotonicTimestamp: TimeInterval, poseEligible: Bool, targetSector: CoverageSector?, quality: QualityDecision, overlapAllowed: Bool, duplicateDecision: DuplicateDecision? = nil, admission: CaptureAdmissionController) { self.monotonicTimestamp = monotonicTimestamp; self.poseEligible = poseEligible; self.targetSector = targetSector; self.quality = quality; self.overlapAllowed = overlapAllowed; self.duplicateDecision = duplicateDecision; self.admission = admission }
}

public struct AutoCaptureDecision: Sendable, Equatable {
    public let allowed: Bool
    public let reasons: [String]
    public init(allowed: Bool, reasons: [String]) { self.allowed = allowed; self.reasons = reasons }
}

public struct AutoCaptureController: Sendable, Equatable {
    public let cooldownSeconds: TimeInterval
    public private(set) var inFlight = false
    public private(set) var cooldownUntil: TimeInterval?
    public init(cooldownSeconds: TimeInterval = 0.75) { self.cooldownSeconds = max(0, cooldownSeconds) }
    public func evaluate(_ input: AutoCaptureInput) -> AutoCaptureDecision {
        var reasons: [String] = []
        if inFlight { reasons.append("auto_capture_in_flight") }
        if let cooldownUntil, input.monotonicTimestamp < cooldownUntil { reasons.append("auto_capture_cooldown") }
        if !input.poseEligible { reasons.append("pose_ineligible") }
        if input.targetSector == nil { reasons.append("coverage_target_missing") }
        if !input.quality.isAcceptable { reasons.append(contentsOf: input.quality.reasons) }
        if !input.overlapAllowed { reasons.append("overlap_not_allowed") }
        if input.duplicateDecision?.isDuplicate == true { reasons.append(input.duplicateDecision?.reasonCode ?? "near_duplicate_candidate") }
        if !input.admission.allowsCapture { reasons.append(input.admission.rejectReason() ?? "capture_admission_blocked") }
        return AutoCaptureDecision(allowed: reasons.isEmpty, reasons: reasons)
    }
    public mutating func begin(_ input: AutoCaptureInput) -> AutoCaptureDecision { let decision = evaluate(input); if decision.allowed { inFlight = true }; return decision }
    public mutating func complete(success: Bool, monotonicTimestamp: TimeInterval) { inFlight = false; if success { cooldownUntil = monotonicTimestamp + cooldownSeconds } }
    public mutating func resetAfterRejectedCandidate() { inFlight = false }
}

/// Production adapter for the existing health-gated still-capture owner.
public actor GuidedAutoCaptureService {
    private let stillCapture: AdmissionControlledStillCaptureService
    private var controller: AutoCaptureController
    public init(stillCapture: AdmissionControlledStillCaptureService, cooldownSeconds: TimeInterval = 0.75) { self.stillCapture = stillCapture; self.controller = AutoCaptureController(cooldownSeconds: cooldownSeconds) }
    public func request(captureID: String, input: AutoCaptureInput) async -> (decision: AutoCaptureDecision, result: StillCaptureResult?) {
        let decision = controller.begin(input)
        guard decision.allowed else { return (decision, nil) }
        let result = await stillCapture.capture(captureID: captureID)
        if case .accepted(let still) = result { controller.complete(success: true, monotonicTimestamp: still.monotonicTimestamp ?? input.monotonicTimestamp) }
        else { controller.resetAfterRejectedCandidate() }
        return (decision, result)
    }
    public func requestManual(captureID: String, monotonicTimestamp: TimeInterval) async -> StillCaptureResult {
        controller.resetAfterRejectedCandidate()
        let result = await stillCapture.capture(captureID: captureID)
        if case .accepted(let still) = result {
            controller.complete(success: true, monotonicTimestamp: still.monotonicTimestamp ?? monotonicTimestamp)
        } else {
            controller.resetAfterRejectedCandidate()
        }
        return result
    }
    public func resetForManualCapture() { controller.resetAfterRejectedCandidate() }
}

public struct DuplicatePolicy: Codable, Sendable, Equatable {
    public let maximumTranslationMeters: Double
    public let maximumElevationDifference: Double
    public let maximumSignatureDistance: Int
    public init(maximumTranslationMeters: Double = 0.04, maximumElevationDifference: Double = 4, maximumSignatureDistance: Int = 2) { self.maximumTranslationMeters = max(0, maximumTranslationMeters); self.maximumElevationDifference = max(0, maximumElevationDifference); self.maximumSignatureDistance = max(0, maximumSignatureDistance) }
    public static let provisional = DuplicatePolicy()
}

public struct DuplicateEvidence: Sendable, Equatable {
    public let captureID: String
    public let pose: PoseSample?
    public let poseBinding: PoseCaptureBinding?
    public let visualSignature: [UInt8]?
    public init(captureID: String, pose: PoseSample?, visualSignature: [UInt8]? = nil) { self.captureID = captureID; self.pose = pose; self.poseBinding = nil; self.visualSignature = visualSignature }
    public init(captureID: String, poseBinding: PoseCaptureBinding?, visualSignature: [UInt8]? = nil) { self.captureID = captureID; self.pose = nil; self.poseBinding = poseBinding; self.visualSignature = visualSignature }
}

public struct DuplicateDecision: Sendable, Equatable {
    public let isDuplicate: Bool
    public let reasonCode: String
    public let matchedCaptureID: String?
    public init(isDuplicate: Bool, reasonCode: String, matchedCaptureID: String? = nil) { self.isDuplicate = isDuplicate; self.reasonCode = reasonCode; self.matchedCaptureID = matchedCaptureID }
}

public enum NearDuplicateDetector {
    public static func evaluate(candidate: DuplicateEvidence, accepted: [DuplicateEvidence], configuration: OrbitCoverageConfiguration = OrbitCoverageConfiguration(), policy: DuplicatePolicy = .provisional) -> DuplicateDecision {
        guard let pose = pose(for: candidate), pose.tracking == .normal, pose.hasValidTransform else { return DuplicateDecision(isDuplicate: false, reasonCode: "duplicate_pose_unavailable") }
        guard let candidatePosition = position(pose) else { return DuplicateDecision(isDuplicate: false, reasonCode: "duplicate_pose_unavailable") }
        let candidateObservation = CoveragePoseMapper.map(captureID: candidate.captureID, pose: pose, configuration: configuration)
        for previous in accepted {
            guard let previousPose = pose(for: previous), previousPose.tracking == .normal, let previousPosition = position(previousPose) else { continue }
            let previousObservation = CoveragePoseMapper.map(captureID: previous.captureID, pose: previousPose, configuration: configuration)
            let distance = sqrt(zip(candidatePosition, previousPosition).reduce(0) { $0 + ($1.0 - $1.1) * ($1.0 - $1.1) })
            let elevationDelta = abs((candidateObservation.elevationDegrees ?? 0) - (previousObservation.elevationDegrees ?? 0))
            let signatureMatch = signaturesMatch(candidate.visualSignature, previous.visualSignature, maximumDistance: policy.maximumSignatureDistance)
            if candidateObservation.sector != nil, candidateObservation.sector == previousObservation.sector, (distance <= policy.maximumTranslationMeters && elevationDelta <= policy.maximumElevationDifference) || signatureMatch {
                return DuplicateDecision(isDuplicate: true, reasonCode: "near_duplicate_candidate", matchedCaptureID: previous.captureID)
            }
        }
        return DuplicateDecision(isDuplicate: false, reasonCode: "useful_candidate")
    }

    private static func pose(for evidence: DuplicateEvidence) -> PoseSample? {
        if let binding = evidence.poseBinding {
            guard binding.captureID == evidence.captureID, binding.aligned.status == "available" else { return nil }
            return binding.aligned.sample
        }
        return evidence.pose
    }
    private static func position(_ pose: PoseSample) -> [Double]? { guard pose.transform.count == 16 else { return nil }; return [pose.transform[3], pose.transform[7], pose.transform[11]] }
    private static func signaturesMatch(_ lhs: [UInt8]?, _ rhs: [UInt8]?, maximumDistance: Int) -> Bool { guard let lhs, let rhs, lhs.count == rhs.count else { return false }; return zip(lhs, rhs).reduce(0) { $0 + ($1.0 == $1.1 ? 0 : 1) } <= maximumDistance }
}

public struct RingCoverageRequirement: Codable, Sendable, Equatable, Identifiable {
    public let ringID: String
    public let minimumSectorCount: Int
    public let required: Bool
    public init(ringID: String, minimumSectorCount: Int, required: Bool = true) { self.ringID = ringID; self.minimumSectorCount = max(0, minimumSectorCount); self.required = required }
    public var id: String { ringID }
}

public struct StandardBottleCoveragePolicy: Codable, Sendable, Equatable {
    public let requirements: [RingCoverageRequirement]
    public init(requirements: [RingCoverageRequirement] = [RingCoverageRequirement(ringID: "lower", minimumSectorCount: 4), RingCoverageRequirement(ringID: "middle", minimumSectorCount: 4), RingCoverageRequirement(ringID: "upper", minimumSectorCount: 4)]) { self.requirements = requirements }
    public static let standard = StandardBottleCoveragePolicy()
}

public struct RingCoverageStatus: Codable, Sendable, Equatable, Identifiable {
    public let ringID: String
    public let capturedSectorCount: Int
    public let minimumSectorCount: Int
    public let missing: Bool
    public var id: String { ringID }
}

public struct RingCoverageEvaluation: Codable, Sendable, Equatable {
    public let statuses: [RingCoverageStatus]
    public let missingRingIDs: [String]
    public let isComplete: Bool
    public let guidance: [String]
    public init(snapshot: OrbitCoverageSnapshot, policy: StandardBottleCoveragePolicy = .standard) {
        statuses = policy.requirements.map { requirement in
            let count = snapshot.capturedSectors.filter { $0.ringID == requirement.ringID }.count
            return RingCoverageStatus(ringID: requirement.ringID, capturedSectorCount: count, minimumSectorCount: requirement.minimumSectorCount, missing: requirement.required && count < requirement.minimumSectorCount)
        }
        missingRingIDs = statuses.filter(\.missing).map(\.ringID)
        isComplete = missingRingIDs.isEmpty
        guidance = missingRingIDs.map { "Capture more \($0) ring sectors" }
    }
}

public enum CapturePassID: String, Codable, Sendable, Equatable, Hashable, CaseIterable { case standard, shoulder, neck, closure, base }

public struct CapturePassMetadata: Codable, Sendable, Equatable {
    public let passID: CapturePassID
    public let required: Bool
    public let evidenceStatus: String
    public init(passID: CapturePassID, required: Bool, evidenceStatus: String) { self.passID = passID; self.required = required; self.evidenceStatus = evidenceStatus }
}

public struct DetailPassPolicy: Codable, Sendable, Equatable {
    public let passID: CapturePassID
    public let minimumFramingFraction: Double
    public let minimumSectorCount: Int
    public let required: Bool
    public init(passID: CapturePassID, minimumFramingFraction: Double = 0.12, minimumSectorCount: Int = 2, required: Bool = true) { self.passID = passID; self.minimumFramingFraction = max(0, min(1, minimumFramingFraction)); self.minimumSectorCount = max(0, minimumSectorCount); self.required = required }
}

public struct DetailPassEvaluation: Codable, Sendable, Equatable {
    public let metadata: CapturePassMetadata
    public let capturedSectorCount: Int
    public let missingGuidance: [String]
    public let isComplete: Bool
    public init(snapshot: OrbitCoverageSnapshot, framing: FramingMetric, policy: DetailPassPolicy) {
        let count = snapshot.capturedSectors.filter { $0.ringID == policy.passID.rawValue }.count
        let framingOkay = framing.band == .acceptable && (framing.objectFraction ?? 0) >= policy.minimumFramingFraction
        capturedSectorCount = count
        missingGuidance = count < policy.minimumSectorCount ? ["Capture missing \(policy.passID.rawValue) detail sectors"] : (framingOkay ? [] : ["Move closer while keeping the supported main camera lens and safe margins"])
        isComplete = policy.required && count >= policy.minimumSectorCount && framingOkay
        metadata = CapturePassMetadata(passID: policy.passID, required: policy.required, evidenceStatus: isComplete ? "complete" : (snapshot.invalidCaptureIDs.isEmpty ? "incomplete" : "pose_evidence_unavailable"))
    }
}

public struct DetailPassAcceptanceDecision: Sendable, Equatable {
    public let allowed: Bool
    public let metadata: CapturePassMetadata
    public let reasons: [String]
    public init(snapshot: OrbitCoverageSnapshot, policy: DetailPassPolicy, quality: QualityDecision, framing: FramingMetric, poseBinding: PoseCaptureBinding?, duplicateDecision: DuplicateDecision?) {
        var reasons: [String] = []
        guard let poseBinding, poseBinding.aligned.status == "available", poseBinding.aligned.sample != nil else { reasons.append("pose_evidence_unavailable") }
        if !quality.isAcceptable { reasons.append(contentsOf: quality.reasons) }
        if framing.band != .acceptable || (framing.objectFraction ?? 0) < policy.minimumFramingFraction { reasons.append("detail_framing_unacceptable") }
        if duplicateDecision == nil { reasons.append("duplicate_evidence_unavailable") }
        else if duplicateDecision?.isDuplicate == true { reasons.append(duplicateDecision?.reasonCode ?? "near_duplicate_candidate") }
        self.allowed = reasons.isEmpty
        self.reasons = reasons
        self.metadata = CapturePassMetadata(passID: policy.passID, required: policy.required, evidenceStatus: reasons.isEmpty ? "accepted" : (reasons.contains("pose_evidence_unavailable") ? "pose_evidence_unavailable" : "rejected"))
    }
}

public struct BasePassAvailability: Codable, Sendable, Equatable {
    public let physicallyFeasible: Bool
    public let reasonCode: String
    public let operatorSkipped: Bool
    public init(physicallyFeasible: Bool, reasonCode: String, operatorSkipped: Bool = false) { self.physicallyFeasible = physicallyFeasible; self.reasonCode = reasonCode; self.operatorSkipped = operatorSkipped }
    private enum CodingKeys: String, CodingKey { case physicallyFeasible, reasonCode, operatorSkipped }
    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        physicallyFeasible = try container.decode(Bool.self, forKey: .physicallyFeasible)
        reasonCode = try container.decode(String.self, forKey: .reasonCode)
        operatorSkipped = try container.decodeIfPresent(Bool.self, forKey: .operatorSkipped) ?? false
    }
}

public struct BasePassEvaluation: Codable, Sendable, Equatable {
    public let metadata: CapturePassMetadata
    public let status: String
    public let capturedSectorCount: Int
    public let guidance: [String]
    public init(snapshot: OrbitCoverageSnapshot, availability: BasePassAvailability, minimumSectorCount: Int = 2) {
        let count = snapshot.capturedSectors.filter { $0.ringID == CapturePassID.base.rawValue }.count
        capturedSectorCount = count
        if availability.operatorSkipped { status = "skipped"; guidance = [availability.reasonCode] }
        else if !availability.physicallyFeasible { status = "unavailable"; guidance = [availability.reasonCode] }
        else if count >= minimumSectorCount { status = "complete"; guidance = [] }
        else { status = "incomplete"; guidance = ["Capture more base sectors without unsafe handling"] }
        metadata = CapturePassMetadata(passID: .base, required: availability.physicallyFeasible && !availability.operatorSkipped, evidenceStatus: status)
    }
    public var isComplete: Bool { status == "complete" }
}

public struct BasePassAcceptanceDecision: Sendable, Equatable {
    public let allowed: Bool
    public let reasons: [String]
    public let evaluation: BasePassEvaluation
    public init(snapshot: OrbitCoverageSnapshot, availability: BasePassAvailability, quality: QualityDecision, poseBinding: PoseCaptureBinding?, duplicateDecision: DuplicateDecision?) {
        var reasons: [String] = []
        if availability.operatorSkipped { reasons.append(availability.reasonCode) }
        else if !availability.physicallyFeasible { reasons.append(availability.reasonCode) }
        guard let poseBinding, poseBinding.aligned.status == "available", poseBinding.aligned.sample != nil else { reasons.append("pose_evidence_unavailable") }
        if !quality.isAcceptable { reasons.append(contentsOf: quality.reasons) }
        if duplicateDecision == nil { reasons.append("duplicate_evidence_unavailable") }
        else if duplicateDecision?.isDuplicate == true { reasons.append(duplicateDecision?.reasonCode ?? "near_duplicate_candidate") }
        self.allowed = reasons.isEmpty
        self.reasons = reasons
        self.evaluation = BasePassEvaluation(snapshot: snapshot, availability: availability)
    }
}

public enum CompletionEvidenceStatus: String, Codable, Sendable, Equatable { case complete, incomplete, unavailable, skipped }

public struct M04QualityGuidanceState: Codable, Sendable, Equatable {
    public let presetID: PackagingPresetID
    public let consecutiveHighlightBlocks: Int
    public let triggerThreshold: Int
    public let guidanceActive: Bool
    public let guidance: [String]
    public init(presetID: PackagingPresetID, consecutiveHighlightBlocks: Int, triggerThreshold: Int = 3, guidanceActive: Bool, guidance: [String]) {
        self.presetID = presetID
        self.consecutiveHighlightBlocks = max(0, consecutiveHighlightBlocks)
        self.triggerThreshold = max(1, triggerThreshold)
        self.guidanceActive = guidanceActive
        self.guidance = guidance
    }
}

public struct CompletionDiagnostics: Codable, Sendable, Equatable {
    public let score: Double
    public let status: CompletionEvidenceStatus
    public let mandatoryMissingAreas: [String]
    public let optionalUnavailableAreas: [String]
    public let guidance: [String]
    public init(rings: RingCoverageEvaluation, detailPasses: [DetailPassEvaluation] = [], base: BasePassEvaluation? = nil, additionalMandatoryMissingAreas: [String] = [], additionalMandatoryAreaCount: Int = 0) {
        let requiredRingCount = rings.statuses.filter { $0.missing || $0.minimumSectorCount > 0 }.count
        let completeRingCount = rings.statuses.filter { !$0.missing }.count
        let requiredDetails = detailPasses.filter { $0.metadata.required }
        let completeDetails = requiredDetails.filter(\.isComplete).count
        let requiredBase = base?.metadata.required == true
        let completeBase = requiredBase && base?.isComplete == true ? 1 : 0
        let additionalRequired = max(additionalMandatoryAreaCount, additionalMandatoryMissingAreas.count)
        let additionalComplete = max(0, additionalRequired - additionalMandatoryMissingAreas.count)
        let denominator = max(1, requiredRingCount + requiredDetails.count + (requiredBase ? 1 : 0) + additionalRequired)
        score = Double(completeRingCount + completeDetails + completeBase + additionalComplete) / Double(denominator)
        mandatoryMissingAreas = rings.missingRingIDs + requiredDetails.filter { !$0.isComplete }.map { $0.metadata.passID.rawValue } + additionalMandatoryMissingAreas
        if requiredBase, base?.isComplete != true { mandatoryMissingAreas.append(CapturePassID.base.rawValue) }
        optionalUnavailableAreas = (base?.status == "unavailable" || base?.status == "skipped") ? [CapturePassID.base.rawValue] : []
        let optionalGuidance: [String]
        if base?.status == "skipped" {
            optionalGuidance = ["Optional \(CapturePassID.base.rawValue) pass skipped; completion is not claimed"]
        } else {
            optionalGuidance = optionalUnavailableAreas.map { "Optional \($0) pass unavailable; completion is not claimed" }
        }
        guidance = mandatoryMissingAreas.map { "Capture missing \($0) coverage" } + optionalGuidance
        let hasCompletionEvidence = !rings.statuses.isEmpty || !requiredDetails.isEmpty || base != nil
        if !mandatoryMissingAreas.isEmpty { status = .incomplete }
        else if base?.status == "skipped" { status = .skipped }
        else if base?.status == "unavailable" { status = .unavailable }
        else { status = hasCompletionEvidence ? .complete : .unavailable }
    }
}

public struct ManualCaptureInput: Sendable, Equatable {
    public let automaticDecision: AutoCaptureDecision
    public let quality: QualityDecision
    public let admission: CaptureAdmissionController
    public let cameraReady: Bool
    public let sessionReady: Bool
    public let sourceIntegrityReady: Bool
    public let metadataReady: Bool
    public let poseEvidenceReady: Bool
    public init(automaticDecision: AutoCaptureDecision, quality: QualityDecision, admission: CaptureAdmissionController, cameraReady: Bool, sessionReady: Bool, sourceIntegrityReady: Bool, metadataReady: Bool, poseEvidenceReady: Bool) { self.automaticDecision = automaticDecision; self.quality = quality; self.admission = admission; self.cameraReady = cameraReady; self.sessionReady = sessionReady; self.sourceIntegrityReady = sourceIntegrityReady; self.metadataReady = metadataReady; self.poseEvidenceReady = poseEvidenceReady }
}

public struct ManualCaptureDecision: Sendable, Equatable {
    public let allowed: Bool
    public let warnings: [String]
    public let blockingReasons: [String]
    public init(allowed: Bool, warnings: [String], blockingReasons: [String]) { self.allowed = allowed; self.warnings = warnings; self.blockingReasons = blockingReasons }
}

public struct ManualCaptureAudit: Codable, Sendable, Equatable {
    public let allowed: Bool
    public let warnings: [String]
    public let blockingReasons: [String]
    public init(decision: ManualCaptureDecision) { self.allowed = decision.allowed; self.warnings = decision.warnings; self.blockingReasons = decision.blockingReasons }
}

public enum ManualCaptureCoordinator {
    public static func evaluate(_ input: ManualCaptureInput) -> ManualCaptureDecision {
        var blocks: [String] = []
        if !input.admission.allowsCapture { blocks.append("health_hard_stop") }
        if !input.cameraReady { blocks.append("camera_not_ready") }
        if !input.sessionReady { blocks.append("session_not_ready") }
        if !input.sourceIntegrityReady { blocks.append("source_integrity_unavailable") }
        if !input.metadataReady { blocks.append("metadata_unavailable") }
        if !input.poseEvidenceReady { blocks.append("pose_evidence_unavailable") }
        var warnings = input.quality.warnings + input.quality.reasons
        if !input.automaticDecision.allowed { warnings.append(contentsOf: input.automaticDecision.reasons) }
        warnings.append("manual_capture_override")
        var seen = Set<String>(); warnings = warnings.filter { seen.insert($0).inserted }
        return ManualCaptureDecision(allowed: blocks.isEmpty, warnings: warnings, blockingReasons: blocks)
    }
}

public enum PackagingPresetID: String, Codable, Sendable, Equatable, CaseIterable { case matteHDPE = "matte_hdpe", glossyPET = "glossy_pet", transparent, asymmetricJerrycan = "asymmetric_jerrycan", closureCap = "closure_cap", turntable }

public struct QualityPolicyConfiguration: Codable, Sendable, Equatable {
    public let sharpness: SharpnessThresholds
    public let highlight: ClippingThresholds
    public let shadow: ClippingThresholds
    public let framing: FramingThresholds
    public let background: BackgroundComplexityThresholds
    public init(sharpness: SharpnessThresholds = .provisional, highlight: ClippingThresholds = .highlightProvisional, shadow: ClippingThresholds = .shadowProvisional, framing: FramingThresholds = .provisional, background: BackgroundComplexityThresholds = .provisional) { self.sharpness = sharpness; self.highlight = highlight; self.shadow = shadow; self.framing = framing; self.background = background }
}

public struct CoveragePolicyConfiguration: Codable, Sendable, Equatable {
    public let orbit: OrbitCoverageConfiguration
    public let ringRequirements: StandardBottleCoveragePolicy
    public let asymmetricCoverage: AsymmetricCoveragePolicy?
    public init(orbit: OrbitCoverageConfiguration = OrbitCoverageConfiguration(), ringRequirements: StandardBottleCoveragePolicy = .standard, asymmetricCoverage: AsymmetricCoveragePolicy? = nil) { self.orbit = orbit; self.ringRequirements = ringRequirements; self.asymmetricCoverage = asymmetricCoverage }
}

public struct PackagingPreset: Codable, Sendable, Equatable, Identifiable {
    public let id: PackagingPresetID
    public let version: String
    public let displayName: String
    public let quality: QualityPolicyConfiguration
    public let coverage: CoveragePolicyConfiguration
    public let lightingGuidance: [String]
    public let preparationGuidance: [String]
    public let requiresPreparationAcknowledgement: Bool
    public let supportedLensRule: String
    public init(id: PackagingPresetID, version: String, displayName: String, quality: QualityPolicyConfiguration, coverage: CoveragePolicyConfiguration, lightingGuidance: [String], preparationGuidance: [String], requiresPreparationAcknowledgement: Bool, supportedLensRule: String = "selected_rear_main_wide_only") { self.id = id; self.version = version; self.displayName = displayName; self.quality = quality; self.coverage = coverage; self.lightingGuidance = lightingGuidance; self.preparationGuidance = preparationGuidance; self.requiresPreparationAcknowledgement = requiresPreparationAcknowledgement; self.supportedLensRule = supportedLensRule }
}

public enum PackagingPresetCatalog {
    public static let matteHDPE = PackagingPreset(id: .matteHDPE, version: "1.0.0", displayName: "Matte / HDPE", quality: QualityPolicyConfiguration(), coverage: CoveragePolicyConfiguration(), lightingGuidance: ["Use broad diffuse lighting.", "Keep exposure stable and avoid hard shadows."], preparationGuidance: ["Use a clean matte or simple background.", "Keep the package dry and free of loose labels."], requiresPreparationAcknowledgement: false)
    public static let glossyPET = PackagingPreset(id: .glossyPET, version: "1.0.0", displayName: "Glossy / PET", quality: QualityPolicyConfiguration(highlight: ClippingThresholds(luminanceCutoff: 0.98, toleratedFraction: 0.005, warningFraction: 0.025, rejectFraction: 0.12)), coverage: CoveragePolicyConfiguration(orbit: OrbitCoverageConfiguration(azimuthBinCount: 12)), lightingGuidance: ["Use large diffuse sources and avoid direct reflections.", "Reframe if highlights spread across the package."], preparationGuidance: ["Keep the glossy surface clean.", "Use a simple non-reflective background."], requiresPreparationAcknowledgement: false)
    public static let transparent = PackagingPreset(id: .transparent, version: "1.0.0", displayName: "Transparent", quality: QualityPolicyConfiguration(), coverage: CoveragePolicyConfiguration(), lightingGuidance: ["Use diffuse lighting and avoid transparent-surface reflections."], preparationGuidance: ["Photogrammetry may fail without temporary matte treatment, textured inserts or background preparation."], requiresPreparationAcknowledgement: true)
    public static let asymmetricJerrycan = PackagingPreset(id: .asymmetricJerrycan, version: "1.0.0", displayName: "Asymmetric / Jerrycan", quality: QualityPolicyConfiguration(), coverage: CoveragePolicyConfiguration(orbit: OrbitCoverageConfiguration(azimuthBinCount: 12), asymmetricCoverage: AsymmetricCoveragePolicy()), lightingGuidance: ["Use even diffuse lighting across front, back and handle regions."], preparationGuidance: ["Keep the handle unobstructed and capture front/back/side regions."], requiresPreparationAcknowledgement: false)
    public static let closureCap = PackagingPreset(id: .closureCap, version: "1.0.0", displayName: "Closure / Cap", quality: QualityPolicyConfiguration(framing: FramingThresholds(minimumObjectFraction: 0.14, maximumObjectFraction: 0.65, minimumMargin: 0.05)), coverage: CoveragePolicyConfiguration(orbit: OrbitCoverageConfiguration(azimuthBinCount: 8, rings: [CoverageRingDefinition(id: "closure", minimumElevation: 10, maximumElevation: 55)]), ringRequirements: StandardBottleCoveragePolicy(requirements: [RingCoverageRequirement(ringID: "closure", minimumSectorCount: 8)])), lightingGuidance: ["Use even diffuse lighting over threads, pump or cap details."], preparationGuidance: ["Move to a safe working distance and keep the cap centered without edge cropping."], requiresPreparationAcknowledgement: false)
    public static let turntable = PackagingPreset(id: .turntable, version: "1.0.0", displayName: "Turntable", quality: QualityPolicyConfiguration(), coverage: CoveragePolicyConfiguration(orbit: OrbitCoverageConfiguration(azimuthBinCount: 24)), lightingGuidance: ["Keep the camera and background static while the object rotates."], preparationGuidance: ["Use a stable turntable and record angle evidence for each frame."], requiresPreparationAcknowledgement: false)
    public static func preset(for id: PackagingPresetID) -> PackagingPreset { switch id { case .glossyPET: return glossyPET; case .transparent: return transparent; case .asymmetricJerrycan: return asymmetricJerrycan; case .closureCap: return closureCap; case .turntable: return turntable; default: return matteHDPE } }
}

public enum CalibrationAvailability: String, Codable, Sendable, Equatable { case ownerVerified = "owner_verified", provisionalTestCalibrated = "provisional_test_calibrated", ownerRequired = "owner_required", unavailable }

public enum PreflightIssueSeverity: String, Codable, Sendable, Equatable { case blocker, warning, information }

public struct PreflightIssue: Codable, Sendable, Equatable, Identifiable {
    public let code: String
    public let severity: PreflightIssueSeverity
    public let message: String
    public var id: String { code }
    public init(code: String, severity: PreflightIssueSeverity, message: String) { self.code = code; self.severity = severity; self.message = message }
}

public struct ScanPreflightInput: Sendable, Equatable {
    public let preset: PackagingPreset
    public let admission: CaptureAdmissionController
    public let cameraReady: Bool
    public let sessionReady: Bool
    public let storageAvailable: Bool
    public let calibration: CalibrationAvailability
    public let preparationAcknowledged: Bool
    public let environmentGuidanceAcknowledged: Bool
    public let transparentTreatment: TransparentTreatmentMode
    public init(preset: PackagingPreset, admission: CaptureAdmissionController = CaptureAdmissionController(), cameraReady: Bool, sessionReady: Bool, storageAvailable: Bool, calibration: CalibrationAvailability, preparationAcknowledged: Bool, environmentGuidanceAcknowledged: Bool, transparentTreatment: TransparentTreatmentMode = .none) { self.preset = preset; self.admission = admission; self.cameraReady = cameraReady; self.sessionReady = sessionReady; self.storageAvailable = storageAvailable; self.calibration = calibration; self.preparationAcknowledged = preparationAcknowledged; self.environmentGuidanceAcknowledged = environmentGuidanceAcknowledged; self.transparentTreatment = transparentTreatment }
}

public struct ScanRuntimeReadiness: Sendable, Equatable {
    public let cameraReady: Bool
    public let sessionReady: Bool
    public let storageAvailable: Bool
    public let calibration: CalibrationAvailability
    public init(cameraReady: Bool, sessionReady: Bool, storageAvailable: Bool, calibration: CalibrationAvailability = .ownerRequired) { self.cameraReady = cameraReady; self.sessionReady = sessionReady; self.storageAvailable = storageAvailable; self.calibration = calibration }
    public static let unavailable = ScanRuntimeReadiness(cameraReady: false, sessionReady: false, storageAvailable: false, calibration: .ownerRequired)
}

public struct ScanPreflightResult: Codable, Sendable, Equatable {
    public let canStart: Bool
    public let issues: [PreflightIssue]
    public let calibration: CalibrationAvailability
    public let preparationAcknowledged: Bool
    public let environmentGuidanceAcknowledged: Bool
    public init(canStart: Bool, issues: [PreflightIssue], calibration: CalibrationAvailability, preparationAcknowledged: Bool, environmentGuidanceAcknowledged: Bool) { self.canStart = canStart; self.issues = issues; self.calibration = calibration; self.preparationAcknowledged = preparationAcknowledged; self.environmentGuidanceAcknowledged = environmentGuidanceAcknowledged }
}

public enum ScanSuitabilityPreflight {
    public static func evaluate(_ input: ScanPreflightInput) -> ScanPreflightResult {
        var issues: [PreflightIssue] = []
        if case .hardStop = input.admission.gate { issues.append(PreflightIssue(code: "health_hard_stop", severity: .blocker, message: "Device health does not admit capture.")) }
        else if case .warning = input.admission.gate { issues.append(PreflightIssue(code: "health_warning", severity: .warning, message: "Device health is degraded.")) }
        if !input.cameraReady { issues.append(PreflightIssue(code: "camera_unavailable", severity: .blocker, message: "The selected camera is unavailable.")) }
        if !input.sessionReady { issues.append(PreflightIssue(code: "session_unready", severity: .blocker, message: "The scan session is not ready.")) }
        if !input.storageAvailable { issues.append(PreflightIssue(code: "storage_unavailable", severity: .blocker, message: "Storage admission is unavailable.")) }
        if input.calibration != .ownerVerified { issues.append(PreflightIssue(code: "calibration_owner_required", severity: .warning, message: "Owner-verified physical calibration is unavailable; thresholds remain provisional.")) }
        if input.preset.requiresPreparationAcknowledgement && !input.preparationAcknowledged { issues.append(PreflightIssue(code: "preparation_acknowledgement_required", severity: .blocker, message: "Required preparation guidance has not been acknowledged.")) }
        if input.preset.id == .transparent && input.transparentTreatment == .none { issues.append(PreflightIssue(code: "transparent_treatment_required", severity: .blocker, message: "Select and perform a transparent-packaging preparation treatment, or do not start.")) }
        if !input.environmentGuidanceAcknowledged { issues.append(PreflightIssue(code: "environment_guidance_required", severity: .blocker, message: "Minimum lighting/background guidance has not been acknowledged.")) }
        else { issues.append(PreflightIssue(code: "environment_guidance_acknowledged", severity: .information, message: "Minimum lighting/background guidance is acknowledged.")) }
        if input.preset.id == .transparent { issues.append(PreflightIssue(code: "transparent_reconstruction_unproven", severity: .warning, message: "Transparent reconstruction reliability is not established.")) }
        let canStart = !issues.contains { $0.severity == .blocker }
        return ScanPreflightResult(canStart: canStart, issues: issues, calibration: input.calibration, preparationAcknowledged: input.preparationAcknowledged, environmentGuidanceAcknowledged: input.environmentGuidanceAcknowledged)
    }
}

public struct M04DetailPassResumeState: Codable, Sendable, Equatable {
    public let passID: CapturePassID
    public let policy: DetailPassPolicy
    public let coverage: OrbitCoverageSnapshot
    public let framing: FramingMetric
    public let evaluation: DetailPassEvaluation
    public init(passID: CapturePassID, policy: DetailPassPolicy, coverage: OrbitCoverageSnapshot, framing: FramingMetric, evaluation: DetailPassEvaluation) {
        self.passID = passID; self.policy = policy; self.coverage = coverage; self.framing = framing; self.evaluation = evaluation
    }
}

public struct M04ScanContext: Codable, Sendable, Equatable {
    public let preset: PackagingPreset
    public let preparationAcknowledged: Bool
    public let treatmentMode: String?
    public let preflight: ScanPreflightResult?
    public let basePass: BasePassEvaluation?
    public let completion: CompletionDiagnostics?
    public let qualityGuidance: M04QualityGuidanceState?
    public let asymmetricCoverage: AsymmetricCoverageEvaluation?
    public let turntableCoverage: TurntableCoverageSnapshot?
    public let orbitCoverage: OrbitCoverageSnapshot?
    public let detailPasses: [M04DetailPassResumeState]?
    public init(preset: PackagingPreset, preparationAcknowledged: Bool = false, treatmentMode: String? = nil, preflight: ScanPreflightResult? = nil, basePass: BasePassEvaluation? = nil, completion: CompletionDiagnostics? = nil, qualityGuidance: M04QualityGuidanceState? = nil, asymmetricCoverage: AsymmetricCoverageEvaluation? = nil, turntableCoverage: TurntableCoverageSnapshot? = nil, orbitCoverage: OrbitCoverageSnapshot? = nil, detailPasses: [M04DetailPassResumeState]? = nil) { self.preset = preset; self.preparationAcknowledged = preparationAcknowledged; self.treatmentMode = treatmentMode; self.preflight = preflight; self.basePass = basePass; self.completion = completion; self.qualityGuidance = qualityGuidance; self.asymmetricCoverage = asymmetricCoverage; self.turntableCoverage = turntableCoverage; self.orbitCoverage = orbitCoverage; self.detailPasses = detailPasses }
}

public extension SessionStorageLayout {
    var m04Context: URL { sessionRoot.appendingPathComponent("m04-context.json") }
}

public actor M04SessionContextStore {
    private let layout: SessionStorageLayout
    public init(layout: SessionStorageLayout) { self.layout = layout }
    public func persist(_ context: M04ScanContext) throws { let data = try JSONEncoder().encode(context); try FileManager.default.createDirectory(at: layout.sessionRoot, withIntermediateDirectories: true); try data.write(to: layout.m04Context, options: .atomic) }
    public func load() throws -> M04ScanContext { try JSONDecoder().decode(M04ScanContext.self, from: Data(contentsOf: layout.m04Context)) }
}

public enum TransparentTreatmentMode: String, Codable, Sendable, Equatable, CaseIterable { case none, temporaryMatte, texturedInsert, preparedBackground }

public struct TransparentPreparationEvaluation: Codable, Sendable, Equatable {
    public let warningCodes: [String]
    public let acknowledgementRequired: Bool
    public let acknowledged: Bool
    public let treatment: TransparentTreatmentMode
    public let suitability: String
    public init(acknowledged: Bool, treatment: TransparentTreatmentMode) { self.warningCodes = ["transparent_reconstruction_unproven", "transparent_preparation_required"]; self.acknowledgementRequired = true; self.acknowledged = acknowledged; self.treatment = treatment; self.suitability = "warning_only_not_physically_verified" }
    public var mayStart: Bool { acknowledged && treatment != .none }
}

public enum AsymmetricCoverageRegion: String, Codable, Sendable, Equatable, CaseIterable { case front, back, left, right, handle, shoulder }

public struct AsymmetricCoveragePolicy: Codable, Sendable, Equatable {
    public let requiredRegions: [AsymmetricCoverageRegion]
    public let minimumSectorsPerRegion: Int
    public init(requiredRegions: [AsymmetricCoverageRegion] = [.front, .back, .left, .right, .handle], minimumSectorsPerRegion: Int = 1) { self.requiredRegions = requiredRegions; self.minimumSectorsPerRegion = max(1, minimumSectorsPerRegion) }
}

public struct AsymmetricCoverageEvaluation: Codable, Sendable, Equatable {
    public let observedRegions: [AsymmetricCoverageRegion: Int]
    public let missingRegions: [AsymmetricCoverageRegion]
    public let isComplete: Bool
    public let guidance: [String]
    public init(observedRegions: [AsymmetricCoverageRegion: Int], policy: AsymmetricCoveragePolicy = AsymmetricCoveragePolicy()) { self.observedRegions = observedRegions; missingRegions = policy.requiredRegions.filter { (observedRegions[$0] ?? 0) < policy.minimumSectorsPerRegion }; isComplete = missingRegions.isEmpty; guidance = missingRegions.map { "Capture \($0.rawValue) region evidence" } }
}

public enum CoverageEvidenceSource: String, Codable, Sendable, Equatable { case arWorldPose = "ar_world_pose", turntableAngle = "turntable_angle" }

public struct TurntablePolicy: Codable, Sendable, Equatable {
    public let expectedAngleCount: Int
    public init(expectedAngleCount: Int = 24) { self.expectedAngleCount = max(1, expectedAngleCount) }
}

public struct TurntableObservation: Codable, Sendable, Equatable {
    public let captureID: String
    public let normalizedAngle: Double
    public let sectorIndex: Int
    public let source: CoverageEvidenceSource
    public let status: String
}

public struct TurntableCoverageSnapshot: Codable, Sendable, Equatable {
    public let policy: TurntablePolicy
    public let capturedSectorIndices: [Int]
    public let missingSectorIndices: [Int]
    public let repeatedCaptureIDs: [String]
    public let observations: [TurntableObservation]
    public let isComplete: Bool
}

public struct TurntableCoverageModel: Sendable, Equatable {
    public let policy: TurntablePolicy
    private var captured: Set<Int> = []
    private var repeats: [String] = []
    private var observations: [TurntableObservation] = []
    public init(policy: TurntablePolicy = TurntablePolicy()) { self.policy = policy }
    public init(snapshot: TurntableCoverageSnapshot) { self.policy = snapshot.policy; self.captured = Set(snapshot.capturedSectorIndices); self.repeats = snapshot.repeatedCaptureIDs; self.observations = snapshot.observations }
    public func sectorIndex(for angleDegrees: Double) -> Int {
        let normalized = (angleDegrees.truncatingRemainder(dividingBy: 360) + 360).truncatingRemainder(dividingBy: 360)
        return min(policy.expectedAngleCount - 1, Int((normalized / 360) * Double(policy.expectedAngleCount)))
    }
    public func isSectorCaptured(angleDegrees: Double) -> Bool { captured.contains(sectorIndex(for: angleDegrees)) }
    public mutating func observe(captureID: String, angleDegrees: Double) -> TurntableObservation {
        let normalized = (angleDegrees.truncatingRemainder(dividingBy: 360) + 360).truncatingRemainder(dividingBy: 360)
        let index = sectorIndex(for: angleDegrees)
        let status = captured.contains(index) ? "repeated_angle" : "captured"
        if captured.contains(index) { repeats.append(captureID) } else { captured.insert(index) }
        let observation = TurntableObservation(captureID: captureID, normalizedAngle: normalized, sectorIndex: index, source: .turntableAngle, status: status); observations.append(observation); return observation
    }
    public func snapshot() -> TurntableCoverageSnapshot { let missing = (0..<policy.expectedAngleCount).filter { !captured.contains($0) }; return TurntableCoverageSnapshot(policy: policy, capturedSectorIndices: captured.sorted(), missingSectorIndices: missing, repeatedCaptureIDs: repeats, observations: observations, isComplete: missing.isEmpty) }
}

public struct CaptureProtocolSection: Sendable, Equatable, Identifiable {
    public let title: String
    public let lines: [String]
    public var id: String { title }
    public init(title: String, lines: [String]) { self.title = title; self.lines = lines }
}

public struct CaptureProtocolViewModel: Sendable {
    public let preset: PackagingPreset
    public let sections: [CaptureProtocolSection]
    public private(set) var acknowledgementGiven: Bool
    public init(preset: PackagingPreset, acknowledgementGiven: Bool = false) { self.preset = preset; self.acknowledgementGiven = acknowledgementGiven; sections = [CaptureProtocolSection(title: "Lighting", lines: preset.lightingGuidance), CaptureProtocolSection(title: "Background and reflections", lines: preset.preparationGuidance), CaptureProtocolSection(title: "Handling and working distance", lines: ["Keep the package stable and centered.", "Use the supported main camera and preserve safe margins."])] }
    public var acknowledgementRequired: Bool { preset.requiresPreparationAcknowledgement }
    public var canContinue: Bool { !acknowledgementRequired || acknowledgementGiven }
    public mutating func acknowledgePreparation() { acknowledgementGiven = true }
}

#if canImport(SwiftUI)
public struct CaptureProtocolView: View {
    public let preset: PackagingPreset
    public let onContinue: (Bool) -> Void
    @State private var acknowledged: Bool
    public init(preset: PackagingPreset, onContinue: @escaping (Bool) -> Void) { self.preset = preset; self.onContinue = onContinue; _acknowledged = State(initialValue: !preset.requiresPreparationAcknowledgement) }
    public var body: some View {
        Form {
            Text(preset.displayName).font(.headline)
            ForEach(CaptureProtocolViewModel(preset: preset).sections) { section in Section(section.title) { ForEach(section.lines, id: \.self) { Text($0) } } }
            if preset.requiresPreparationAcknowledgement { Toggle("I understand the preparation warnings", isOn: $acknowledged) }
            Button("Continue") { onContinue(acknowledged) }.disabled(preset.requiresPreparationAcknowledgement && !acknowledged)
        }.navigationTitle("Capture protocol")
    }
}
#endif

#if canImport(SwiftUI)
public struct CoverageGridView: View {
    public let model: CoverageViewModel
    public init(model: CoverageViewModel) { self.model = model }
    public var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(model.statusText).accessibilityAddTraits(.isHeader)
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 90))], spacing: 6) {
                ForEach(model.items) { item in
                    Text(item.label).font(.caption2).padding(6).frame(maxWidth: .infinity).background(color(for: item.status).opacity(0.2)).clipShape(RoundedRectangle(cornerRadius: 6)).accessibilityLabel(item.label)
                }
            }
        }.accessibilityElement(children: .contain).accessibilityLabel(model.accessibilityText)
    }
    private func color(for status: CoverageDisplayStatus) -> Color {
        switch status { case .captured: return .green; case .targeted: return .blue; case .missing: return .orange; case .unavailable: return .gray }
    }
}
#endif
