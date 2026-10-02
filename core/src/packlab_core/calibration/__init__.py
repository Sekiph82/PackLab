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
from .reconstruction_scale import (
    PhysicalMarkerReference,
    ReconstructedMarkerGeometry,
    ReconstructionScaleError,
    ReconstructionScaleEstimate,
    ReconstructionScaleObservation,
    estimate_reconstruction_scale,
)
from .scale_estimation import KnownMarkerObservation, ScaleEstimate, estimate_scale
from .scale_provenance import (
    ScalePromotionEvidence,
    ScaleProvenance,
    ScaleProvenanceError,
    VerifiedPhysicalReference,
    append_scale_provenance_revision,
    create_scale_provenance,
    promote_scale_provenance,
    serialize_scale_provenance,
)

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
    "PhysicalMarkerReference",
    "ReconstructedMarkerGeometry",
    "ReconstructionScaleError",
    "ReconstructionScaleEstimate",
    "ReconstructionScaleObservation",
    "ScaleEstimate",
    "ScalePromotionEvidence",
    "ScaleProvenance",
    "ScaleProvenanceError",
    "VerifiedPhysicalReference",
    "append_scale_provenance_revision",
    "check_profile_compatibility",
    "associate_marker_detections",
    "associated_observations_digest",
    "detect_markers",
    "estimate_scale",
    "estimate_reconstruction_scale",
    "create_scale_provenance",
    "promote_scale_provenance",
    "score_calibration_confidence",
    "serialize_associated_observations",
    "serialize_scale_provenance",
]
