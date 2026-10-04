from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from tests.core.test_mating_references import _create as create_mating_references
from tests.core.test_mating_references import _fixture as mating_fixture
from tests.core.test_trigger_pump_library import _fixture as library_fixture

from packlab_core.assembly_graph import (
    AssemblyComponentInput,
    AssemblyComponentRole,
    create_parametric_assembly_graph,
)
from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    PackageFamily,
    create_design_model_revision,
    revise_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.mating_references import MatingReferenceStatus
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import mesh_sha256
from packlab_core.trigger_pump_alignment import (
    TriggerPumpAlignmentError,
    TriggerPumpAttachmentFrame,
    align_library_trigger_pump,
)
from packlab_core.trigger_pump_library import import_local_trigger_pump_component

ACTOR = "alignment-fixture-operator"
CREATED = "2026-10-04T15:00:00Z"


def _setup(tmp_path: Path):
    scan, geometry, source_model, neck, cap, neck_sections, closure_sections = mating_fixture()
    mating = create_mating_references(
        (scan, geometry, source_model, neck, cap, neck_sections, closure_sections)
    )
    assert mating.model is not None
    body = DesignModelFeatureReference(
        stable_feature_id("bottle-body", FeatureKind.BODY, "bottle-body"),
        "bottle-body",
        FeatureKind.BODY,
        "bottle-body",
    )
    body_closure_model = revise_design_model_revision(
        mating.model,
        parameters=mating.model.parameters,
        features=(*mating.model.features, body),
        actor_id=ACTOR,
        reason="Add body role to the exact synthetic mating source graph.",
        created_at_utc=CREATED,
    )
    binding = bind_design_model_parent(
        scan,
        actor_id=ACTOR,
        reason="Bind synthetic library component model to the same captured parent.",
        created_at_utc=CREATED,
    )
    pump = DesignModelFeatureReference(
        stable_feature_id("synthetic-trigger-pump", FeatureKind.TRIGGER_PUMP, "actuator-mount-v1"),
        "synthetic-trigger-pump",
        FeatureKind.TRIGGER_PUMP,
        "actuator-mount-v1",
    )
    pump_model = create_design_model_revision(
        binding,
        package_family=PackageFamily.OTHER,
        features=(pump,),
        actor_id=ACTOR,
        reason="Create synthetic trigger/pump component Design Model.",
        created_at_utc=CREATED,
    )
    tube = DesignModelFeatureReference(
        stable_feature_id("synthetic-dip-tube", FeatureKind.DIP_TUBE, "tube-reference"),
        "synthetic-dip-tube",
        FeatureKind.DIP_TUBE,
        "tube-reference",
    )
    tube_model = create_design_model_revision(
        binding,
        package_family=PackageFamily.OTHER,
        features=(tube,),
        actor_id=ACTOR,
        reason="Create synthetic dip tube component Design Model.",
        created_at_utc=CREATED,
    )
    inputs = (
        AssemblyComponentInput(
            AssemblyComponentRole.BODY,
            body_closure_model,
            body_closure_model.revision_id,
            body.feature_id,
        ),
        AssemblyComponentInput(
            AssemblyComponentRole.CLOSURE,
            body_closure_model,
            body_closure_model.revision_id,
            cap.feature_id,
        ),
        AssemblyComponentInput(
            AssemblyComponentRole.TRIGGER_PUMP,
            pump_model,
            pump_model.revision_id,
            pump.feature_id,
        ),
        AssemblyComponentInput(
            AssemblyComponentRole.DIP_TUBE,
            tube_model,
            tube_model.revision_id,
            tube.feature_id,
        ),
    )
    graph = create_parametric_assembly_graph(
        inputs,
        expected_component_revision_ids={item.role: item.model.revision_id for item in inputs},
        actor_id=ACTOR,
        reason="Build exact synthetic bottle/closure/pump/tube assembly graph.",
        created_at_utc=CREATED,
    )
    library_fixture(tmp_path / "library")
    library = import_local_trigger_pump_component(tmp_path / "library", "manifest.json")
    attachment = TriggerPumpAttachmentFrame(
        library.component_id,
        library.import_id,
        library.attachment_semantic_key,
        library.coordinate_unit,
        graph.scale_state,
        mating.closure_plane.origin,
        (0.0, 0.0, 1.0),
        (0.0, 0.0, 1.0),
    )
    kwargs = {
        "expected_body_model_revision_id": body_closure_model.revision_id,
        "expected_closure_model_revision_id": body_closure_model.revision_id,
        "expected_trigger_pump_model_revision_id": pump_model.revision_id,
        "expected_mating_source_model_revision_id": source_model.revision_id,
    }
    return (
        scan,
        source_model,
        body_closure_model,
        pump_model,
        inputs,
        graph,
        mating,
        library,
        attachment,
        kwargs,
    )


def test_identity_and_known_rigid_alignment_are_deterministic_without_component_mutation(
    tmp_path: Path,
) -> None:
    (
        scan,
        _source_model,
        body_closure_model,
        _pump_model,
        inputs,
        graph,
        mating,
        library,
        attachment,
        kwargs,
    ) = _setup(tmp_path)
    scan_digest = mesh_sha256(scan.mesh)
    original_body = body_closure_model.as_dict()

    identity = align_library_trigger_pump(library, attachment, graph, inputs, mating, **kwargs)
    repeated = align_library_trigger_pump(library, attachment, graph, inputs, mating, **kwargs)
    assert identity == repeated
    assert identity.revision_id == repeated.revision_id
    assert identity.placement_matrix == (
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
    payload = identity.as_dict()
    assert payload["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert payload["bottle_geometry_modified"] is False
    assert payload["thread_compatibility_claimed"] is False
    assert payload["seal_compatibility_claimed"] is False
    assert identity.body_model_revision_id == body_closure_model.revision_id
    assert identity.closure_model_revision_id == body_closure_model.revision_id
    assert body_closure_model.as_dict() == original_body
    assert mesh_sha256(scan.mesh) == scan_digest

    known = replace(
        attachment,
        origin=(0.0, 0.0, 0.0),
        axis=(1.0, 0.0, 0.0),
        plane_normal=(1.0, 0.0, 0.0),
    )
    rotated = align_library_trigger_pump(library, known, graph, inputs, mating, **kwargs)
    assert rotated.placement_matrix[:12] == pytest.approx(
        (0.0, 0.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 15.5)
    )


def test_axis_plane_and_mating_status_mismatches_reject(tmp_path: Path) -> None:
    (_scan, _source, _body, _pump, inputs, graph, mating, library, attachment, kwargs) = _setup(
        tmp_path
    )
    invalid_frame = replace(attachment, axis=(1.0, 0.0, 0.0))
    with pytest.raises(TriggerPumpAlignmentError, match="axis_plane_mismatch"):
        align_library_trigger_pump(library, invalid_frame, graph, inputs, mating, **kwargs)

    unaligned = replace(
        mating,
        status=MatingReferenceStatus.AXIS_MISMATCH_REVIEW_REQUIRED,
        review_required=True,
    )
    with pytest.raises(TriggerPumpAlignmentError, match="mating_reference_stale_or_incompatible"):
        align_library_trigger_pump(library, attachment, graph, inputs, unaligned, **kwargs)


def test_stale_component_parent_and_unit_scale_mismatch_reject(tmp_path: Path) -> None:
    (_scan, _source, _body, _pump, inputs, graph, mating, library, attachment, kwargs) = _setup(
        tmp_path
    )
    stale_inputs = (
        replace(inputs[0], expected_model_revision_id="design-model:stale"),
        *inputs[1:],
    )
    with pytest.raises(TriggerPumpAlignmentError, match="component_revision_stale"):
        align_library_trigger_pump(library, attachment, graph, stale_inputs, mating, **kwargs)

    with pytest.raises(TriggerPumpAlignmentError, match="unit_or_scale_mismatch"):
        align_library_trigger_pump(
            library,
            replace(attachment, coordinate_unit="reconstruction_units"),
            graph,
            inputs,
            mating,
            **kwargs,
        )
    with pytest.raises(TriggerPumpAlignmentError, match="unit_or_scale_mismatch"):
        align_library_trigger_pump(
            library,
            replace(attachment, scale_state=ScaleState.RELATIVE),
            graph,
            inputs,
            mating,
            **kwargs,
        )

    stale_parent = replace(mating, source_model_revision_id="design-model:stale")
    with pytest.raises(TriggerPumpAlignmentError, match="mating_reference_stale_or_incompatible"):
        align_library_trigger_pump(library, attachment, graph, inputs, stale_parent, **kwargs)
