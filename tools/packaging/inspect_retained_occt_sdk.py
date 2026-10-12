"""Read-only, bounded inspection of the immutable PL-0350 R02 OCCT SDK artifact."""

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

REPOSITORY = "Sekiph82/PackLab"
ARTIFACT_ID = 11755977987
ARTIFACT_NAME = "packlab-occt-sdk-38263302823-1"
PRODUCER_RUN_ID = "38263302823"
PRODUCER_ATTEMPT = "1"
PRODUCER_SHA = "4f064e2f44359a40298d13baece02dcb18fb01f7"
ARCHIVE_BYTES = 56_405_631
ARCHIVE_SHA256 = "1ad03b366958f0a81d98813fac313d85d0133e79db9e85f4844d783b0306d0ae"
MAX_ARCHIVE_BYTES = 60 * 1024 * 1024
MAX_EXTRACTED_BYTES = 512 * 1024 * 1024
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
    endpoint = (
        f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/{ARTIFACT_ID}/zip"
    )
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
            raise ValueError("GitHub artifact redirect did not provide a download location") from error
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
        raise ValueError("Downloaded retained SDK outer ZIP size or SHA-256 differs from GitHub metadata")


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
            if any(token in line.casefold() for token in ("tkopengl", "opengl", "include_directories"))
        ]
        if interesting:
            cmake_refs.append(
                {"file": path.relative_to(sdk).as_posix(), "references": " | ".join(interesting[:20])}
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
        raise ValueError("Retained SDK producer run or source revision differs from the frozen identity")
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
    if not isinstance(cache_key, str) or not cache_key.startswith("Windows-x64-occt-sdk-v2-"):
        raise ValueError("Retained SDK metadata has an unexpected producer cache key")
    validated = validate_sdk(sdk, PRODUCER_RUN_ID, PRODUCER_ATTEMPT, cache_key)
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
        **result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.scratch)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
