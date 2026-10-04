from __future__ import annotations

from pathlib import Path

import pytest
from tests.core.test_trigger_pump_alignment import _setup as alignment_setup

from packlab_core.assembly_clearance import (
    AssemblyClearanceError,
    AssemblyComponentPlacement,
    AssemblyComponentProxy,
    PairDiagnosticStatus,
    diagnose_assembly_clearance,
)
from packlab_core.assembly_graph import (
    AssemblyComponentInput,
    AssemblyComponentRole,
    create_parametric_assembly_graph,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.design_preview import DesignPreview
from packlab_core.dip_tube import DipTubePath, create_dip_tube_component
from packlab_core.geometry_adapter import TriangleMeshData

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


def _translated(x: float, y: float = 0.0, z: float = 0.0) -> tuple[float, ...]:
    return (*_IDENTITY[:3], x, *_IDENTITY[4:7], y, *_IDENTITY[8:11], z, *_IDENTITY[12:])


def _box(minimum: tuple[float, float, float], maximum: tuple[float, float, float]):
    return tuple(
        (x, y, z)
        for x in (minimum[0], maximum[0])
        for y in (minimum[1], maximum[1])
        for z in (minimum[2], maximum[2])
    )


def _scenario(tmp_path: Path):
    (
        scan,
        _source,
        _body_model,
        pump_model,
        original_inputs,
        _old_graph,
        _mating,
        _library,
        _kwargs,
    ) = alignment_setup(tmp_path)
    pump_input = next(
        item for item in original_inputs if item.role is AssemblyComponentRole.TRIGGER_PUMP
    )
    pump_feature_id = pump_input.feature_id
    binding = bind_design_model_parent(
        scan,
        actor_id="clearance-test-operator",
        reason="Bind synthetic dip tube to the exact pump Scan Master parent.",
        created_at_utc="2026-10-04T18:00:00Z",
    )
    dip_tube = create_dip_tube_component(
        binding,
        pump_model,
        expected_trigger_pump_revision_id=pump_model.revision_id,
        trigger_pump_feature_id=pump_feature_id,
        component_id="clearance-test-dip-tube",
        semantic_key="tube-centerline",
        path=DipTubePath.straight((0.0, 0.0, 0.0), (0.0, 0.0, -10.0)),
        length=10.0,
        diameter=1.0,
        actor_id="clearance-test-operator",
        reason="Create explicit synthetic dip-tube for proxy diagnostics.",
        created_at_utc="2026-10-04T18:00:00Z",
    )
    inputs = tuple(
        AssemblyComponentInput(
            AssemblyComponentRole.DIP_TUBE,
            dip_tube.model,
            dip_tube.revision_id,
            dip_tube.feature_id,
        )
        if item.role is AssemblyComponentRole.DIP_TUBE
        else item
        for item in original_inputs
    )
    graph = create_parametric_assembly_graph(
        inputs,
        expected_component_revision_ids={item.role: item.model.revision_id for item in inputs},
        actor_id="clearance-test-operator",
        reason="Pin synthetic assembly for candidate clearance tests.",
        created_at_utc="2026-10-04T18:00:00Z",
    )
    refs = {item.role: item for item in graph.components}
    placements = tuple(
        AssemblyComponentPlacement(
            role,
            refs[role].model_revision_id,
            refs[role].feature_id,
            f"placement-{role.value}-v1",
            _IDENTITY,
        )
        for role in sorted(AssemblyComponentRole, key=lambda item: item.value)
    )
    models = {item.role: item.model for item in inputs}
    return graph, inputs, dip_tube, placements, models, refs


def _proxy(role, model, feature_id, minimum, maximum):
    preview = DesignPreview(
        TriangleMeshData(_box(minimum, maximum), ((0, 1, 2),)),
        model.revision_id,
        model.fitted_to_scan_master_revision_id,
        model.scan_master_geometry_sha256,
        model.parent_binding_revision_id,
        model.scale_state,
        model.coordinate_unit,
        model.physical_accuracy_validation_status,
        model.mold_use_authorized,
        ((feature_id, tuple(range(8))),),
    )
    return AssemblyComponentProxy.from_preview(role, model, feature_id, preview)


def _run(graph, inputs, tube, placements, models, refs, boxes, *, tolerance=0.0):
    proxies = tuple(
        AssemblyComponentProxy.unsupported(
            role, models[role], refs[role].feature_id, "preview_not_available"
        )
        if bounds is None
        else _proxy(role, models[role], refs[role].feature_id, *bounds)
        for role, bounds in sorted(boxes.items(), key=lambda item: item[0].value)
    )
    return diagnose_assembly_clearance(
        graph, inputs, tube, placements, proxies, clearance_tolerance=tolerance
    )


def test_separated_proxies_and_dip_tube_report_ordered_clearances(tmp_path: Path) -> None:
    graph, inputs, tube, placements, models, refs = _scenario(tmp_path)
    boxes = {
        AssemblyComponentRole.BODY: ((-2.0, -2.0, -2.0), (2.0, 2.0, 2.0)),
        AssemblyComponentRole.CLOSURE: ((10.0, -2.0, -2.0), (12.0, 2.0, 2.0)),
        AssemblyComponentRole.TRIGGER_PUMP: ((20.0, -2.0, -2.0), (22.0, 2.0, 2.0)),
    }
    placed = tuple(
        AssemblyComponentPlacement(
            item.role,
            item.model_revision_id,
            item.feature_id,
            item.placement_revision_id,
            _translated(40.0) if item.role is AssemblyComponentRole.DIP_TUBE else item.transform,
        )
        for item in placements
    )
    result = _run(graph, inputs, tube, placed, models, refs, boxes)

    assert len(result.pair_diagnostics) == 6
    assert all(item.status is PairDiagnosticStatus.CLEARANCE for item in result.pair_diagnostics)
    assert tuple(
        (item.first_role.value, item.second_role.value) for item in result.pair_diagnostics
    ) == tuple(
        sorted((item.first_role.value, item.second_role.value) for item in result.pair_diagnostics)
    )
    assert result.placements == tuple(sorted(placed, key=lambda item: item.role.value))
    assert result.scale_state is graph.scale_state
    assert result.as_dict()["certified_fit_claimed"] is False
    assert result.as_dict()["manufacturing_interference_claimed"] is False


def test_overlapping_boxes_are_candidate_only_not_certified_collision(tmp_path: Path) -> None:
    graph, inputs, tube, placements, models, refs = _scenario(tmp_path)
    boxes = {
        AssemblyComponentRole.BODY: ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0)),
        AssemblyComponentRole.CLOSURE: ((0.5, -0.5, -0.5), (2.0, 0.5, 0.5)),
        AssemblyComponentRole.TRIGGER_PUMP: ((10.0, -1.0, -1.0), (11.0, 1.0, 1.0)),
    }
    result = _run(graph, inputs, tube, placements, models, refs, boxes)
    pair = next(
        item
        for item in result.pair_diagnostics
        if (item.first_role, item.second_role)
        == (AssemblyComponentRole.BODY, AssemblyComponentRole.CLOSURE)
    )
    assert pair.status is PairDiagnosticStatus.CANDIDATE_OVERLAP
    assert pair.overlap_depth_estimate == pytest.approx(0.5)
    assert pair.as_dict()["certified_fit_claimed"] is False


def test_clearance_at_tolerance_boundary_is_near_clearance(tmp_path: Path) -> None:
    graph, inputs, tube, placements, models, refs = _scenario(tmp_path)
    boxes = {
        AssemblyComponentRole.BODY: ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0)),
        AssemblyComponentRole.CLOSURE: ((3.0, -1.0, -1.0), (4.0, 1.0, 1.0)),
        AssemblyComponentRole.TRIGGER_PUMP: ((10.0, -1.0, -1.0), (11.0, 1.0, 1.0)),
    }
    result = _run(graph, inputs, tube, placements, models, refs, boxes, tolerance=2.0)
    pair = result.pair_diagnostics[0]
    assert (pair.first_role, pair.second_role) == (
        AssemblyComponentRole.BODY,
        AssemblyComponentRole.CLOSURE,
    )
    assert pair.status is PairDiagnosticStatus.NEAR_CLEARANCE
    assert pair.clearance_estimate == pytest.approx(2.0)


def test_unsupported_proxy_reports_unknown_cases_and_is_deterministic(tmp_path: Path) -> None:
    graph, inputs, tube, placements, models, refs = _scenario(tmp_path)
    boxes = {
        AssemblyComponentRole.BODY: ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0)),
        AssemblyComponentRole.CLOSURE: None,
        AssemblyComponentRole.TRIGGER_PUMP: ((10.0, -1.0, -1.0), (11.0, 1.0, 1.0)),
    }
    first = _run(graph, inputs, tube, placements, models, refs, boxes)
    repeated = _run(graph, inputs, tube, placements, models, refs, boxes)
    assert first == repeated
    assert first.revision_id == repeated.revision_id
    assert all(
        item.status is PairDiagnosticStatus.UNKNOWN_PROXY_UNSUPPORTED
        for item in first.pair_diagnostics
        if AssemblyComponentRole.CLOSURE in {item.first_role, item.second_role}
    )


def test_stale_placement_parent_is_rejected(tmp_path: Path) -> None:
    graph, inputs, tube, placements, models, refs = _scenario(tmp_path)
    boxes = {
        AssemblyComponentRole.BODY: ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0)),
        AssemblyComponentRole.CLOSURE: ((5.0, -1.0, -1.0), (6.0, 1.0, 1.0)),
        AssemblyComponentRole.TRIGGER_PUMP: ((10.0, -1.0, -1.0), (11.0, 1.0, 1.0)),
    }
    stale = (
        AssemblyComponentPlacement(
            AssemblyComponentRole.TRIGGER_PUMP,
            "design-model:stale",
            refs[AssemblyComponentRole.TRIGGER_PUMP].feature_id,
            "placement-stale",
            _IDENTITY,
        ),
        *tuple(item for item in placements if item.role is not AssemblyComponentRole.TRIGGER_PUMP),
    )
    with pytest.raises(AssemblyClearanceError, match="placement_component_pin_stale"):
        _run(graph, inputs, tube, stale, models, refs, boxes)
