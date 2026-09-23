"""Draft 2020-12 validation for diagnostics privacy boundaries."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def _validator(repo_root: Path) -> Draft202012Validator:
    schema = _load_json(repo_root / "schemas" / "packscan" / "diagnostics.schema.json")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "diagnostics-invalid-private-path.json",
        "diagnostics-invalid-credential-password.json",
        "diagnostics-invalid-credential-token.json",
        "diagnostics-invalid-credential-apikey.json",
    ],
)
def test_diagnostics_privacy_negative_fixtures_reject(repo_root: Path, fixture_name: str) -> None:
    fixture = _load_json(repo_root / "tests" / "fixtures" / "packscan" / fixture_name)
    assert not _validator(repo_root).is_valid(fixture)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "diagnostics-valid.json",
        "diagnostics-valid-redacted.json",
    ],
)
def test_diagnostics_redacted_fixtures_remain_valid(repo_root: Path, fixture_name: str) -> None:
    fixture = _load_json(repo_root / "tests" / "fixtures" / "packscan" / fixture_name)
    _validator(repo_root).validate(fixture)


def test_credential_pattern_is_portable_and_case_explicit(repo_root: Path) -> None:
    schema = _load_json(repo_root / "schemas" / "packscan" / "diagnostics.schema.json")
    message_schema = schema["$defs"]["entry"]["properties"]["message"]
    patterns = [item["not"]["pattern"] for item in message_schema["allOf"]]
    credential_pattern = patterns[1]
    assert "(?i" not in credential_pattern
    assert "[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]" in credential_pattern
    assert "[Tt][Oo][Kk][Ee][Nn]" in credential_pattern
    assert "[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]" in credential_pattern
