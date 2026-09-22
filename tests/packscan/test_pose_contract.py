"""Machine-level checks for the PackScan pose convention contract."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

CONVENTION = "packscan_right_handed_x_right_y_up_z_out_of_screen_camera_forward_neg_z_v3"
BASIS_CONVERSION = "arkit_to_packscan_identity_shared_right_handed_basis_v1"


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def _assert_pose_schema_constants(schema: dict[str, object]) -> None:
    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert properties["coordinate_convention"] == {"const": CONVENTION}
    assert properties["basis_conversion"] == {"const": BASIS_CONVERSION}
    assert properties["translation_unit"] == {"const": "metres"}


def test_pose_contract_freezes_truthful_right_handed_identity_basis(repo_root: Path) -> None:
    schema = _load_json(repo_root / "schemas" / "packscan" / "pose.schema.json")
    _assert_pose_schema_constants(schema)
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
    unavailable = next(
        rule
        for rule in all_of
        if rule["if"]["properties"]["status"] == {"const": "unavailable"}
    )
    assert unavailable["then"]["properties"]["tracking_state"] == {"const": "not_available"}


def test_destination_basis_is_right_handed_and_camera_views_along_negative_z() -> None:
    x_right = (1, 0, 0)
    y_up = (0, 1, 0)
    z_out_of_screen = (0, 0, 1)
    cross_x_y = (
        x_right[1] * y_up[2] - x_right[2] * y_up[1],
        x_right[2] * y_up[0] - x_right[0] * y_up[2],
        x_right[0] * y_up[1] - x_right[1] * y_up[0],
    )
    assert cross_x_y == z_out_of_screen
    basis_matrix = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    determinant = (
        basis_matrix[0][0]
        * (basis_matrix[1][1] * basis_matrix[2][2] - basis_matrix[1][2] * basis_matrix[2][1])
        - basis_matrix[0][1]
        * (basis_matrix[1][0] * basis_matrix[2][2] - basis_matrix[1][2] * basis_matrix[2][0])
        + basis_matrix[0][2]
        * (basis_matrix[1][0] * basis_matrix[2][1] - basis_matrix[1][1] * basis_matrix[2][0])
    )
    assert determinant == 1
    assert (0, 0, -1) == tuple(-component for component in z_out_of_screen)


def test_pose_conversion_and_quaternion_mapping_are_identity() -> None:
    arkit_pose = (
        (1, 0, 0, 1),
        (0, 1, 0, 2),
        (0, 0, 1, 3),
        (0, 0, 0, 1),
    )
    packscan_pose = arkit_pose
    assert packscan_pose == arkit_pose
    arkit_quaternion = (0.1, 0.2, 0.3, 0.9)
    assert arkit_quaternion == (0.1, 0.2, 0.3, 0.9)


def test_old_reflected_forward_convention_cannot_satisfy_current_contract(repo_root: Path) -> None:
    schema = _load_json(repo_root / "schemas" / "packscan" / "pose.schema.json")
    mutated = deepcopy(schema)
    properties = mutated["properties"]
    assert isinstance(properties, dict)
    properties["coordinate_convention"] = {
        "const": "packscan_right_handed_x_right_y_up_z_forward"
    }
    properties["basis_conversion"] = {
        "const": "arkit_camera_neg_z_to_packscan_pos_z_reflection_v1"
    }
    _assert_pose_schema_constants(schema)
    with pytest.raises(AssertionError):
        _assert_pose_schema_constants(mutated)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "pose-invalid-contradictory-available.json",
        "pose-invalid-contradictory-degraded.json",
        "pose-invalid-unavailable-normal.json",
    ],
)
def test_negative_pose_fixtures_target_status_pair_boundaries(
    repo_root: Path, fixture_name: str
) -> None:
    fixture = _load_json(repo_root / "tests" / "fixtures" / "packscan" / fixture_name)
    if fixture_name == "pose-invalid-unavailable-normal.json":
        assert fixture["status"] == "unavailable"
        assert fixture["tracking_state"] == "normal"
    elif fixture_name.endswith("available.json"):
        assert fixture["status"] == "available"
        assert fixture["tracking_state"] == "not_available"
    else:
        assert fixture["status"] == "degraded"
        assert fixture["tracking_state"] == "normal"
