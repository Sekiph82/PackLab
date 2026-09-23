"""OpenCV marker detection behind a PackLab-owned, scale-free API."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

CORNER_ORDER = "clockwise_from_top_left_image_coordinates"


class MarkerPolicyError(ValueError):
    """Raised when the PackLab marker policy cannot select an OpenCV dictionary."""


def _policy_path() -> Path:
    return (
        Path(__file__).resolve().parents[4]
        / "schemas"
        / "packscan"
        / ("calibration-marker-policy.json")
    )


def load_marker_policy(path: str | Path | None = None) -> dict[str, object]:
    """Load the PackLab-owned marker dictionary policy."""

    policy_path = Path(path) if path is not None else _policy_path()
    try:
        value = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MarkerPolicyError("marker_policy_unavailable") from error
    if not isinstance(value, dict):
        raise MarkerPolicyError("marker_policy_invalid")
    return value


def _policy_string(policy: Mapping[str, object], key: str) -> str:
    value = policy.get(key)
    if not isinstance(value, str) or not value:
        raise MarkerPolicyError(f"marker_policy_missing_{key}")
    return value


def _policy_dictionary_name(policy: Mapping[str, object]) -> str:
    return _policy_string(policy, "opencv_dictionary")


def _policy_version(policy: Mapping[str, object]) -> str:
    return _policy_string(policy, "policy_version")


def resolve_policy_dictionary(cv2_module: ModuleType | Any, policy: Mapping[str, object]) -> Any:
    """Resolve the policy dictionary to an OpenCV predefined dictionary."""

    dictionary_name = _policy_dictionary_name(policy)
    aruco = getattr(cv2_module, "aruco", None)
    if aruco is None or not hasattr(aruco, dictionary_name):
        raise MarkerPolicyError(f"unsupported_marker_dictionary:{dictionary_name}")
    return aruco.getPredefinedDictionary(getattr(aruco, dictionary_name))


_DEFAULT_POLICY = load_marker_policy()
DICTIONARY_NAME = _policy_dictionary_name(_DEFAULT_POLICY)
DICTIONARY_POLICY_VERSION = _policy_version(_DEFAULT_POLICY)


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
        policy = load_marker_policy()
        dictionary = resolve_policy_dictionary(cv2, policy)
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
    except MarkerPolicyError as error:
        return DetectionBatch("unavailable", (), (str(error),), _provenance())
    except (AttributeError, cv2.error, TypeError, ValueError):
        return DetectionBatch("invalid_input", (), ("opencv_detection_failed",), _provenance())
    if raw_ids is None or len(raw_ids) == 0:
        return DetectionBatch("no_markers", (), (), _provenance())

    duplicate_result = _duplicate_marker_result(raw_ids)
    if duplicate_result is not None:
        return duplicate_result
    ids = _raw_marker_ids(raw_ids)
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


def _raw_marker_ids(raw_ids: Any) -> tuple[int, ...]:
    if hasattr(raw_ids, "reshape"):
        return tuple(int(value) for value in raw_ids.reshape(-1))
    return tuple(
        int(value) for row in raw_ids for value in (row if isinstance(row, list) else [row])
    )


def _duplicate_marker_result(raw_ids: Any) -> DetectionBatch | None:
    ids = _raw_marker_ids(raw_ids)
    if len(set(ids)) != len(ids):
        return DetectionBatch("invalid", (), ("duplicate_marker_id",), _provenance())
    return None


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
