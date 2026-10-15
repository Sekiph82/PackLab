from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/pl0351-clean-windows-installer-smoke.yml"


def test_pl0351_uses_exact_private_installer_in_separate_pinned_windows_job() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "runs-on: windows-2022" in workflow
    assert "if: github.ref == 'refs/heads/main'" in workflow
    assert "permissions:\n  actions: read\n  contents: read" in workflow
    assert "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c" in workflow
    assert "38649528145" in workflow
    assert "11935390977" in workflow
    assert "3e9762e4d3faf6d0363f9714bfbdcb0d0b2d9dc9e73769ebfaac757c9af23e15" in workflow
    assert "3e7c13c18674fbe0a4de843a2ac329055850d07901a7e33fac8a3dc742d92da6" in workflow
    assert "452fe8934b0d56011af8c117555dd059d5c63462" in workflow
    assert "38649528145" in workflow and "artifact.workflow_run.head_sha" in workflow
    assert "actions: read" in workflow
    assert "workflow_dispatch" in workflow and "pull_request:" not in workflow
    assert "run_native_build" not in workflow
    assert "build_controlled_ocp" not in workflow


def test_pl0351_smokes_installed_app_under_sanitized_environment_and_always_uninstalls() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for fragment in (
        "PackLabStudio.exe",
        "-Filter 'QtCore.pyd'",
        "-Filter 'Qt6Core.dll'",
        "QT_QPA_PLATFORM = 'offscreen'",
        "PYTHONPATH",
        "PYTHONHOME",
        "QT_PLUGIN_PATH",
        "QML2_IMPORT_PATH",
        "PYSIDE_DESIGNER_PLUGINS",
        "--packlab-build-smoke",
        "qt_studio_gui",
        "qt_vector_pdf",
        "ocp_cad",
        "step_io",
        "dxf_export",
        "open3d_geometry",
        "Open3D=$($manifest.capability_groups.open3d_geometry.observed_version)",
        "network -ne 'NONE'",
        "if: always()",
        "unins*.exe",
        "PL0351_FINAL_ACCEPTANCE_GATE_FAILED",
        "PL0351_MICROSOFT_VC_X64_PREREQUISITE_NOT_SATISFIED",
        "producerEvidence.installed_executable_sha256",
        "PL0351_INSTALLED_EXECUTABLE_PROVENANCE_MISMATCH",
        "Get-AuthenticodeSignature",
        "THIRD_PARTY_NOTICES.txt",
        "RELINKING_AND_SOURCE_GUIDE.txt",
        "source-delivery-manifest.json",
        "OPEN3D-THIRD-PARTY-LICENSES.txt",
        "INSTALLED_CORRESPONDING_SOURCE_INCOMPLETE",
        "diagnostic_omitted_path_detected",
        "no_path_free_app_diagnostic",
        "$expectedRevision = $env:PACKLAB_EXPECTED_SOURCE_REVISION",
        "$expectedStudioVersion = $env:PACKLAB_STUDIO_VERSION",
        "$env:PACKLAB_BUILD_REVISION = $expectedRevision",
        "$env:PACKLAB_STUDIO_VERSION = $expectedStudioVersion",
        "$manifest.PACKLAB_BUILD_REVISION -ne $expectedRevision",
        "$manifest.studio_version -ne $expectedStudioVersion",
        "automatic_download=none",
    ):
        assert fragment in workflow
