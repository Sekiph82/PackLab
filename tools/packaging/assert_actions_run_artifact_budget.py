"""Fail closed when current-run Actions artifacts plus a pending upload exceed budget."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from typing import Any

REPOSITORY = "Sekiph82/PackLab"


def current_run_artifact_bytes(artifacts: list[dict[str, Any]], run_id: str) -> int:
    return sum(
        int(item["size_in_bytes"])
        for item in artifacts
        if str((item.get("workflow_run") or {}).get("id")) == str(run_id)
    )


def ensure_artifact_budget(current_bytes: int, additional_bytes: int, max_bytes: int) -> None:
    if min(current_bytes, additional_bytes, max_bytes) < 0:
        raise ValueError("artifact byte counts and budget must be non-negative")
    if current_bytes + additional_bytes > max_bytes:
        raise ValueError(
            f"current-run artifacts ({current_bytes}) plus pending upload ({additional_bytes}) "
            f"exceed the {max_bytes}-byte run ceiling"
        )


def fetch_artifacts(token: str, run_id: str) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError) as error:
        raise ValueError("could not read the bounded GitHub Actions artifact inventory") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("artifacts"), list):
        raise ValueError("GitHub Actions artifact inventory has an unexpected response shape")
    if payload.get("total_count", 0) > 100:
        raise ValueError("current-run Actions artifact inventory exceeds the bounded 100-item page")
    return payload["artifacts"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID"), required=False)
    parser.add_argument("--max-bytes", required=True, type=int)
    parser.add_argument("--additional-bytes", required=True, type=int)
    args = parser.parse_args()
    token = os.environ.get("GH_TOKEN")
    if not token or not args.run_id:
        raise ValueError("GH_TOKEN and GITHUB_RUN_ID are required")
    current = current_run_artifact_bytes(fetch_artifacts(token, args.run_id), args.run_id)
    ensure_artifact_budget(current, args.additional_bytes, args.max_bytes)
    print(
        f"ACTIONS_RUN_ARTIFACT_BUDGET_PASS current={current} "
        f"pending={args.additional_bytes} maximum={args.max_bytes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
