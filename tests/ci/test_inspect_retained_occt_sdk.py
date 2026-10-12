from __future__ import annotations

import stat
import zipfile
from pathlib import Path

import pytest

from tools.packaging.inspect_retained_occt_sdk import safe_extract


def test_safe_extract_accepts_regular_bounded_archive(tmp_path: Path) -> None:
    archive = tmp_path / "sdk.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("occt-sdk/include/OpenGl_Context.hxx", "header")
        zipped.writestr("occt-sdk/lib/TKOpenGl.lib", "import library")

    output = tmp_path / "out"
    safe_extract(archive, output)

    assert (output / "occt-sdk/include/OpenGl_Context.hxx").read_text() == "header"
    assert (output / "occt-sdk/lib/TKOpenGl.lib").read_text() == "import library"


@pytest.mark.parametrize(
    "entries",
    [
        [("../escape.txt", "outside")],
        [("sdk/Name.h", "first"), ("sdk/name.h", "case collision")],
    ],
)
def test_safe_extract_rejects_traversal_and_casefold_collisions(
    tmp_path: Path, entries: list[tuple[str, str]]
) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        for name, content in entries:
            zipped.writestr(name, content)

    with pytest.raises(ValueError, match="unsafe or case-colliding"):
        safe_extract(archive, tmp_path / "out")


def test_safe_extract_rejects_symbolic_link_entries(tmp_path: Path) -> None:
    archive = tmp_path / "symlink.zip"
    info = zipfile.ZipInfo("sdk/link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(info, "target")

    with pytest.raises(ValueError, match="unsafe or case-colliding"):
        safe_extract(archive, tmp_path / "out")
