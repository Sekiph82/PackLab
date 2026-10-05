from __future__ import annotations

import json

import pytest
from tests.core.test_label_zone import COMPONENT_ID, _model

from packlab_core.component_visual_assignments import (
    ComponentVisualAssignmentError,
    create_component_visual_assignment_state,
    create_content_appearance_assignment,
    create_geometry_material_assignment,
    remove_content_appearance_assignment,
    remove_geometry_material_assignment,
)
from packlab_core.visual_material_library import (
    MaterialFamily,
    MaterialSourceClass,
    VisualMaterialRecord,
    create_visual_material_library,
)


def _library():
    return create_visual_material_library(
        (
            VisualMaterialRecord(
                "material-hdpe",
                MaterialFamily.HDPE,
                "HDPE visual reference",
                (0.8, 0.85, 0.9, 1.0),
                0.0,
                0.4,
                MaterialSourceClass.USER_AUTHORED_VISUAL,
            ),
            VisualMaterialRecord(
                "material-pet",
                MaterialFamily.PET,
                "PET visual reference",
                (0.7, 0.85, 0.8, 0.4),
                0.0,
                0.2,
                MaterialSourceClass.REFERENCE_VISUAL_ONLY,
                alpha_mode="BLEND",
            ),
        )
    )


def _content(model, *, color=(0.1, 0.5, 0.9, 0.35), opacity=0.35, previous=None):
    return create_content_appearance_assignment(
        model,
        COMPONENT_ID,
        display_name="Blue product content visual",
        display_color_rgba=color,
        opacity_factor=opacity,
        source_classification=MaterialSourceClass.USER_AUTHORED_VISUAL,
        previous=previous,
    )


def test_geometry_only_and_content_only_channels_are_independent() -> None:
    model = _model(label="component-visual-independent")
    library = _library()
    before = model.as_dict()
    geometry = create_geometry_material_assignment(model, COMPONENT_ID, library, "material-hdpe")
    content = _content(model)
    geometry_state = create_component_visual_assignment_state(geometry_material_assignment=geometry)
    content_state = create_component_visual_assignment_state(content_appearance_assignment=content)

    assert geometry_state.geometry_material_assignment is geometry
    assert geometry_state.content_appearance_assignment is None
    assert content_state.geometry_material_assignment is None
    assert content_state.content_appearance_assignment is content
    assert "content_appearance_assignment" not in geometry.as_dict()
    assert "geometry_material_assignment" not in content.as_dict()
    assert model.as_dict() == before


def test_combined_state_pins_both_channels_to_same_exact_component_and_model() -> None:
    model = _model(label="component-visual-combined")
    geometry = create_geometry_material_assignment(model, COMPONENT_ID, _library(), "material-hdpe")
    content = _content(model)
    state = create_component_visual_assignment_state(geometry, content)

    serialized = state.as_dict()
    assert state.source_design_model_revision_id == model.revision_id
    assert state.component_id == COMPONENT_ID
    assert serialized["geometry_and_content_channels_independent"] is True
    assert serialized["geometry_material_assignment"]["material_id"] == "material-hdpe"
    assert serialized["content_appearance_assignment"]["display_name"] == content.display_name
    assert serialized["fill_volume_inferred"] is False
    assert serialized["formulation_inferred"] is False
    json.dumps(serialized, sort_keys=True, allow_nan=False)


def test_channel_replacement_preserves_the_other_channel_and_removal_is_reversible() -> None:
    model = _model(label="component-visual-replacement")
    library = _library()
    geometry_v1 = create_geometry_material_assignment(model, COMPONENT_ID, library, "material-hdpe")
    content_v1 = _content(model)
    combined_v1 = create_component_visual_assignment_state(geometry_v1, content_v1)

    geometry_v2 = create_geometry_material_assignment(
        model, COMPONENT_ID, library, "material-pet", previous=geometry_v1
    )
    geometry_replaced = create_component_visual_assignment_state(geometry_v2, content_v1)
    content_v2 = _content(model, color=(0.9, 0.3, 0.1, 0.8), opacity=0.8, previous=content_v1)
    content_replaced = create_component_visual_assignment_state(geometry_v2, content_v2)

    removed_geometry = remove_geometry_material_assignment(geometry_v2)
    removed_content = remove_content_appearance_assignment(content_v2)
    geometry_removed_state = create_component_visual_assignment_state(
        content_appearance_assignment=content_v2
    )
    content_removed_state = create_component_visual_assignment_state(
        geometry_material_assignment=geometry_v2
    )

    assert geometry_v2.previous_revision_id == geometry_v1.revision_id
    assert content_v2.previous_revision_id == content_v1.revision_id
    assert geometry_replaced.content_appearance_assignment is content_v1
    assert content_replaced.geometry_material_assignment is geometry_v2
    assert combined_v1.geometry_material_assignment is geometry_v1
    assert combined_v1.content_appearance_assignment is content_v1
    assert removed_geometry.status == removed_content.status == "REMOVED"
    assert removed_geometry.previous_revision_id == geometry_v2.revision_id
    assert removed_content.previous_revision_id == content_v2.revision_id
    assert geometry_removed_state.geometry_material_assignment is None
    assert geometry_removed_state.content_appearance_assignment is content_v2
    assert content_removed_state.geometry_material_assignment is geometry_v2
    assert content_removed_state.content_appearance_assignment is None


def test_assignment_ids_are_deterministic_and_change_with_channel_content() -> None:
    model = _model(label="component-visual-deterministic")
    library = _library()
    geometry_a = create_geometry_material_assignment(model, COMPONENT_ID, library, "material-hdpe")
    geometry_b = create_geometry_material_assignment(model, COMPONENT_ID, library, "material-hdpe")
    content_a = _content(model, color=(0, 0.5, 1, 0.5), opacity=0.5)
    content_b = _content(model, color=(0.0, 0.5, 1.0, 0.5), opacity=0.5)
    changed_content = _content(model, color=(0.0, 0.4, 1.0, 0.5), opacity=0.5)

    assert geometry_a == geometry_b
    assert content_a == content_b
    assert content_a.revision_id != changed_content.revision_id
    assert create_component_visual_assignment_state(geometry_a, content_a).revision_id == (
        create_component_visual_assignment_state(geometry_b, content_b).revision_id
    )


def test_component_and_library_binding_rejects_unknown_or_wrong_sources() -> None:
    model = _model(label="component-visual-binding")
    with pytest.raises(ComponentVisualAssignmentError, match="component_id_not_in_design_model"):
        create_geometry_material_assignment(model, "component-missing", _library(), "material-hdpe")
    with pytest.raises(ComponentVisualAssignmentError, match="not_in_library"):
        create_geometry_material_assignment(model, COMPONENT_ID, _library(), "material-unknown")
    geometry = create_geometry_material_assignment(model, COMPONENT_ID, _library(), "material-hdpe")
    other_model = _model(label="component-visual-other-model")
    content = _content(model)
    with pytest.raises(ComponentVisualAssignmentError, match="state_assignment_mismatch"):
        create_component_visual_assignment_state(
            geometry,
            create_content_appearance_assignment(
                other_model,
                COMPONENT_ID,
                display_name="Other model content",
                display_color_rgba=(1, 1, 1, 1),
                opacity_factor=1,
            ),
        )
    assert content.source_design_model_revision_id == model.revision_id


def test_content_appearance_never_infers_fill_volume_or_formulation() -> None:
    content = _content(_model(label="component-visual-no-inference"))
    serialized = content.as_dict()

    assert serialized["authority_semantics"] == "NON_CERTIFIED_VISUAL_REFERENCE"
    assert serialized["fill_volume_inferred"] is False
    assert serialized["formulation_inferred"] is False
    assert "fill_volume" not in serialized
    assert "formulation" not in serialized
    assert "geometry_material" not in serialized
