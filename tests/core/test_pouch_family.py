from __future__ import annotations

import pytest

from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    create_standalone_design_geometry_root,
)
from packlab_core.design_serialization import deserialize_design_model, serialize_design_model
from packlab_core.pouch_family import (
    PouchArtworkAnchor,
    PouchFamilyDimensions,
    PouchFamilyError,
    build_pouch_family,
    edit_pouch_family,
)
from packlab_core.reconstruction import ScaleState

PROJECT = "pouch-family-project"
NOW = "2026-10-04T12:00:00Z"


def _root():
    return create_standalone_design_geometry_root(
        project_id=PROJECT,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id="nominal-input:operator-session-1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        unit_provenance_id="unit-selection:mm-unverified",
        actor_id="operator-1",
        reason="Start a nominal pouch design.",
        created_at_utc=NOW,
    )


def _dimensions():
    return PouchFamilyDimensions(
        overall_width=120.0,
        overall_height=180.0,
        thickness=8.0,
        top_seal_width=10.0,
        bottom_seal_width=12.0,
        left_seal_width=6.0,
        right_seal_width=6.0,
    )


def test_standalone_sachet_pouch_has_dimensions_seals_and_stable_artwork_surfaces():
    pouch = build_pouch_family(
        _root(),
        _dimensions(),
        component_id="sachet-main",
        actor_id="operator-1",
        reason="Create a simple front and back design surface.",
        created_at_utc=NOW,
    )

    data = pouch.as_dict()
    assert pouch.model.parent_kind.value == "STANDALONE_DESIGN_GEOMETRY"
    assert pouch.model.standalone_root is not None
    assert pouch.model.standalone_root.scale_state is ScaleState.METRIC_UNVERIFIED
    assert pouch.model.coordinate_unit == "mm_unverified"
    assert data["visualization_only"] is True
    assert data["captured_surface_claimed"] is False
    assert data["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert data["mold_use_authorized"] is False
    assert data["manufacturing_authority"] is False
    assert data["cad_or_brep_generated"] is False
    assert data["dimensions"]["overall_width"] == 120.0  # type: ignore[index]
    assert data["dimensions"]["seal_zones"] == {  # type: ignore[index]
        "top": 10.0,
        "bottom": 12.0,
        "left": 6.0,
        "right": 6.0,
    }
    assert pouch.front_artwork_feature_id != pouch.back_artwork_feature_id
    assert pouch.preview.authority_class == "PREVIEW_PROXY"
    assert pouch.preview.standalone_root_revision_id == pouch.model.standalone_root.revision_id
    assert pouch.preview.scan_master_revision_id is None
    assert len(pouch.preview.mesh.vertices) == 578
    assert len(pouch.preview.mesh.triangles) == 1152
    model_payload = pouch.model.as_dict()
    assert "parent_authority" in model_payload
    assert not any("scan_master" in key or "scale_provenance" in key for key in model_payload)
    assert serialize_design_model(
        deserialize_design_model(serialize_design_model(pouch.model)).model
    ) == serialize_design_model(pouch.model)


def test_pouch_graph_and_preview_are_deterministic():
    first = build_pouch_family(
        _root(),
        _dimensions(),
        component_id="sachet-main",
        actor_id="operator-1",
        reason="Create a simple front and back design surface.",
        created_at_utc=NOW,
    )
    second = build_pouch_family(
        _root(),
        _dimensions(),
        component_id="sachet-main",
        actor_id="operator-1",
        reason="Create a simple front and back design surface.",
        created_at_utc=NOW,
    )
    assert first.model.revision_id == second.model.revision_id
    assert first.model.as_dict() == second.model.as_dict()
    assert first.preview.as_dict() == second.preview.as_dict()
    assert first.preview.mesh == second.preview.mesh
    assert first.front_artwork_feature_id == second.front_artwork_feature_id


def test_flexible_surface_edit_preserves_parent_features_and_artwork_coordinates():
    pouch = build_pouch_family(
        _root(),
        _dimensions(),
        component_id="sachet-main",
        actor_id="operator-1",
        reason="Create the initial pouch design.",
        created_at_utc=NOW,
    )
    front_anchor = next(
        anchor for anchor in pouch.artwork_anchors if anchor.anchor_id == "front-center"
    )
    changed = edit_pouch_family(
        pouch,
        dimensions=PouchFamilyDimensions(
            overall_width=130.0,
            overall_height=190.0,
            thickness=9.0,
            top_seal_width=11.0,
            bottom_seal_width=12.0,
            left_seal_width=7.0,
            right_seal_width=7.0,
        ),
        front_bulge=5.0,
        back_bulge=3.0,
        actor_id="operator-1",
        reason="Adjust nominal artwork panels and simplified surface bulges.",
        created_at_utc="2026-10-04T12:01:00Z",
    )

    assert changed.model.previous_revision_id == pouch.model.revision_id
    assert changed.model.parent_kind is pouch.model.parent_kind
    assert changed.model.standalone_root == pouch.model.standalone_root
    assert changed.front_artwork_feature_id == pouch.front_artwork_feature_id
    assert changed.back_artwork_feature_id == pouch.back_artwork_feature_id
    assert changed.artwork_anchors == pouch.artwork_anchors
    assert (
        next(anchor for anchor in changed.artwork_anchors if anchor.anchor_id == "front-center")
        == front_anchor
    )
    assert changed.front_bulge == 5.0
    assert changed.preview.mesh.vertices[8 * 17 + 8][2] == pytest.approx(-4.5 - 3.0)
    assert changed.preview.mesh.vertices[17 * 17 + 8 * 17 + 8][2] == pytest.approx(4.5 + 5.0)
    assert changed.preview.mesh.vertices[16 * 17 + 8][2] == pytest.approx(-4.5)
    assert changed.preview.mesh.vertices[17 * 17 + 8][2] == pytest.approx(4.5)
    assert (
        changed.as_dict()["flexible_surface_design"]["bulge_is_measured_film_deformation"] is False
    )  # type: ignore[index]


@pytest.mark.parametrize("front_bulge", [-0.01, 12.01, float("nan")])
def test_unbounded_or_negative_surface_bulge_rejects(front_bulge):
    with pytest.raises(PouchFamilyError, match="pouch_bulge_out_of_bounds"):
        build_pouch_family(
            _root(),
            _dimensions(),
            component_id="sachet-main",
            actor_id="operator-1",
            reason="Reject an invalid bulge input.",
            created_at_utc=NOW,
            front_bulge=front_bulge,
        )


def test_artwork_coordinates_reject_out_of_surface_ranges():
    with pytest.raises(PouchFamilyError, match="artwork_coordinate_out_of_bounds"):
        PouchArtworkAnchor("front-label", "packlab-feature:front", 1.01, 0.5)


@pytest.mark.parametrize(
    "changes",
    [
        {"overall_width": 0.0},
        {"overall_height": float("inf")},
        {"thickness": 180.0},
        {"left_seal_width": 60.0, "right_seal_width": 60.0},
        {"top_seal_width": 90.0},
    ],
)
def test_invalid_pouch_dimensions_and_seal_relationships_reject(changes):
    values = {
        "overall_width": 120.0,
        "overall_height": 180.0,
        "thickness": 8.0,
        "top_seal_width": 10.0,
        "bottom_seal_width": 12.0,
        "left_seal_width": 6.0,
        "right_seal_width": 6.0,
    }
    values.update(changes)
    with pytest.raises(PouchFamilyError):
        PouchFamilyDimensions(**values)
