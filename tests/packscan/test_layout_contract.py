"""Machine-level checks for the PackScan ZIP layout contract."""

from __future__ import annotations

import json
import zipfile
from copy import deepcopy
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pytest

CANONICAL_TIMESTAMP = "1980-01-01T00:00:00"
CANONICAL_DOS_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def _load_layout(repo_root: Path) -> dict[str, object]:
    layout_path = repo_root / "schemas" / "packscan" / "layout.json"
    with layout_path.open(encoding="utf-8") as layout_file:
        return json.load(layout_file)


def _assert_canonical_timestamp(layout: dict[str, object]) -> None:
    compression = layout["compression"]
    assert isinstance(compression, dict)
    timestamps = compression["timestamps"]
    assert timestamps == {
        "central_directory": CANONICAL_TIMESTAMP,
        "extra_fields": "omit",
    }

    central_directory = timestamps["central_directory"]
    parsed = datetime.strptime(central_directory, "%Y-%m-%dT%H:%M:%S")
    assert parsed == datetime(1980, 1, 1, 0, 0, 0)
    assert parsed.year >= 1980
    assert parsed.second % 2 == 0

    info = zipfile.ZipInfo("entry.bin", date_time=parsed.timetuple()[:6])
    archive = BytesIO()
    with zipfile.ZipFile(archive, mode="w", compression=zipfile.ZIP_DEFLATED) as writer:
        writer.writestr(info, b"payload")
    with zipfile.ZipFile(BytesIO(archive.getvalue())) as reader:
        assert reader.infolist()[0].date_time == CANONICAL_DOS_TIMESTAMP


def test_layout_freezes_a_standards_valid_zip_timestamp(repo_root: Path) -> None:
    """The machine-readable contract must define one exact ZIP boundary value."""

    _assert_canonical_timestamp(_load_layout(repo_root))


def test_layout_rejects_the_pre_remediation_advisory_timestamp(repo_root: Path) -> None:
    """The regression must fail if the old optional/advisory rule returns."""

    mutated_layout = deepcopy(_load_layout(repo_root))
    compression = mutated_layout["compression"]
    assert isinstance(compression, dict)
    compression["timestamps"] = "zeroed DOS timestamp where the writer permits it"

    with pytest.raises((AssertionError, KeyError, TypeError, ValueError)):
        _assert_canonical_timestamp(mutated_layout)
