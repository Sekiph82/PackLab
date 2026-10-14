"""Normalize NumPy's private MSVC import to the Windows-installed CRT.

The locked NumPy wheel carries one Microsoft MSVCP140 binary under a hash
alias.  This packaging-only transformation patches NumPy's import-name strings
to the canonical redistributable DLL name, validates the machine prerequisite,
and removes the wheel-private copy so PackLab does not redistribute Microsoft
runtime bytes.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import tempfile
from pathlib import Path
from typing import Any

from tools.packaging.validate_windows_native_runtime_policy import (
    installed_vc_runtime,
)
from tools.packaging.windows_native_runtime_policy import (
    minimum_runtime_version,
    runtime_is_supported,
)

NUMPY_VERSION = "2.5.3"
NUMPY_WHEEL_SHA256 = "0a59a421a32580a009e8a1751345bf829631b990dc1794b80514ab722b435def"
PRIVATE_DLL_NAME = "msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll"
PRIVATE_DLL_SHA256 = "a4c2229bdc2a2a630acdc095b4d86008e5c3e3bc7773174354f3da4f5beb9cde"
PRIVATE_IMPORT = PRIVATE_DLL_NAME.encode("ascii")
CANONICAL_IMPORT = b"msvcp140.dll"
EXPECTED_IMPORTS = {
    "numpy/_core/_multiarray_umath.cp312-win_amd64.pyd": "a9d5c4202cf109bf24305f3f1180e0509aaf661ba850612bd75df7cfd9f928b8",
    "numpy/fft/_pocketfft_umath.cp312-win_amd64.pyd": "3ed9c2f73c7dc165e41e98ecfd0a4f66481a5afec7e39148a2af317b9a4ff62e",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _import_entries(data: bytes) -> list[tuple[int, bytes]]:
    import pefile

    image = pefile.PE(data=data, fast_load=True)
    image.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
    )
    rows: list[tuple[int, bytes]] = []
    for entry in getattr(image, "DIRECTORY_ENTRY_IMPORT", ()):
        if entry.dll.lower() == PRIVATE_IMPORT:
            offset = image.get_offset_from_rva(entry.struct.Name)
            rows.append((offset, entry.dll))
    return rows


def patch_numpy_imports(numpy_root: Path, private_dll: Path) -> list[dict[str, str]]:
    """Patch the exact locked wheel's two import descriptors and remove its alias."""
    numpy_root = numpy_root.resolve(strict=True)
    private_dll = private_dll.resolve(strict=True)
    if private_dll.name.casefold() != PRIVATE_DLL_NAME.casefold():
        raise ValueError("The NumPy private-runtime filename differs from the locked wheel.")
    dll_bytes = private_dll.read_bytes()
    if sha256_bytes(dll_bytes) != PRIVATE_DLL_SHA256:
        raise ValueError("The NumPy private MSVCP140 binary differs from the locked wheel.")

    patches: list[tuple[Path, bytes, bytearray, list[int]]] = []
    for relative, expected_sha in EXPECTED_IMPORTS.items():
        path = numpy_root.parent / Path(relative)
        original = path.read_bytes()
        if sha256_bytes(original) != expected_sha:
            raise ValueError(f"Locked NumPy extension digest mismatch: {relative}")
        entries = _import_entries(original)
        if len(entries) != 1:
            raise ValueError(f"Expected exactly one private MSVCP140 import in {relative}.")
        offsets = [offset for offset, _ in entries]
        patched = bytearray(original)
        for offset in offsets:
            end = offset + len(PRIVATE_IMPORT) + 1
            field = patched[offset:end]
            if field != PRIVATE_IMPORT + b"\0":
                raise ValueError(f"NumPy import-name field is not canonical in {relative}.")
            patched[offset:end] = CANONICAL_IMPORT + b"\0" * (
                len(PRIVATE_IMPORT) + 1 - len(CANONICAL_IMPORT)
            )
        if any(name.lower() == PRIVATE_IMPORT for _, name in _import_entries(bytes(patched))):
            raise ValueError(f"Private MSVCP140 import remains after patching {relative}.")
        patches.append((path, original, patched, offsets))

    discovered = {
        path.relative_to(numpy_root.parent).as_posix(): sha256_bytes(original)
        for path, original, _, _ in patches
    }
    if discovered != EXPECTED_IMPORTS:
        raise ValueError("The private MSVCP140 import set differs from the reviewed wheel.")

    changed: list[dict[str, str]] = []
    for path, _, patched, offsets in patches:
        _atomic_write(path, bytes(patched))
        changed.append(
            {
                "path": path.relative_to(numpy_root.parent).as_posix(),
                "old_sha256": sha256_bytes(_),
                "new_sha256": sha256_bytes(bytes(patched)),
                "rewritten_imports": str(len(offsets)),
                "from_import": PRIVATE_DLL_NAME,
                "to_import": CANONICAL_IMPORT.decode("ascii"),
            }
        )
    private_dll.unlink()
    if private_dll.exists():
        raise ValueError("The NumPy private MSVCP140 DLL remained after removal.")
    return changed


def _atomic_write(path: Path, data: bytes) -> None:
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def _update_record(
    distribution: importlib.metadata.Distribution, changed: list[dict[str, str]]
) -> None:
    site_packages = Path(str(distribution.locate_file(""))).resolve(strict=True)
    record = Path(str(distribution.locate_file("numpy-2.5.3.dist-info/RECORD")))
    if not record.is_file():
        raise ValueError("The exact NumPy wheel RECORD is missing.")
    updated = {row[0]: row for row in csv.reader(record.open(encoding="utf-8", newline=""))}
    for item in changed:
        path = item["path"]
        data = (site_packages / Path(path)).read_bytes()
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
        updated[path] = [path, f"sha256={digest}", str(len(data))]
    updated.pop(f"numpy.libs/{PRIVATE_DLL_NAME}", None)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=record.parent, delete=False
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        for key in sorted(updated, key=str.casefold):
            writer.writerow(updated[key])
        temporary = Path(handle.name)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(record)


def _verify_system_prerequisite(policy_path: Path) -> dict[str, Any]:
    import pefile

    if os.name != "nt" or platform.machine().casefold() not in {"amd64", "x86_64"}:
        raise ValueError("NumPy runtime normalization requires native x64 Windows.")
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    minimum = minimum_runtime_version(policy)
    version, fields = installed_vc_runtime()
    if not runtime_is_supported(
        installed=fields["Installed"] == 1,
        architecture="x64",
        version=version,
        minimum=minimum,
    ):
        raise ValueError("The x64 Microsoft VC++ Redistributable prerequisite is not satisfied.")

    system32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    runtime_path = (system32 / "msvcp140.dll").resolve(strict=True)
    if runtime_path.parent != system32.resolve(strict=True):
        raise ValueError("The canonical MSVCP140 runtime did not resolve inside System32.")
    handle = pefile.PE(str(runtime_path))
    version_info = getattr(handle, "VS_FIXEDFILEINFO", None)
    if not version_info:
        raise ValueError("The System32 MSVCP140 runtime has no fixed file version metadata.")
    file_version = version_info[0]
    actual_file_version = (
        file_version.FileVersionMS >> 16,
        file_version.FileVersionMS & 0xFFFF,
        file_version.FileVersionLS >> 16,
        file_version.FileVersionLS & 0xFFFF,
    )
    if actual_file_version < minimum:
        raise ValueError("The System32 MSVCP140 DLL is below the prerequisite version floor.")
    return {
        "architecture": "x64",
        "deployment_role": "MICROSOFT_SIGNED_PREREQUISITE",
        "minimum_version": ".".join(map(str, minimum)),
        "installed_version": ".".join(map(str, version)),
        "canonical_runtime_filename": "msvcp140.dll",
        "canonical_runtime_location": "Windows System32",
        "canonical_runtime_file_version": ".".join(map(str, actual_file_version)),
        "application_payload_contains_microsoft_runtime": False,
    }


def normalize_installed_numpy(
    *, revision: str, studio_version: str, policy_path: Path, report_path: Path
) -> dict[str, Any]:
    distribution = importlib.metadata.distribution("numpy")
    if distribution.version != NUMPY_VERSION:
        raise ValueError(f"Expected locked NumPy {NUMPY_VERSION}, found {distribution.version}.")
    runtime = _verify_system_prerequisite(policy_path)
    site_packages = Path(str(distribution.locate_file(""))).resolve(strict=True)
    numpy_root = (site_packages / "numpy").resolve(strict=True)
    private_dll = (site_packages / "numpy.libs" / PRIVATE_DLL_NAME).resolve(strict=True)
    changed = patch_numpy_imports(numpy_root, private_dll)
    _update_record(distribution, changed)
    result: dict[str, Any] = {
        "schema_version": 1,
        "PACKLAB_BUILD_REVISION": revision,
        "studio_version": studio_version,
        "status": "PASS",
        "numpy_version": NUMPY_VERSION,
        "numpy_wheel_sha256": NUMPY_WHEEL_SHA256,
        "removed_private_msvc_runtime": {
            "filename": PRIVATE_DLL_NAME,
            "sha256": PRIVATE_DLL_SHA256,
        },
        "rewritten_imports": changed,
        "external_prerequisite": runtime,
        "source_reference": "uv.lock exact numpy 2.5.3 win_amd64 wheel SHA-256",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--studio-version", required=True)
    parser.add_argument("--runtime-policy", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = normalize_installed_numpy(
        revision=args.revision,
        studio_version=args.studio_version,
        policy_path=args.runtime_policy,
        report_path=args.report,
    )
    print(
        "NUMPY_MSVCP_NORMALIZATION_PASS "
        f"version={result['numpy_version']} rewritten_pyds={len(result['rewritten_imports'])} "
        "redistributed_msvc_dll=false"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
