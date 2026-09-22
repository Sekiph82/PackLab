"""Lightweight regression checks for the optional object-mask contract."""

from __future__ import annotations

import json
from pathlib import Path


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def _first_mask(fixture: dict[str, object]) -> dict[str, object]:
    masks = fixture["masks"]
    assert isinstance(masks, list) and len(masks) == 1
    mask = masks[0]
    assert isinstance(mask, dict)
    return mask


def _assert_mask_runtime_invariants(
    mask: dict[str, object], expected_photo_by_image: dict[str, str]
) -> None:
    source_dimensions = mask["source_dimensions"]
    mask_dimensions = mask["mask_dimensions"]
    assert isinstance(source_dimensions, dict)
    assert isinstance(mask_dimensions, dict)
    assert mask_dimensions == source_dimensions

    source_image_path = mask["source_image_path"]
    source_photo_id = mask["source_photo_id"]
    assert expected_photo_by_image[source_image_path] == source_photo_id


def test_omitted_masks_are_a_valid_optional_state(repo_root: Path) -> None:
    fixture = _load_json(repo_root / "tests" / "fixtures" / "packscan" / "masks-omitted.json")
    assert fixture == {"schema_version": "1.0.0", "masks": []}


def test_valid_mask_satisfies_fixture_level_runtime_invariants(repo_root: Path) -> None:
    fixture = _load_json(repo_root / "tests" / "fixtures" / "packscan" / "masks-valid.json")
    _assert_mask_runtime_invariants(
        _first_mask(fixture), {"images/0001.jpg": "photo-0001"}
    )


def test_dimension_mismatch_fixture_is_detected(repo_root: Path) -> None:
    fixture = _load_json(
        repo_root / "tests" / "fixtures" / "packscan" / "masks-invalid-dimensions.json"
    )
    mask = _first_mask(fixture)
    assert mask["mask_dimensions"] != mask["source_dimensions"]


def test_linkage_mismatch_fixture_is_detected(repo_root: Path) -> None:
    fixture = _load_json(
        repo_root / "tests" / "fixtures" / "packscan" / "masks-invalid-linkage.json"
    )
    mask = _first_mask(fixture)
    assert mask["source_photo_id"] != {"images/0001.jpg": "photo-0001"}[mask["source_image_path"]]
