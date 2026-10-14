from __future__ import annotations

from packlab_core.cad_adapter import (
    CAD_RUNTIME_VERSION_STATUS_OBSERVED,
    CadCapability,
    CadCapabilityStatus,
    CadRuntimeDiagnostics,
    CadRuntimeStatus,
)
from packlab_studio import app as studio_app
from packlab_studio import build_smoke


def test_cad_probe_failure_code_reports_failed_capabilities_without_paths() -> None:
    diagnostics = CadRuntimeDiagnostics(
        status=CadRuntimeStatus.PARTIAL,
        binding_package="cadquery-ocp-novtk",
        binding_version="7.9.3.1.1",
        binding_version_status=CAD_RUNTIME_VERSION_STATUS_OBSERVED,
        kernel_version=None,
        kernel_version_status="UNAVAILABLE",
        platform_system="Windows",
        platform_machine="AMD64",
        capabilities=(
            CadCapability("brep_construction", CadCapabilityStatus.AVAILABLE),
            CadCapability("topology_validation", CadCapabilityStatus.ERROR, "AttributeError"),
        ),
        error_code="kernel_detail",
    )

    assert build_smoke._cad_probe_failure_code(diagnostics) == (
        "ocp_cad_probe_not_ready:kernel=kernel_detail;"
        "capabilities=topology_validation:ERROR:AttributeError"
    )


def test_cad_version_failure_code_reports_safe_observation_statuses() -> None:
    diagnostics = CadRuntimeDiagnostics(
        status=CadRuntimeStatus.READY,
        binding_package="cadquery-ocp-novtk",
        binding_version="7.9.3.1.1",
        binding_version_status=CAD_RUNTIME_VERSION_STATUS_OBSERVED,
        kernel_version=None,
        kernel_version_status="UNAVAILABLE",
        platform_system="Windows",
        platform_machine="AMD64",
        capabilities=(),
        error_code="kernel_binary_identity_unavailable",
    )

    assert build_smoke._cad_version_failure_code(diagnostics) == (
        "ocp_cad_software_version_unobserved:binding=OBSERVED;"
        "kernel=UNAVAILABLE;detail=kernel_binary_identity_unavailable"
    )


def test_open3d_probe_failure_code_classifies_path_free_import_detail() -> None:
    assert (
        build_smoke._open3d_probe_failure_code(
            "UNAVAILABLE", "Open3D import unavailable (open3d.cpu.pybind)"
        )
        == "open3d_probe_failed:status=UNAVAILABLE;detail=module_unavailable_open3d_cpu_pybind"
    )
    assert (
        build_smoke._open3d_probe_failure_code(
            "UNKNOWN", "Open3D import failed (OSError;winerror=126)"
        )
        == "open3d_probe_failed:status=UNKNOWN;detail=import_failed_OSError_winerror_126"
    )
    assert (
        build_smoke._open3d_probe_failure_code(
            "UNKNOWN",
            "Open3D import failed (ImportError;module=open3d.pybind;reason=dll_module_missing)",
        )
        == "open3d_probe_failed:status=UNKNOWN;"
        "detail=import_failed_ImportError_module_open3d_pybind_dll_module_missing"
    )
    assert (
        build_smoke._open3d_probe_failure_code(
            "UNKNOWN",
            "Open3D import failed (ImportError;module=open3d.pybind;reason=symbol_missing)",
        )
        == "open3d_probe_failed:status=UNKNOWN;"
        "detail=import_failed_ImportError_module_open3d_pybind_symbol_missing"
    )
    assert (
        build_smoke._open3d_probe_failure_code(
            "UNKNOWN",
            "Open3D import failed (ImportError;reason=import_error;"
            "trace=open3d._build_config.failing_import)",
        )
        == "open3d_probe_failed:status=UNKNOWN;"
        "detail=import_failed_ImportError_import_error_"
        "trace_open3d__build_config_failing_import"
    )
    assert (
        build_smoke._open3d_probe_failure_code(
            "UNKNOWN", "Open3D import unavailable (C:\\private\\cache)"
        )
        == "open3d_probe_failed:status=UNKNOWN;detail=module_unavailable"
    )


def test_app_build_smoke_constructs_and_closes_the_real_window(monkeypatch) -> None:
    events: list[str] = []
    created_argv: list[str] = []

    class FakeApplication:
        def processEvents(self) -> None:
            events.append("process")

        def quit(self) -> None:
            events.append("quit")

    class FakeWindow:
        def show(self) -> None:
            events.append("show")

        def close(self) -> bool:
            events.append("close")
            return True

    def create_application(argv: list[str] | None) -> FakeApplication:
        created_argv.extend(argv or [])
        return FakeApplication()

    monkeypatch.setattr(studio_app, "create_application", create_application)
    monkeypatch.setattr(studio_app, "StudioMainWindow", FakeWindow)
    monkeypatch.setattr(build_smoke, "run_frozen_capability_smoke", lambda: {"status": "PASS"})

    assert (
        studio_app.run(["PackLabStudio", studio_app.BUILD_SMOKE_ARGUMENT])
        == studio_app.EXIT_SUCCESS
    )
    assert created_argv == ["PackLabStudio"]
    assert events == ["show", "process", "close", "process", "quit"]


def test_app_build_smoke_records_path_free_failure(monkeypatch, tmp_path) -> None:
    log_path = tmp_path / "studio-smoke.log"
    monkeypatch.setenv("PACKLAB_BUILD_SMOKE_LOG", str(log_path))
    monkeypatch.setattr(studio_app, "create_application", lambda _argv: object())

    def fail_to_create_window() -> None:
        raise RuntimeError("packaged startup detail at C:\\Users\\private\\cache")

    monkeypatch.setattr(studio_app, "StudioMainWindow", fail_to_create_window)

    assert (
        studio_app.run(["PackLabStudio", studio_app.BUILD_SMOKE_ARGUMENT])
        == studio_app.EXIT_STARTUP_FAILURE
    )
    assert log_path.read_text(encoding="utf-8") == (
        "PackLab frozen capability smoke failed (RuntimeError): "
        "diagnostic omitted because it contains an absolute path\n"
    )
    assert str(tmp_path) not in log_path.read_text(encoding="utf-8")
