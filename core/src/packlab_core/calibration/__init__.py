"""PackLab calibration services with device-independent boundaries."""

from .confidence import CalibrationConfidence, score_calibration_confidence
from .marker_association import (
    AssociatedMarkerObservation,
    CameraImageBinding,
    MarkerAssociationError,
    associate_marker_detections,
    associated_observations_digest,
    serialize_associated_observations,
)
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
    "AssociatedMarkerObservation",
    "CalibrationProfile",
    "CalibrationProfileKey",
    "CalibrationQualityEvidence",
    "CaptureProfileRequest",
    "CameraImageBinding",
    "DICTIONARY_NAME",
    "DetectionBatch",
    "KnownMarkerObservation",
    "MarkerObservation",
    "MarkerAssociationError",
    "ProfileCompatibilityResult",
    "ScaleEstimate",
    "check_profile_compatibility",
    "associate_marker_detections",
    "associated_observations_digest",
    "detect_markers",
    "estimate_scale",
    "score_calibration_confidence",
    "serialize_associated_observations",
]
