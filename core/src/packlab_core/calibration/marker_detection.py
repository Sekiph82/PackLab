"""OpenCV marker detection behind a PackLab-owned, scale-free API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DICTIONARY_NAME = "DICT_APRILTAG_36h11"
DICTIONARY_POLICY_VERSION = "1.0.0"
CORNER_ORDER = "clockwise_from_top_left_image_coordinates"


@dataclass(frozen=True)
class MarkerObservation:
    """One detected marker in image pixels; no real-world dimension is inferred."""

    marker_id: int
    corners_px: tuple[
        tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]
    ]
    quality: dict[str, object]
    provenance: dict[str, str]


@dataclass(frozen=True)
class DetectionBatch:
    """Detection result that keeps malformed/duplicate input non-fatal."""

    status: str
    observations: tuple[MarkerObservation, ...]
    errors: tuple[str, ...]
    provenance: dict[str, str]


def detect_markers(image: Any) -> DetectionBatch:
    """Detect and deterministically refine AprilTag markers in a uint8 image.

    Supported inputs are non-empty grayscale or 1/3-channel uint8 arrays. The
    result contains ordered pixel corners and geometry quality metadata only;
    it deliberately contains no millimetre, scale, distance, or pose field.
    """

    shape = getattr(image, "shape", None)
    dtype = str(getattr(image, "dtype", ""))
    if not _supported_image(shape, dtype):
        return DetectionBatch(
            "invalid_input", (), ("unsupported_image_shape_or_dtype",), _provenance()
        )
    try:
        import cv2
    except ImportError:
        return DetectionBatch("unavailable", (), ("opencv_unavailable",), _provenance())
    try:
        gray = image if len(shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
        parameters = cv2.aruco.DetectorParameters()
        if hasattr(parameters, "cornerRefinementMethod") and hasattr(
            cv2.aruco, "CORNER_REFINE_APRILTAG"
        ):
            parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_APRILTAG
        if hasattr(cv2.aruco, "ArucoDetector"):
            detector = cv2.aruco.ArucoDetector(dictionary, parameters)
            raw_corners, raw_ids, _ = detector.detectMarkers(gray)
        else:
            raw_corners, raw_ids, _ = cv2.aruco.detectMarkers(
                gray, dictionary, parameters=parameters
            )
    except (AttributeError, cv2.error, TypeError, ValueError):
        return DetectionBatch("invalid_input", (), ("opencv_detection_failed",), _provenance())
    if raw_ids is None or len(raw_ids) == 0:
        return DetectionBatch("no_markers", (), (), _provenance())

    ids = [int(value) for value in raw_ids.reshape(-1)]
    if len(set(ids)) != len(ids):
        return DetectionBatch("invalid", (), ("duplicate_marker_id",), _provenance())
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.001)
    observations: list[MarkerObservation] = []
    height, width = int(shape[0]), int(shape[1])
    for marker_id, raw in zip(ids, raw_corners, strict=True):
        try:
            refined = cv2.cornerSubPix(gray, raw.astype("float32"), (5, 5), (-1, -1), criteria)
            points = [(float(point[0]), float(point[1])) for point in refined.reshape(4, 2)]
            corners = _ordered_corners(points)
        except (AttributeError, cv2.error, TypeError, ValueError):
            return DetectionBatch("invalid", (), ("malformed_marker_corners",), _provenance())
        area = abs(_polygon_area(corners))
        score = min(1.0, max(0.0, area / max(1.0, float(width * height)) * 100.0))
        observations.append(
            MarkerObservation(
                marker_id,
                corners,
                {
                    "quality_label": "detected_geometry",
                    "quality_score": round(score, 6),
                    "image_area_px": area,
                    "corner_refinement": "cornerSubPix_fixed_5x5_eps_0.001_30_iterations",
                    "confidence_semantics": "geometry_quality_not_detection_probability",
                },
                _provenance(),
            )
        )
    return DetectionBatch("detected", tuple(observations), (), _provenance())


def _supported_image(shape: Any, dtype: str) -> bool:
    if dtype != "uint8" or not isinstance(shape, tuple) or len(shape) not in {2, 3}:
        return False
    if shape[0] <= 0 or shape[1] <= 0:
        return False
    return len(shape) == 2 or shape[2] in {1, 3}


def _ordered_corners(
    points: list[tuple[float, float]],
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]:
    start = min(range(4), key=lambda index: (points[index][1], points[index][0]))
    ordered = [points[(start + offset) % 4] for offset in range(4)]
    if _polygon_area(ordered) < 0:
        ordered = [ordered[0], ordered[3], ordered[2], ordered[1]]
    return tuple(ordered)  # type: ignore[return-value]


def _polygon_area(points: list[tuple[float, float]] | tuple[tuple[float, float], ...]) -> float:
    return 0.5 * sum(
        points[index][0] * points[(index + 1) % 4][1]
        - points[(index + 1) % 4][0] * points[index][1]
        for index in range(4)
    )


def _provenance() -> dict[str, str]:
    return {
        "detector": "opencv.aruco",
        "dictionary": DICTIONARY_NAME,
        "policy_version": DICTIONARY_POLICY_VERSION,
        "coordinate_unit": "image_pixels",
    }
