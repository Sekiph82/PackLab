"""Authenticate and inspect the immutable, recovered PL-0350 R04 OCCT SDK."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from tools.packaging.validate_controlled_occt_sdk import validate_sdk
from tools.packaging.windows_sdk_source_lock_compatibility import (
    validate_sdk_source_lock_compatibility,
    validate_sdk_toolchain_contract_compatibility,
)

REPOSITORY = "Sekiph82/PackLab"
ARTIFACT_ID = 11796717315
ARTIFACT_NAME = "packlab-pl0350-r04-sdk-recovery-38366186522-1"
PRODUCER_RUN_ID = "38366186522"
PRODUCER_ATTEMPT = "1"
PRODUCER_SHA = "cfcbaa99621868e1238a3210e7113fe77a896d4d"
ARCHIVE_BYTES = 114_366_551
ARCHIVE_SHA256 = "3339c28cd99605c3c928f9c4f145245b39efb1f7ed99a19a17c1547d8e101c4e"
MAX_ARCHIVE_BYTES = 120 * 1024 * 1024
MAX_EXTRACTED_BYTES = 300 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 100_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Keep the GitHub bearer token away from the signed blob redirect host."""

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str):
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def request_json(url: str, token: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError("GitHub API returned a non-object response")
    return value


def download_archive(token: str, destination: Path) -> None:
    endpoint = f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/{ARTIFACT_ID}/zip"
    request = urllib.request.Request(
        endpoint,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    opener = urllib.request.build_opener(NoRedirect)
    try:
        response = opener.open(request, timeout=30)
    except urllib.error.HTTPError as error:
        if error.code not in (301, 302, 303, 307, 308):
            raise
        location = error.headers.get("Location")
        if not location:
            raise ValueError(
                "GitHub artifact redirect did not provide a download location"
            ) from error
        response = urllib.request.urlopen(location, timeout=60)
    total = 0
    with response, destination.open("xb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_ARCHIVE_BYTES:
                raise ValueError("Retained SDK archive exceeds the bounded 60 MiB download limit")
            output.write(chunk)
    if total != ARCHIVE_BYTES or sha256_file(destination) != ARCHIVE_SHA256:
        raise ValueError(
            "Downloaded retained SDK outer ZIP size or SHA-256 differs from GitHub metadata"
        )


def safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    total = 0
    seen: set[str] = set()
    with zipfile.ZipFile(archive) as zipped:
        infos = zipped.infolist()
        if len(infos) > MAX_ARCHIVE_ENTRIES:
            raise ValueError("Retained SDK ZIP exceeds the bounded entry count")
        for info in infos:
            relative = PurePosixPath(info.filename)
            folded = relative.as_posix().casefold().rstrip("/")
            mode = (info.external_attr >> 16) & 0xFFFF
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or not folded
                or folded in seen
                or (mode & 0o170000) == 0o120000
            ):
                raise ValueError("Retained SDK ZIP contains an unsafe or case-colliding path")
            seen.add(folded)
            total += info.file_size
            if total > MAX_EXTRACTED_BYTES:
                raise ValueError("Retained SDK ZIP exceeds the bounded 512 MiB extraction limit")
            target = destination.joinpath(*relative.parts)
            resolved = target.resolve()
            if destination.resolve() not in resolved.parents and resolved != destination.resolve():
                raise ValueError("Retained SDK ZIP entry escapes the bounded scratch directory")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipped.open(info) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output, 1024 * 1024)


def inventory(sdk: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    files = [entry["relative_path"] for entry in metadata["files"]]
    opengl_header = [name for name in files if name.casefold().endswith("/opengl_context.hxx")]
    tk_lib = [name for name in files if name.casefold().endswith("/tkopengl.lib")]
    tk_dll = [name for name in files if name.casefold().endswith("/tkopengl.dll")]
    include_dirs = sorted(
        {
            str(path.relative_to(sdk)).replace("\\", "/")
            for path in sdk.rglob("*")
            if path.is_dir() and path.name.casefold() in {"include", "inc"}
        },
        key=str.casefold,
    )
    cmake_refs: list[dict[str, str]] = []
    for path in sdk.rglob("*.cmake"):
        if path.is_symlink() or not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        interesting = [
            line.strip()
            for line in content.splitlines()
            if any(
                token in line.casefold() for token in ("tkopengl", "opengl", "include_directories")
            )
        ]
        if interesting:
            cmake_refs.append(
                {
                    "file": path.relative_to(sdk).as_posix(),
                    "references": " | ".join(interesting[:20]),
                }
            )
    return {
        "OpenGl_Context.hxx": opengl_header,
        "TKOpenGl.lib": tk_lib,
        "TKOpenGl.dll": tk_dll,
        "installed_include_directories": include_dirs,
        "cmake_export_references": cmake_refs,
    }


def inspect(scratch: Path) -> dict[str, Any]:
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise ValueError("GH_TOKEN is required to download the retained Actions artifact")
    if scratch.exists():
        raise ValueError("Inspection scratch path must not already exist")
    scratch.mkdir(parents=True)
    metadata = request_json(
        f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/{ARTIFACT_ID}", token
    )
    workflow = metadata.get("workflow_run") or {}
    expected = {
        "id": ARTIFACT_ID,
        "name": ARTIFACT_NAME,
        "size_in_bytes": ARCHIVE_BYTES,
        "digest": f"sha256:{ARCHIVE_SHA256}",
        "expired": False,
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ValueError("Retained SDK artifact metadata differs from the frozen identity")
    if (
        str(workflow.get("id")) != PRODUCER_RUN_ID
        or workflow.get("head_branch") != "main"
        or workflow.get("head_sha") != PRODUCER_SHA
    ):
        raise ValueError(
            "Retained SDK producer run or source revision differs from the frozen identity"
        )
    archive = scratch / "retained-occt-sdk.zip"
    extracted = scratch / "sdk"
    download_archive(token, archive)
    safe_extract(archive, extracted)
    if (extracted / "occt-sdk-metadata.json").is_file():
        sdk = extracted
    else:
        sdk_dirs = [path for path in extracted.iterdir() if path.is_dir()]
        sdk_roots = [path for path in sdk_dirs if (path / "occt-sdk-metadata.json").is_file()]
        if len(sdk_roots) != 1:
            raise ValueError("Retained SDK archive does not have one unambiguous SDK root")
        sdk = sdk_roots[0]
    metadata_path = sdk / "occt-sdk-metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    cache_key = metadata.get("cache_key")
    lineage_path = extracted / "sdk-recovery-lineage.json"
    if not lineage_path.is_file():
        raise ValueError("Recovered SDK artifact is missing its immutable origin lineage")
    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    expected_origin_artifacts = {
        11790440856: "467b44ab0fb747343cb55e55e71a0dd4ecadb989fd7eed22d1e49fff3153ddf8",
        11790585684: "091c391b8d6ccda19823f57eae891b1dd45383b164c117ca05928df6bafd2018",
    }
    if (
        lineage.get("schema_version") != 1
        or lineage.get("status") != "VERIFIED_ORIGINAL_BYTES_REPUBLISHED"
        or str((lineage.get("recovery_run") or {}).get("run_id")) != PRODUCER_RUN_ID
        or str((lineage.get("origin_run") or {}).get("run_id")) != "38346317865"
        or (lineage.get("origin_run") or {}).get("head_sha")
        != "a2805616c9c0dd665e48b1de82c8436ea64b0805"
        or {int(row.get("id")): row.get("sha256") for row in lineage.get("origin_artifacts", [])}
        != expected_origin_artifacts
    ):
        raise ValueError(
            "Recovered SDK origin artifact/run lineage differs from the frozen evidence"
        )
    if (
        not isinstance(cache_key, str)
        or cache_key
        != "Windows-x64-occt-sdk-v4-11b7a8319d065c3592f9bcaf6c39639a3de6bf623176cdd97319165b318775eb"
    ):
        raise ValueError("Recovered SDK metadata has an unexpected original producer cache key")
    origin_metadata_sha = sha256_file(metadata_path)
    if (lineage.get("sdk") or {}).get("original_metadata_sha256") != origin_metadata_sha:
        raise ValueError("Recovered SDK metadata bytes differ from the recovery lineage")
    validated = validate_sdk(sdk, "38346317865", "1", cache_key, require_opengl=True)
    compatibility = validate_sdk_source_lock_compatibility(
        validated, Path("tools/packaging/windows_native_source_lock.json")
    )
    toolchain_compatibility = validate_sdk_toolchain_contract_compatibility(validated)
    if compatibility.get("mode") != "R04_ORIGIN_COMPATIBLE":
        raise ValueError(
            "Recovered SDK did not use the explicit R04 source-lock compatibility bridge"
        )
    result = inventory(sdk, validated)
    return {
        "artifact_id": ARTIFACT_ID,
        "artifact_name": ARTIFACT_NAME,
        "producer_run_id": PRODUCER_RUN_ID,
        "producer_attempt": PRODUCER_ATTEMPT,
        "producer_sha": PRODUCER_SHA,
        "outer_archive_bytes": archive.stat().st_size,
        "outer_archive_sha256": sha256_file(archive),
        "cache_key": cache_key,
        "source_lock_sha256": validated["source_lock_sha256"],
        "occt_source_id": validated["occt_source_id"],
        "occt_source_revision": validated["occt_source_revision"],
        "occt_source_sha256": validated["occt_source_sha256"],
        "windows_sdk": validated["windows_sdk"],
        "python": validated["python"],
        "cmake": validated["cmake"],
        "compiler": validated["compiler"],
        "parallelism": validated["parallelism"],
        "sealed_file_count": validated["file_count"],
        "sealed_byte_count": validated["byte_count"],
        "inner_payload_sha256": validated["payload_sha256"],
        "source_lock_compatibility": compatibility,
        "toolchain_contract_compatibility": toolchain_compatibility,
        "recovery_lineage_sha256": sha256_file(lineage_path),
        **result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = inspect(args.scratch)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
