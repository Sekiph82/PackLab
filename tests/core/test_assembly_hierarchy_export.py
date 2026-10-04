from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from tests.core.test_trigger_pump_alignment import _setup as alignment_setup

from packlab_core.assembly_graph import (
    AssemblyComponentInput,
    AssemblyComponentRole,
    create_parametric_assembly_graph,
)
from packlab_core.assembly_hierarchy_export import (
    AssemblyHierarchyExportError,
    AssemblyHierarchyPlacement,
    create_assembly_hierarchy_export_handoff,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.dip_tube import DipTubePath, create_dip_tube_component
from packlab_core.trigger_pump_alignment import align_library_trigger_pump

_IDENTITY = (
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
)


def _scenario(tmp_path: Path):
    scan, _source, _body, pump, inputs, _old_graph, mating, library, alignment_kwargs = (
        alignment_setup(tmp_path)
    )
    binding = bind_design_model_parent(
        scan,
        actor_id="hierarchy-export-operator",
        reason="Bind synthetic hierarchy dip tube to the exact Scan Master.",
        created_at_utc="2026-10-04T20:00:00Z",
    )
    pump_input = next(item for item in inputs if item.role is AssemblyComponentRole.TRIGGER_PUMP)
    tube = create_dip_tube_component(
        binding,
        pump,
        expected_trigger_pump_revision_id=pump.revision_id,
        trigger_pump_feature_id=pump_input.feature_id,
        component_id="hierarchy-export-dip-tube",
        semantic_key="centerline-v1",
        path=DipTubePath.straight((0.0, 0.0, 0.0), (0.0, 0.0, -40.0)),
        length=40.0,
        diameter=3.0,
        actor_id="hierarchy-export-operator",
        reason="Create explicit synthetic tube for hierarchy handoff tests.",
        created_at_utc="2026-10-04T20:00:00Z",
    )
    components = tuple(
        AssemblyComponentInput(
            AssemblyComponentRole.DIP_TUBE,
            tube.model,
            tube.revision_id,
            tube.feature_id,
        )
        if item.role is AssemblyComponentRole.DIP_TUBE
        else item
        for item in inputs
    )
    graph = create_parametric_assembly_graph(
        components,
        expected_component_revision_ids={item.role: item.model.revision_id for item in components},
        actor_id="hierarchy-export-operator",
        reason="Create exact graph for non-CAD hierarchy handoff.",
        created_at_utc="2026-10-04T20:00:00Z",
    )
    alignment = align_library_trigger_pump(
        library,
        graph,
        components,
        mating,
        **alignment_kwargs,
    )
    refs = {item.role: item for item in graph.components}
    placements = tuple(
        AssemblyHierarchyPlacement(
            role,
            refs[role].model_revision_id,
            refs[role].feature_id,
            alignment.revision_id
            if role is AssemblyComponentRole.TRIGGER_PUMP
            else f"placement:{role.value}:v1",
            alignment.placement_matrix if role is AssemblyComponentRole.TRIGGER_PUMP else _IDENTITY,
        )
        for role in (
            AssemblyComponentRole.BODY,
            AssemblyComponentRole.CLOSURE,
            AssemblyComponentRole.TRIGGER_PUMP,
            AssemblyComponentRole.DIP_TUBE,
        )
    )
    kwargs = {
        "expected_graph_revision_id": graph.revision_id,
        "expected_library_import_id": library.import_id,
        "expected_alignment_revision_id": alignment.revision_id,
    }
    return graph, components, tube, library, alignment, placements, kwargs


def _create(scenario, **overrides):
    graph, components, tube, library, alignment, placements, kwargs = scenario
    return create_assembly_hierarchy_export_handoff(
        graph,
        components,
        tube,
        library,
        alignment,
        overrides.get("placements", placements),
        **(kwargs | overrides.get("kwargs", {})),
    )


def test_handoff_preserves_hierarchy_revisions_placements_and_library_provenance(
    tmp_path: Path,
) -> None:
    scenario = _scenario(tmp_path)
    first = _create(scenario)
    repeated = _create(scenario)
    graph, components, _tube, library, alignment, placements, _kwargs = scenario
    manifest = first.as_dict()
    hierarchy = manifest["component_hierarchy"]
    nodes = hierarchy["nodes"]

    assert first == repeated
    assert first.handoff_id == repeated.handoff_id
    assert [item["role"] for item in nodes] == ["body", "closure", "trigger_pump", "dip_tube"]
    assert [item["component_revision_id"] for item in nodes] == [
        next(item.model.revision_id for item in components if item.role is role)
        for role in (
            AssemblyComponentRole.BODY,
            AssemblyComponentRole.CLOSURE,
            AssemblyComponentRole.TRIGGER_PUMP,
            AssemblyComponentRole.DIP_TUBE,
        )
    ]
    pump_node = nodes[2]
    assert pump_node["placement"]["matrix"] == list(alignment.placement_matrix)
    assert pump_node["placement"]["placement_revision_id"] == alignment.revision_id
    library_ref = pump_node["library_component_reference"]
    assert library_ref["import_id"] == library.import_id
    assert library_ref["source"]["provenance_id"] == library.provenance_id
    assert library_ref["license"]["evidence_sha256"] == library.license_evidence_sha256
    assert library_ref["geometry"]["asset_sha256"] == library.geometry_asset_sha256
    assert hierarchy["relationships"] == [item.as_dict() for item in graph.relationships]
    assert manifest["scale_state"] == "metric-unverified"
    assert manifest["coordinate_unit"] == "mm_unverified"
    assert manifest["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert manifest["mold_use_authorized"] is False
    assert manifest["cad_geometry_exported"] is False
    assert manifest["step_exported"] is False
    assert manifest["glb_exported"] is False
    assert manifest["export_executed"] is False


def test_stale_missing_component_or_alignment_is_rejected(tmp_path: Path) -> None:
    scenario = _scenario(tmp_path)
    graph, components, tube, library, alignment, placements, kwargs = scenario
    with pytest.raises(AssemblyHierarchyExportError, match="assembly_graph_revision_stale"):
        _create(scenario, kwargs={"expected_graph_revision_id": "assembly-graph:stale"})
    with pytest.raises(
        AssemblyHierarchyExportError, match="assembly_required_component_role_missing"
    ):
        create_assembly_hierarchy_export_handoff(
            graph,
            tuple(item for item in components if item.role is not AssemblyComponentRole.CLOSURE),
            tube,
            library,
            alignment,
            placements,
            **kwargs,
        )
    stale_pump_placement = tuple(
        replace(item, model_revision_id="design-model:stale")
        if item.role is AssemblyComponentRole.TRIGGER_PUMP
        else item
        for item in placements
    )
    with pytest.raises(
        AssemblyHierarchyExportError, match="hierarchy_placement_component_pin_stale"
    ):
        _create(scenario, placements=stale_pump_placement)
    stale_alignment = replace(alignment, assembly_graph_revision_id="assembly-graph:stale")
    with pytest.raises(
        AssemblyHierarchyExportError, match="hierarchy_pump_alignment_stale_or_incompatible"
    ):
        create_assembly_hierarchy_export_handoff(
            graph,
            components,
            tube,
            library,
            stale_alignment,
            placements,
            **(kwargs | {"expected_alignment_revision_id": stale_alignment.revision_id}),
        )


def test_unverifiable_library_provenance_and_stale_scan_ancestry_are_rejected(
    tmp_path: Path,
) -> None:
    scenario = _scenario(tmp_path)
    graph, components, tube, library, alignment, placements, kwargs = scenario
    incomplete_library = replace(library, source_reference=" ")
    with pytest.raises(
        AssemblyHierarchyExportError,
        match="hierarchy_library_provenance_or_authority_invalid",
    ):
        create_assembly_hierarchy_export_handoff(
            graph,
            components,
            tube,
            incomplete_library,
            alignment,
            placements,
            **(kwargs | {"expected_library_import_id": incomplete_library.import_id}),
        )
    stale_scan_ancestry = replace(alignment, scan_master_geometry_sha256="0" * 64)
    with pytest.raises(
        AssemblyHierarchyExportError, match="hierarchy_pump_alignment_stale_or_incompatible"
    ):
        create_assembly_hierarchy_export_handoff(
            graph,
            components,
            tube,
            library,
            stale_scan_ancestry,
            placements,
            **(kwargs | {"expected_alignment_revision_id": stale_scan_ancestry.revision_id}),
        )
