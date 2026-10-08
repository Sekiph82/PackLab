"""Fetch exact corresponding-source archives and verify the native source lock."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from tools.packaging.validate_windows_native_source_lock import load_source_lock

SOURCE_ROLES = {
    "SOURCE_BUILD_INPUT",
    "CORRESPONDING_SOURCE_AND_NOTICES",
    "CORRESPONDING_SOURCE_AND_THIRD_PARTY_INVENTORY",
    "CORRESPONDING_SOURCE_AND_NOTICE",
}


def fetch_verified_sources(
    lock_path: Path, destination: Path, evidence_path: Path
) -> dict[str, object]:
    lock = load_source_lock(lock_path)
    destination.mkdir(parents=True, exist_ok=True)
    evidence_records: list[dict[str, object]] = []
    for record in lock["records"]:
        if record["source_availability_role"] not in SOURCE_ROLES:
            continue
        filename = Path(urlparse(record["url"]).path).name
        target = destination / f"{record['id']}--{filename}"
        request = Request(record["url"], headers={"User-Agent": "PackLab-native-source-lock/1"})
        digest = hashlib.sha256()
        byte_length = 0
        with urlopen(request, timeout=120) as response, target.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                output.write(chunk)
                byte_length += len(chunk)
        actual = digest.hexdigest()
        if actual != record["sha256"]:
            target.unlink(missing_ok=True)
            raise ValueError(f"SHA-256 mismatch for source record {record['id']}")
        evidence_records.append(
            {
                "record_id": record["id"],
                "filename": filename,
                "expected_sha256": record["sha256"],
                "observed_sha256": actual,
                "byte_length": byte_length,
                "retained_runtime_surface": record["retained_runtime_surface"],
                "status": "PASS",
            }
        )
    evidence = {
        "schema_version": 1,
        "source_lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        "status": "PASS",
        "verified_source_count": len(evidence_records),
        "records": evidence_records,
    }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lock", type=Path, default=Path("tools/packaging/windows_native_source_lock.json")
    )
    parser.add_argument("--download-dir", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    result = fetch_verified_sources(args.lock, args.download_dir, args.evidence)
    print(
        f"WINDOWS_NATIVE_SOURCES_PASS count={result['verified_source_count']} sha256={result['source_lock_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
