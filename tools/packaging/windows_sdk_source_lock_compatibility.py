"""Validate the narrowly authorized R04-to-R05 SDK source-lock bridge."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

COMPATIBILITY_CONTRACT = Path("tools/packaging/windows_sdk_source_lock_compatibility.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sdk_relevant_projection(lock: dict[str, Any], allowed_additions: list[str]) -> dict[str, Any]:
    records = lock.get("records")
    if not isinstance(records, list):
        raise ValueError("Native source lock has no record list")
    by_id: dict[str, dict[str, Any]] = {}
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise ValueError("Native source lock contains a malformed source record")
        source_id = row["id"]
        if source_id in by_id:
            raise ValueError("Native source lock has duplicate records")
        by_id[source_id] = row
    if len(by_id) != len(records):
        raise ValueError("Native source lock has duplicate records")
    required_ids = lock.get("required_source_ids")
    production_components = lock.get("production_components")
    if not isinstance(required_ids, list) or not isinstance(production_components, dict):
        raise ValueError("Native source lock is missing its source and production contracts")
    return {
        "schema_version": lock.get("schema_version"),
        "lock_id": lock.get("lock_id"),
        "target": lock.get("target"),
        "build_environment_lock": lock.get("build_environment_lock"),
        "required_source_ids": sorted(set(required_ids) - set(allowed_additions)),
        "production_components": {
            name: sorted(set(source_ids) - set(allowed_additions))
            for name, source_ids in sorted(production_components.items())
        },
        "records": [by_id[source_id] for source_id in sorted(set(by_id) - set(allowed_additions))],
    }


def projection_sha256(projection: dict[str, Any]) -> str:
    payload = json.dumps(projection, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_sdk_source_lock_compatibility(
    metadata: dict[str, Any],
    source_lock_path: Path,
    compatibility_path: Path = COMPATIBILITY_CONTRACT,
) -> dict[str, str]:
    contract = json.loads(compatibility_path.read_text(encoding="utf-8"))
    lock = json.loads(source_lock_path.read_text(encoding="utf-8"))
    source_lock_sha = metadata.get("source_lock_sha256")
    current_sha = sha256(source_lock_path)
    if source_lock_sha == current_sha:
        return {"mode": "EXACT_CURRENT_SOURCE_LOCK", "source_lock_sha256": current_sha}
    if contract.get("schema_version") != 1 or source_lock_sha != contract.get(
        "accepted_origin_source_lock_sha256"
    ):
        raise ValueError("SDK checkpoint source-lock identity is neither current nor approved R04")
    additions = contract.get("allowed_post_origin_source_ids")
    if not isinstance(additions, list) or not additions:
        raise ValueError(
            "SDK source-lock compatibility contract has no explicit post-origin additions"
        )
    projection = sdk_relevant_projection(lock, additions)
    actual_projection_sha = projection_sha256(projection)
    if actual_projection_sha != contract.get("sdk_relevant_projection_sha256"):
        raise ValueError("Current SDK-relevant source inputs differ from the frozen R04 projection")
    return {
        "mode": "R04_ORIGIN_COMPATIBLE",
        "source_lock_sha256": source_lock_sha,
        "current_source_lock_sha256": current_sha,
        "sdk_relevant_projection_sha256": actual_projection_sha,
    }


def validate_sdk_toolchain_contract_compatibility(
    metadata: dict[str, Any],
    runtime_contract_path: Path = Path("tools/packaging/controlled_ocp_runtime_contract.json"),
    compatibility_path: Path = COMPATIBILITY_CONTRACT,
) -> dict[str, str]:
    contract = json.loads(compatibility_path.read_text(encoding="utf-8"))
    runtime_contract = json.loads(runtime_contract_path.read_text(encoding="utf-8"))
    contract_sha = metadata.get("toolchain_contract_sha256")
    current_sha = sha256(runtime_contract_path)
    if contract_sha == current_sha:
        return {
            "mode": "EXACT_CURRENT_TOOLCHAIN_CONTRACT",
            "toolchain_contract_sha256": current_sha,
        }
    if contract_sha != contract.get("accepted_origin_toolchain_contract_sha256"):
        raise ValueError("SDK checkpoint toolchain contract is neither current nor approved R04")
    projection = {
        key: value for key, value in runtime_contract.items() if key != "windows_runtime_deployment"
    }
    actual_projection_sha = projection_sha256(projection)
    if actual_projection_sha != contract.get("sdk_toolchain_contract_projection_sha256"):
        raise ValueError(
            "Current SDK toolchain inputs differ from the frozen R04 contract projection"
        )
    return {
        "mode": "R04_ORIGIN_COMPATIBLE",
        "toolchain_contract_sha256": contract_sha,
        "current_toolchain_contract_sha256": current_sha,
        "sdk_toolchain_contract_projection_sha256": actual_projection_sha,
    }
