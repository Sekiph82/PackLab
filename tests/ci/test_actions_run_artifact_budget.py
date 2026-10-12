from __future__ import annotations

from typing import Any

import pytest
from tools.packaging.assert_actions_run_artifact_budget import (
    current_run_artifact_bytes,
    ensure_artifact_budget,
)


def test_current_artifact_bytes_counts_only_the_requested_run() -> None:
    artifacts: list[dict[str, Any]] = [
        {"size_in_bytes": 12, "workflow_run": {"id": 42}},
        {"size_in_bytes": 30, "workflow_run": {"id": 7}},
        {"size_in_bytes": 8, "workflow_run": None},
        {"size_in_bytes": 5, "workflow_run": {"id": "42"}},
    ]

    assert current_run_artifact_bytes(artifacts, "42") == 17


def test_budget_accepts_exact_boundary_and_rejects_overflow() -> None:
    ensure_artifact_budget(60, 40, 100)

    with pytest.raises(ValueError, match="exceed"):
        ensure_artifact_budget(60, 41, 100)


@pytest.mark.parametrize("counts", [(-1, 0, 10), (0, -1, 10), (0, 0, -1)])
def test_budget_rejects_negative_counts(counts: tuple[int, int, int]) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        ensure_artifact_budget(*counts)
