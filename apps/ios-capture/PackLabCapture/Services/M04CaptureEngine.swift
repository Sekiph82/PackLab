import Foundation

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
        let band: SharpnessBand = variance >= thresholds.acceptMinimum ? .accept : (variance >= thresholds.warnMinimum ? .warn : .reject)
        return SharpnessMetric(availability: .available, normalizedLaplacianVariance: variance, sampleCount: responses.count, band: band, reasonCode: "sharpness_(band.rawValue)")
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
            return MotionBlurAssessment(risk: imageBlurred ? .warning : .unavailable, availability: motion.status == "stale" ? .stale : .unavailable, rotationRateMagnitude: nil, reasons: imageBlurred ? ["image_blur_motion_stale"] : ["motion_(motion.status)"])
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
        let band: ClippingBand = selectedFraction >= thresholds.rejectFraction ? .reject : (selectedFraction > thresholds.toleratedFraction ? .warn : .pass)
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
        else if metrics.highlightClipping.band == .warn || (metrics.highlightClipping.band == .unavailable && !policy.rejectUnavailableClipping) { warnings.append(contentsOf: metrics.highlightClipping.reasons) }
        if metrics.shadowClipping.band == .reject { hard.append(contentsOf: metrics.shadowClipping.reasons.filter { $0.hasSuffix("_reject") }) }
        else if metrics.shadowClipping.band == .warn || (metrics.shadowClipping.band == .unavailable && !policy.rejectUnavailableClipping) { warnings.append(contentsOf: metrics.shadowClipping.reasons) }
        if metrics.framing.band == .tooSmall || metrics.framing.band == .cropped || (metrics.framing.band == .unavailable && policy.rejectUnavailableFraming) { hard.append(contentsOf: metrics.framing.reasons) }
        if metrics.background.band == .warning || metrics.background.band == .unavailable { warnings.append(contentsOf: metrics.background.reasons) }
        func unique(_ values: [String]) -> [String] { var seen = Set<String>(); return values.filter { seen.insert($0).inserted } }
        let uniqueHard = unique(hard)
        let uniqueWarnings = unique(warnings)
        return QualityDecision(decision: uniqueHard.isEmpty ? .accept : .reject, reasons: uniqueHard, warnings: uniqueWarnings, metrics: metrics)
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
    public init(sessionID: String, captureID: String, sequence: Int, monotonicTimestamp: TimeInterval, decision: QualityDecision) {
        self.sessionID = QualityLogSanitizer.identifier(sessionID)
        self.captureID = QualityLogSanitizer.identifier(captureID)
        self.sequence = max(0, sequence)
        self.monotonicTimestamp = monotonicTimestamp.isFinite ? monotonicTimestamp : 0
        self.decision = decision.decision
        self.reasons = Array(decision.reasons.prefix(32)).map(QualityLogSanitizer.reason)
        self.warnings = Array(decision.warnings.prefix(32)).map(QualityLogSanitizer.reason)
        self.metrics = decision.metrics
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
    public mutating func observe(captureID: String, pose: PoseSample?) -> CoveragePoseObservation {
        let observation = CoveragePoseMapper.map(captureID: captureID, pose: pose, configuration: configuration); recordedObservations.append(observation)
        guard let sector = observation.sector, observation.status == "available" else { invalidIDs.append(captureID); return observation }
        if captured.contains(sector) { duplicateIDs.append(captureID) } else { captured.insert(sector) }
        return observation
    }
    public func snapshot() -> OrbitCoverageSnapshot {
        let all = configuration.rings.flatMap { ring in (0..<configuration.azimuthBinCount).map { CoverageSector(ringID: ring.id, azimuthIndex: $0) } }
        return OrbitCoverageSnapshot(configuration: configuration, capturedSectors: all.filter { captured.contains($0) }, missingSectors: all.filter { !captured.contains($0) }, duplicateCaptureIDs: duplicateIDs, invalidCaptureIDs: invalidIDs, observations: recordedObservations)
    }
}
