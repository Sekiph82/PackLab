from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[2] / ".github" / "workflows" / "windows-python-quality.yml"
)


def test_windows_python_quality_workflow_has_locked_least_privilege_contract() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "name: PackLab Windows Python Quality" in workflow
    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "branches:\n      - main" in workflow
    assert '"pyproject.toml"' in workflow
    assert '"uv.lock"' in workflow
    assert '"core/**"' in workflow
    assert '"apps/windows-studio/**"' in workflow
    assert '"tests/**"' in workflow
    assert '"tools/**"' in workflow
    assert "workflow_dispatch:" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "runs-on: windows-latest" in workflow
    assert "timeout-minutes: 45" in workflow
    assert 'python-version: "3.12"' in workflow
    assert 'version: "0.11.26"' in workflow
    assert "enable-cache: false" in workflow
    assert "persist-credentials: false" in workflow
    assert "fetch-depth: 0" in workflow
    assert "uv lock --check" in workflow
    assert "uv sync --locked --all-groups" in workflow
    assert "uv run --locked ruff check core apps tools tests" in workflow
    assert "uv run --locked ruff format --check -- $changedPython" in workflow
    assert "uv run --locked mypy core apps tools" in workflow
    assert "uv run --locked pytest -q" in workflow
    assert workflow.count("steps.locked-env.outcome == 'success'") == 4

    action_refs = re.findall(r"^\s+uses:\s+[^@\s]+@([^\s]+)", workflow, re.MULTILINE)
    assert len(action_refs) == 3
    assert all(re.fullmatch(r"[0-9a-f]{40}", revision) for revision in action_refs)
    assert "secrets." not in workflow
    assert "pull_request_target" not in workflow


def test_existing_preview_workflow_remains_separate() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    preview = WORKFLOW.with_name("packlab-preview-windows.yml")

    assert preview.is_file()
    assert "Build standalone preview EXE" not in workflow
    assert "PackLab Studio Preview Windows" in preview.read_text(encoding="utf-8")
