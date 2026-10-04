from __future__ import annotations

from pathlib import Path

import pytest
from tests.core.test_trigger_pump_alignment import _setup as alignment_setup

from packlab_core.assembly_graph import (
    AssemblyComponentInput,
    AssemblyComponentRole,
    create_parametric_assembly_graph,
)
from packlab_core.assembly_variant_swap import (
    AssemblyVariantSwapError,
    swap_trigger_pump_variant,
)
from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    PackageFamily,
    create_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.dip_tube import DipTubePath, create_dip_tube_component

_ACTOR = "variant-swap-test-operator"
_CREATED = "2026-10-04T19:00:00Z"


def _scenario(tmp_path: Path):
    scan, _source, body_model, _pump, original_inputs, _graph, _mating, _library, _kwargs = (
        alignment_setup(tmp_path)
    )
    old_pump_input = next(
        item for item in original_inputs if item.role is AssemblyComponentRole.TRIGGER_PUMP
    )
    binding = bind_design_model_parent(
        scan,
        actor_id=_ACTOR,
        reason="Bind synthetic variant and tube to the exact Scan Master parent.",
        created_at_utc=_CREATED,
    )
    tube = create_dip_tube_component(
        binding,
        old_pump_input.model,
        expected_trigger_pump_revision_id=old_pump_input.model.revision_id,
        trigger_pump_feature_id=old_pump_input.feature_id,
        component_id="swap-test-dip-tube",
        semantic_key="tube-centerline",
        path=DipTubePath.straight((0.0, 0.0, 0.0), (0.0, 0.0, -30.0)),
        length=30.0,
        diameter=3.0,
        actor_id=_ACTOR,
        reason="Create a synthetic dip tube for variant-swap regression.",
        created_at_utc=_CREATED,
    )
    current_components = tuple(
        AssemblyComponentInput(
            AssemblyComponentRole.DIP_TUBE,
            tube.model,
            tube.revision_id,
            tube.feature_id,
        )
        if item.role is AssemblyComponentRole.DIP_TUBE
        else item
        for item in original_inputs
    )
    graph = create_parametric_assembly_graph(
        current_components,
        expected_component_revision_ids={
            item.role: item.model.revision_id for item in current_components
        },
        actor_id=_ACTOR,
        reason="Create pre-swap four-role assembly graph.",
        created_at_utc=_CREATED,
    )
    old_pump_feature = next(
        item
        for item in old_pump_input.model.features
        if item.feature_id == old_pump_input.feature_id
    )
    candidate_feature = DesignModelFeatureReference(
        stable_feature_id(
            "alternate-trigger-pump", FeatureKind.TRIGGER_PUMP, old_pump_feature.semantic_key
        ),
        "alternate-trigger-pump",
        FeatureKind.TRIGGER_PUMP,
        old_pump_feature.semantic_key,
    )
    candidate_model = create_design_model_revision(
        binding,
        package_family=PackageFamily.OTHER,
        features=(candidate_feature,),
        actor_id=_ACTOR,
        reason="Create synthetic alternate trigger-pump variant with matching outlet semantic.",
        created_at_utc=_CREATED,
    )
    args = {
        "expected_current_graph_revision_id": graph.revision_id,
        "expected_current_dip_tube_revision_id": tube.revision_id,
        "expected_candidate_pump_revision_id": candidate_model.revision_id,
        "candidate_pump_feature_id": candidate_feature.feature_id,
        "actor_id": _ACTOR,
        "reason": "Swap to the explicitly compatible alternate outlet variant.",
        "created_at_utc": _CREATED,
    }
    return (
        graph,
        current_components,
        tube,
        candidate_model,
        candidate_feature,
        body_model,
        args,
        binding,
    )


def _swap(scenario):
    graph, components, tube, candidate, _feature, _body_model, args, _binding = scenario
    return swap_trigger_pump_variant(graph, components, tube, candidate, **args)


def test_compatible_swap_is_deterministic_preserves_bottle_and_keeps_old_history(
    tmp_path: Path,
) -> None:
    scenario = _scenario(tmp_path)
    graph, components, tube, _candidate, _feature, _body_model, _args, _binding = scenario
    body_before = next(item.model for item in components if item.role is AssemblyComponentRole.BODY)
    closure_before = next(
        item.model for item in components if item.role is AssemblyComponentRole.CLOSURE
    )
    body_bytes_before = body_before.as_dict()
    closure_bytes_before = closure_before.as_dict()
    scan_parent_before = (
        body_before.fitted_to_scan_master_revision_id,
        body_before.scan_master_geometry_sha256,
    )
    graph_bytes_before = graph.as_dict()
    first = _swap(scenario)
    repeated = _swap(scenario)

    assert first.revision == repeated.revision
    assert first.snapshot.graph.revision_id == repeated.snapshot.graph.revision_id
    assert first.snapshot.graph.revision_id != graph.revision_id
    assert first.snapshot.graph.as_dict() != graph_bytes_before
    assert first.revision.previous_assembly_graph_revision_id == graph.revision_id
    assert first.revision.body_model_revision_id == body_before.revision_id
    assert first.revision.scan_master_revision_id == scan_parent_before[0]
    assert first.revision.scan_master_geometry_sha256 == scan_parent_before[1]
    assert body_before.as_dict() == body_bytes_before
    assert next(
        item for item in first.snapshot.components if item.role is AssemblyComponentRole.BODY
    ) is next(item for item in components if item.role is AssemblyComponentRole.BODY)
    assert first.history.current.revision_id == first.snapshot.revision_id
    assert first.history.can_undo
    undone = first.history.undo()
    assert undone.current.graph is graph
    assert undone.current.revision_id == graph.revision_id
    redone = undone.redo()
    assert redone.current.revision_id == first.snapshot.revision_id
    assert redone.current.graph is first.snapshot.graph
    assert first.snapshot.components is not components
    assert closure_before.as_dict() == closure_bytes_before
    updated_tube_model = next(
        item.model
        for item in first.snapshot.components
        if item.role is AssemblyComponentRole.DIP_TUBE
    )
    assert tube.revision_id == first.revision.previous_dip_tube_model_revision_id
    assert first.revision.dip_tube_model_revision_id != tube.revision_id
    assert updated_tube_model.previous_revision_id == tube.revision_id
    old_parameters = {item.parameter_id: item.as_dict() for item in tube.model.parameters}
    updated_parameters = {
        item.parameter_id: item.as_dict() for item in updated_tube_model.parameters
    }
    for parameter_id in ("dip_tube.path", "dip_tube.length", "dip_tube.diameter"):
        assert updated_parameters[parameter_id] == old_parameters[parameter_id]
    assert updated_parameters["dip_tube.attachment"] != old_parameters["dip_tube.attachment"]
    assert (
        updated_parameters["dip_tube.attachment"]["value"]["model_revision_id"]
        == first.revision.trigger_pump_model_revision_id
    )
    assert first.revision.as_dict()["body_geometry_modified"] is False
    assert first.revision.as_dict()["scan_master_modified"] is False
    assert first.revision.as_dict()["physical_attachment_compatibility_claimed"] is False


def test_incompatible_attachment_semantic_fails_closed(tmp_path: Path) -> None:
    graph, components, tube, _candidate, _candidate_feature, _body, args, binding = _scenario(
        tmp_path
    )
    wrong_feature = DesignModelFeatureReference(
        stable_feature_id("alternate-trigger-pump", FeatureKind.TRIGGER_PUMP, "different-outlet"),
        "alternate-trigger-pump",
        FeatureKind.TRIGGER_PUMP,
        "different-outlet",
    )
    incompatible = create_design_model_revision(
        binding,
        package_family=PackageFamily.OTHER,
        features=(wrong_feature,),
        actor_id=_ACTOR,
        reason="Create pump variant with incompatible dip tube outlet semantic.",
        created_at_utc=_CREATED,
    )
    with pytest.raises(AssemblyVariantSwapError, match="attachment_semantic_incompatible"):
        swap_trigger_pump_variant(
            graph,
            components,
            tube,
            incompatible,
            **(
                args
                | {
                    "expected_candidate_pump_revision_id": incompatible.revision_id,
                    "candidate_pump_feature_id": wrong_feature.feature_id,
                }
            ),
        )


def test_stale_candidate_and_current_graph_reject_without_mutation(tmp_path: Path) -> None:
    scenario = _scenario(tmp_path)
    graph, components, tube, candidate, _feature, _body, args, _binding = scenario
    original = graph.as_dict()
    with pytest.raises(AssemblyVariantSwapError, match="candidate_trigger_pump_revision_stale"):
        swap_trigger_pump_variant(
            graph,
            components,
            tube,
            candidate,
            **(args | {"expected_candidate_pump_revision_id": "design-model:stale"}),
        )
    with pytest.raises(AssemblyVariantSwapError, match="assembly_graph_revision_stale"):
        swap_trigger_pump_variant(
            graph,
            components,
            tube,
            candidate,
            **(args | {"expected_current_graph_revision_id": "assembly-graph:stale"}),
        )
    assert graph.as_dict() == original
