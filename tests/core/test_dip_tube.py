from __future__ import annotations

from dataclasses import replace

import pytest
from tests.core.test_mating_references import _fixture as mating_fixture

from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    PackageFamily,
    create_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.dip_tube import (
    CubicBezierSegment,
    DipTubeError,
    DipTubePath,
    create_dip_tube_component,
    edit_dip_tube_component,
)
from packlab_core.reconstruction import ScaleState

ACTOR = "dip-tube-fixture-operator"
CREATED = "2026-10-04T16:00:00Z"


def _fixture():
    scan, _geometry, _source_model, *_ = mating_fixture()
    binding = bind_design_model_parent(
        scan,
        actor_id=ACTOR,
        reason="Bind synthetic dip-tube fixture to exact deferred Scan Master parent.",
        created_at_utc=CREATED,
    )
    pump_feature = DesignModelFeatureReference(
        stable_feature_id("fixture-pump", FeatureKind.TRIGGER_PUMP, "outlet"),
        "fixture-pump",
        FeatureKind.TRIGGER_PUMP,
        "outlet",
    )
    pump = create_design_model_revision(
        binding,
        package_family=PackageFamily.OTHER,
        features=(pump_feature,),
        actor_id=ACTOR,
        reason="Create synthetic pump component with explicit outlet reference.",
        created_at_utc=CREATED,
    )
    return binding, pump, pump_feature


def _create(path: DipTubePath, length: float | None = None):
    binding, pump, feature = _fixture()
    return create_dip_tube_component(
        binding,
        pump,
        expected_trigger_pump_revision_id=pump.revision_id,
        trigger_pump_feature_id=feature.feature_id,
        component_id="fixture-dip-tube",
        semantic_key="tube-centerline",
        path=path,
        length=path.length() if length is None else length,
        diameter=3.2,
        actor_id=ACTOR,
        reason="Create authored synthetic dip-tube parameters.",
        created_at_utc=CREATED,
    )


def test_straight_and_curved_paths_create_deterministic_unverified_components() -> None:
    straight = DipTubePath.straight((0.0, 0.0, 0.0), (0.0, 0.0, -100.0))
    curve = DipTubePath(
        (
            CubicBezierSegment(
                (
                    (0.0, 0.0, 0.0),
                    (10.0, 0.0, -30.0),
                    (10.0, 10.0, -70.0),
                    (0.0, 10.0, -100.0),
                )
            ),
        )
    )
    first = _create(straight)
    same = _create(straight)
    curved = _create(curve)

    assert straight.length() == pytest.approx(100.0)
    assert curve.length() > straight.length()
    assert first == same
    assert first.revision_id == same.revision_id
    assert curved.revision_id != first.revision_id
    assert first.model.scale_state is ScaleState.METRIC_UNVERIFIED
    assert first.model.coordinate_unit == "mm_unverified"
    assert first.model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.model.mold_use_authorized is False
    payload = first.as_dict()
    assert payload["geometry_generated"] is False
    assert payload["collision_checked"] is False
    assert payload["attachment"]["model_revision_id"]


def test_path_rejects_discontinuous_degenerate_and_over_limit_segments() -> None:
    first = CubicBezierSegment.straight((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    second = CubicBezierSegment.straight((1.0, 0.0, 1.0), (1.0, 0.0, 2.0))
    with pytest.raises(DipTubeError, match="discontinuous"):
        DipTubePath((first, second))
    with pytest.raises(DipTubeError, match="degenerate"):
        CubicBezierSegment.straight((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    with pytest.raises(DipTubeError, match="segment_count"):
        DipTubePath((first,) * 33)
    cusp = CubicBezierSegment(
        (
            (0.0, 0.0, 1.0),
            (1.0, 0.0, 1.0),
            (1.0, 0.0, 2.0),
            (1.0, 0.0, 3.0),
        )
    )
    with pytest.raises(DipTubeError, match="piecewise_smooth"):
        DipTubePath((first, cusp))


@pytest.mark.parametrize("length,diameter", [(0.0, 2.0), (-1.0, 2.0), (1.0, 0.0), (1.0, -2.0)])
def test_positive_length_and_diameter_are_required(length: float, diameter: float) -> None:
    binding, pump, feature = _fixture()
    with pytest.raises(DipTubeError, match="must_be_positive"):
        create_dip_tube_component(
            binding,
            pump,
            expected_trigger_pump_revision_id=pump.revision_id,
            trigger_pump_feature_id=feature.feature_id,
            component_id="fixture-dip-tube",
            semantic_key="tube-centerline",
            path=DipTubePath.straight((0.0, 0.0, 0.0), (0.0, 0.0, -10.0)),
            length=length,
            diameter=diameter,
            actor_id=ACTOR,
            reason="Reject invalid authored dimensions.",
            created_at_utc=CREATED,
        )


def test_attachment_revision_and_feature_are_exact() -> None:
    binding, pump, feature = _fixture()
    path = DipTubePath.straight((0.0, 0.0, 0.0), (0.0, 0.0, -10.0))
    with pytest.raises(DipTubeError, match="revision_stale"):
        create_dip_tube_component(
            binding,
            pump,
            expected_trigger_pump_revision_id="trigger-pump:stale",
            trigger_pump_feature_id=feature.feature_id,
            component_id="fixture-dip-tube",
            semantic_key="tube-centerline",
            path=path,
            length=10.0,
            diameter=3.2,
            actor_id=ACTOR,
            reason="Reject stale pump parent.",
            created_at_utc=CREATED,
        )
    with pytest.raises(DipTubeError, match="feature_stale"):
        create_dip_tube_component(
            binding,
            pump,
            expected_trigger_pump_revision_id=pump.revision_id,
            trigger_pump_feature_id="packlab-feature:missing",
            component_id="fixture-dip-tube",
            semantic_key="tube-centerline",
            path=path,
            length=10.0,
            diameter=3.2,
            actor_id=ACTOR,
            reason="Reject stale pump feature.",
            created_at_utc=CREATED,
        )
    wrong_kind = replace(
        feature,
        feature_id=stable_feature_id("fixture-pump", FeatureKind.DIP_TUBE, "outlet"),
        feature_kind=FeatureKind.DIP_TUBE,
    )
    incompatible_pump = create_design_model_revision(
        binding,
        package_family=PackageFamily.OTHER,
        features=(wrong_kind,),
        actor_id=ACTOR,
        reason="Create incompatible synthetic pump attachment feature kind.",
        created_at_utc=CREATED,
    )
    with pytest.raises(DipTubeError, match="feature_invalid"):
        create_dip_tube_component(
            binding,
            incompatible_pump,
            expected_trigger_pump_revision_id=incompatible_pump.revision_id,
            trigger_pump_feature_id=wrong_kind.feature_id,
            component_id="fixture-dip-tube",
            semantic_key="tube-centerline",
            path=path,
            length=10.0,
            diameter=3.2,
            actor_id=ACTOR,
            reason="Reject attachment to a non-pump feature.",
            created_at_utc=CREATED,
        )


def test_collision_independent_edit_creates_new_exact_parented_revision() -> None:
    tube = _create(DipTubePath.straight((0.0, 0.0, 0.0), (0.0, 0.0, -10.0)))
    _binding, pump, feature = _fixture()
    edited_path = DipTubePath.straight((0.0, 0.0, 0.0), (0.0, 0.0, -12.0))
    edited = edit_dip_tube_component(
        tube,
        pump,
        expected_current_revision_id=tube.revision_id,
        expected_trigger_pump_revision_id=pump.revision_id,
        trigger_pump_feature_id=feature.feature_id,
        path=edited_path,
        length=12.0,
        diameter=3.5,
        actor_id=ACTOR,
        reason="Edit authored dip-tube length and diameter parameters.",
        created_at_utc=CREATED,
    )

    assert edited.revision_id != tube.revision_id
    assert edited.model.previous_revision_id == tube.revision_id
    assert edited.model.parent_binding_revision_id == tube.model.parent_binding_revision_id
    assert (
        edited.model.fitted_to_scan_master_revision_id
        == tube.model.fitted_to_scan_master_revision_id
    )
    assert edited.model.scan_master_geometry_sha256 == tube.model.scan_master_geometry_sha256
    assert edited.model.scale_state is tube.model.scale_state
    assert edited.model.coordinate_unit == "mm_unverified"
    assert edited.attachment.trigger_pump_model_revision_id == pump.revision_id
    assert edited.length == pytest.approx(12.0)
    assert edited.diameter == pytest.approx(3.5)
    with pytest.raises(DipTubeError, match="revision_stale"):
        edit_dip_tube_component(
            tube,
            pump,
            expected_current_revision_id="dip-tube:stale",
            expected_trigger_pump_revision_id=pump.revision_id,
            trigger_pump_feature_id=feature.feature_id,
            path=edited_path,
            length=12.0,
            diameter=3.5,
            actor_id=ACTOR,
            reason="Reject stale edit input.",
            created_at_utc=CREATED,
        )
