from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "windows-studio-build.yml"


def test_native_workflow_is_manual_only_and_requires_exact_owner_inputs() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    contract = json.loads(
        (ROOT / "tools/packaging/controlled_ocp_runtime_contract.json").read_text(encoding="utf-8")
    )
    assert "  push:" not in workflow
    assert "  pull_request:" not in workflow
    assert "workflow_dispatch:" in workflow
    assert "run_native_build:" in workflow
    assert "build_revision:" in workflow
    assert "inputs.run_native_build == true" in workflow
    assert "inputs.build_revision == github.sha" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "capacity-preflight:" in workflow
    assert "retained-sdk-inspection:" in workflow
    assert "inspect_retained_sdk == true" in workflow
    inspection = workflow.split("  retained-sdk-inspection:\n", 1)[1].split(
        "  capacity-preflight:\n", 1
    )[0]
    sdk_job = workflow.split("  occt-sdk:\n", 1)[1].split("  controlled-ocp-runtime:\n", 1)[0]
    assert "inputs.preflight_only == true" not in inspection
    assert "Verify complete hosted diagnostic evidence" in inspection
    assert "fmt ownership/source/import dependency gate failed:" in inspection
    assert "if: always()" in inspection
    assert "if-no-files-found: warn" in inspection
    assert 'Join-Path $generatedRoot "OCP_src_stubs_Windows/CMakeLists.txt"' in inspection
    assert (
        "uv run --locked --no-sync python -m tools.packaging.probe_fmt_dependency --prefix $nativePrefix"
        in inspection
    )
    assert "needs: [capacity-preflight, retained-sdk-inspection]" in sdk_job
    assert "inspect_retained_occt_sdk" in workflow
    assert "actions: read" in workflow
    assert "python -m tools.packaging.prepare_official_ocp_generated_sources --archive" in workflow
    assert "python -S -m tools.packaging.verify_windows_workflow_python_imports" in workflow
    assert "8 GiB free on the build volume" in workflow
    assert "two authorized runs under the" in workflow
    assert "max-run-artifact-bytes" in workflow
    assert "python -S -m tools.packaging.preflight_occt_sdk_layout" in workflow
    assert "Math]::Floor(($twoRunArtifactCap - $artifactBytes) / 2)" in workflow
    assert workflow.count("assert_actions_run_artifact_budget --max-bytes") >= 5
    assert "retention-days: 1" in workflow
    assert workflow.count("timeout-minutes: 330") == 3
    assert contract["schema_version"] == 2
    assert contract["cmake_parallel"] == 4
    assert contract["official_generated_source"]["input_modules"] == 319
    assert contract["official_generated_source"]["output_modules"] == 315
    assert contract["official_generated_source"]["pywrap_generation"] is False


def test_bootstrap_and_native_python_identities_are_separate_and_preflight_is_gated() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    contract = json.loads(
        (ROOT / "tools/packaging/controlled_ocp_runtime_contract.json").read_text(encoding="utf-8")
    )
    native_lock = (ROOT / "tools/packaging/packlab-ocp-bindings-win.lock").read_text(
        encoding="utf-8"
    )
    occt_builder = (ROOT / "tools/packaging/build_controlled_occt_sdk.py").read_text(
        encoding="utf-8"
    )
    dependency_audit = (
        ROOT / "tools/packaging/audit_controlled_occt_sdk_dependencies.py"
    ).read_text(encoding="utf-8")
    ocp_builder = (
        ROOT / "tools/packaging/build_controlled_ocp_from_generated_sources.py"
    ).read_text(encoding="utf-8")

    preflight = workflow.split("  capacity-preflight:\n", 1)[1].split("  occt-sdk:\n", 1)[0]
    sdk = workflow.split("  occt-sdk:\n", 1)[1].split("  controlled-ocp-runtime:\n", 1)[0]
    ocp = workflow.split("  controlled-ocp-runtime:\n", 1)[1].split("  build-studio:\n", 1)[0]
    inspection = workflow.split("  retained-sdk-inspection:\n", 1)[1].split(
        "  capacity-preflight:\n", 1
    )[0]
    studio = workflow.split("  build-studio:\n", 1)[1]

    assert (
        "default: false\n        type: boolean" in workflow.split("      preflight_only:\n", 1)[1]
    )
    assert 'python-version: "3.12.10"' in preflight
    assert 'python-version: "3.12.10"' in sdk
    assert 'python-version: "3.12.10"' in ocp
    assert workflow.count('python-version: "3.12.10"') == 4
    assert 'python-version: "3.12.15"' not in workflow
    assert 'python-version: "3.12"' in studio
    assert workflow.count("inputs.preflight_only != true") == 3
    assert "inputs.preflight_only != true" not in preflight
    for job in (sdk, ocp, studio):
        condition = job.split("    if: >-\n", 1)[1].split("\n    runs-on:", 1)[0]
        assert "inputs.preflight_only != true" in condition
        assert "inputs.run_native_build == true" in condition
        assert "github.ref == 'refs/heads/main'" in condition
        assert "inputs.build_revision == github.sha" in condition

    assert "Bootstrap Python: $bootstrapPython" in preflight
    assert '$bootstrapPython = Join-Path $env:pythonLocation "python.exe"' in inspection
    assert preflight.index("preflight_occt_sdk_layout") < preflight.index("Invoke-WebRequest")
    assert "sys.version_info[:3] == (3,12,10)" in preflight
    native_assertion = "sys.version_info[:3] == (3,12,15)"
    assert native_assertion in sdk and native_assertion in ocp
    assert sdk.index("Assert native OCCT build Python 3.12.15") < sdk.index(
        "Restore and authenticate the owner-approved R04 SDK checkpoint"
    )
    assert ocp.index("Assert native OCP compiler Python 3.12.15") < ocp.index(
        "build_controlled_ocp_from_generated_sources.py"
    )
    assert contract["target"]["python_version"] == "3.12.15"
    assert "version: 3.12.15" in native_lock
    assert 'sys.version.split()[0] != contract["target"]["python_version"]' in occt_builder
    assert 'sys.version.split()[0] != contract["target"]["python_version"]' in ocp_builder
    assert '"USE_OPENGL": True' in occt_builder
    assert '"USE_VTK": False' in occt_builder
    assert '"USE_OPENGL"' in occt_builder
    assert "-D{key}=" in occt_builder
    assert "Windows-x64-occt-sdk-v5-" in workflow
    assert "controlled-ocp315-v4-" in workflow
    sdk_cache = sdk.split("Restore exact OCCT SDK cache", 1)[1].split(
        "Fetch and verify locked corresponding-source archives", 1
    )[0]
    assert "hashFiles(" in sdk_cache
    assert "Windows-x64-occt-sdk-v5-" in sdk_cache
    assert ".github/workflows/windows-studio-build.yml" not in sdk_cache
    sdk_cache_contract = json.loads(
        (ROOT / "tools/packaging/windows_occt_sdk_build_contract.json").read_text(encoding="utf-8")
    )
    assert (
        "tools/packaging/windows_occt_sdk_build_contract.json"
        in sdk_cache_contract["cache_identity_files"]
    )
    assert "controlled_ocp_runtime_contract.json" not in sdk_cache_contract["cache_identity_files"]
    assert "OpenGl_Context.hxx" in dependency_audit
    assert "OpenCASCADE_LIBRARIES" in dependency_audit
    assert "windows_opengl_prerequisites" in dependency_audit
    assert 'f"-DPython_EXECUTABLE={sys.executable}"' in ocp_builder
    assert 'f"-DCMAKE_PREFIX_PATH={args.occt_sdk};{sys.prefix}"' in ocp_builder
    assert (
        ocp_builder.index("dependency_audit = audit_dependencies(")
        < ocp_builder.index('"tools.packaging.probe_fmt_dependency"')
        < ocp_builder.index("if args.prebuilt_extension:")
    )
    assert (
        "& micromamba run -n packlab-ocp-bindings python -m tools.packaging.build_controlled_occt_sdk"
        not in sdk
    )
    assert "Restore and authenticate the owner-approved R04 SDK checkpoint" in sdk
    assert "Do not start a new OCCT build from this assignment" in sdk
    assert "& micromamba run -n packlab-ocp-bindings python @builderArgs" in ocp
    assert "reuse_quarantined_ocp_run_id:" in workflow
    assert "inputs.reuse_quarantined_ocp_run_id != ''" in ocp
    assert '"38399051467"' in ocp
    assert "c9db27bf7d3e95932a0ddb512c35bfe19a63e50394da0d9978355db28842fa29" in ocp
    assert "--prebuilt-extension" in ocp_builder
    assert "REUSED_QUARANTINED_EXTENSION" in ocp_builder
    assert (
        '"uv",\n            "run",\n            "--locked",\n            "--no-sync"' in ocp_builder
    )
    assert '"tools.packaging.probe_fmt_dependency"' in ocp_builder


def test_windows_workflow_python_modules_resolve_from_checkout_root() -> None:
    from tools.packaging.verify_windows_workflow_python_imports import verify_workflow_imports

    modules = verify_workflow_imports(ROOT)
    assert set(modules) == {
        "tools.packaging.assert_actions_run_artifact_budget",
        "tools.packaging.assert_staged_qt_surface",
        "tools.packaging.audit_controlled_occt_sdk_dependencies",
        "tools.packaging.build_controlled_occt_sdk",
        "tools.packaging.build_controlled_ocp_from_generated_sources",
        "tools.packaging.build_controlled_ocp_runtime",
        "tools.packaging.controlled_ocp_runtime_bundle",
        "tools.packaging.fetch_verify_windows_native_sources",
        "tools.packaging.inspect_retained_occt_sdk",
        "tools.packaging.preflight_occt_sdk_layout",
        "tools.packaging.prepare_official_ocp_generated_sources",
        "tools.packaging.probe_fmt_dependency",
        "tools.packaging.recover_pl0350_sdk_artifacts",
        "tools.packaging.validate_controlled_occt_sdk",
        "tools.packaging.validate_controlled_ocp_manifest",
        "tools.packaging.validate_windows_native_runtime_policy",
        "tools.packaging.validate_windows_native_source_lock",
        "tools.packaging.validate_windows_occt_sdk_build_contract",
        "tools.packaging.verify_windows_workflow_python_imports",
        "tools.packaging.windows_redistribution_inventory",
    }


def test_windows_workflow_rejects_repository_script_file_path_invocations() -> None:
    from tools.packaging.verify_windows_workflow_python_imports import SCRIPT_CALL

    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert SCRIPT_CALL.findall(workflow) == []
    assert SCRIPT_CALL.findall("python tools/packaging/example.py") == ["example"]
    assert SCRIPT_CALL.findall("python.exe -S .\\tools\\packaging\\example.py") == ["example"]


def test_native_pipeline_seals_same_run_occt_and_generated_ocp_stages() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    sdk = workflow.split("  occt-sdk:\n", 1)[1].split("  controlled-ocp-runtime:\n", 1)[0]
    ocp = workflow.split("  controlled-ocp-runtime:\n", 1)[1].split("  build-studio:\n", 1)[0]
    packaging = workflow.split("  build-studio:\n", 1)[1]

    assert "build_controlled_occt_sdk.py" in sdk
    assert "validate_controlled_occt_sdk.py" in sdk
    assert "actions/cache/restore@" in sdk
    assert "actions/cache/save@" not in sdk
    assert "actions/upload-artifact@" in sdk
    assert "1 GiB stage-A artifact budget" in sdk
    assert "retention-days: 1" in sdk
    assert "actions/download-artifact@" in ocp
    assert "needs: occt-sdk" in ocp
    assert "sdk-producer-run-id" in ocp
    assert "sdk-producer-attempt" in ocp
    assert "OCP_src_stubs_Windows.zip" in ocp
    assert "prepare_official_ocp_generated_sources.py" in ocp
    assert "build_controlled_ocp_from_generated_sources.py" in ocp
    assert "--quarantine-dir" in ocp
    assert "OCP_POST_LINK_QUARANTINE_PASS" in (
        ROOT / "tools/packaging/build_controlled_ocp_from_generated_sources.py"
    ).read_text(encoding="utf-8")
    assert "post-link OCP quarantine" in ocp
    assert "python -m tools.packaging.controlled_ocp_runtime_bundle seal" in ocp
    assert "generated-source-patch-manifest.json" in ocp
    assert "python -m tools.packaging.controlled_ocp_runtime_bundle smoke" in ocp
    assert "pywrap_generation" not in ocp
    assert "1 GiB stage-B artifact budget" in ocp
    assert "restore-keys:" not in workflow
    assert "needs: controlled-ocp-runtime" in packaging
    assert "needs.controlled-ocp-runtime.outputs.bundle-artifact-name" in packaging
    assert "actions/download-artifact@" in packaging
    assert "Enforce redistribution clearance" in packaging
    assert "Build versioned unsigned installer" in packaging
    assert "100 MiB artifact budget" in packaging
    assert "1,800 MiB installer budget" in packaging
    assert "Upload cleared versioned installer" in packaging
    runtime_identity = ocp.split("Record exact OCP runtime artifact identity", 1)[1].split(
        "Save exact OCP runtime cache after size validation", 1
    )[0]
    assert (
        "$runtimeBinarySha = (Get-FileHash -LiteralPath $runtimeBinary.FullName" in runtime_identity
    )
    assert '"- OCP runtime binary SHA-256: $runtimeBinarySha"' in runtime_identity
    assert "Get-FileHash -LiteralPath (Get-ChildItem" not in runtime_identity


def test_packaged_runtime_smoke_covers_cad_step_dxf_pdf_and_open3d() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    smoke = (ROOT / "apps/windows-studio/src/packlab_studio/build_smoke.py").read_text(
        encoding="utf-8"
    )
    package_builder = (
        ROOT / "tools/packaging/build_controlled_ocp_from_generated_sources.py"
    ).read_text(encoding="utf-8")
    bundle = (ROOT / "tools/packaging/controlled_ocp_runtime_bundle.py").read_text(encoding="utf-8")
    assert '"step_io", "dxf_export"' in workflow
    assert "export_design_model_step" in smoke
    assert "vectors.dxf_bytes" in smoke
    assert '"round_trip_status": "PASS"' in smoke
    assert '"format": "R2000 ASCII"' in smoke
    assert "REQUIRED_PACKLAB_MODULES" in package_builder
    assert '"pywrap_generation_invoked": False' in package_builder
    assert '"phase": "ocp_native_compile_link"' in package_builder
    assert "generated-source-patch-manifest.json" in bundle
    assert "STEP read/transfer failed" in bundle
    assert "OCP.IVtk" not in bundle
    assert "secrets." not in workflow


def test_packaged_studio_smoke_diagnostics_are_retained_on_failure() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    packaging = workflow.split("  build-studio:\n", 1)[1]

    assert '$smokeLog = Join-Path $env:RUNNER_TEMP "packlab-studio-smoke.log"' in packaging
    assert '"PACKLAB_BUILD_SMOKE_LOG=$smokeLog" >> $env:GITHUB_ENV' in packaging
    assert "- Sanitized diagnostic: $smokeDiagnostic" in packaging
    assert "Upload packaged Studio smoke diagnostics\n        if: always()" in packaging
    diagnostic_upload = packaging.split("Upload packaged Studio smoke diagnostics", 1)[1].split(
        "Validate bidirectional controlled OCP manifest", 1
    )[0]
    assert "${{ runner.temp }}/packlab-studio-smoke.log" in diagnostic_upload
    assert "windows-runtime-capabilities.json" in diagnostic_upload
    assert "qt-staged-surface.json" in diagnostic_upload
