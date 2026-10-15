from __future__ import annotations

import re
from pathlib import Path

from tools.ci.ci_data_safety import TAINTED_ENVIRONMENT

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
    assert "ruff format --check --config" in workflow
    assert "format.line-ending = 'auto'" in workflow
    assert "-- $changedPython" in workflow
    assert "uv run --locked mypy core apps tools" in workflow
    assert "uv run --locked pytest -q" in workflow
    assert workflow.count("steps.locked-env.outcome == 'success'") == 4
    assert "Guard tracked data and developer-runtime boundaries" in workflow
    assert "--tracked --check-workflows --check-environment" in workflow
    assert workflow.index("Set up Python 3.12") < workflow.index("ci_data_safety")
    assert workflow.index("ci_data_safety") < workflow.index("Install pinned uv")
    assert workflow.index("ci_data_safety") < workflow.index("Unit and repository tests")
    assert 'PYTHONNOUSERSITE: "1"' in workflow
    for name in TAINTED_ENVIRONMENT:
        assert f'{name}: ""' in workflow

    action_refs = re.findall(r"^\s+uses:\s+[^@\s]+@([^\s]+)", workflow, re.MULTILINE)
    assert len(action_refs) == 4
    assert all(re.fullmatch(r"[0-9a-f]{40}", revision) for revision in action_refs)
    assert "secrets." not in workflow
    assert "pull_request_target" not in workflow


def test_windows_quality_cache_is_exact_locked_uv_package_cache() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "uses: actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9" in workflow
    assert "path: ${{ runner.temp }}/uv-cache" in workflow
    assert 'Join-Path $env:RUNNER_TEMP "uv-cache"' in workflow
    assert '"UV_CACHE_DIR=$uvCacheDir" >> $env:GITHUB_ENV' in workflow
    assert (
        "key: ${{ runner.os }}-${{ runner.arch }}-python-3.12-uv-0.11.26-"
        "${{ hashFiles('uv.lock') }}"
    ) in workflow
    assert "restore-keys:" not in workflow
    assert (
        workflow.index("Restore exact uv dependency cache")
        < workflow.index("Configure uv dependency cache directory")
        < workflow.index("uv lock --check")
    )
    assert '".venv"' not in workflow
    assert ".packscan" not in workflow
    assert "packaging-library" not in workflow
    assert "secrets." not in workflow


def test_existing_preview_workflow_remains_separate() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    preview = WORKFLOW.with_name("packlab-preview-windows.yml")

    assert preview.is_file()
    assert "Build standalone preview EXE" not in workflow
    preview_text = preview.read_text(encoding="utf-8")
    assert "PackLab Studio Preview Windows" in preview_text
    assert "actions/checkout@v4" not in preview_text
    assert "actions/setup-python@v5" not in preview_text
    assert 'version = "6.22.3"' in (WORKFLOW.parents[2] / "uv.lock").read_text(encoding="utf-8")
    assert "uv lock --check" in preview_text
    assert "uv sync --locked --only-group dev --no-install-project" in preview_text
    assert "uv run --locked --no-sync pyinstaller" in preview_text
    assert "python -m pip install" not in preview_text
    assert "Guard source and developer-runtime boundaries" in preview_text
    assert "Guard preview artifact inputs" in preview_text
    assert 'PYTHONNOUSERSITE: "1"' in preview_text
    for name in TAINTED_ENVIRONMENT:
        assert f'{name}: ""' in preview_text
    assert preview_text.index("ci_data_safety") < preview_text.index("Install PyInstaller")
    assert (
        "--path dist/PackLabStudioPreview.exe --path dist-installer/PackLabStudioPreviewSetup.exe"
        in preview_text
    )
    assert preview_text.index("Guard preview artifact inputs") < preview_text.index(
        "actions/upload-artifact@"
    )
    preview_action_refs = re.findall(r"^\s+uses:\s+[^@\s]+@([^\s]+)", preview_text, re.MULTILINE)
    assert len(preview_action_refs) == 4
    assert all(re.fullmatch(r"[0-9a-f]{40}", revision) for revision in preview_action_refs)
    assert "permissions:\n  contents: read" in preview_text
    assert "secrets." not in preview_text
