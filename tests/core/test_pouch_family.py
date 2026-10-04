from __future__ import annotations

import pytest

from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    create_standalone_design_geometry_root,
)
from packlab_core.design_serialization import deserialize_design_model, serialize_design_model
from packlab_core.pouch_family import PouchFamilyDimensions, PouchFamilyError, build_pouch_family
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
    assert len(pouch.preview.mesh.vertices) == 8
    assert len(pouch.preview.mesh.triangles) == 12
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
