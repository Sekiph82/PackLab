"""Declarative multi-ring capture plans; no camera or turntable control."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

MULTI_RING_CAPTURE_RECIPE_CONTRACT = "packlab.multi-ring-capture-recipe.v1"
_MAX_RINGS = 32
_MAX_AZIMUTHS_PER_RING = 128
_MAX_POSES = 512


class MultiRingCaptureRecipeError(ValueError):
    """Raised when a declarative capture recipe exceeds its safe contract."""


@dataclass(frozen=True, slots=True)
class PlannedCapturePose:
    pose_id: str
    ordinal: int
    ring_index: int
    object_height_fraction: float
    azimuth_index: int
    planned_azimuth_degrees: float

    def as_dict(self) -> dict[str, object]:
        return {
            "pose_id": self.pose_id,
            "ordinal": self.ordinal,
            "ring_index": self.ring_index,
            "object_height_fraction": self.object_height_fraction,
            "azimuth_index": self.azimuth_index,
            "planned_azimuth_degrees": self.planned_azimuth_degrees,
            "angle_status": "PLANNED_NOT_OBSERVED",
            "capture_status": "NOT_CAPTURED",
        }


@dataclass(frozen=True, slots=True)
class MultiRingCaptureRecipe:
    recipe_id: str
    ring_elevation_fractions: tuple[float, ...]
    azimuths_per_ring: int
    starting_angle_degrees: float = 0.0
    alternate_half_step: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.ring_elevation_fractions, tuple) or not (
            1 <= len(self.ring_elevation_fractions) <= _MAX_RINGS
        ):
            raise MultiRingCaptureRecipeError("ring_count_out_of_bounds")
        normalized: list[float] = []
        for fraction in self.ring_elevation_fractions:
            if (
                isinstance(fraction, bool)
                or not isinstance(fraction, (int, float))
                or not math.isfinite(fraction)
                or not 0.0 <= fraction <= 1.0
            ):
                raise MultiRingCaptureRecipeError("ring_elevation_fraction_invalid")
            normalized.append(float(fraction))
        if any(left >= right for left, right in zip(normalized, normalized[1:])):
            raise MultiRingCaptureRecipeError("ring_elevations_not_strictly_increasing")
        object.__setattr__(self, "ring_elevation_fractions", tuple(normalized))
        if (
            isinstance(self.azimuths_per_ring, bool)
            or not isinstance(self.azimuths_per_ring, int)
            or not 3 <= self.azimuths_per_ring <= _MAX_AZIMUTHS_PER_RING
        ):
            raise MultiRingCaptureRecipeError("azimuth_count_out_of_bounds")
        if len(normalized) * self.azimuths_per_ring > _MAX_POSES:
            raise MultiRingCaptureRecipeError("total_pose_count_exceeds_limit")
        if (
            isinstance(self.starting_angle_degrees, bool)
            or not isinstance(self.starting_angle_degrees, (int, float))
            or not math.isfinite(self.starting_angle_degrees)
        ):
            raise MultiRingCaptureRecipeError("starting_angle_invalid")
        object.__setattr__(
            self, "starting_angle_degrees", float(self.starting_angle_degrees) % 360.0
        )
        if not isinstance(self.alternate_half_step, bool):
            raise MultiRingCaptureRecipeError("alternate_half_step_invalid")
        expected_id = "multi-ring-recipe:" + _digest(self._identity())
        if self.recipe_id != expected_id:
            raise MultiRingCaptureRecipeError("recipe_identity_mismatch")

    @classmethod
    def create(
        cls,
        ring_elevation_fractions: tuple[float, ...],
        azimuths_per_ring: int,
        *,
        starting_angle_degrees: float = 0.0,
        alternate_half_step: bool = True,
    ) -> MultiRingCaptureRecipe:
        if (
            isinstance(starting_angle_degrees, bool)
            or not isinstance(starting_angle_degrees, (int, float))
            or not math.isfinite(starting_angle_degrees)
        ):
            raise MultiRingCaptureRecipeError("starting_angle_invalid")
        normalized_start = float(starting_angle_degrees) % 360.0
        identity = {
            "contract": MULTI_RING_CAPTURE_RECIPE_CONTRACT,
            "ring_elevation_fractions": [float(value) for value in ring_elevation_fractions],
            "azimuths_per_ring": azimuths_per_ring,
            "starting_angle_degrees": normalized_start,
            "alternate_half_step": alternate_half_step,
        }
        return cls(
            "multi-ring-recipe:" + _digest(identity),
            ring_elevation_fractions,
            azimuths_per_ring,
            normalized_start,
            alternate_half_step,
        )

    @property
    def pose_count(self) -> int:
        return len(self.ring_elevation_fractions) * self.azimuths_per_ring

    def _identity(self) -> dict[str, object]:
        return {
            "contract": MULTI_RING_CAPTURE_RECIPE_CONTRACT,
            "ring_elevation_fractions": list(self.ring_elevation_fractions),
            "azimuths_per_ring": self.azimuths_per_ring,
            "starting_angle_degrees": self.starting_angle_degrees,
            "alternate_half_step": self.alternate_half_step,
        }

    def schedule(self) -> tuple[PlannedCapturePose, ...]:
        poses: list[PlannedCapturePose] = []
        step = 360.0 / self.azimuths_per_ring
        for ring_index, elevation in enumerate(self.ring_elevation_fractions):
            ring_offset = step / 2.0 if self.alternate_half_step and ring_index % 2 else 0.0
            for azimuth_index in range(self.azimuths_per_ring):
                ordinal = len(poses)
                angle = (self.starting_angle_degrees + ring_offset + step * azimuth_index) % 360.0
                pose_identity = f"{self.recipe_id}:{ordinal}:{ring_index}:{azimuth_index}"
                pose_id = (
                    "capture-pose:" + hashlib.sha256(pose_identity.encode("ascii")).hexdigest()
                )
                poses.append(
                    PlannedCapturePose(
                        pose_id,
                        ordinal,
                        ring_index,
                        elevation,
                        azimuth_index,
                        round(angle, 9),
                    )
                )
        return tuple(poses)

    def as_dict(self) -> dict[str, object]:
        return {
            **self._identity(),
            "recipe_id": self.recipe_id,
            "pose_count": self.pose_count,
            "poses": [pose.as_dict() for pose in self.schedule()],
            "authority_class": "PLANNED_CAPTURE_RECIPE",
            "physical_angles_observed": False,
            "capture_performed": False,
            "calibration_performed": False,
            "hardware_control_performed": False,
            "scan_master_replaced": False,
        }


def _digest(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


__all__ = [
    "MULTI_RING_CAPTURE_RECIPE_CONTRACT",
    "MultiRingCaptureRecipe",
    "MultiRingCaptureRecipeError",
    "PlannedCapturePose",
]
