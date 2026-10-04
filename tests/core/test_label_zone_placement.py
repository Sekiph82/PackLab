from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest
from tests.core.test_design_model import _parent as captured_parent
from tests.core.test_label_zone import _model, _representation

from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    PackageFamily,
    create_design_model_revision,
    stable_feature_id,
)
from packlab_core.label_zone import (
    LabelZoneBoundary,
    LabelZoneKind,
    create_label_zone,
)
from packlab_core.label_zone_placement import (
    LabelZonePlacementError,
    canonical_label_zone_surface_frame,
    create_label_zone_placement_revision,
    edit_label_zone_placement,
)
from packlab_core.reconstruction import ScaleState

NOW = "2026-10-04T14:00:00Z"
BOUNDARY = LabelZoneBoundary(0.1, 0.1, 0.7, 0.8)
MOVED = LabelZoneBoundary(0.2, 0.15, 0.9, 0.85)


def _zone(kind: LabelZoneKind, *, parent="standalone", scale_state=ScaleState.METRIC_UNVERIFIED):
    if parent == "standalone":
        model = _model(scale_state)
    else:
        feature = DesignModelFeatureReference(
            stable_feature_id("captured-container", FeatureKind.BODY, "main-body"),
            "captured-container",
            FeatureKind.BODY,
            "main-body",
        )
        model = create_design_model_revision(
            captured_parent(scale_state),
            package_family=PackageFamily.BOTTLE,
            features=(feature,),
            actor_id="operator-1",
            reason="Create a captured-parent label-zone placement fixture.",
            created_at_utc=NOW,
        )
    feature = next(item for item in model.features if item.feature_kind is FeatureKind.BODY)
    representation = _representation(model, (feature.feature_id,))
    zone = create_label_zone(
        model,
        representation,
        zone_kind=kind,
        component_id=feature.component_id,
        feature_id=feature.feature_id,
        boundary=BOUNDARY,
    )
    return model, representation, zone


@pytest.mark.parametrize(
    ("kind", "normal", "u_axis", "v_axis", "seam"),
    [
        (LabelZoneKind.FRONT, "+Y", "+X", "+Z", None),
        (LabelZoneKind.BACK, "-Y", "-X", "+Z", None),
        (
            LabelZoneKind.WRAP,
            "RADIAL_OUTWARD",
            "AZIMUTHAL_FROM_FRONT_TOWARD_RIGHT",
            "+Z",
            "+Y",
        ),
    ],
)
def test_canonical_surface_frames_pin_orientation_and_normalized_bounds(
    kind: LabelZoneKind, normal: str, u_axis: str, v_axis: str, seam: str | None
) -> None:
    frame = canonical_label_zone_surface_frame(kind)
    assert frame.canonical_world_frame == "packlab_right_handed_x_right_y_front_z_up_v1"
    assert frame.surface_normal == normal
    assert frame.u_axis == u_axis
    assert frame.v_axis == v_axis
    assert frame.seam_direction == seam
    model, representation, zone = _zone(kind)
    revision = create_label_zone_placement_revision(
        zone,
        BOUNDARY,
        actor_id="operator-1",
        reason="Place the zone in its canonical surface frame.",
        created_at_utc=NOW,
    )
    value = revision.as_dict()
    assert revision.surface_frame == frame
    assert value["surface_frame"]["canonical_world_frame"] == frame.canonical_world_frame
    assert value["placement"]["coordinate_range"] == [0.0, 1.0]
    assert value["placement"]["boundary"] == BOUNDARY.as_dict()
    assert revision.label_zone.source_design_model_revision_id == model.revision_id
    assert revision.label_zone.source_brep_revision_id == representation.revision_id
    assert value["mutates_source_geometry"] is False


def test_initial_and_edit_revisions_are_deterministic_and_keep_zone_identity() -> None:
    _, _, zone = _zone(LabelZoneKind.FRONT)
    initial = create_label_zone_placement_revision(
        zone,
        BOUNDARY,
        actor_id="operator-1",
        reason="Initial front placement.",
        created_at_utc=NOW,
    )
    repeat = create_label_zone_placement_revision(
        zone,
        BOUNDARY,
        actor_id="operator-1",
        reason="Initial front placement.",
        created_at_utc=NOW,
    )
    edited = edit_label_zone_placement(
        initial,
        MOVED,
        actor_id="operator-1",
        reason="Move the front zone within its normalized surface domain.",
        created_at_utc="2026-10-04T14:01:00Z",
    )
    edited_repeat = edit_label_zone_placement(
        initial,
        MOVED,
        actor_id="operator-1",
        reason="Move the front zone within its normalized surface domain.",
        created_at_utc="2026-10-04T14:01:00Z",
    )
    assert initial.revision_id == repeat.revision_id
    assert edited.revision_id == edited_repeat.revision_id
    assert initial.revision_id != edited.revision_id
    assert edited.zone_id == initial.zone_id == zone.zone_id
    assert edited.previous_revision_id == initial.revision_id
    assert edited.boundary == MOVED
    with pytest.raises(FrozenInstanceError):
        edited.boundary.u_min = 0.4  # type: ignore[misc]


def test_invalid_boundaries_and_non_finite_values_are_rejected_as_out_of_surface():
    with pytest.raises(ValueError, match="label_zone_u_bounds_invalid"):
        LabelZoneBoundary(-0.01, 0.0, 0.5, 1.0)
    with pytest.raises(ValueError, match="label_zone_v_bounds_invalid"):
        LabelZoneBoundary(0.0, 0.0, 1.0, 1.01)
    with pytest.raises(ValueError, match="label_zone_u_min_must_be_finite_number"):
        LabelZoneBoundary(float("nan"), 0.0, 1.0, 1.0)


@pytest.mark.parametrize(
    ("parent", "scale_state", "unit"),
    [
        ("captured", ScaleState.METRIC_UNVERIFIED, "mm_unverified"),
        ("captured", ScaleState.RELATIVE, "reconstruction_units"),
        ("standalone", ScaleState.RELATIVE, "reconstruction_units"),
        ("standalone", ScaleState.METRIC_UNVERIFIED, "mm_unverified"),
    ],
)
def test_captured_and_standalone_parent_and_unit_authority_are_preserved(
    parent: str, scale_state: ScaleState, unit: str
) -> None:
    model, representation, zone = _zone(
        LabelZoneKind.WRAP,
        parent=parent,
        scale_state=scale_state,
    )
    revision = create_label_zone_placement_revision(
        zone,
        BOUNDARY,
        actor_id="operator-2",
        reason="Place on the exact selected component feature.",
        created_at_utc=NOW,
    )
    assert revision.label_zone.parent_kind is model.parent_kind
    assert (
        revision.label_zone.parent_authority_revision_id
        == representation.parent_authority_revision_id
    )
    assert revision.label_zone.coordinate_unit == unit
    assert revision.label_zone.scale_state is scale_state
    assert revision.as_dict()["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert revision.as_dict()["mold_use_authorized"] is False


def test_edit_preserves_exact_source_and_does_not_mutate_model_or_brep() -> None:
    model, representation, zone = _zone(LabelZoneKind.BACK)
    before_model = model.as_dict()
    before_brep = representation.as_dict()
    first = create_label_zone_placement_revision(
        zone,
        BOUNDARY,
        actor_id="operator-1",
        reason="Initial back placement.",
        created_at_utc=NOW,
    )
    updated = edit_label_zone_placement(
        first,
        MOVED,
        actor_id="operator-1",
        reason="Adjust the normalized back boundary.",
        created_at_utc="2026-10-04T14:02:00Z",
    )
    assert updated.label_zone.source_design_model_revision_id == model.revision_id
    assert updated.label_zone.source_brep_revision_id == representation.revision_id
    assert model.as_dict() == before_model
    assert representation.as_dict() == before_brep


def test_revision_rejects_bad_previous_revision_and_non_utc_or_unbounded_metadata() -> None:
    _, _, zone = _zone(LabelZoneKind.FRONT)
    first = create_label_zone_placement_revision(
        zone,
        BOUNDARY,
        actor_id="operator-1",
        reason="Initial placement.",
        created_at_utc=NOW,
    )
    with pytest.raises(
        LabelZonePlacementError, match="previous_label_zone_placement_revision_required"
    ):
        edit_label_zone_placement(
            object(),  # type: ignore[arg-type]
            MOVED,
            actor_id="operator-1",
            reason="Invalid predecessor.",
            created_at_utc=NOW,
        )
    with pytest.raises(LabelZonePlacementError, match="created_at_must_be_utc_z"):
        create_label_zone_placement_revision(
            zone,
            BOUNDARY,
            actor_id="operator-1",
            reason="Invalid local time.",
            created_at_utc="2026-10-04T14:00:00+03:00",
        )
    assert json.dumps(first.as_dict(), sort_keys=True, allow_nan=False)
