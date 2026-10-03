"""Deterministic, unit-aware 2D profile splines owned by PackLab."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .reconstruction import ScaleState

MAX_PROFILE_CONTROL_POINTS = 4096
MAX_PROFILE_SAMPLES = 4096
_PROFILE_PREFIX = "design-profile:"


class DesignProfileError(ValueError):
    """Raised when a profile is invalid or evaluated outside its bounded domain."""


@dataclass(frozen=True, slots=True)
class ProfilePoint:
    """One ordered axial/radial control point; tangent is d(radius)/d(axial)."""

    axial: float
    radius: float
    tangent: float | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(self.axial) or not math.isfinite(self.radius):
            raise DesignProfileError("profile_coordinates_must_be_finite")
        if self.radius < 0:
            raise DesignProfileError("profile_radius_must_be_nonnegative")
        if self.tangent is not None and not math.isfinite(self.tangent):
            raise DesignProfileError("profile_tangent_must_be_finite")


@dataclass(frozen=True, slots=True)
class ProfileSample:
    axial: float
    radius: float
    parameter: float


@dataclass(frozen=True, slots=True)
class DesignProfile:
    """Immutable piecewise cubic Hermite profile with a normalized bounded parameter."""

    profile_id: str
    points: tuple[ProfilePoint, ...]
    scale_state: ScaleState
    coordinate_unit: str

    def __post_init__(self) -> None:
        if not isinstance(self.points, tuple) or any(
            not isinstance(point, ProfilePoint) for point in self.points
        ):
            raise DesignProfileError("profile_points_must_be_immutable_tuple")
        if len(self.points) < 2:
            raise DesignProfileError("profile_requires_two_control_points")
        if len(self.points) > MAX_PROFILE_CONTROL_POINTS:
            raise DesignProfileError("profile_control_point_limit_exceeded")
        if not isinstance(self.scale_state, ScaleState) or self.scale_state not in {
            ScaleState.RELATIVE,
            ScaleState.METRIC_UNVERIFIED,
        }:
            raise DesignProfileError("profile_scale_state_unauthorized")
        expected_unit = (
            "reconstruction_units" if self.scale_state is ScaleState.RELATIVE else "mm_unverified"
        )
        if self.coordinate_unit != expected_unit:
            raise DesignProfileError("profile_coordinate_unit_mismatch")
        if any(right.axial <= left.axial for left, right in zip(self.points, self.points[1:])):
            raise DesignProfileError("profile_axial_points_must_be_strictly_increasing")
        if self.profile_id != _profile_id(self.points, self.scale_state, self.coordinate_unit):
            raise DesignProfileError("profile_id_mismatch")

    @property
    def domain(self) -> tuple[float, float]:
        return (self.points[0].axial, self.points[-1].axial)

    def evaluate_parameter(self, parameter: float) -> ProfileSample:
        """Evaluate a strictly bounded normalized parameter in [0, 1]."""
        if not math.isfinite(parameter) or not 0.0 <= parameter <= 1.0:
            raise DesignProfileError("profile_parameter_out_of_range")
        start, end = self.domain
        return self.evaluate(start + parameter * (end - start), parameter=parameter)

    def evaluate(self, axial: float, *, parameter: float | None = None) -> ProfileSample:
        """Evaluate with piecewise cubic Hermite interpolation and no extrapolation."""
        if not math.isfinite(axial):
            raise DesignProfileError("profile_coordinate_must_be_finite")
        start, end = self.domain
        if axial < start or axial > end:
            raise DesignProfileError("profile_coordinate_out_of_range")
        if axial == end:
            segment_index = len(self.points) - 2
        else:
            segment_index = next(
                index
                for index, point in enumerate(self.points[:-1])
                if point.axial <= axial < self.points[index + 1].axial
            )
        left = self.points[segment_index]
        right = self.points[segment_index + 1]
        width = right.axial - left.axial
        t = (axial - left.axial) / width
        left_tangent = self._tangent(segment_index)
        right_tangent = self._tangent(segment_index + 1)
        t2 = t * t
        t3 = t2 * t
        radius = (
            (2 * t3 - 3 * t2 + 1) * left.radius
            + (t3 - 2 * t2 + t) * width * left_tangent
            + (-2 * t3 + 3 * t2) * right.radius
            + (t3 - t2) * width * right_tangent
        )
        if not math.isfinite(radius) or radius < 0:
            raise DesignProfileError("profile_interpolation_invalid_radius")
        normalized = (axial - start) / (end - start) if parameter is None else parameter
        return ProfileSample(axial, radius, normalized)

    def sample(self, count: int) -> tuple[ProfileSample, ...]:
        """Return deterministic, endpoint-inclusive samples under a fixed count bound."""
        if isinstance(count, bool) or not isinstance(count, int):
            raise DesignProfileError("profile_sample_count_invalid")
        if not 2 <= count <= MAX_PROFILE_SAMPLES:
            raise DesignProfileError("profile_sample_count_out_of_range")
        return tuple(self.evaluate_parameter(index / (count - 1)) for index in range(count))

    def _tangent(self, index: int) -> float:
        point = self.points[index]
        if point.tangent is not None:
            return point.tangent
        if index == 0:
            left, right = self.points[0], self.points[1]
        elif index == len(self.points) - 1:
            left, right = self.points[-2], self.points[-1]
        else:
            left, right = self.points[index - 1], self.points[index + 1]
        return (right.radius - left.radius) / (right.axial - left.axial)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.design-profile.v1",
            "profile_id": self.profile_id,
            "interpolation": "piecewise-cubic-hermite-v1",
            "point_order": "strictly-increasing-axial-coordinate",
            "endpoint_policy": "exact-control-point-value; no-extrapolation",
            "tangent_policy": "explicit-drdz-or-one-sided/centered-secant",
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "control_points": [
                {"axial": point.axial, "radius": point.radius, "tangent": point.tangent}
                for point in self.points
            ],
        }


def create_design_profile(
    points: tuple[ProfilePoint, ...], scale_state: ScaleState
) -> DesignProfile:
    """Create a deterministically identified profile using inherited scale semantics."""
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    ordered = points
    profile_id = _profile_id(ordered, scale_state, unit)
    return DesignProfile(profile_id, ordered, scale_state, unit)


def _profile_id(
    points: tuple[ProfilePoint, ...], scale_state: ScaleState, coordinate_unit: str
) -> str:
    payload = {
        "contract": "packlab.design-profile.v1",
        "scale_state": scale_state.value,
        "coordinate_unit": coordinate_unit,
        "points": [
            {"axial": point.axial, "radius": point.radius, "tangent": point.tangent}
            for point in points
        ],
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return _PROFILE_PREFIX + digest


__all__ = [
    "DesignProfile",
    "DesignProfileError",
    "ProfilePoint",
    "ProfileSample",
    "create_design_profile",
]
