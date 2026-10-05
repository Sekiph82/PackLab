from __future__ import annotations

import json

import pytest

from packlab_core.visual_material_library import (
    MaterialFamily,
    MaterialSourceClass,
    VisualMaterialLibraryError,
    VisualMaterialRecord,
    create_starter_visual_material_library,
    create_visual_material_library,
)


def _material(
    material_id: str = "material-test-1",
    family: MaterialFamily = MaterialFamily.HDPE,
    **overrides: object,
) -> VisualMaterialRecord:
    values: dict[str, object] = {
        "material_id": material_id,
        "family": family,
        "display_name": "Test visual material",
        "base_color_rgba": (0.2, 0.4, 0.6, 1.0),
        "metallic_factor": 0.0,
        "roughness_factor": 0.5,
        "source_classification": MaterialSourceClass.USER_AUTHORED_VISUAL,
    }
    values.update(overrides)
    return VisualMaterialRecord(**values)  # type: ignore[arg-type]


def test_starter_library_supports_hdpe_pet_pp_and_extensible_other() -> None:
    library = create_starter_visual_material_library()

    assert {item.family for item in library.materials} == {
        MaterialFamily.HDPE,
        MaterialFamily.PET,
        MaterialFamily.PP,
        MaterialFamily.OTHER,
    }
    other = next(item for item in library.materials if item.family is MaterialFamily.OTHER)
    assert other.other_family_label == "Other packaging material"
    assert len({item.material_id for item in library.materials}) == 4


def test_library_serialization_and_revision_are_deterministic_and_order_independent() -> None:
    materials = (
        _material("material-pet", MaterialFamily.PET),
        _material("material-hdpe", MaterialFamily.HDPE),
        _material("material-other", MaterialFamily.OTHER, other_family_label="Paper laminate"),
    )

    first = create_visual_material_library(materials)
    second = create_visual_material_library(tuple(reversed(materials)))

    assert first == second
    assert first.revision_id == second.revision_id
    assert [item.material_id for item in first.materials] == sorted(
        item.material_id for item in materials
    )
    assert json.dumps(first.as_dict(), sort_keys=True, allow_nan=False) == json.dumps(
        second.as_dict(), sort_keys=True, allow_nan=False
    )


def test_equivalent_integer_and_float_pbr_values_have_canonical_serialization() -> None:
    integer_input = _material(base_color_rgba=(0, 0, 0, 1), metallic_factor=0, roughness_factor=1)
    float_input = _material(
        base_color_rgba=(0.0, 0.0, 0.0, 1.0), metallic_factor=0.0, roughness_factor=1.0
    )

    assert integer_input.as_dict() == float_input.as_dict()
    assert create_visual_material_library((integer_input,)).revision_id == (
        create_visual_material_library((float_input,)).revision_id
    )


def test_duplicate_material_ids_and_mutable_library_inputs_reject() -> None:
    record = _material()
    with pytest.raises(VisualMaterialLibraryError, match="id_duplicate"):
        create_visual_material_library((record, record))
    with pytest.raises(VisualMaterialLibraryError, match="nonempty_tuple"):
        create_visual_material_library([record])  # type: ignore[arg-type]
    with pytest.raises(VisualMaterialLibraryError, match="nonempty_tuple"):
        create_visual_material_library(())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("material_id", "../private", "id_invalid"),
        ("display_name", "   ", "display_name_invalid"),
        ("display_name", "x" * 81, "display_name_invalid"),
        ("display_name", "name\nunsafe", "display_name_invalid"),
        ("source_reference_id", "C:\\private\\source", "source_reference_id_invalid"),
        ("roughness_factor", -0.01, "roughness_factor_invalid"),
        ("roughness_factor", float("nan"), "roughness_factor_invalid"),
        ("metallic_factor", float("inf"), "metallic_factor_invalid"),
        ("metallic_factor", True, "metallic_factor_invalid"),
        ("pcr_visual_reference_fraction", 1.01, "pcr_visual_reference_fraction_invalid"),
        ("base_color_rgba", (0.1, 0.2, 0.3, 1.1), "base_color_invalid"),
        ("base_color_rgba", (0.1, 0.2, 0.3), "base_color_invalid"),
    ],
)
def test_bounded_text_and_numeric_schema_validation(
    field: str, value: object, message: str
) -> None:
    with pytest.raises(VisualMaterialLibraryError, match=message):
        _material(**{field: value})


def test_visual_authority_flags_never_infer_certified_properties() -> None:
    record = _material(
        pcr_visual_reference_fraction=0.35,
        source_classification=MaterialSourceClass.REFERENCE_VISUAL_ONLY,
        source_reference_id="visual-ref-2026-01",
    )
    serialized = record.as_dict()

    assert serialized["authority_semantics"] == "NON_CERTIFIED_VISUAL_REFERENCE"
    assert serialized["pcr_visual_reference_fraction"] == 0.35
    assert serialized["material_certified"] is False
    assert serialized["recycled_content_certified"] is False
    assert serialized["food_contact_approved"] is False
    assert serialized["barrier_properties_verified"] is False
    assert serialized["mechanical_properties_verified"] is False
    assert serialized["regulatory_approval"] is False
    assert serialized["physical_or_regulatory_claim"] is False
    assert serialized["provenance"]["source_reference_id"] == "visual-ref-2026-01"


def test_optional_exact_design_model_and_component_provenance_is_preserved() -> None:
    record = _material(
        source_design_model_revision_id="design-model:revision-42",
        source_component_id="component-bottle-body",
    )

    provenance = record.as_dict()["provenance"]
    assert provenance["source_design_model_revision_id"] == "design-model:revision-42"
    assert provenance["source_component_id"] == "component-bottle-body"
    with pytest.raises(VisualMaterialLibraryError, match="provenance_incomplete"):
        _material(source_design_model_revision_id="design-model:revision-42")


def test_other_family_requires_its_bounded_extensible_label() -> None:
    with pytest.raises(VisualMaterialLibraryError, match="other_family_label_invalid"):
        _material(family=MaterialFamily.OTHER)
    with pytest.raises(VisualMaterialLibraryError, match="other_label_wrong_family"):
        _material(other_family_label="Paper")
    with pytest.raises(VisualMaterialLibraryError, match="other_family_label_invalid"):
        _material(
            family=MaterialFamily.OTHER,
            other_family_label="P" * 81,
        )
