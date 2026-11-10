"""Bounded planned azimuth density from digest-bound complexity inputs."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass

ADAPTIVE_ANGLE_PLAN_CONTRACT = "packlab.adaptive-angle-plan.v1"
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$", re.ASCII)
_SHA256 = re.compile(r"^[0-9a-f]{64}$", re.ASCII)
_MAX_SECTORS = 64
_MAX_ANGLES = 512


class AdaptiveAnglePlanError(ValueError):
    """Raised when geometry complexity inputs or their planned schedule are invalid."""


@dataclass(frozen=True, slots=True)
class AngularComplexityEvidence:
    sector_id: str
    start_degrees: float
    end_degrees: float
    normalized_complexity: float
    evidence_sha256: str

    def __post_init__(self) -> None:
        _identifier(self.sector_id, "sector_id")
        for name in ("start_degrees", "end_degrees", "normalized_complexity"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise AdaptiveAnglePlanError(f"{name}_invalid")
            object.__setattr__(self, name, float(value))
        if not 0.0 <= self.start_degrees < self.end_degrees <= 360.0:
            raise AdaptiveAnglePlanError("sector_interval_invalid")
        if not 0.0 <= self.normalized_complexity <= 1.0:
            raise AdaptiveAnglePlanError("normalized_complexity_out_of_range")
        _digest(self.evidence_sha256, "evidence_sha256")

    def as_dict(self) -> dict[str, object]:
        return {
            "sector_id": self.sector_id,
            "start_degrees": self.start_degrees,
            "end_degrees": self.end_degrees,
            "normalized_complexity": self.normalized_complexity,
            "evidence_sha256": self.evidence_sha256,
        }


@dataclass(frozen=True, slots=True)
class AdaptiveAngleDensityPolicy:
    minimum_angles_per_sector: int = 1
    maximum_angles_per_sector: int = 4
    maximum_sector_count: int = _MAX_SECTORS
    maximum_total_angles: int = _MAX_ANGLES

    def __post_init__(self) -> None:
        for name in (
            "minimum_angles_per_sector",
            "maximum_angles_per_sector",
            "maximum_sector_count",
            "maximum_total_angles",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise AdaptiveAnglePlanError(f"{name}_invalid")
        if self.minimum_angles_per_sector > self.maximum_angles_per_sector:
            raise AdaptiveAnglePlanError("angle_count_range_invalid")
        if self.maximum_sector_count > _MAX_SECTORS or self.maximum_total_angles > _MAX_ANGLES:
            raise AdaptiveAnglePlanError("policy_exceeds_hard_limit")
        if self.maximum_angles_per_sector > self.maximum_total_angles:
            raise AdaptiveAnglePlanError("per_sector_count_exceeds_total_limit")


@dataclass(frozen=True, slots=True)
class PlannedAzimuth:
    ordinal: int
    sector_id: str
    sector_angle_index: int
    angle_degrees: float
    evidence_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "sector_id": self.sector_id,
            "sector_angle_index": self.sector_angle_index,
            "planned_azimuth_degrees": self.angle_degrees,
            "angle_status": "PLANNED_NOT_OBSERVED",
            "evidence_sha256": self.evidence_sha256,
        }


@dataclass(frozen=True, slots=True)
class AdaptiveAnglePlan:
    plan_id: str
    geometry_revision_id: str
    geometry_sha256: str
    policy: AdaptiveAngleDensityPolicy
    sectors: tuple[AngularComplexityEvidence, ...]
    angles: tuple[PlannedAzimuth, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": ADAPTIVE_ANGLE_PLAN_CONTRACT,
            "plan_id": self.plan_id,
            "geometry_revision_id": self.geometry_revision_id,
            "geometry_sha256": self.geometry_sha256,
            "complexity_source": "CALLER_SUPPLIED_UNTRUSTED_NORMALIZED_SCORE",
            "policy": {
                "minimum_angles_per_sector": self.policy.minimum_angles_per_sector,
                "maximum_angles_per_sector": self.policy.maximum_angles_per_sector,
                "maximum_sector_count": self.policy.maximum_sector_count,
                "maximum_total_angles": self.policy.maximum_total_angles,
            },
            "sectors": [item.as_dict() for item in self.sectors],
            "angles": [item.as_dict() for item in self.angles],
            "authority_class": "ADAPTIVE_CAPTURE_PLAN_PROPOSAL",
            "generated": True,
            "accepted": False,
            "physical_angles_observed": False,
            "hardware_control_performed": False,
            "capture_performed": False,
            "scan_master_replaced": False,
        }


def plan_adaptive_angles(
    geometry_revision_id: str,
    geometry_sha256: str,
    sectors: tuple[AngularComplexityEvidence, ...],
    *,
    policy: AdaptiveAngleDensityPolicy = AdaptiveAngleDensityPolicy(),
) -> AdaptiveAnglePlan:
    """Allocate planned views by score; this does not calculate complexity or control devices."""

    _identifier(geometry_revision_id, "geometry_revision_id")
    _digest(geometry_sha256, "geometry_sha256")
    if not isinstance(policy, AdaptiveAngleDensityPolicy):
        raise AdaptiveAnglePlanError("policy_required")
    if (
        not isinstance(sectors, tuple)
        or not 1 <= len(sectors) <= min(policy.maximum_sector_count, _MAX_SECTORS)
        or any(not isinstance(item, AngularComplexityEvidence) for item in sectors)
    ):
        raise AdaptiveAnglePlanError("sector_evidence_invalid")
    if len({item.sector_id for item in sectors}) != len(sectors):
        raise AdaptiveAnglePlanError("sector_id_duplicate")
    if sectors[0].start_degrees != 0.0 or sectors[-1].end_degrees != 360.0:
        raise AdaptiveAnglePlanError("sector_coverage_must_span_zero_to_360")
    if any(left.end_degrees != right.start_degrees for left, right in zip(sectors, sectors[1:])):
        raise AdaptiveAnglePlanError("sector_coverage_gap_or_overlap")

    angles: list[PlannedAzimuth] = []
    count_span = policy.maximum_angles_per_sector - policy.minimum_angles_per_sector
    for sector in sectors:
        count = policy.minimum_angles_per_sector + math.floor(
            sector.normalized_complexity * count_span + 0.5
        )
        if len(angles) + count > min(policy.maximum_total_angles, _MAX_ANGLES):
            raise AdaptiveAnglePlanError("planned_angle_count_exceeds_limit")
        sector_width = sector.end_degrees - sector.start_degrees
        for sector_index in range(count):
            angle = sector.start_degrees + (sector_index + 0.5) * sector_width / count
            angles.append(
                PlannedAzimuth(
                    len(angles),
                    sector.sector_id,
                    sector_index,
                    round(angle, 9),
                    sector.evidence_sha256,
                )
            )
    identity = {
        "contract": ADAPTIVE_ANGLE_PLAN_CONTRACT,
        "geometry_revision_id": geometry_revision_id,
        "geometry_sha256": geometry_sha256,
        "policy": {
            "minimum_angles_per_sector": policy.minimum_angles_per_sector,
            "maximum_angles_per_sector": policy.maximum_angles_per_sector,
            "maximum_sector_count": policy.maximum_sector_count,
            "maximum_total_angles": policy.maximum_total_angles,
        },
        "sectors": [item.as_dict() for item in sectors],
        "angles": [item.as_dict() for item in angles],
    }
    plan_id = (
        "adaptive-angle-plan:"
        + hashlib.sha256(
            json.dumps(
                identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
            ).encode("ascii")
        ).hexdigest()
    )
    return AdaptiveAnglePlan(
        plan_id, geometry_revision_id, geometry_sha256, policy, sectors, tuple(angles)
    )


def _identifier(value: object, name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise AdaptiveAnglePlanError(f"{name}_invalid")


def _digest(value: object, name: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise AdaptiveAnglePlanError(f"{name}_invalid")


__all__ = [
    "ADAPTIVE_ANGLE_PLAN_CONTRACT",
    "AdaptiveAngleDensityPolicy",
    "AdaptiveAnglePlan",
    "AdaptiveAnglePlanError",
    "AngularComplexityEvidence",
    "PlannedAzimuth",
    "plan_adaptive_angles",
]
