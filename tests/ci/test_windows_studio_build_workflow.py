from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "windows-studio-build.yml"


def test_windows_studio_build_is_pinned_and_limited_to_staging() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "runs-on: windows-latest" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0" in workflow
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97" in workflow
    assert "astral-sh/setup-uv@bec219d24cd3e171d82865faccec33120bb574f4" in workflow
    assert "actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9" in workflow
    assert "uv lock --check" in workflow
    assert "uv sync --locked --all-groups" in workflow
    assert "uv run --locked python @pyinstallerArgs" in workflow
    assert '"--onedir", "--windowed", "--noupx"' in workflow
    assert '"tools/packaging/packlab_studio_entry.py"' in workflow
    assert '"$schemaPath;schemas"' in workflow
    assert '"PACKLAB_BUILD_REVISION=$revision"' in workflow
    assert "Start-Process -FilePath $studioExe" in workflow
    assert '"--packlab-build-smoke"' in workflow
    assert "WaitForExit(30000)" in workflow
    assert "PACKLAB_BUILD_SMOKE_LOG" in workflow
    assert "PL-0350 owns native/runtime inventory" in workflow
    assert "actions/upload-artifact" not in workflow
    assert "packlab_preview" not in workflow
    assert "secrets." not in workflow


def test_studio_entry_shim_invokes_production_application() -> None:
    entry = (ROOT / "tools" / "packaging" / "packlab_studio_entry.py").read_text(encoding="utf-8")

    assert "from packlab_studio.app import main" in entry
    assert "raise SystemExit(main())" in entry
