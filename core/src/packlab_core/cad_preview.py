"""Provenance-bound, disposable mesh previews derived from accepted CAD BREP."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from .cad_adapter import CadAdapterError, cad_shape_bounds, tessellate_cad_shape
from .cad_brep import CadBrepRepresentationRevision
from .cad_feature_map import map_design_model_features_to_brep
from .cad_validation import validate_cad_brep
from .design_model import DesignModelRevision
from .geometry_adapter import TriangleMeshData

CAD_PREVIEW_CONTRACT = "packlab.cad-brep-preview.v1"


class CadPreviewError(ValueError):
    """Raised when a BREP cannot safely produce a bounded disposable preview."""


@dataclass(frozen=True, slots=True)
class CadPreviewFeatureReference:
    feature_id: str
    status: str
    preview_triangle_indices: tuple[int, ...]
    mapping_reference_id: str
    mapping_scope: str

    def as_dict(self) -> dict[str, object]:
        return {
            "feature_id": self.feature_id,
            "status": self.status,
            "preview_triangle_indices": list(self.preview_triangle_indices),
            "mapping_reference_id": self.mapping_reference_id,
            "mapping_scope": self.mapping_scope,
        }


@dataclass(frozen=True, slots=True)
class CadPreviewMeshRevision:
    revision_id: str
    mesh: TriangleMeshData
    source_brep_revision_id: str
    source_design_model_revision_id: str
    source_operation_id: str
    parent_kind: str
    parent_authority_revision_id: str
    scale_state: str
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    linear_deflection: float
    angular_deflection: float
    maximum_vertices: int
    maximum_triangles: int
    maximum_faces: int
    source_face_count: int
    source_bounds: tuple[float, float, float, float, float, float]
    preview_bounds: tuple[float, float, float, float, float, float]
    maximum_bounds_delta: float
    bounds_consistent: bool
    feature_mapping_revision_id: str
    feature_references: tuple[CadPreviewFeatureReference, ...]
    limitations: tuple[str, ...]
    contract: str = CAD_PREVIEW_CONTRACT
    authority_class: str = "PREVIEW_PROXY"

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": self.authority_class,
            "revision_id": self.revision_id,
            "source_brep_revision_id": self.source_brep_revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_operation_id": self.source_operation_id,
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "scale_state": self.scale_state,
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "tessellation": {
                "linear_deflection": self.linear_deflection,
                "angular_deflection_radians": self.angular_deflection,
                "maximum_vertices": self.maximum_vertices,
                "maximum_triangles": self.maximum_triangles,
                "maximum_faces": self.maximum_faces,
                "source_face_count": self.source_face_count,
                "preview_vertex_count": len(self.mesh.vertices),
                "preview_triangle_count": len(self.mesh.triangles),
            },
            "geometry": {
                "vertices": [list(vertex) for vertex in self.mesh.vertices],
                "triangles": [list(triangle) for triangle in self.mesh.triangles],
            },
            "bounds_comparison": {
                "source_brep_bounds": list(self.source_bounds),
                "preview_mesh_bounds": list(self.preview_bounds),
                "maximum_axis_delta": self.maximum_bounds_delta,
                "consistent_within_linear_deflection": self.bounds_consistent,
            },
            "feature_mapping_revision_id": self.feature_mapping_revision_id,
            "feature_references": [item.as_dict() for item in self.feature_references],
            "limitations": list(self.limitations),
            "disposable": True,
            "brep_truth_modified": False,
            "design_model_replaced": False,
            "scan_master_promoted": False,
            "physical_accuracy_inferred": False,
            "manufacturing_suitability_inferred": False,
        }


def tessellate_brep_preview(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    *,
    linear_deflection: float = 0.1,
    angular_deflection: float = 0.5,
    maximum_vertices: int = 250_000,
    maximum_triangles: int = 500_000,
    maximum_faces: int = 10_000,
) -> CadPreviewMeshRevision:
    """Derive a bounded preview from one valid, exact-model-bound BREP revision."""
    if not isinstance(model, DesignModelRevision):
        raise CadPreviewError("design_model_revision_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise CadPreviewError("cad_brep_representation_required")
    if representation.source_design_model_revision_id != model.revision_id:
        raise CadPreviewError("cad_preview_model_revision_mismatch")
    if representation.parent_kind is not model.parent_kind:
        raise CadPreviewError("cad_preview_parent_authority_mismatch")
    parent_revision = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if representation.parent_authority_revision_id != parent_revision:
        raise CadPreviewError("cad_preview_parent_revision_mismatch")
    if (
        representation.scale_state is not model.scale_state
        or representation.coordinate_unit != model.coordinate_unit
        or representation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or representation.mold_use_authorized is not False
    ):
        raise CadPreviewError("cad_preview_authority_metadata_mismatch")
    try:
        validation = validate_cad_brep(representation)
    except Exception as error:
        raise CadPreviewError("cad_preview_brep_validation_failed") from error
    if not validation.valid_closed_solid:
        raise CadPreviewError("cad_preview_valid_closed_solid_required")
    try:
        feature_mapping = map_design_model_features_to_brep(model, representation)
        tessellation = tessellate_cad_shape(
            representation.shape_handle,
            linear_deflection=linear_deflection,
            angular_deflection=angular_deflection,
            maximum_vertices=maximum_vertices,
            maximum_triangles=maximum_triangles,
            maximum_faces=maximum_faces,
        )
        # Bnd_Box.Get uses grouped minima then grouped maxima; preview records use
        # interleaved axis pairs to match the backend-neutral AABB convention.
        raw_bounds = cad_shape_bounds(representation.shape_handle)
        source_bounds = (
            raw_bounds[0],
            raw_bounds[3],
            raw_bounds[1],
            raw_bounds[4],
            raw_bounds[2],
            raw_bounds[5],
        )
    except (CadAdapterError, ValueError) as error:
        raise CadPreviewError(str(error)) from error

    preview_bounds = _mesh_bounds(tessellation.mesh)
    maximum_delta = max(abs(left - right) for left, right in zip(source_bounds, preview_bounds))
    bounds_consistent = maximum_delta <= max(float(linear_deflection), 1e-7)
    all_triangle_indices = tuple(range(len(tessellation.mesh.triangles)))
    feature_references = tuple(
        CadPreviewFeatureReference(
            feature_id=reference.feature_id,
            status=reference.status,
            preview_triangle_indices=(
                all_triangle_indices if reference.status in {"MAPPED", "MAPPED_COARSE"} else ()
            ),
            mapping_reference_id=reference.named_reference_id,
            mapping_scope=(
                "whole_output_solid_preview"
                if reference.status in {"MAPPED", "MAPPED_COARSE"}
                else "none"
            ),
        )
        for reference in feature_mapping.references
    )
    revision_material = {
        "contract": CAD_PREVIEW_CONTRACT,
        "brep_revision_id": representation.revision_id,
        "feature_mapping_revision_id": feature_mapping.revision_id,
        "linear_deflection": tessellation.linear_deflection,
        "angular_deflection": tessellation.angular_deflection,
        "vertices": tessellation.mesh.vertices,
        "triangles": tessellation.mesh.triangles,
    }
    revision_id = (
        "cad-preview:"
        + hashlib.sha256(
            json.dumps(revision_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
    )
    return CadPreviewMeshRevision(
        revision_id=revision_id,
        mesh=tessellation.mesh,
        source_brep_revision_id=representation.revision_id,
        source_design_model_revision_id=model.revision_id,
        source_operation_id=representation.source_operation_id,
        parent_kind=representation.parent_kind.value,
        parent_authority_revision_id=representation.parent_authority_revision_id,
        scale_state=representation.scale_state.value,
        coordinate_unit=representation.coordinate_unit,
        physical_accuracy_validation_status=representation.physical_accuracy_validation_status,
        mold_use_authorized=representation.mold_use_authorized,
        linear_deflection=tessellation.linear_deflection,
        angular_deflection=tessellation.angular_deflection,
        maximum_vertices=tessellation.maximum_vertices,
        maximum_triangles=tessellation.maximum_triangles,
        maximum_faces=tessellation.maximum_faces,
        source_face_count=tessellation.face_count,
        source_bounds=source_bounds,
        preview_bounds=preview_bounds,
        maximum_bounds_delta=maximum_delta,
        bounds_consistent=bounds_consistent,
        feature_mapping_revision_id=feature_mapping.revision_id,
        feature_references=feature_references,
        limitations=(
            "mesh_is_disposable_preview_only",
            "tessellation_tolerance_limits_surface_approximation_not_physical_accuracy",
            "whole_solid_feature_mappings_do_not_identify_face_or_vertex_subsets",
            "bounds_comparison_is_axis_aligned_and_tolerance_bounded",
        ),
    )


def _mesh_bounds(mesh: TriangleMeshData) -> tuple[float, float, float, float, float, float]:
    components = tuple(zip(*mesh.vertices))
    bounds = tuple(value for axis in components for value in (min(axis), max(axis)))
    if len(bounds) != 6 or any(not math.isfinite(value) for value in bounds):
        raise CadPreviewError("cad_preview_bounds_invalid")
    return bounds


__all__ = [
    "CAD_PREVIEW_CONTRACT",
    "CadPreviewError",
    "CadPreviewFeatureReference",
    "CadPreviewMeshRevision",
    "tessellate_brep_preview",
]
