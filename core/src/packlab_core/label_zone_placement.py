"""Manual, revisioned Label Zone placement in canonical PackLab frames."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime

from .coordinate_frame import PACKLAB_NORMALIZED_FRAME
from .label_zone import LABEL_ZONE_CONTRACT, LabelZone, LabelZoneBoundary, LabelZoneKind

LABEL_ZONE_SURFACE_FRAME_CONTRACT = "packlab.label-zone-surface-frame.v1"
_REVISION_PREFIX = "label-zone-placement:"
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")


class LabelZonePlacementError(ValueError):
    """Raised when a placement edit is stale, invalid, or out of its surface domain."""


@dataclass(frozen=True, slots=True)
class LabelZoneSurfaceFrame:
    """Canonical normalized surface orientation for one front/back/wrap zone."""

    frame_id: str
    canonical_world_frame: str
    surface_normal: str
    u_axis: str
    v_axis: str
    seam_direction: str | None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "frame_id": self.frame_id,
            "canonical_world_frame": self.canonical_world_frame,
            "surface_normal": self.surface_normal,
            "u_axis": self.u_axis,
            "v_axis": self.v_axis,
            "seam_direction": self.seam_direction,
        }


def canonical_label_zone_surface_frame(zone_kind: LabelZoneKind) -> LabelZoneSurfaceFrame:
    """Return the frozen M14 orientation for a front, back, or wrap zone."""
    if not isinstance(zone_kind, LabelZoneKind):
        raise LabelZonePlacementError("label_zone_kind_invalid")
    common = {
        "canonical_world_frame": PACKLAB_NORMALIZED_FRAME,
        "v_axis": "+Z",
    }
    if zone_kind is LabelZoneKind.FRONT:
        return LabelZoneSurfaceFrame(
            frame_id=f"{LABEL_ZONE_SURFACE_FRAME_CONTRACT}:front",
            surface_normal="+Y",
            u_axis="+X",
            seam_direction=None,
            **common,
        )
    if zone_kind is LabelZoneKind.BACK:
        return LabelZoneSurfaceFrame(
            frame_id=f"{LABEL_ZONE_SURFACE_FRAME_CONTRACT}:back",
            surface_normal="-Y",
            u_axis="-X",
            seam_direction=None,
            **common,
        )
    return LabelZoneSurfaceFrame(
        frame_id=f"{LABEL_ZONE_SURFACE_FRAME_CONTRACT}:wrap",
        surface_normal="RADIAL_OUTWARD",
        u_axis="AZIMUTHAL_FROM_FRONT_TOWARD_RIGHT",
        seam_direction="+Y",
        **common,
    )


@dataclass(frozen=True, slots=True)
class LabelZonePlacementRevision:
    """Immutable placement snapshot; editing creates a deterministic successor."""

    revision_id: str
    label_zone: LabelZone
    boundary: LabelZoneBoundary
    surface_frame: LabelZoneSurfaceFrame
    previous_revision_id: str | None
    actor_id: str
    reason: str
    created_at_utc: str
    contract: str = "packlab.label-zone-placement-revision.v1"

    def __post_init__(self) -> None:
        if self.contract != "packlab.label-zone-placement-revision.v1":
            raise LabelZonePlacementError("label_zone_placement_contract_invalid")
        if not isinstance(self.label_zone, LabelZone):
            raise LabelZonePlacementError("label_zone_required")
        if not isinstance(self.boundary, LabelZoneBoundary):
            raise LabelZonePlacementError("label_zone_boundary_invalid")
        if not isinstance(self.surface_frame, LabelZoneSurfaceFrame):
            raise LabelZonePlacementError("label_zone_surface_frame_invalid")
        if self.surface_frame != canonical_label_zone_surface_frame(self.label_zone.zone_kind):
            raise LabelZonePlacementError("label_zone_surface_frame_kind_mismatch")
        if not isinstance(self.revision_id, str) or not _IDENTIFIER.fullmatch(self.revision_id):
            raise LabelZonePlacementError("label_zone_placement_revision_id_invalid")
        if self.previous_revision_id is not None and (
            not isinstance(self.previous_revision_id, str)
            or not _IDENTIFIER.fullmatch(self.previous_revision_id)
        ):
            raise LabelZonePlacementError("label_zone_previous_revision_id_invalid")
        if not isinstance(self.actor_id, str) or not _IDENTIFIER.fullmatch(self.actor_id):
            raise LabelZonePlacementError("label_zone_actor_id_invalid")
        if not isinstance(self.reason, str) or not self.reason.strip() or len(self.reason) > 1000:
            raise LabelZonePlacementError("label_zone_reason_invalid")
        if not isinstance(self.created_at_utc, str) or not self.created_at_utc.endswith("Z"):
            raise LabelZonePlacementError("label_zone_created_at_must_be_utc_z")
        try:
            parsed = datetime.fromisoformat(self.created_at_utc[:-1] + "+00:00")
        except ValueError as error:
            raise LabelZonePlacementError("label_zone_created_at_invalid") from error
        offset = parsed.utcoffset()
        if offset is None or offset.total_seconds() != 0:
            raise LabelZonePlacementError("label_zone_created_at_must_be_utc_z")
        if self.revision_id != _revision_id(_identity(self)):
            raise LabelZonePlacementError("label_zone_placement_revision_identity_mismatch")

    @property
    def zone_id(self) -> str:
        return self.label_zone.zone_id

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "DERIVED_LABEL_ZONE_PLACEMENT_INTENT",
            "revision_id": self.revision_id,
            "zone_id": self.zone_id,
            "zone_contract": LABEL_ZONE_CONTRACT,
            "zone_kind": self.label_zone.zone_kind.value,
            "source_design_model_revision_id": self.label_zone.source_design_model_revision_id,
            "source_brep_revision_id": self.label_zone.source_brep_revision_id,
            "source_brep_geometry_sha256": self.label_zone.source_brep_geometry_sha256,
            "parent_authority": {
                "kind": self.label_zone.parent_kind.value,
                "revision_id": self.label_zone.parent_authority_revision_id,
            },
            "scale_state": self.label_zone.scale_state.value,
            "coordinate_unit": self.label_zone.coordinate_unit,
            "component_id": self.label_zone.component_id,
            "feature_id": self.label_zone.feature_id,
            "surface_frame": self.surface_frame.as_dict(),
            "placement": {
                "coordinate_range": [0.0, 1.0],
                "coordinate_unit": "unitless_normalized",
                "boundary": self.boundary.as_dict(),
            },
            "previous_revision_id": self.previous_revision_id,
            "actor_id": self.actor_id,
            "reason": self.reason,
            "created_at_utc": self.created_at_utc,
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "physical_fit_inferred": False,
            "manufacturing_suitability_inferred": False,
            "mutates_source_geometry": False,
        }


def create_label_zone_placement_revision(
    label_zone: LabelZone,
    boundary: LabelZoneBoundary,
    *,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> LabelZonePlacementRevision:
    """Create the first manual placement snapshot for a zone."""
    return _create_revision(
        label_zone,
        boundary,
        previous_revision_id=None,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )


def edit_label_zone_placement(
    previous: LabelZonePlacementRevision,
    boundary: LabelZoneBoundary,
    *,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> LabelZonePlacementRevision:
    """Create an immutable successor placement while preserving the stable zone ID."""
    if not isinstance(previous, LabelZonePlacementRevision):
        raise LabelZonePlacementError("previous_label_zone_placement_revision_required")
    return _create_revision(
        previous.label_zone,
        boundary,
        previous_revision_id=previous.revision_id,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )


def _create_revision(
    label_zone: LabelZone,
    boundary: LabelZoneBoundary,
    *,
    previous_revision_id: str | None,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> LabelZonePlacementRevision:
    if not isinstance(label_zone, LabelZone):
        raise LabelZonePlacementError("label_zone_required")
    if not isinstance(boundary, LabelZoneBoundary):
        raise LabelZonePlacementError("label_zone_boundary_invalid")
    frame = canonical_label_zone_surface_frame(label_zone.zone_kind)
    values: dict[str, object] = {
        "contract": "packlab.label-zone-placement-revision.v1",
        "zone_id": label_zone.zone_id,
        "zone_kind": label_zone.zone_kind.value,
        "source_design_model_revision_id": label_zone.source_design_model_revision_id,
        "source_brep_revision_id": label_zone.source_brep_revision_id,
        "source_brep_geometry_sha256": label_zone.source_brep_geometry_sha256,
        "parent_kind": label_zone.parent_kind.value,
        "parent_authority_revision_id": label_zone.parent_authority_revision_id,
        "scale_state": label_zone.scale_state.value,
        "coordinate_unit": label_zone.coordinate_unit,
        "component_id": label_zone.component_id,
        "feature_id": label_zone.feature_id,
        "surface_frame": frame.as_dict(),
        "boundary": boundary.as_dict(),
        "previous_revision_id": previous_revision_id,
        "actor_id": actor_id,
        "reason": reason,
        "created_at_utc": created_at_utc,
    }
    revision_id = _revision_id(values)
    return LabelZonePlacementRevision(
        revision_id=revision_id,
        label_zone=label_zone,
        boundary=boundary,
        surface_frame=frame,
        previous_revision_id=previous_revision_id,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )


def _identity(revision: LabelZonePlacementRevision) -> dict[str, object]:
    return {
        "contract": revision.contract,
        "zone_id": revision.zone_id,
        "zone_kind": revision.label_zone.zone_kind.value,
        "source_design_model_revision_id": revision.label_zone.source_design_model_revision_id,
        "source_brep_revision_id": revision.label_zone.source_brep_revision_id,
        "source_brep_geometry_sha256": revision.label_zone.source_brep_geometry_sha256,
        "parent_kind": revision.label_zone.parent_kind.value,
        "parent_authority_revision_id": revision.label_zone.parent_authority_revision_id,
        "scale_state": revision.label_zone.scale_state.value,
        "coordinate_unit": revision.label_zone.coordinate_unit,
        "component_id": revision.label_zone.component_id,
        "feature_id": revision.label_zone.feature_id,
        "surface_frame": revision.surface_frame.as_dict(),
        "boundary": revision.boundary.as_dict(),
        "previous_revision_id": revision.previous_revision_id,
        "actor_id": revision.actor_id,
        "reason": revision.reason,
        "created_at_utc": revision.created_at_utc,
    }


def _revision_id(identity: dict[str, object]) -> str:
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return _REVISION_PREFIX + digest


__all__ = [
    "LABEL_ZONE_SURFACE_FRAME_CONTRACT",
    "LabelZonePlacementError",
    "LabelZonePlacementRevision",
    "LabelZoneSurfaceFrame",
    "canonical_label_zone_surface_frame",
    "create_label_zone_placement_revision",
    "edit_label_zone_placement",
]
