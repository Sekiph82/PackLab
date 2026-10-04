"""Deterministic component-hierarchy metadata for future assembly-capable exporters."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
from dataclasses import dataclass

from .assembly_graph import (
    AssemblyComponentInput,
    AssemblyComponentRole,
    AssemblyGraphError,
    ParametricAssemblyGraph,
    validate_parametric_assembly_graph,
)
from .design_model import (
    DesignModelError,
    resolve_design_model_feature,
)
from .dip_tube import DipTubeComponentRevision
from .trigger_pump_alignment import TriggerPumpAlignmentRevision
from .trigger_pump_library import ImportedTriggerPumpComponent

_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_EPSILON = 1e-8
_MAX_COORDINATE = 1e9
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ROLE_ORDER = (
    AssemblyComponentRole.BODY,
    AssemblyComponentRole.CLOSURE,
    AssemblyComponentRole.TRIGGER_PUMP,
    AssemblyComponentRole.DIP_TUBE,
)


class AssemblyHierarchyExportError(ValueError):
    """Raised when component hierarchy handoff metadata is stale or incomplete."""


@dataclass(frozen=True, slots=True)
class AssemblyHierarchyPlacement:
    """Exact rigid transform pin for one assembly graph component."""

    role: AssemblyComponentRole
    model_revision_id: str
    feature_id: str
    placement_revision_id: str
    transform: tuple[float, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.role, AssemblyComponentRole):
            raise AssemblyHierarchyExportError("hierarchy_placement_role_invalid")
        for value, field in (
            (self.model_revision_id, "model_revision_id"),
            (self.feature_id, "feature_id"),
            (self.placement_revision_id, "placement_revision_id"),
        ):
            if not isinstance(value, str) or not _ID.fullmatch(value):
                raise AssemblyHierarchyExportError(f"hierarchy_placement_{field}_invalid")
        _validate_matrix(self.transform)

    def as_dict(self) -> dict[str, object]:
        return {
            "placement_revision_id": self.placement_revision_id,
            "transform_convention": "row_major_4x4_column_vectors_v1",
            "matrix": list(self.transform),
        }


@dataclass(frozen=True, slots=True)
class AssemblyHierarchyExportHandoff:
    """Canonical immutable JSON handoff; it never contains exported geometry or CAD files."""

    handoff_id: str
    canonical_json: str

    def as_dict(self) -> dict[str, object]:
        value = json.loads(self.canonical_json)
        if not isinstance(value, dict):
            raise AssemblyHierarchyExportError("hierarchy_manifest_invalid")
        return value


def create_assembly_hierarchy_export_handoff(
    graph: ParametricAssemblyGraph,
    current_components: tuple[AssemblyComponentInput, ...],
    dip_tube: DipTubeComponentRevision,
    library_component: ImportedTriggerPumpComponent,
    trigger_pump_alignment: TriggerPumpAlignmentRevision,
    placements: tuple[AssemblyHierarchyPlacement, ...],
    *,
    expected_graph_revision_id: str,
    expected_library_import_id: str,
    expected_alignment_revision_id: str,
) -> AssemblyHierarchyExportHandoff:
    """Create a stable metadata manifest for a later non-M13 component-capable exporter."""
    if not isinstance(graph, ParametricAssemblyGraph):
        raise AssemblyHierarchyExportError("assembly_graph_required")
    if graph.revision_id != expected_graph_revision_id:
        raise AssemblyHierarchyExportError("assembly_graph_revision_stale")
    try:
        validate_parametric_assembly_graph(graph, current_components)
    except AssemblyGraphError as error:
        raise AssemblyHierarchyExportError(str(error)) from error
    if not isinstance(dip_tube, DipTubeComponentRevision):
        raise AssemblyHierarchyExportError("dip_tube_component_required")
    if not isinstance(library_component, ImportedTriggerPumpComponent):
        raise AssemblyHierarchyExportError("library_component_required")
    if not isinstance(trigger_pump_alignment, TriggerPumpAlignmentRevision):
        raise AssemblyHierarchyExportError("trigger_pump_alignment_required")
    if (
        not isinstance(expected_library_import_id, str)
        or library_component.import_id != expected_library_import_id
        or trigger_pump_alignment.library_import_id != expected_library_import_id
    ):
        raise AssemblyHierarchyExportError("library_component_reference_stale")
    if trigger_pump_alignment.revision_id != expected_alignment_revision_id:
        raise AssemblyHierarchyExportError("trigger_pump_alignment_revision_stale")
    if (
        not isinstance(placements, tuple)
        or len(placements) != len(_ROLE_ORDER)
        or any(not isinstance(item, AssemblyHierarchyPlacement) for item in placements)
        or len({item.role for item in placements}) != len(placements)
        or {item.role for item in placements} != set(_ROLE_ORDER)
    ):
        raise AssemblyHierarchyExportError("hierarchy_placements_must_pin_each_role_once")
    placement_by_role = {item.role: item for item in placements}
    references = {item.role: item for item in graph.components}
    models = {item.role: item.model for item in current_components}
    for role in _ROLE_ORDER:
        placement = placement_by_role[role]
        reference = references[role]
        if (
            placement.model_revision_id != reference.model_revision_id
            or placement.feature_id != reference.feature_id
        ):
            raise AssemblyHierarchyExportError("hierarchy_placement_component_pin_stale")
    pump = references[AssemblyComponentRole.TRIGGER_PUMP]
    pump_model = models[AssemblyComponentRole.TRIGGER_PUMP]
    body_model = models[AssemblyComponentRole.BODY]
    closure_model = models[AssemblyComponentRole.CLOSURE]
    try:
        pump_feature = resolve_design_model_feature(pump_model, pump.feature_id)
    except DesignModelError as error:
        raise AssemblyHierarchyExportError("hierarchy_pump_feature_stale") from error
    if (
        library_component.component_id != pump.component_id
        or library_component.attachment_semantic_key != pump_feature.semantic_key
        or library_component.coordinate_unit != graph.coordinate_unit
        or library_component.scale_state is not graph.scale_state
    ):
        raise AssemblyHierarchyExportError("hierarchy_library_attachment_or_scale_mismatch")
    library_payload = library_component.as_dict()
    source = library_payload.get("source")
    license_evidence = library_payload.get("license")
    geometry = library_payload.get("geometry")
    if (
        library_payload.get("contract") != "packlab.imported-trigger-pump-component.v1"
        or not isinstance(source, dict)
        or not isinstance(license_evidence, dict)
        or not isinstance(geometry, dict)
        or not all(
            isinstance(value, str) and value.strip()
            for value in (
                source.get("kind"),
                source.get("reference"),
                source.get("provenance_id"),
                license_evidence.get("identifier"),
                license_evidence.get("reviewed_by"),
            )
        )
        or not isinstance(license_evidence.get("evidence_sha256"), str)
        or not _SHA256.fullmatch(license_evidence["evidence_sha256"])
        or geometry.get("authority_class") != "LIBRARY_DESIGN_COMPONENT"
        or not isinstance(geometry.get("asset_sha256"), str)
        or not _SHA256.fullmatch(geometry["asset_sha256"])
        or library_payload.get("physical_accuracy_validation_status") != _DEFERRED
        or library_payload.get("mold_use_authorized") is not False
        or library_payload.get("scan_master_revision_id") is not None
        or library_payload.get("downloaded") is not False
        or library_payload.get("network_accessed") is not False
    ):
        raise AssemblyHierarchyExportError("hierarchy_library_provenance_or_authority_invalid")
    if (
        trigger_pump_alignment.assembly_graph_revision_id != graph.revision_id
        or trigger_pump_alignment.trigger_pump_model_revision_id != pump.model_revision_id
        or trigger_pump_alignment.trigger_pump_feature_id != pump.feature_id
        or trigger_pump_alignment.body_model_revision_id
        != references[AssemblyComponentRole.BODY].model_revision_id
        or trigger_pump_alignment.closure_model_revision_id
        != references[AssemblyComponentRole.CLOSURE].model_revision_id
        or trigger_pump_alignment.scan_master_revision_id
        != body_model.fitted_to_scan_master_revision_id
        or trigger_pump_alignment.scan_master_revision_id
        != closure_model.fitted_to_scan_master_revision_id
        or trigger_pump_alignment.scan_master_geometry_sha256
        != body_model.scan_master_geometry_sha256
        or trigger_pump_alignment.scan_master_geometry_sha256
        != closure_model.scan_master_geometry_sha256
        or trigger_pump_alignment.library_import_id != library_component.import_id
        or trigger_pump_alignment.scale_state is not graph.scale_state
        or trigger_pump_alignment.coordinate_unit != graph.coordinate_unit
        or trigger_pump_alignment.physical_accuracy_validation_status != _DEFERRED
        or placement_by_role[AssemblyComponentRole.TRIGGER_PUMP].placement_revision_id
        != trigger_pump_alignment.revision_id
        or placement_by_role[AssemblyComponentRole.TRIGGER_PUMP].transform
        != trigger_pump_alignment.placement_matrix
    ):
        raise AssemblyHierarchyExportError("hierarchy_pump_alignment_stale_or_incompatible")
    tube_reference = references[AssemblyComponentRole.DIP_TUBE]
    if (
        dip_tube.revision_id != tube_reference.model_revision_id
        or dip_tube.feature_id != tube_reference.feature_id
        or dip_tube.model.coordinate_unit != graph.coordinate_unit
        or dip_tube.model.scale_state is not graph.scale_state
        or dip_tube.attachment.trigger_pump_model_revision_id != pump.model_revision_id
        or dip_tube.attachment.trigger_pump_feature_id != pump.feature_id
    ):
        raise AssemblyHierarchyExportError("hierarchy_dip_tube_reference_stale_or_incompatible")

    nodes = []
    for role in _ROLE_ORDER:
        reference = references[role]
        model = models[role]
        try:
            feature = resolve_design_model_feature(model, reference.feature_id)
        except DesignModelError as error:
            raise AssemblyHierarchyExportError("hierarchy_component_feature_stale") from error
        if (
            feature.feature_kind is not reference.feature_kind
            or model.physical_accuracy_validation_status != _DEFERRED
            or model.mold_use_authorized is not False
        ):
            raise AssemblyHierarchyExportError("hierarchy_component_authority_invalid")
        node: dict[str, object] = {
            "role": role.value,
            "component_revision_id": model.revision_id,
            "feature_id": feature.feature_id,
            "component_id": feature.component_id,
            "feature_kind": feature.feature_kind.value,
            "previous_model_revision_id": model.previous_revision_id,
            "parent": {
                "binding_revision_id": model.parent_binding_revision_id,
                "scan_master_revision_id": model.fitted_to_scan_master_revision_id,
                "scan_master_geometry_sha256": model.scan_master_geometry_sha256,
                "scale_provenance_id": model.scale_provenance_id,
            },
            "coordinate_unit": model.coordinate_unit,
            "scale_state": model.scale_state.value,
            "physical_accuracy_validation_status": model.physical_accuracy_validation_status,
            "mold_use_authorized": model.mold_use_authorized,
            "placement": placement_by_role[role].as_dict(),
            "geometry_embedded": False,
        }
        if role is AssemblyComponentRole.TRIGGER_PUMP:
            node["library_component_reference"] = library_component.as_dict()
            node["alignment_revision_id"] = trigger_pump_alignment.revision_id
        elif role is AssemblyComponentRole.DIP_TUBE:
            node["parametric_definition"] = dip_tube.as_dict()
        nodes.append(node)
    edges = [
        item.as_dict() for item in sorted(graph.relationships, key=lambda item: item.kind.value)
    ]
    base_manifest: dict[str, object] = {
        "contract": "packlab.assembly-hierarchy-export-handoff.v1",
        "authority_class": "PARAMETRIC_ASSEMBLY_EXPORT_HANDOFF_METADATA",
        "assembly_graph_revision_id": graph.revision_id,
        "project_id": graph.project_id,
        "component_hierarchy": {
            "root_role": AssemblyComponentRole.BODY.value,
            "nodes": nodes,
            "relationships": edges,
        },
        "library_references": [library_component.as_dict()],
        "scale_state": graph.scale_state.value,
        "coordinate_unit": graph.coordinate_unit,
        "physical_accuracy_validation_status": _DEFERRED,
        "mold_use_authorized": False,
        "target": "future_component_capable_exporter",
        "metadata_handoff_ready": True,
        "export_executed": False,
        "geometry_embedded": False,
        "glb_exported": False,
        "cad_geometry_exported": False,
        "step_exported": False,
        "certified_fit_claimed": False,
        "manufacturing_interference_claimed": False,
        "scan_master_mutated": False,
    }
    canonical_base = json.dumps(
        base_manifest, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    handoff_id = (
        "assembly-hierarchy-handoff:" + hashlib.sha256(canonical_base.encode("utf-8")).hexdigest()
    )
    manifest = {"handoff_id": handoff_id, **base_manifest}
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return AssemblyHierarchyExportHandoff(handoff_id, canonical)


def _validate_matrix(matrix: tuple[float, ...]) -> None:
    if (
        not isinstance(matrix, tuple)
        or len(matrix) != 16
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or abs(value) > _MAX_COORDINATE
            for value in matrix
        )
    ):
        raise AssemblyHierarchyExportError("hierarchy_transform_invalid")
    if any(
        abs(matrix[index] - expected) > _EPSILON
        for index, expected in ((12, 0.0), (13, 0.0), (14, 0.0), (15, 1.0))
    ):
        raise AssemblyHierarchyExportError("hierarchy_transform_not_affine")
    axes = tuple(tuple(float(matrix[row * 4 + column]) for row in range(3)) for column in range(3))
    for first, second in itertools.combinations(axes, 2):
        if abs(math.fsum(first[index] * second[index] for index in range(3))) > _EPSILON:
            raise AssemblyHierarchyExportError("hierarchy_transform_not_rigid")
    if any(
        abs(math.sqrt(math.fsum(value * value for value in axis)) - 1.0) > _EPSILON for axis in axes
    ):
        raise AssemblyHierarchyExportError("hierarchy_transform_not_rigid")
    determinant = (
        matrix[0] * (matrix[5] * matrix[10] - matrix[6] * matrix[9])
        - matrix[1] * (matrix[4] * matrix[10] - matrix[6] * matrix[8])
        + matrix[2] * (matrix[4] * matrix[9] - matrix[5] * matrix[8])
    )
    if abs(determinant - 1.0) > _EPSILON:
        raise AssemblyHierarchyExportError("hierarchy_transform_not_proper_rotation")


__all__ = [
    "AssemblyHierarchyExportError",
    "AssemblyHierarchyExportHandoff",
    "AssemblyHierarchyPlacement",
    "create_assembly_hierarchy_export_handoff",
]
