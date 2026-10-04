"""Deterministic derived BREP revisions for PackLab Design Models."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .cad_adapter import CadAdapterError, CadShapeHandle, build_revolved_shape
from .design_model import DesignModelParentKind, DesignModelRevision
from .design_operations import DesignOperation
from .design_profile import DesignProfile
from .reconstruction import ScaleState

CAD_BREP_CONTRACT = "packlab.cad-brep-revision.v1"
_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class CadBrepError(ValueError):
    """Raised when a derived CAD representation lacks valid Design Model authority."""


@dataclass(frozen=True, slots=True)
class CadBrepRepresentationRevision:
    revision_id: str
    geometry_sha256: str
    source_design_model_revision_id: str
    source_operation_id: str
    shape_handle: CadShapeHandle
    parent_kind: DesignModelParentKind
    parent_authority_revision_id: str
    scale_state: ScaleState
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    solid_count: int
    profile_sample_count: int
    contract: str = CAD_BREP_CONTRACT
    representation_type: str = "BREP_SOLID"

    def __post_init__(self) -> None:
        if self.contract != CAD_BREP_CONTRACT or self.representation_type != "BREP_SOLID":
            raise CadBrepError("cad_brep_contract_invalid")
        if not _DIGEST_PATTERN.fullmatch(self.geometry_sha256):
            raise CadBrepError("cad_brep_geometry_digest_invalid")
        if not isinstance(self.shape_handle, CadShapeHandle):
            raise CadBrepError("cad_brep_shape_handle_invalid")
        if self.parent_kind is not self.shape_handle.parent_kind:
            raise CadBrepError("cad_brep_parent_kind_mismatch")
        if self.parent_authority_revision_id != self.shape_handle.parent_authority_revision_id:
            raise CadBrepError("cad_brep_parent_revision_mismatch")
        if (
            self.source_design_model_revision_id
            != self.shape_handle.source_design_model_revision_id
        ):
            raise CadBrepError("cad_brep_source_model_mismatch")
        if self.scale_state is not self.shape_handle.scale_state:
            raise CadBrepError("cad_brep_scale_state_mismatch")
        if self.coordinate_unit != self.shape_handle.coordinate_unit:
            raise CadBrepError("cad_brep_coordinate_unit_mismatch")
        if (
            self.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
            or self.shape_handle.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        ):
            raise CadBrepError("cad_brep_physical_validation_must_remain_deferred")
        if (
            self.mold_use_authorized is not False
            or self.shape_handle.mold_use_authorized is not False
        ):
            raise CadBrepError("cad_brep_mold_use_forbidden")
        if self.solid_count != 1:
            raise CadBrepError("cad_brep_single_solid_required")
        if (
            not isinstance(self.profile_sample_count, int)
            or isinstance(self.profile_sample_count, bool)
            or not 3 <= self.profile_sample_count <= 2048
        ):
            raise CadBrepError("cad_brep_profile_sample_count_invalid")
        if self.revision_id != _revision_id(self):
            raise CadBrepError("cad_brep_revision_id_mismatch")

    def as_dict(self) -> dict[str, object]:
        parent_authority: dict[str, str]
        if self.parent_kind is DesignModelParentKind.STANDALONE_DESIGN_GEOMETRY:
            parent_authority = {
                "kind": self.parent_kind.value,
                "root_revision_id": self.parent_authority_revision_id,
            }
        else:
            parent_authority = {
                "kind": self.parent_kind.value,
                "binding_revision_id": self.parent_authority_revision_id,
            }
        return {
            "contract": self.contract,
            "authority_class": "DERIVED_CAD_BREP",
            "revision_id": self.revision_id,
            "representation_type": self.representation_type,
            "geometry_sha256": self.geometry_sha256,
            "shape_handle_id": self.shape_handle.handle_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_operation_id": self.source_operation_id,
            "parent_authority": parent_authority,
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "solid_count": self.solid_count,
            "profile_sampling": {
                "method": "uniform_axial_samples_closed_to_revolve_axis",
                "sample_count": self.profile_sample_count,
            },
            "scan_master_promoted": False,
            "design_model_replaced": False,
        }


def revolve_design_model_to_brep(
    model: DesignModelRevision,
    profile: DesignProfile,
    operation: DesignOperation,
    *,
    profile_sample_count: int = 257,
) -> CadBrepRepresentationRevision:
    """Derive one reproducible BREP solid without mutating Design Model authority."""
    if not isinstance(model, DesignModelRevision):
        raise CadBrepError("design_model_revision_required")
    if not isinstance(profile, DesignProfile):
        raise CadBrepError("design_profile_required")
    if not isinstance(operation, DesignOperation):
        raise CadBrepError("design_model_revolve_operation_required")
    try:
        shape_build = build_revolved_shape(
            model, profile, operation, profile_sample_count=profile_sample_count
        )
    except CadAdapterError as error:
        raise CadBrepError(str(error)) from error
    except Exception as error:
        raise CadBrepError("cad_brep_backend_operation_failed") from error
    parent_authority_revision_id = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if parent_authority_revision_id is None:
        raise CadBrepError("design_model_parent_authority_missing")
    provisional = object.__new__(CadBrepRepresentationRevision)
    values = (
        ("contract", CAD_BREP_CONTRACT),
        ("representation_type", "BREP_SOLID"),
        ("geometry_sha256", shape_build.geometry_sha256),
        ("source_design_model_revision_id", model.revision_id),
        ("source_operation_id", operation.operation_id),
        ("shape_handle", shape_build.shape_handle),
        ("parent_kind", model.parent_kind),
        ("parent_authority_revision_id", parent_authority_revision_id),
        ("scale_state", model.scale_state),
        ("coordinate_unit", model.coordinate_unit),
        ("physical_accuracy_validation_status", model.physical_accuracy_validation_status),
        ("mold_use_authorized", model.mold_use_authorized),
        ("solid_count", shape_build.solid_count),
        ("profile_sample_count", profile_sample_count),
    )
    for name, value in values:
        object.__setattr__(provisional, name, value)
    return CadBrepRepresentationRevision(
        revision_id=_revision_id(provisional),
        geometry_sha256=shape_build.geometry_sha256,
        source_design_model_revision_id=model.revision_id,
        source_operation_id=operation.operation_id,
        shape_handle=shape_build.shape_handle,
        parent_kind=model.parent_kind,
        parent_authority_revision_id=parent_authority_revision_id,
        scale_state=model.scale_state,
        coordinate_unit=model.coordinate_unit,
        physical_accuracy_validation_status=model.physical_accuracy_validation_status,
        mold_use_authorized=model.mold_use_authorized,
        solid_count=shape_build.solid_count,
        profile_sample_count=profile_sample_count,
    )


def _revision_id(revision: CadBrepRepresentationRevision) -> str:
    payload = {
        "contract": revision.contract,
        "geometry_sha256": revision.geometry_sha256,
        "source_design_model_revision_id": revision.source_design_model_revision_id,
        "source_operation_id": revision.source_operation_id,
        "shape_handle_id": revision.shape_handle.handle_id,
        "parent_kind": revision.parent_kind.value,
        "parent_authority_revision_id": revision.parent_authority_revision_id,
        "scale_state": revision.scale_state.value,
        "coordinate_unit": revision.coordinate_unit,
        "physical_accuracy_validation_status": revision.physical_accuracy_validation_status,
        "mold_use_authorized": revision.mold_use_authorized,
        "solid_count": revision.solid_count,
        "profile_sample_count": revision.profile_sample_count,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return f"cad-brep:{digest}"


__all__ = [
    "CAD_BREP_CONTRACT",
    "CadBrepError",
    "CadBrepRepresentationRevision",
    "revolve_design_model_to_brep",
]
