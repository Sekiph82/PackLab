from __future__ import annotations

import hashlib
import importlib.metadata
import shutil
import sys
from pathlib import Path

import pefile
import pytest
from tools.packaging.normalize_numpy_msvc_runtime import (
    EXPECTED_IMPORTS,
    PRIVATE_DLL_NAME,
    PRIVATE_DLL_SHA256,
    patch_numpy_imports,
)
from tools.packaging.windows_redistribution_inventory import (
    _valid_numpy_runtime_normalization_report,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows NumPy wheel only")


def _copy_locked_inputs(tmp_path: Path) -> tuple[Path, Path]:
    distribution = importlib.metadata.distribution("numpy")
    if distribution.version != "2.5.3":
        pytest.skip("The test environment does not contain the PL-0350 locked NumPy wheel")
    numpy_root = tmp_path / "numpy"
    for relative, expected_hash in EXPECTED_IMPORTS.items():
        source = Path(distribution.locate_file(relative))
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected_hash:
            pytest.skip("The test environment NumPy binary differs from the reviewed wheel")
        destination = tmp_path / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    private_source = Path(distribution.locate_file(f"numpy.libs/{PRIVATE_DLL_NAME}"))
    if hashlib.sha256(private_source.read_bytes()).hexdigest() != PRIVATE_DLL_SHA256:
        pytest.skip("The test environment NumPy runtime differs from the reviewed wheel")
    private_destination = tmp_path / "numpy.libs" / PRIVATE_DLL_NAME
    private_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(private_source, private_destination)
    return numpy_root, private_destination


def test_locked_numpy_imports_can_use_external_canonical_runtime(tmp_path: Path) -> None:
    numpy_root, private_dll = _copy_locked_inputs(tmp_path)

    changed = patch_numpy_imports(numpy_root, private_dll)

    assert {row["path"] for row in changed} == set(EXPECTED_IMPORTS)
    assert {row["from_import"] for row in changed} == {PRIVATE_DLL_NAME}
    assert {row["to_import"] for row in changed} == {"msvcp140.dll"}
    assert not private_dll.exists()
    for relative in EXPECTED_IMPORTS:
        path = tmp_path / Path(relative)
        image = pefile.PE(data=path.read_bytes(), fast_load=True)
        image.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
        )
        imports = {entry.dll.lower() for entry in image.DIRECTORY_ENTRY_IMPORT}
        assert PRIVATE_DLL_NAME.encode().lower() not in imports
        assert b"msvcp140.dll" in imports


def test_numpy_normalization_fails_closed_on_tampered_runtime(tmp_path: Path) -> None:
    numpy_root, private_dll = _copy_locked_inputs(tmp_path)
    original_hashes = {
        relative: hashlib.sha256((tmp_path / Path(relative)).read_bytes()).hexdigest()
        for relative in EXPECTED_IMPORTS
    }
    private_dll.write_bytes(private_dll.read_bytes() + b"tamper")

    with pytest.raises(ValueError, match="differs from the locked wheel"):
        patch_numpy_imports(numpy_root, private_dll)

    assert private_dll.exists()
    assert {
        relative: hashlib.sha256((tmp_path / Path(relative)).read_bytes()).hexdigest()
        for relative in EXPECTED_IMPORTS
    } == original_hashes


def test_normalization_evidence_requires_exact_runtime_and_import_mapping() -> None:
    report = {
        "numpy_version": "2.5.3",
        "numpy_wheel_sha256": "0a59a421a32580a009e8a1751345bf829631b990dc1794b80514ab722b435def",
        "removed_private_msvc_runtime": {
            "sha256": "a4c2229bdc2a2a630acdc095b4d86008e5c3e3bc7773174354f3da4f5beb9cde"
        },
        "external_prerequisite": {
            "application_payload_contains_microsoft_runtime": False,
            "canonical_runtime_filename": "msvcp140.dll",
            "canonical_runtime_location": "Windows System32",
        },
        "rewritten_imports": [
            {
                "path": path,
                "from_import": PRIVATE_DLL_NAME,
                "to_import": "msvcp140.dll",
                "new_sha256": "a" * 64,
            }
            for path in EXPECTED_IMPORTS
        ],
    }
    assert _valid_numpy_runtime_normalization_report(report)

    report["external_prerequisite"]["application_payload_contains_microsoft_runtime"] = True
    assert not _valid_numpy_runtime_normalization_report(report)
    assert not _valid_numpy_runtime_normalization_report({"external_prerequisite": None})
