"""Verify and preserve the exact PL-0350 R04 SDK/source-evidence artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from tools.packaging.validate_controlled_occt_sdk import validate_sdk
from tools.packaging.validate_windows_native_source_lock import load_source_lock

API = "https://api.github.com"
REPOSITORY = "Sekiph82/PackLab"
ORIGIN_RUN = "38346317865"
ORIGIN_HEAD = "a2805616c9c0dd665e48b1de82c8436ea64b0805"
SDK_ARTIFACT: dict[str, Any] = {
    "id": 11790440856,
    "name": "packlab-occt-sdk-38346317865-1",
    "size": 57520243,
    "digest": "sha256:467b44ab0fb747343cb55e55e71a0dd4ecadb989fd7eed22d1e49fff3153ddf8",
    "created_at": "2026-10-13T05:03:08Z",
    "expires_at": "2026-10-14T05:03:02Z",
}
SOURCE_ARTIFACT: dict[str, Any] = {
    "id": 11790585684,
    "name": "packlab-native-source-evidence-38346317865-1",
    "size": 1398,
    "digest": "sha256:091c391b8d6ccda19823f57eae891b1dd45383b164c117ca05928df6bafd2018",
    "created_at": "2026-10-13T05:03:10Z",
    "expires_at": "2026-10-14T05:03:09Z",
}
ORIGINAL_CACHE_KEY = (
    "Windows-x64-occt-sdk-v4-11b7a8319d065c3592f9bcaf6c39639a3de6bf623176cdd97319165b318775eb"
)
MAX_SDK_ZIP = 100 * 1024 * 1024
MAX_SOURCE_ZIP = 1024 * 1024
MAX_SDK_EXPANDED = 300 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def api_json(url: str, token: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "PackLab-PL0350-R05-recovery/1",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def download_artifact(artifact_id: int, token: str, destination: Path) -> None:
    url = f"{API}/repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "PackLab-PL0350-R05-recovery/1",
        },
    )
    # Fetch the API redirect first. Never forward the repository token to the
    # object-storage host; the signed Location URL is independently sufficient.
    opener = urllib.request.build_opener(NoRedirect())
    try:
        opener.open(request, timeout=60)
    except urllib.error.HTTPError as redirect_error:
        if redirect_error.code not in (301, 302, 303, 307, 308):
            raise
        location = redirect_error.headers.get("Location")
        if not location:
            raise ValueError("GitHub artifact API redirect omitted Location") from redirect_error
    else:
        raise ValueError("GitHub artifact API did not return a download redirect")
    parsed = urllib.parse.urlparse(location)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("GitHub artifact redirect is not a secure absolute URL")
    request = urllib.request.Request(location, headers={"User-Agent": "PackLab-artifact-recovery/1"})
    with urllib.request.urlopen(request, timeout=180) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output, length=1024 * 1024)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def extract_zip(archive: Path, destination: Path, maximum_bytes: int) -> list[dict[str, Any]]:
    destination.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    names: set[str] = set()
    expanded = 0
    with zipfile.ZipFile(archive) as zipped:
        for member in zipped.infolist():
            path = PurePosixPath(member.filename)
            mode = member.external_attr >> 16
            raw_parts = member.filename.split("/")
            if member.is_dir() and raw_parts[-1] == "":
                raw_parts.pop()
            if (
                path.is_absolute()
                or chr(92) in member.filename
                or any(part in {"", ".", ".."} for part in raw_parts)
                or (raw_parts and ":" in raw_parts[0])
                or stat.S_ISLNK(mode)
                or member.filename.casefold() in names
            ):
                raise ValueError(f"Unsafe, duplicate, or linked artifact member: {member.filename!r}")
            names.add(member.filename.casefold())
            expanded += member.file_size
            if expanded > maximum_bytes:
                raise ValueError("Artifact expanded size exceeds its fixed recovery bound")
            if member.is_dir():
                (destination / Path(*path.parts)).mkdir(parents=True, exist_ok=True)
                continue
            target = destination / Path(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            count = 0
            with zipped.open(member) as source, target.open("xb") as output:
                while block := source.read(1024 * 1024):
                    count += len(block)
                    if count > member.file_size:
                        raise ValueError("ZIP member exceeded declared byte length")
                    digest.update(block)
                    output.write(block)
            if count != member.file_size:
                raise ValueError(f"ZIP member byte length differs: {member.filename}")
            entries.append({"path": member.filename, "byte_length": count, "sha256": digest.hexdigest()})
    return entries


def artifact_metadata(artifact_id: int, expected: dict[str, Any], token: str) -> dict[str, Any]:
    item = api_json(f"{API}/repos/{REPOSITORY}/actions/artifacts/{artifact_id}", token)
    run = item.get("workflow_run") or {}
    if (
        item.get("id") != expected["id"]
        or item.get("name") != expected["name"]
        or item.get("size_in_bytes") != expected["size"]
        or item.get("digest") != expected["digest"]
        or item.get("expired") is not False
        or item.get("created_at") != expected["created_at"]
        or item.get("expires_at") != expected["expires_at"]
        or str(run.get("id")) != ORIGIN_RUN
        or run.get("head_sha") != ORIGIN_HEAD
    ):
        raise ValueError(f"Original artifact identity/expiry mismatch for ID {artifact_id}: {item}")
    expires_at = datetime.fromisoformat(item["expires_at"].replace("Z", "+00:00"))
    if expires_at <= datetime.now(UTC):
        raise ValueError(f"Original artifact expired before recovery: {artifact_id}")
    return item


def validate_source_evidence(path: Path) -> dict[str, Any]:
    lock_path = Path("tools/packaging/windows_native_source_lock.json")
    lock = load_source_lock(lock_path)
    expected = {
        row["id"]: row
        for row in lock["records"]
        if row["source_availability_role"]
        in {
            "SOURCE_BUILD_INPUT",
            "CORRESPONDING_SOURCE_AND_NOTICES",
            "CORRESPONDING_SOURCE_AND_THIRD_PARTY_INVENTORY",
            "CORRESPONDING_SOURCE_AND_NOTICE",
        }
    }
    evidence = json.loads(path.read_text(encoding="utf-8"))
    rows = evidence.get("records")
    if (
        evidence.get("schema_version") != 1
        or evidence.get("status") != "PASS"
        or evidence.get("source_lock_sha256") != sha256(lock_path)
        or evidence.get("verified_source_count") != len(expected)
        or not isinstance(rows, list)
        or {row.get("record_id") for row in rows} != set(expected)
    ):
        raise ValueError("Source-evidence artifact does not match the current frozen source lock")
    for row in rows:
        locked = expected[row["record_id"]]
        if (
            row.get("status") != "PASS"
            or row.get("expected_sha256") != locked["sha256"]
            or row.get("observed_sha256") != locked["sha256"]
            or row.get("retained_runtime_surface") != locked["retained_runtime_surface"]
            or not isinstance(row.get("byte_length"), int)
            or row["byte_length"] <= 0
        ):
            raise ValueError(f"Source evidence differs from its lock record: {row.get('record_id')}")
    return evidence


def recover(destination: Path, token: str, current_run_id: str, current_attempt: str) -> dict[str, Any]:
    if not token or not current_run_id or not current_attempt:
        raise ValueError("GitHub token and current run identity are required")
    workflow = api_json(f"{API}/repos/{REPOSITORY}/actions/runs/{ORIGIN_RUN}", token)
    if workflow.get("id") != int(ORIGIN_RUN) or workflow.get("head_sha") != ORIGIN_HEAD:
        raise ValueError("Origin workflow run identity differs from the frozen R04 run")
    destination.mkdir(parents=True, exist_ok=False)
    originals = destination / "origin-artifacts"
    originals.mkdir()
    sdk_raw = originals / "r04-occt-sdk-original.zip"
    source_raw = originals / "r04-source-evidence-original.zip"
    sdk_meta = artifact_metadata(SDK_ARTIFACT["id"], SDK_ARTIFACT, token)
    source_meta = artifact_metadata(SOURCE_ARTIFACT["id"], SOURCE_ARTIFACT, token)
    download_artifact(SDK_ARTIFACT["id"], token, sdk_raw)
    download_artifact(SOURCE_ARTIFACT["id"], token, source_raw)
    for path, expected, max_bytes in (
        (sdk_raw, SDK_ARTIFACT, MAX_SDK_ZIP),
        (source_raw, SOURCE_ARTIFACT, MAX_SOURCE_ZIP),
    ):
        actual_sha = sha256(path)
        actual_size = path.stat().st_size
        if actual_sha != expected["digest"].removeprefix("sha256:") or actual_size != expected["size"]:
            raise ValueError(f"Original artifact outer ZIP digest/size mismatch: {path.name}")
        if actual_size > max_bytes:
            raise ValueError(f"Original artifact exceeds fixed transfer bound: {path.name}")
    sdk_dir = destination / "sdk"
    sdk_members = extract_zip(sdk_raw, sdk_dir, MAX_SDK_EXPANDED)
    evidence_dir = destination / "source-evidence"
    evidence_members = extract_zip(source_raw, evidence_dir, MAX_SOURCE_ZIP)
    sdk_metadata = validate_sdk(sdk_dir, ORIGIN_RUN, "1", ORIGINAL_CACHE_KEY, require_opengl=True)
    evidence_candidates = list(evidence_dir.rglob("windows-native-source-evidence.json"))
    if len(evidence_candidates) != 1:
        raise ValueError("Source-evidence ZIP must contain exactly one canonical evidence JSON")
    evidence = validate_source_evidence(evidence_candidates[0])
    if (
        sdk_metadata["occt_source_id"] != "occt-source-7.9.3"
        or sdk_metadata["occt_source_revision"] != "a016080bf6738d6aeae020badee4e888ad1540a5"
        or sdk_metadata["compiler"] != "MSVC 19.44.35229.0"
        or sdk_metadata["windows_sdk"] != "10.0.26100.0"
        or sdk_metadata["python"] != "3.12.15"
        or sdk_metadata["cmake"] != "cmake version 3.31.8"
        or sdk_metadata["cmake_options"].get("USE_OPENGL") is not True
        or sdk_metadata["cmake_options"].get("USE_VTK") is not False
    ):
        raise ValueError("SDK source/toolchain/options do not meet the frozen R04 contract")
    layout_paths = {row["relative_path"] for row in sdk_metadata["files"]}
    for required in (
        "inc/OpenGl_Context.hxx",
        "win64/vc14/lib/TKOpenGl.lib",
        "win64/vc14/bin/TKOpenGl.dll",
    ):
        if required not in layout_paths:
            raise ValueError(f"Canonical nested SDK path missing: {required}")
    lineage = {
        "schema_version": 1,
        "status": "VERIFIED_ORIGINAL_BYTES_REPUBLISHED",
        "recovery_run": {"run_id": current_run_id, "attempt": current_attempt},
        "origin_run": {
            "run_id": ORIGIN_RUN,
            "head_sha": ORIGIN_HEAD,
            "workflow": workflow.get("path"),
            "run_attempt": workflow.get("run_attempt"),
        },
        "origin_artifacts": [
            {
                "id": entry["id"],
                "name": entry["name"],
                "size_bytes": entry["size"],
                "sha256": entry["digest"].removeprefix("sha256:"),
                "created_at": metadata.get("created_at"),
                "expires_at": metadata.get("expires_at"),
                "downloaded_sha256": sha256(raw),
                "downloaded_size_bytes": raw.stat().st_size,
                "original_workflow_run_id": str((metadata.get("workflow_run") or {}).get("id")),
                "original_head_sha": (metadata.get("workflow_run") or {}).get("head_sha"),
            }
            for entry, metadata, raw in (
                (SDK_ARTIFACT, sdk_meta, sdk_raw),
                (SOURCE_ARTIFACT, source_meta, source_raw),
            )
        ],
        "sdk": {
            "original_metadata_sha256": sha256(sdk_dir / "occt-sdk-metadata.json"),
            "original_producer_run_id": sdk_metadata["producer_run_id"],
            "original_producer_run_attempt": sdk_metadata["producer_run_attempt"],
            "original_cache_key": sdk_metadata["cache_key"],
            "source_lock_sha256": sdk_metadata["source_lock_sha256"],
            "toolchain_contract_sha256": sdk_metadata["toolchain_contract_sha256"],
            "occt_source_id": sdk_metadata["occt_source_id"],
            "occt_source_revision": sdk_metadata["occt_source_revision"],
            "occt_source_sha256": sdk_metadata["occt_source_sha256"],
            "compiler": sdk_metadata["compiler"],
            "windows_sdk": sdk_metadata["windows_sdk"],
            "python": sdk_metadata["python"],
            "cmake": sdk_metadata["cmake"],
            "cmake_options": sdk_metadata["cmake_options"],
            "file_count": sdk_metadata["file_count"],
            "byte_count": sdk_metadata["byte_count"],
            "payload_sha256": sdk_metadata["payload_sha256"],
            "sdk_zip_members": sdk_members,
        },
        "source_evidence": {
            "sha256": sha256(evidence_candidates[0]),
            "source_lock_sha256": evidence["source_lock_sha256"],
            "verified_source_count": evidence["verified_source_count"],
            "zip_members": evidence_members,
        },
        "preservation_rule": "Original archives and SDK metadata bytes are retained unchanged; lineage is additive.",
    }
    (destination / "sdk-recovery-lineage.json").write_text(
        json.dumps(lineage, indent=2) + "\n", encoding="utf-8"
    )
    return lineage


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lineage = recover(
        args.output,
        os.environ.get("GH_TOKEN", ""),
        os.environ.get("GITHUB_RUN_ID", ""),
        os.environ.get("GITHUB_RUN_ATTEMPT", ""),
    )
    print(
        "PL0350_R04_CHECKPOINT_RECOVERY_PASS "
        f"sdk_files={lineage['sdk']['file_count']} sdk_bytes={lineage['sdk']['byte_count']} "
        f"sdk_payload_sha256={lineage['sdk']['payload_sha256']} "
        f"source_records={lineage['source_evidence']['verified_source_count']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"PL0350_R04_CHECKPOINT_RECOVERY_BLOCKED: {error}", file=sys.stderr)
        raise SystemExit(1)
