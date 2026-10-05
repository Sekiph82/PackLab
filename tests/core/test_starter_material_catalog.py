from __future__ import annotations

import hashlib
import json

from packlab_core.starter_material_catalog import create_starter_packaging_material_catalog
from packlab_core.visual_material_library import MaterialFamily


def test_starter_catalog_has_the_five_required_visual_material_entries() -> None:
    catalog = create_starter_packaging_material_catalog()
    by_name = {entry.material.display_name: entry for entry in catalog.entries}

    assert set(by_name) == {
        "Natural HDPE visual reference",
        "White HDPE visual reference",
        "Clear PET visual reference",
        "Colored PET visual reference",
        "PP cap visual reference",
    }
    assert len(catalog.entries) == 5
    assert len({entry.material.material_id for entry in catalog.entries}) == 5
    assert by_name["Natural HDPE visual reference"].material.family is MaterialFamily.HDPE
    assert by_name["White HDPE visual reference"].material.family is MaterialFamily.HDPE
    assert by_name["Clear PET visual reference"].material.family is MaterialFamily.PET
    assert by_name["Colored PET visual reference"].material.family is MaterialFamily.PET
    assert by_name["PP cap visual reference"].material.family is MaterialFamily.PP


def test_starter_catalog_has_valid_coherent_pbr_visual_ranges() -> None:
    catalog = create_starter_packaging_material_catalog()

    for entry in catalog.entries:
        assert all(0.0 <= channel <= 1.0 for channel in entry.material.base_color_rgba)
        assert 0.0 <= entry.material.metallic_factor <= 1.0
        assert 0.0 <= entry.material.roughness_factor <= 1.0
        assert 0.0 <= entry.transmission_factor <= 1.0
        assert 0.0 <= entry.opacity_factor <= 1.0
        assert 1.0 <= entry.ior <= 3.0
        assert entry.normal_detail is None
        if entry.opacity_factor < 1.0:
            assert entry.transmission_factor == 0.0
            assert entry.material.alpha_mode == "BLEND"
        if entry.transmission_factor > 0.0:
            assert entry.opacity_factor == 1.0
            assert entry.material.alpha_mode == "OPAQUE"


def test_clear_and_colored_pet_use_distinct_coherent_render_channels() -> None:
    catalog = create_starter_packaging_material_catalog()
    by_name = {entry.material.display_name: entry for entry in catalog.entries}
    clear = by_name["Clear PET visual reference"]
    colored = by_name["Colored PET visual reference"]

    assert clear.transmission_factor > 0.0
    assert clear.opacity_factor == 1.0
    assert clear.material.alpha_mode == "OPAQUE"
    assert colored.transmission_factor == 0.0
    assert colored.opacity_factor < 1.0
    assert colored.material.alpha_mode == "BLEND"


def test_starter_catalog_and_canonical_bytes_are_deterministic() -> None:
    first = create_starter_packaging_material_catalog()
    second = create_starter_packaging_material_catalog()

    assert first == second
    assert first.revision_id == second.revision_id
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.canonical_bytes().endswith(b"\n")
    parsed = json.loads(first.canonical_bytes())
    assert parsed["revision_id"] == first.revision_id
    assert len(parsed["entries"]) == 5
    assert hashlib.sha256(first.canonical_bytes()).hexdigest()


def test_every_starter_entry_is_authored_visual_only_without_material_claims() -> None:
    catalog = create_starter_packaging_material_catalog()
    serialized = catalog.as_dict()

    assert serialized["authority_semantics"] == "NON_CERTIFIED_VISUAL_REFERENCE"
    assert serialized["values_are_measured_or_certified_specifications"] is False
    assert serialized["physical_performance_inferred"] is False
    assert serialized["material_certified"] is False
    assert serialized["recycled_content_certified"] is False
    assert serialized["regulatory_approval"] is False
    for entry in serialized["entries"]:
        material = entry["material"]
        assert material["authority_semantics"] == "NON_CERTIFIED_VISUAL_REFERENCE"
        assert material["provenance"]["source_classification"] == "USER_AUTHORED_VISUAL"
        assert material["material_certified"] is False
        assert material["food_contact_approved"] is False
        assert material["barrier_properties_verified"] is False
        assert material["mechanical_properties_verified"] is False
        assert entry["values_are_measured_or_certified_specifications"] is False
        assert entry["physical_performance_inferred"] is False
        assert entry["pbr_visual_parameters"]["normal_detail"] is None
