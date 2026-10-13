from __future__ import annotations

import io
import json
from typing import Any

import pytest
from tools.packaging.assert_actions_run_artifact_budget import (
    current_run_artifact_bytes,
    ensure_artifact_budget,
    fetch_artifacts,
)


def test_current_artifact_bytes_counts_only_the_requested_run() -> None:
    artifacts: list[dict[str, Any]] = [
        {"size_in_bytes": 12, "workflow_run": {"id": 42}},
        {"size_in_bytes": 30, "workflow_run": {"id": 7}},
        {"size_in_bytes": 8, "workflow_run": None},
        {"size_in_bytes": 5, "workflow_run": {"id": "42"}},
    ]

    assert current_run_artifact_bytes(artifacts, "42") == 17


def test_fetch_artifacts_uses_the_bounded_current_run_inventory(monkeypatch) -> None:
    response = io.BytesIO(
        json.dumps(
            {
                "total_count": 1,
                "artifacts": [
                    {"size_in_bytes": 12, "workflow_run": {"id": 42}},
                ],
            }
        ).encode()
    )
    captured: dict[str, Any] = {}

    def open_request(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        return response

    monkeypatch.setattr(
        "tools.packaging.assert_actions_run_artifact_budget.urllib.request.urlopen", open_request
    )

    artifacts = fetch_artifacts("test-token", "42")

    assert artifacts == [{"size_in_bytes": 12, "workflow_run": {"id": 42}}]
    assert captured == {
        "url": "https://api.github.com/repos/Sekiph82/PackLab/actions/runs/42/artifacts?per_page=100",
        "authorization": "Bearer test-token",
        "timeout": 30,
    }


def test_fetch_artifacts_rejects_overflow_for_the_current_run(monkeypatch) -> None:
    response = io.BytesIO(json.dumps({"total_count": 101, "artifacts": []}).encode())
    monkeypatch.setattr(
        "tools.packaging.assert_actions_run_artifact_budget.urllib.request.urlopen",
        lambda request, timeout: response,
    )

    with pytest.raises(ValueError, match="current-run.*100-item"):
        fetch_artifacts("test-token", "42")


def test_budget_accepts_exact_boundary_and_rejects_overflow() -> None:
    ensure_artifact_budget(60, 40, 100)

    with pytest.raises(ValueError, match="exceed"):
        ensure_artifact_budget(60, 41, 100)


@pytest.mark.parametrize("counts", [(-1, 0, 10), (0, -1, 10), (0, 0, -1)])
def test_budget_rejects_negative_counts(counts: tuple[int, int, int]) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        ensure_artifact_budget(*counts)
