from __future__ import annotations

import sys

from packlab_core.resource_paths import packlab_data_root


def test_packlab_data_root_uses_frozen_bundle_root(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert packlab_data_root() == tmp_path


def test_packlab_data_root_uses_repository_root_in_source_checkout(monkeypatch) -> None:
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)

    assert packlab_data_root().joinpath("pyproject.toml").is_file()
