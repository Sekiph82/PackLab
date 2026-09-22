"""Machine-level checks for the PackScan pose basis contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

BASIS = (
    (1, 0, 0, 0),
    (0, 1, 0, 0),
    (0, 0, -1, 0),
    (0, 0, 0, 1),
)


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def _matmul(
    left: tuple[tuple[int, ...], ...], right: tuple[tuple[int, ...], ...]
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(
            sum(left[row][index] * right[index][column] for index in range(4))
            for column in range(4)
        )
        for row in range(4)
    )


def _convert_arkit_to_packscan(
    matrix: tuple[tuple[int, ...], ...],
) -> tuple[tuple[int, ...], ...]:
    return _matmul(_matmul(BASIS, matrix), BASIS)


def test_pose_contract_freezes_basis_units_and_status_rules(repo_root: Path) -> None:
    schema = _load_json(repo_root / "schemas" / "packscan" / "pose.schema.json")
    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert properties["basis_conversion"] == {
        "const": "arkit_camera_neg_z_to_packscan_pos_z_reflection_v1"
    }
    assert properties["translation_unit"] == {"const": "metres"}
    assert properties["coordinate_convention"] == {
        "const": "packscan_right_handed_x_right_y_up_z_forward"
    }

    all_of = schema["allOf"]
    assert isinstance(all_of, list)
    assert any(
        rule["then"]["properties"]["tracking_state"] == {"const": "normal"}
        for rule in all_of
    )
    assert any(
        rule["then"]["properties"]["tracking_state"] == {"const": "limited"}
        for rule in all_of
    )


def test_synthetic_basis_vectors_and_pose_convert_negative_z_to_positive_z() -> None:
    arkit_translation = (
        (1, 0, 0, 1),
        (0, 1, 0, 2),
        (0, 0, 1, 3),
        (0, 0, 0, 1),
    )
    converted = _convert_arkit_to_packscan(arkit_translation)
    assert converted == (
        (1, 0, 0, 1),
        (0, 1, 0, 2),
        (0, 0, 1, -3),
        (0, 0, 0, 1),
    )
    arkit_forward = (0, 0, -1, 1)
    packscan_forward = tuple(
        sum(BASIS[row][index] * arkit_forward[index] for index in range(4))
        for row in range(4)
    )
    assert packscan_forward == (0, 0, 1, 1)


@pytest.mark.parametrize(
    "fixture_name",
    ["pose-invalid-contradictory-available.json", "pose-invalid-contradictory-degraded.json"],
)
def test_negative_pose_fixtures_target_contradictory_tracking_states(
    repo_root: Path, fixture_name: str
) -> None:
    fixture = _load_json(repo_root / "tests" / "fixtures" / "packscan" / fixture_name)
    expected_status = "available" if "available" in fixture_name else "degraded"
    assert fixture["status"] == expected_status
    assert fixture["tracking_state"] in {"not_available", "normal"}
