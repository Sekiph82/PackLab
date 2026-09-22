"""Machine-level checks for the PackScan per-photo metadata contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

MEASUREMENT_DEFS = {
    "focal_length_mm": ("focal_length_measurement", "mm", "positive"),
    "exposure": ("exposure_measurement", "s", "positive"),
    "iso": ("iso_measurement", "iso", "integer"),
    "white_balance_kelvin": ("white_balance_measurement", "K", "kelvin"),
}


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def _schema_definitions(schema: dict[str, object]) -> dict[str, object]:
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    return definitions


def _assert_field_contracts(schema: dict[str, object]) -> None:
    definitions = _schema_definitions(schema)
    properties = schema["properties"]
    assert isinstance(properties, dict)
    photos = properties["photos"]
    assert isinstance(photos, dict)
    photo_ref = photos["items"]
    assert photo_ref == {"$ref": "#/$defs/photo"}

    photo = definitions["photo"]
    assert isinstance(photo, dict)
    photo_properties = photo["properties"]
    assert isinstance(photo_properties, dict)

    for field, (definition_name, unit, range_kind) in MEASUREMENT_DEFS.items():
        assert photo_properties[field] == {"$ref": f"#/$defs/{definition_name}"}
        measurement = definitions[definition_name]
        assert isinstance(measurement, dict)
        measurement_properties = measurement["properties"]
        assert isinstance(measurement_properties, dict)
        assert measurement_properties["unit"] == {"const": unit}
        value_schema = measurement_properties["value"]
        assert isinstance(value_schema, dict)
        assert "finite" not in value_schema
        if range_kind == "positive":
            assert value_schema == {"type": "number", "exclusiveMinimum": 0}
        elif range_kind == "integer":
            assert value_schema == {"type": "integer", "minimum": 1, "maximum": 1000000}
        else:
            assert value_schema == {"type": "number", "minimum": 1000, "maximum": 100000}


def _assert_fixture_violates_field_contract(
    fixture: dict[str, object], field: str, violation: str
) -> None:
    photos = fixture["photos"]
    assert isinstance(photos, list) and len(photos) == 1
    photo = photos[0]
    assert isinstance(photo, dict)
    measurement = photo[field]
    assert isinstance(measurement, dict)
    if violation == "unit":
        assert measurement["unit"] != MEASUREMENT_DEFS[field][1]
    elif violation == "nonpositive":
        assert measurement["value"] <= 0
    else:
        assert not isinstance(measurement["value"], int)


def test_photo_schema_freezes_field_specific_units_and_ranges(repo_root: Path) -> None:
    """The actual schema must not collapse four measurements into one generic type."""

    _assert_field_contracts(_load_json(repo_root / "schemas" / "packscan" / "photo-metadata.schema.json"))


@pytest.mark.parametrize(
    ("fixture_name", "fields", "violation"),
    [
        ("photos-invalid-wrong-units.json", tuple(MEASUREMENT_DEFS), "unit"),
        ("photos-invalid-nonpositive-values.json", tuple(MEASUREMENT_DEFS), "nonpositive"),
        ("photos-invalid-fractional-iso.json", ("iso",), "fractional"),
    ],
)
def test_negative_fixtures_exercise_frozen_measurement_boundaries(
    repo_root: Path, fixture_name: str, fields: tuple[str, ...], violation: str
) -> None:
    """Negative fixtures target each newly frozen unit/range boundary."""

    fixture = _load_json(repo_root / "tests" / "fixtures" / "packscan" / fixture_name)
    for field in fields:
        _assert_fixture_violates_field_contract(fixture, field, violation)


def test_unavailable_measurements_remain_value_free(repo_root: Path) -> None:
    fixture = _load_json(repo_root / "tests" / "fixtures" / "packscan" / "photos-valid-unavailable.json")
    photos = fixture["photos"]
    assert isinstance(photos, list)
    photo = photos[0]
    assert isinstance(photo, dict)
    white_balance = photo["white_balance_kelvin"]
    assert isinstance(white_balance, dict)
    assert white_balance == {"status": "unavailable"}
