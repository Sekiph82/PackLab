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
    assert "--verify-build-lock --verify-conda-lock --verify-uv-lock" in workflow
    assert "mamba-org/setup-micromamba@f457c30a868e4760d3a6fcea5f25dc655b8edf39" in workflow
    assert "uv tool run --from conda-lock==3.0.0 conda-lock render" in workflow
    assert "--kind explicit" in workflow
    assert "--platform win-64" in workflow
    assert "environment-file: ${{ steps.render_ocp_lock.outputs.path }}" in workflow
    assert workflow.index("Render hash-pinned OCP explicit package lock") < workflow.index(
        "Create exact OCP source-build environment"
    )
    assert 'micromamba-version: "2.0.5-0"' in workflow
    assert "fetch_verify_windows_native_sources.py" in workflow
    assert workflow.index("Fetch and verify every locked corresponding source") < workflow.index(
        "Build and overlay the controlled OCP/OCCT runtime"
    )
    assert "build_controlled_ocp_runtime.py" in workflow
    assert "validate_controlled_ocp_manifest.py" in workflow
    assert workflow.index("Build and overlay the controlled OCP/OCCT runtime") < workflow.index(
        "Build one-directory production Studio staging output"
    )
    assert "--ocp-manifest $env:PACKLAB_CONTROLLED_OCP_MANIFEST" in workflow
    assert '"tools/packaging/packlab_studio.spec"' in workflow
    assert '"--noupx"' not in workflow
    assert "Assert staged Qt module surface" in workflow
    assert "assert_staged_qt_surface.py" in workflow
    assert "PACKLAB_RUNTIME_CAPABILITIES_PATH" in workflow
    assert "qt_vector_pdf" in workflow
    assert "ocp_cad" in workflow
    assert "open3d_geometry" in workflow
    assert "windows-runtime-capabilities.json" in workflow
    assert '"PACKLAB_BUILD_REVISION=$revision"' in workflow
    assert "Start-Process -FilePath $studioExe" in workflow
    assert '"--packlab-build-smoke"' in workflow
    assert "WaitForExit(120000)" in workflow
    assert "PACKLAB_BUILD_SMOKE_LOG" in workflow
    assert "PL-0350 owns native/runtime inventory" in workflow
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in workflow
    assert "--staging-dir $appDirectory" in workflow
    assert "--collect-toc $collectMatches[0].FullName" in workflow
    assert "compliance-validation.json" in workflow
    assert "unresolved_count -ne 0" in workflow
    assert "if-no-files-found: error" in workflow
    assert workflow.count("retention-days: 1") == 3
    assert workflow.index("Upload text-only pre-clearance evidence") < workflow.index(
        "Enforce redistribution clearance"
    )
    assert workflow.index("Revalidate exact installer input tree") < workflow.index(
        "Install pinned Inno Setup"
    )
    assert "if: steps.clearance.outputs.cleared == 'true'" in workflow
    assert "9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732" in workflow
    assert "packlab_preview" not in workflow
    assert "secrets." not in workflow
    spec = (ROOT / "tools" / "packaging" / "packlab_studio.spec").read_text(encoding="utf-8")
    assert '"PySide6.QtPdf"' in spec
    assert '"PySide6.QtSvg"' in spec
    assert '"OCP.BRepAlgoAPI"' in spec
    assert '"open3d.pybind"' in spec
    assert 'copy_metadata("cadquery-ocp-novtk")' in spec
    assert "upx=False" in spec
    assert 'base.startswith("icu")' in spec
    assert "collect_all" not in spec
    assert '"IPython", "jedi", "nbformat", "pytest"' in spec


def test_studio_entry_shim_invokes_production_application() -> None:
    entry = (ROOT / "tools" / "packaging" / "packlab_studio_entry.py").read_text(encoding="utf-8")

    assert entry.index("register_frozen_native_directories()") < entry.index(
        "from packlab_studio.app import main"
    )
    assert "from packlab_studio.app import main" in entry
    assert "raise SystemExit(main())" in entry
