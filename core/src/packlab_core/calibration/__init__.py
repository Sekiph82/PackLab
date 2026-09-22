"""PackLab calibration services with device-independent boundaries."""

from .confidence import CalibrationConfidence, score_calibration_confidence
from .marker_detection import (
    DICTIONARY_NAME,
    DetectionBatch,
    MarkerObservation,
    detect_markers,
)
from .profile import (
    CalibrationProfile,
    CalibrationProfileKey,
    CalibrationQualityEvidence,
    CaptureProfileRequest,
    ProfileCompatibilityResult,
    check_profile_compatibility,
)
from .scale_estimation import KnownMarkerObservation, ScaleEstimate, estimate_scale

__all__ = [
    "CalibrationConfidence",
    "CalibrationProfile",
    "CalibrationProfileKey",
    "CalibrationQualityEvidence",
    "CaptureProfileRequest",
    "DICTIONARY_NAME",
    "DetectionBatch",
    "KnownMarkerObservation",
    "MarkerObservation",
    "ProfileCompatibilityResult",
    "ScaleEstimate",
    "check_profile_compatibility",
    "detect_markers",
    "estimate_scale",
    "score_calibration_confidence",
]
