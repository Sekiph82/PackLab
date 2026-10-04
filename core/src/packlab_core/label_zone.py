"""Immutable geometric label-zone intent, independent of artwork assets."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum

from .cad_brep import CadBrepRepresentationRevision
from .design_model import (
    DesignModelError,
    DesignModelParentKind,
    DesignModelRevision,
    resolve_design_model_feature,
)
from .reconstruction import ScaleState

LABEL_ZONE_CONTRACT = "packlab.label-zone.v1"
_ZONE_ID_PREFIX = "label-zone:"
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,255}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class LabelZoneError(ValueError):
    """Raised when label-zone placement lacks current source authority."""


class LabelZoneKind(StrEnum):
    FRONT = "front"
    BACK = "back"
    WRAP = "wrap"


@dataclass(frozen=True, slots=True)
class LabelZoneBoundary:
    """A non-empty rectangle in normalized feature-local UV coordinates."""

    u_min: float
    v_min: float
    u_max: float
    v_max: float

    def __post_init__(self) -> None:
        values = (self.u_min, self.v_min, self.u_max, self.v_max)
        names = ("u_min", "v_min", "u_max", "v_max")
        for name, value in zip(names, values, strict=True):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise LabelZoneError(f"label_zone_{name}_must_be_finite_number")
            try:
                normalized = float(value)
            except OverflowError as error:
                raise LabelZoneError(f"label_zone_{name}_must_be_finite_number") from error
            if not math.isfinite(normalized):
                raise LabelZoneError(f"label_zone_{name}_must_be_finite_number")
            object.__setattr__(self, name, normalized)
        if not (0.0 <= self.u_min < self.u_max <= 1.0):
            raise LabelZoneError("label_zone_u_bounds_invalid")
        if not (0.0 <= self.v_min < self.v_max <= 1.0):
            raise LabelZoneError("label_zone_v_bounds_invalid")

    def as_dict(self) -> dict[str, float]:
        return {
            "u_min": self.u_min,
            "v_min": self.v_min,
            "u_max": self.u_max,
            "v_max": self.v_max,
        }


@dataclass(frozen=True, slots=True)
class LabelZone:
    """One immutable label placement intent pinned to exact model and CAD revisions."""

    zone_id: str
    zone_kind: LabelZoneKind
    source_design_model_revision_id: str
    source_brep_revision_id: str
    source_brep_geometry_sha256: str
    parent_kind: DesignModelParentKind
    parent_authority_revision_id: str
    scale_state: ScaleState
    coordinate_unit: str
    component_id: str
    feature_id: str
    boundary: LabelZoneBoundary
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    contract: str = LABEL_ZONE_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != LABEL_ZONE_CONTRACT:
            raise LabelZoneError("label_zone_contract_invalid")
        if not isinstance(self.zone_kind, LabelZoneKind):
            raise LabelZoneError("label_zone_kind_invalid")
        if not isinstance(self.parent_kind, DesignModelParentKind):
            raise LabelZoneError("label_zone_parent_kind_invalid")
        if not isinstance(self.scale_state, ScaleState) or self.scale_state not in {
            ScaleState.RELATIVE,
            ScaleState.METRIC_UNVERIFIED,
        }:
            raise LabelZoneError("label_zone_scale_state_invalid")
        expected_unit = (
            "reconstruction_units" if self.scale_state is ScaleState.RELATIVE else "mm_unverified"
        )
        if self.coordinate_unit != expected_unit:
            raise LabelZoneError("label_zone_coordinate_unit_mismatch")
        for name in (
            "zone_id",
            "source_design_model_revision_id",
            "source_brep_revision_id",
            "parent_authority_revision_id",
            "component_id",
            "feature_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
                raise LabelZoneError(f"label_zone_{name}_invalid")
        if not isinstance(self.source_brep_geometry_sha256, str) or not _SHA256.fullmatch(
            self.source_brep_geometry_sha256
        ):
            raise LabelZoneError("label_zone_brep_digest_invalid")
        if not isinstance(self.boundary, LabelZoneBoundary):
            raise LabelZoneError("label_zone_boundary_invalid")
        if self.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION":
            raise LabelZoneError("label_zone_physical_validation_must_remain_deferred")
        if self.mold_use_authorized is not False:
            raise LabelZoneError("label_zone_mold_use_forbidden")
        if self.zone_id != _zone_id(_identity(self)):
            raise LabelZoneError("label_zone_identity_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "DERIVED_LABEL_ZONE_DESIGN_INTENT",
            "zone_id": self.zone_id,
            "zone_kind": self.zone_kind.value,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_cad_brep": {
                "revision_id": self.source_brep_revision_id,
                "geometry_sha256": self.source_brep_geometry_sha256,
            },
            "parent_authority": {
                "kind": self.parent_kind.value,
                "revision_id": self.parent_authority_revision_id,
            },
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "component_id": self.component_id,
            "feature_id": self.feature_id,
            "placement": {
                "coordinate_frame": "FEATURE_NORMALIZED_UV",
                "coordinate_range": [0.0, 1.0],
                "coordinate_unit": "unitless_normalized",
                "boundary": self.boundary.as_dict(),
            },
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "artwork_bytes_included": False,
            "artwork_affects_identity": False,
            "physical_fit_inferred": False,
            "manufacturing_suitability_inferred": False,
        }


def create_label_zone(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    *,
    zone_kind: LabelZoneKind,
    component_id: str,
    feature_id: str,
    boundary: LabelZoneBoundary,
) -> LabelZone:
    """Create a deterministic label zone from exact model/BREP and feature ancestry."""
    if not isinstance(model, DesignModelRevision):
        raise LabelZoneError("label_zone_design_model_revision_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise LabelZoneError("label_zone_cad_brep_representation_required")
    if not isinstance(zone_kind, LabelZoneKind):
        raise LabelZoneError("label_zone_kind_invalid")
    if not isinstance(boundary, LabelZoneBoundary):
        raise LabelZoneError("label_zone_boundary_invalid")
    if not isinstance(component_id, str) or not _IDENTIFIER.fullmatch(component_id):
        raise LabelZoneError("label_zone_component_id_invalid")
    if not isinstance(feature_id, str) or not _IDENTIFIER.fullmatch(feature_id):
        raise LabelZoneError("label_zone_feature_id_invalid")

    parent_revision_id = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if parent_revision_id is None:
        raise LabelZoneError("label_zone_parent_authority_missing")
    if (
        representation.source_design_model_revision_id != model.revision_id
        or representation.parent_kind is not model.parent_kind
        or representation.parent_authority_revision_id != parent_revision_id
        or representation.scale_state is not model.scale_state
        or representation.coordinate_unit != model.coordinate_unit
        or representation.physical_accuracy_validation_status
        != model.physical_accuracy_validation_status
        or representation.mold_use_authorized is not model.mold_use_authorized
        or representation.solid_count != 1
    ):
        raise LabelZoneError("label_zone_model_cad_authority_mismatch")
    try:
        feature = resolve_design_model_feature(model, feature_id)
    except DesignModelError as error:
        raise LabelZoneError(f"label_zone_{error}") from error
    if feature.component_id != component_id:
        raise LabelZoneError("label_zone_component_feature_mismatch")
    if feature_id not in representation.source_feature_ids:
        raise LabelZoneError("label_zone_feature_not_in_brep_lineage")

    identity: dict[str, object] = {
        "contract": LABEL_ZONE_CONTRACT,
        "zone_kind": zone_kind.value,
        "source_design_model_revision_id": model.revision_id,
        "source_brep_revision_id": representation.revision_id,
        "source_brep_geometry_sha256": representation.geometry_sha256,
        "parent_kind": model.parent_kind.value,
        "parent_authority_revision_id": parent_revision_id,
        "scale_state": model.scale_state.value,
        "coordinate_unit": model.coordinate_unit,
        "component_id": component_id,
        "feature_id": feature_id,
        "boundary": boundary.as_dict(),
    }
    return LabelZone(
        zone_id=_zone_id(identity),
        zone_kind=zone_kind,
        source_design_model_revision_id=model.revision_id,
        source_brep_revision_id=representation.revision_id,
        source_brep_geometry_sha256=representation.geometry_sha256,
        parent_kind=model.parent_kind,
        parent_authority_revision_id=parent_revision_id,
        scale_state=model.scale_state,
        coordinate_unit=model.coordinate_unit,
        component_id=component_id,
        feature_id=feature_id,
        boundary=boundary,
        physical_accuracy_validation_status=model.physical_accuracy_validation_status,
        mold_use_authorized=model.mold_use_authorized,
    )


def _identity(zone: LabelZone) -> dict[str, object]:
    return {
        "contract": LABEL_ZONE_CONTRACT,
        "zone_kind": zone.zone_kind.value,
        "source_design_model_revision_id": zone.source_design_model_revision_id,
        "source_brep_revision_id": zone.source_brep_revision_id,
        "source_brep_geometry_sha256": zone.source_brep_geometry_sha256,
        "parent_kind": zone.parent_kind.value,
        "parent_authority_revision_id": zone.parent_authority_revision_id,
        "scale_state": zone.scale_state.value,
        "coordinate_unit": zone.coordinate_unit,
        "component_id": zone.component_id,
        "feature_id": zone.feature_id,
        "boundary": zone.boundary.as_dict(),
    }


def _zone_id(identity: dict[str, object]) -> str:
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return _ZONE_ID_PREFIX + digest


__all__ = [
    "LABEL_ZONE_CONTRACT",
    "LabelZone",
    "LabelZoneBoundary",
    "LabelZoneError",
    "LabelZoneKind",
    "create_label_zone",
]
