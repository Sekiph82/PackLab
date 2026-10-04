from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, replace

import pytest

from packlab_core.cad_adapter import _registered_shape_build
from packlab_core.cad_brep import _representation_from_lineage
from packlab_core.design_model import (
    DesignModelFeatureReference,
    FeatureKind,
    PackageFamily,
    create_standalone_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    create_standalone_design_geometry_root,
)
from packlab_core.label_zone import (
    LabelZoneBoundary,
    LabelZoneError,
    LabelZoneKind,
    create_label_zone,
)
from packlab_core.reconstruction import ScaleState

PROJECT_ID = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
NOW = "2026-10-04T12:00:00Z"
COMPONENT_ID = "package-body"
BODY_ID = stable_feature_id(COMPONENT_ID, FeatureKind.BODY, "main-body")
NECK_ID = stable_feature_id(COMPONENT_ID, FeatureKind.NECK, "neck-finish")
BOUNDARY = LabelZoneBoundary(0.1, 0.2, 0.8, 0.9)


def _model(
    scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED,
    *,
    label: str = "fixture",
    include_neck: bool = True,
):
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    root = create_standalone_design_geometry_root(
        project_id=PROJECT_ID,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id=f"nominal-input:{label}",
        scale_state=scale_state,
        unit_provenance_id=f"unit-choice:{unit}",
        actor_id="operator-1",
        reason=f"Create a label zone test model: {label}.",
        created_at_utc=NOW,
    )
    features = [DesignModelFeatureReference(BODY_ID, COMPONENT_ID, FeatureKind.BODY, "main-body")]
    if include_neck:
        features.append(
            DesignModelFeatureReference(NECK_ID, COMPONENT_ID, FeatureKind.NECK, "neck-finish")
        )
    return create_standalone_design_model_revision(
        root,
        package_family=PackageFamily.BOTTLE,
        features=tuple(features),
        actor_id="operator-1",
        reason=f"Create a label zone test model: {label}.",
        created_at_utc=NOW,
    )


def _representation(model, feature_ids: tuple[str, ...] = (BODY_ID,)):
    primitive = importlib.import_module("OCP.BRepPrimAPI")
    shape = primitive.BRepPrimAPI_MakeBox(100.0, 60.0, 40.0).Shape()
    shape_build = _registered_shape_build(model, "label-zone-fixture-op", feature_ids, shape, 1)
    return _representation_from_lineage(
        model,
        "label-zone-fixture-op",
        feature_ids,
        shape_build,
        source_feature_ids=feature_ids,
    )


def _zone(kind: LabelZoneKind = LabelZoneKind.FRONT, *, scale_state=ScaleState.METRIC_UNVERIFIED):
    model = _model(scale_state)
    return create_label_zone(
        model,
        _representation(model),
        zone_kind=kind,
        component_id=COMPONENT_ID,
        feature_id=BODY_ID,
        boundary=BOUNDARY,
    )


@pytest.mark.parametrize("kind", [LabelZoneKind.FRONT, LabelZoneKind.BACK, LabelZoneKind.WRAP])
def test_zone_kinds_pin_exact_source_and_serialize_as_geometric_intent(kind: LabelZoneKind) -> None:
    model = _model()
    representation = _representation(model)
    zone = create_label_zone(
        model,
        representation,
        zone_kind=kind,
        component_id=COMPONENT_ID,
        feature_id=BODY_ID,
        boundary=BOUNDARY,
    )
    value = zone.as_dict()
    assert zone.zone_kind is kind
    assert zone.zone_id.startswith("label-zone:")
    assert zone.source_design_model_revision_id == model.revision_id
    assert zone.source_brep_revision_id == representation.revision_id
    assert zone.source_brep_geometry_sha256 == representation.geometry_sha256
    assert zone.parent_authority_revision_id == model.standalone_root.revision_id
    assert zone.coordinate_unit == "mm_unverified"
    assert value["placement"]["coordinate_frame"] == "FEATURE_NORMALIZED_UV"
    assert value["placement"]["coordinate_unit"] == "unitless_normalized"
    assert value["artwork_bytes_included"] is False
    assert value["artwork_affects_identity"] is False
    assert value["physical_fit_inferred"] is False
    assert value["manufacturing_suitability_inferred"] is False
    assert "image" not in str(value).lower()
    assert "artwork" not in str(value["placement"]).lower()


def test_zone_identity_is_deterministic_and_independent_of_artwork_inputs() -> None:
    first = _zone()
    no_artwork = _zone()
    artwork_a = {"image_bytes": b"artwork A", "digest": "a" * 64}
    artwork_b = {"image_bytes": b"different artwork", "digest": "b" * 64}
    with_artwork_a = _zone()
    with_artwork_b = _zone()
    assert artwork_a != artwork_b
    assert first.zone_id == no_artwork.zone_id
    assert with_artwork_a.zone_id == with_artwork_b.zone_id == first.zone_id
    assert first.as_dict() == no_artwork.as_dict()


def test_zone_identity_changes_with_geometry_intent_or_authority_revision() -> None:
    original = _zone()
    model = _model()
    representation = _representation(model)
    moved = create_label_zone(
        model,
        representation,
        zone_kind=LabelZoneKind.FRONT,
        component_id=COMPONENT_ID,
        feature_id=BODY_ID,
        boundary=LabelZoneBoundary(0.2, 0.2, 0.8, 0.9),
    )
    other_kind = _zone(LabelZoneKind.BACK)
    other_model = _model(label="other-source")
    other_authority = create_label_zone(
        other_model,
        _representation(other_model),
        zone_kind=LabelZoneKind.FRONT,
        component_id=COMPONENT_ID,
        feature_id=BODY_ID,
        boundary=BOUNDARY,
    )
    assert len({original.zone_id, moved.zone_id, other_kind.zone_id, other_authority.zone_id}) == 4


def test_zone_and_boundary_are_immutable() -> None:
    zone = _zone()
    with pytest.raises(FrozenInstanceError):
        zone.zone_kind = LabelZoneKind.BACK  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        zone.boundary.u_min = 0.3  # type: ignore[misc]


@pytest.mark.parametrize(
    ("values", "error"),
    [
        ((float("nan"), 0.0, 1.0, 1.0), "label_zone_u_min_must_be_finite_number"),
        ((0.0, 0.0, float("inf"), 1.0), "label_zone_u_max_must_be_finite_number"),
        ((10**10000, 0.0, 1.0, 1.0), "label_zone_u_min_must_be_finite_number"),
        ((-0.1, 0.0, 0.5, 1.0), "label_zone_u_bounds_invalid"),
        ((0.0, 0.0, 1.1, 1.0), "label_zone_u_bounds_invalid"),
        ((0.5, 0.0, 0.5, 1.0), "label_zone_u_bounds_invalid"),
        ((0.0, 0.7, 1.0, 0.7), "label_zone_v_bounds_invalid"),
        ((True, 0.0, 1.0, 1.0), "label_zone_u_min_must_be_finite_number"),
    ],
)
def test_boundary_rejects_non_finite_unbounded_or_empty_placement(values, error: str) -> None:
    with pytest.raises(LabelZoneError, match=error):
        LabelZoneBoundary(*values)


def test_stale_or_deleted_feature_is_rejected_without_retargeting() -> None:
    model = _model(include_neck=False)
    representation = _representation(model)
    with pytest.raises(LabelZoneError, match="feature_reference_stale_or_deleted"):
        create_label_zone(
            model,
            representation,
            zone_kind=LabelZoneKind.FRONT,
            component_id=COMPONENT_ID,
            feature_id=NECK_ID,
            boundary=BOUNDARY,
        )


def test_component_mismatch_and_feature_outside_exact_brep_lineage_are_rejected() -> None:
    model = _model()
    representation = _representation(model)
    with pytest.raises(LabelZoneError, match="component_feature_mismatch"):
        create_label_zone(
            model,
            representation,
            zone_kind=LabelZoneKind.FRONT,
            component_id="different-component",
            feature_id=BODY_ID,
            boundary=BOUNDARY,
        )
    with pytest.raises(LabelZoneError, match="feature_not_in_brep_lineage"):
        create_label_zone(
            model,
            representation,
            zone_kind=LabelZoneKind.BACK,
            component_id=COMPONENT_ID,
            feature_id=NECK_ID,
            boundary=BOUNDARY,
        )


def test_stale_design_model_and_brep_pair_is_rejected() -> None:
    model = _model(label="one")
    other_model = _model(label="two")
    with pytest.raises(LabelZoneError, match="model_cad_authority_mismatch"):
        create_label_zone(
            model,
            _representation(other_model),
            zone_kind=LabelZoneKind.FRONT,
            component_id=COMPONENT_ID,
            feature_id=BODY_ID,
            boundary=BOUNDARY,
        )


@pytest.mark.parametrize(
    ("scale_state", "coordinate_unit"),
    [
        (ScaleState.RELATIVE, "reconstruction_units"),
        (ScaleState.METRIC_UNVERIFIED, "mm_unverified"),
    ],
)
def test_scale_state_and_unit_are_preserved(scale_state: ScaleState, coordinate_unit: str) -> None:
    zone = _zone(scale_state=scale_state)
    assert zone.scale_state is scale_state
    assert zone.coordinate_unit == coordinate_unit
    assert zone.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert zone.mold_use_authorized is False
    with pytest.raises(LabelZoneError, match="coordinate_unit_mismatch|identity_mismatch"):
        replace(zone, coordinate_unit="mm")


def test_serialization_is_canonical_json_and_excludes_artwork_payloads() -> None:
    first = _zone().as_dict()
    second = _zone().as_dict()

    def encode(value: object) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)

    assert encode(first) == encode(second)
    assert not {"image_bytes", "artwork_bytes", "artwork_digest", "image_digest"}.intersection(
        first
    )
    assert first["artwork_bytes_included"] is False
