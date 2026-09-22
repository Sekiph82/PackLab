"""Corpus-level checks for every public PackScan manifest fixture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from packlab_core.packscan import PackScanError
from packlab_core.packscan.container import _validate_manifest


def test_current_manifest_fixture_corpus_is_accepted(repo_root: Path) -> None:
    fixture_dir = repo_root / "tests" / "fixtures" / "packscan"
    accepted = (
        "manifest-valid.json",
        "manifest-valid-guided-orbit.json",
        "manifest-valid-turntable.json",
        "manifest-derived-present.json",
        "manifest-derived-omitted.json",
    )
    for name in accepted:
        value = json.loads((fixture_dir / name).read_text(encoding="utf-8"))
        _validate_manifest(value)


def test_negative_manifest_fixture_corpus_is_rejected(repo_root: Path) -> None:
    fixture_dir = repo_root / "tests" / "fixtures" / "packscan"
    rejected = (
        "manifest-invalid-local-time.json",
        "manifest-invalid-unknown-property.json",
        "manifest-invalid-mixed-mode.json",
        "manifest-invalid-turntable-guided.json",
        "manifest-derived-mismatched.json",
        "manifest-derived-corrupt.json",
    )
    for name in rejected:
        value = json.loads((fixture_dir / name).read_text(encoding="utf-8"))
        with pytest.raises(PackScanError):
            _validate_manifest(value)


def test_version_gate_and_corrupt_fixture_are_distinguished(repo_root: Path) -> None:
    corpus = repo_root / "tests" / "fixtures" / "packscan" / "corpus"
    for name, code in (
        ("old-version-manifest.json", "unsupported_version"),
        ("future-version-manifest.json", "unsupported_future_version"),
    ):
        value = json.loads((corpus / name).read_text(encoding="utf-8"))
        with pytest.raises(PackScanError) as error:
            _validate_manifest(value)
        assert error.value.code == code
    with pytest.raises(json.JSONDecodeError):
        json.loads((corpus / "corrupt-json.json").read_text(encoding="utf-8"))
    incomplete = json.loads((corpus / "incomplete-manifest.json").read_text(encoding="utf-8"))
    with pytest.raises(PackScanError) as error:
        _validate_manifest(incomplete)
    assert error.value.code == "schema_invalid"
