"""Machine-level checks for the PackScan manifest checksum contract."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

CANONICALIZATION = "sha256_32_bytes_lowercase_hex_64_chars_v1"
SHA256_PATTERN = "^[0-9a-f]{64}$"


def _load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def _assert_checksum_contract(schema: dict[str, object]) -> None:
    properties = schema["properties"]
    assert isinstance(properties, dict)
    checksums = properties["checksums"]
    assert isinstance(checksums, dict)
    checksum_properties = checksums["properties"]
    assert isinstance(checksum_properties, dict)
    assert checksum_properties["algorithm"] == {"const": "sha256"}
    assert checksum_properties["canonicalization"] == {"const": CANONICALIZATION}

    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    payload = definitions["payload"]
    assert isinstance(payload, dict)
    payload_properties = payload["properties"]
    assert isinstance(payload_properties, dict)
    assert payload_properties["sha256"] == {"type": "string", "pattern": SHA256_PATTERN}

    digest = hashlib.sha256(b"PackLab checksum contract").digest()
    rendered = digest.hex()
    assert len(digest) == 32
    assert len(rendered) == 64
    assert re.fullmatch(SHA256_PATTERN.removeprefix("^").removesuffix("$"), rendered)
    assert rendered == rendered.lower()


def test_manifest_checksum_identifier_matches_sha256_representation(repo_root: Path) -> None:
    """The schema's identifier and digest constraints describe the same value."""

    _assert_checksum_contract(_load_json(repo_root / "schemas" / "packscan" / "manifest.schema.json"))


def test_manifest_checksum_contract_rejects_unit_drift(repo_root: Path) -> None:
    """The regression fails for the former 64-byte identifier or a 32-char regex."""

    schema = _load_json(repo_root / "schemas" / "packscan" / "manifest.schema.json")
    properties = schema["properties"]
    assert isinstance(properties, dict)
    checksums = properties["checksums"]
    assert isinstance(checksums, dict)
    checksum_properties = checksums["properties"]
    assert isinstance(checksum_properties, dict)

    old_identifier = deepcopy(schema)
    old_properties = old_identifier["properties"]
    assert isinstance(old_properties, dict)
    old_checksums = old_properties["checksums"]
    assert isinstance(old_checksums, dict)
    old_checksum_properties = old_checksums["properties"]
    assert isinstance(old_checksum_properties, dict)
    old_checksum_properties["canonicalization"] = {"const": "lowercase_hex_64_bytes"}
    with pytest.raises(AssertionError):
        _assert_checksum_contract(old_identifier)

    short_regex = deepcopy(schema)
    short_definitions = short_regex["$defs"]
    assert isinstance(short_definitions, dict)
    short_payload = short_definitions["payload"]
    assert isinstance(short_payload, dict)
    short_payload_properties = short_payload["properties"]
    assert isinstance(short_payload_properties, dict)
    short_payload_properties["sha256"] = {"type": "string", "pattern": "^[0-9a-f]{32}$"}
    with pytest.raises(AssertionError):
        _assert_checksum_contract(short_regex)
