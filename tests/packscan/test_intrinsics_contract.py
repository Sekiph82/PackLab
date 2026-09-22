"""Machine-level checks for the PackScan camera-intrinsics contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

EXPECTED_BRANCHES = {
    "none": ("none_v1", [], []),
    "fisheye": ("opencv_fisheye_v1", ["k1", "k2", "k3", "k4"], 4),
    "brown_conrady": ("opencv_brown_conrady_v1", ["k1", "k2", "p1", "p2", "k3"], 5),
}


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def _assert_distortion_branches(schema: dict[str, object]) -> None:
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    distortion = definitions["distortion"]
    assert isinstance(distortion, dict)
    assert distortion["required"] == ["model", "coefficient_order_version", "coefficient_order", "coefficients"]
    branches = distortion["oneOf"]
    assert isinstance(branches, list) and len(branches) == 3

    for branch in branches:
        assert isinstance(branch, dict)
        properties = branch["properties"]
        assert isinstance(properties, dict)
        model_schema = properties["model"]
        assert isinstance(model_schema, dict)
        model = model_schema["const"]
        expected_version, expected_order, expected_count = EXPECTED_BRANCHES[model]
        assert properties["coefficient_order_version"] == {"const": expected_version}
        assert properties["coefficient_order"] == {"const": expected_order}
        coefficient_schema = properties["coefficients"]
        assert isinstance(coefficient_schema, dict)
        if model == "none":
            assert coefficient_schema == {"const": []}
        else:
            assert coefficient_schema["minItems"] == expected_count
            assert coefficient_schema["maxItems"] == expected_count


def _assert_fixture_target(fixture: dict[str, object], target: str) -> None:
    photos = fixture.get("photos")
    assert photos is None
    distortion = fixture["distortion"]
    assert isinstance(distortion, dict)
    if target == "wrong_order":
        assert distortion["coefficient_order"] != ["k1", "k2", "k3", "k4"]
    elif target == "missing_coefficients":
        assert "coefficients" not in distortion
    elif target == "mismatched_lengths":
        assert len(distortion["coefficient_order"]) != len(distortion["coefficients"])
    else:
        assert distortion["model"] == "none"
        assert distortion["coefficient_order"] != []
        assert distortion["coefficients"] != []


def test_intrinsics_schema_freezes_model_specific_distortion_branches(repo_root: Path) -> None:
    """The actual schema must expose exact, versioned distortion branches."""

    _assert_distortion_branches(
        _load_json(repo_root / "schemas" / "packscan" / "camera-intrinsics.schema.json")
    )


@pytest.mark.parametrize(
    ("fixture_name", "target"),
    [
        ("intrinsics-invalid-wrong-order.json", "wrong_order"),
        ("intrinsics-invalid-missing-coefficients.json", "missing_coefficients"),
        ("intrinsics-invalid-mismatched-lengths.json", "mismatched_lengths"),
        ("intrinsics-invalid-none-coefficients.json", "none_coefficients"),
    ],
)
def test_negative_intrinsics_fixtures_target_distortion_boundaries(
    repo_root: Path, fixture_name: str, target: str
) -> None:
    fixture = _load_json(repo_root / "tests" / "fixtures" / "packscan" / fixture_name)
    _assert_fixture_target(fixture, target)
