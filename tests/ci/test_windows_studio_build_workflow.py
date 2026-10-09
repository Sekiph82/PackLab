from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "windows-studio-build.yml"


def test_controlled_runtime_producer_is_isolated_and_fail_closed() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "runs-on: windows-2022" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0" in workflow
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97" in workflow
    assert "astral-sh/setup-uv@bec219d24cd3e171d82865faccec33120bb574f4" in workflow
    assert "actions/cache/restore@55cc8345863c7cc4c66a329aec7e433d2d1c52a9" in workflow
    assert "actions/cache/save@55cc8345863c7cc4c66a329aec7e433d2d1c52a9" in workflow
    assert "actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f" in workflow
    assert "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c" in workflow

    producer = workflow.split("  controlled-ocp-runtime:\n", 1)[1].split("  build-studio:\n", 1)[0]
    assert "timeout-minutes: 480" in producer
    assert "N_PROC=4" in producer or "--bindgen-workers 4" in producer
    assert "--cmake-parallel 4" in producer
    assert "build_controlled_ocp_runtime.py" in producer
    assert "fetch_verify_windows_native_sources.py" in producer
    assert "controlled_ocp_runtime_bundle.py seal" in producer
    assert "controlled_ocp_runtime_bundle.py validate" in producer
    assert "controlled_ocp_runtime_bundle.py install" in producer
    assert "controlled_ocp_runtime_bundle.py smoke" in producer
    assert "Record controlled-runtime source and environment setup timing" in producer
    assert "Start controlled-runtime validation and transfer timing" in producer
    assert "Record controlled-runtime validation and transfer timing" in producer
    assert "bundle-artifact-bytes" in producer
    assert "artifact_bytes=$artifactBytes" in producer
    assert "CONTROLLED_OCP_CACHE_HIT_VALIDATED" in producer
    assert "CONTROLLED_OCP_CACHE_REJECTED_REBUILD" in producer
    assert "steps.bundle_cache_check.outputs.valid != 'true'" in producer
    assert "controlled-ocp-py3.12-v1-${{ hashFiles(" in producer
    assert "restore-keys:" not in producer
    cache_key_line = next(
        line for line in producer.splitlines() if "controlled-ocp-py3.12-v1-${{ hashFiles(" in line
    )
    for native_input in (
        "windows_native_source_lock.json",
        "packlab-ocp-bindings-win.lock",
        "build_controlled_ocp_runtime.py",
        "controlled_ocp_runtime_bundle.py",
        "validate_controlled_ocp_manifest.py",
        "validate_windows_native_source_lock.py",
        "fetch_verify_windows_native_sources.py",
        "controlled_ocp_runtime_contract.json",
    ):
        assert native_input in cache_key_line
    assert "${{ github.sha }}" not in cache_key_line
    assert "${{ github.ref }}" not in cache_key_line
    assert "windows-studio-build.yml" not in cache_key_line
    assert "tests/ci/" not in cache_key_line
    assert "N_PROC=4" in (ROOT / "tools/packaging/controlled_ocp_runtime_contract.json").read_text(
        encoding="utf-8"
    ) or '"ocp_bindgen_workers": 4' in (
        ROOT / "tools/packaging/controlled_ocp_runtime_contract.json"
    ).read_text(encoding="utf-8")
    contract = json.loads(
        (ROOT / "tools/packaging/controlled_ocp_runtime_contract.json").read_text(encoding="utf-8")
    )
    assert contract["ocp_bindgen_workers"] == 4
    assert contract["cmake_parallel"] == 4
    assert contract["target"]["python_minor"] == "3.12"

    builder = (ROOT / "tools/packaging/build_controlled_ocp_runtime.py").read_text(encoding="utf-8")
    assert '"-DN_PROC={args.bindgen_workers}"' in builder
    assert '"--target",\n            "pywrap"' in builder
    assert '"--parallel",\n            str(args.cmake_parallel)' in builder
    assert '"pywrap_generation"' in builder
    assert '"ocp_native_compile_link"' in builder

    bundle_helper = (ROOT / "tools/packaging/controlled_ocp_runtime_bundle.py").read_text(
        encoding="utf-8"
    )
    assert '"bundle_validator_sha256"' in bundle_helper
    assert '"runtime_files": runtime_files' in bundle_helper
    assert '"bundle_content_sha256"' in bundle_helper
    assert '"cache_key": args.cache_key' in bundle_helper
    assert "validate_staged_tree(bundle, manifest)" in bundle_helper
    assert "cadquery_ocp_novtk.libs" in bundle_helper
    assert "symbolic links" in bundle_helper


def test_packaging_job_consumes_only_same_run_validated_artifact() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    producer = workflow.split("  controlled-ocp-runtime:\n", 1)[1].split("  build-studio:\n", 1)[0]
    packaging = workflow.split("  build-studio:\n", 1)[1]

    assert "needs: controlled-ocp-runtime" in packaging
    assert "needs.controlled-ocp-runtime.outputs.bundle-artifact-name" in packaging
    assert "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c" in packaging
    assert "controlled_ocp_runtime_bundle.py validate" in packaging
    assert "controlled_ocp_runtime_bundle.py install" in packaging
    assert "build_controlled_ocp_runtime.py" not in packaging
    assert "fetch_verify_windows_native_sources.py" not in packaging
    assert "micromamba" not in packaging
    assert "controlled_ocp_runtime_bundle.py smoke" in producer
    smoke_step = producer.split(
        "      - name: Install and smoke-test controlled runtime in producer environment\n", 1
    )[1].split("      - name:", 1)[0]
    assert "if:" not in smoke_step
    assert producer.index("controlled_ocp_runtime_bundle.py smoke") < producer.index(
        "Upload same-run verified controlled runtime"
    )
    assert "Record packaging job start" in packaging
    assert "Record packaging job duration" in packaging
    assert "Downloaded bundle bytes" in packaging
    assert "Validate bidirectional controlled OCP manifest" in packaging
    assert "Smoke-test packaged Studio without network" in packaging
    assert "Enforce redistribution clearance" in packaging
    assert "Build versioned unsigned installer" in packaging


def test_windows_studio_build_keeps_quality_and_privacy_contracts() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    packaging = workflow.split("  build-studio:\n", 1)[1]
    assert "uv lock --check" in workflow
    assert "uv sync --locked --all-groups" in workflow
    assert "--verify-build-lock --verify-conda-lock --verify-uv-lock" in workflow
    assert "mamba-org/setup-micromamba@f457c30a868e4760d3a6fcea5f25dc655b8edf39" in workflow
    assert "uv tool run --from conda-lock==3.0.0 conda-lock render" in workflow
    assert "--kind explicit" in workflow
    assert "--platform win-64" in workflow
    assert "environment-file: ${{ steps.render_ocp_lock.outputs.path }}" in workflow
    assert 'micromamba-version: "2.0.5-0"' in workflow
    assert "PYTHONPATH: ${{ github.workspace }}" in workflow
    assert "Remove-Item Env:Python_ROOT_DIR,Env:Python2_ROOT_DIR,Env:Python3_ROOT_DIR" in workflow
    ocp_builder = (ROOT / "tools" / "packaging" / "build_controlled_ocp_runtime.py").read_text(
        encoding="utf-8"
    )
    assert 'OCP_PYWRAP_SOURCE_ID = "ocp-pywrap-source-9251940"' in ocp_builder
    assert 'shutil.copytree(pywrap_source, ocp_source / "pywrap")' in ocp_builder
    assert '"ocp_pywrap_source_revision"' in ocp_builder
    assert '"-DOPENGL_INCLUDE_DIR={windows_gl_include}"' in ocp_builder
    assert 'WINDOWS_SDK_VERSION = "10.0.26100.0"' in ocp_builder
    assert ocp_builder.count('f"-DCMAKE_SYSTEM_VERSION={WINDOWS_SDK_VERSION}"') == 3
    assert '"windows_sdk": windows_sdk_version' in ocp_builder
    assert 'f"-DPython_EXECUTABLE={sys.executable}"' in ocp_builder
    assert '"-DPLATFORM=Windows"' not in ocp_builder
    assert "validate_controlled_ocp_manifest.py" in workflow
    assert "--ocp-manifest $env:PACKLAB_CONTROLLED_OCP_MANIFEST" in packaging
    assert '"tools/packaging/packlab_studio.spec"' in packaging
    assert '"--noupx"' not in packaging
    assert "Assert staged Qt module surface" in packaging
    assert "assert_staged_qt_surface.py" in packaging
    assert "PACKLAB_RUNTIME_CAPABILITIES_PATH" in packaging
    assert "qt_vector_pdf" in packaging
    assert "ocp_cad" in packaging
    assert "open3d_geometry" in packaging
    assert "windows-runtime-capabilities.json" in packaging
    assert '"PACKLAB_BUILD_REVISION=$revision"' in packaging
    assert "Start-Process -FilePath $studioExe" in packaging
    assert '"--packlab-build-smoke"' in packaging
    assert "WaitForExit(120000)" in packaging
    assert "PACKLAB_BUILD_SMOKE_LOG" in packaging
    assert "PL-0350 owns native/runtime inventory" in packaging
    assert "--staging-dir $appDirectory" in packaging
    assert "--collect-toc $collectMatches[0].FullName" in packaging
    assert "compliance-validation.json" in packaging
    assert "unresolved_count -ne 0" in packaging
    assert "if-no-files-found: error" in packaging
    assert packaging.count("retention-days: 1") == 3
    assert packaging.index("Upload text-only pre-clearance evidence") < packaging.index(
        "Enforce redistribution clearance"
    )
    assert packaging.index("Revalidate exact installer input tree") < packaging.index(
        "Install pinned Inno Setup"
    )
    assert "if: steps.clearance.outputs.cleared == 'true'" in packaging
    assert "9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732" in packaging
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
