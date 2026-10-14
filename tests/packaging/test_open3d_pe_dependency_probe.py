from pathlib import Path

from tools.packaging.open3d_pe_dependency_probe import _OPTIONAL_EXCLUDED_DLLS, _resolution
from tools.packaging.windows_native_runtime_policy import is_windows_runtime_dll


def test_open3d_dependency_resolution_prioritizes_staged_and_system_runtime(tmp_path: Path):
    system = tmp_path / "System32"
    system.mkdir()
    (system / "Open3D.dll").write_bytes(b"system")
    (system / "user32.dll").write_bytes(b"system")
    (system / "vcomp140.dll").write_bytes(b"runtime")

    assert _resolution("Open3D.dll", {"open3d.dll"}, ()) == "STAGED"
    assert _resolution("user32.dll", set(), (system,)) == "HOST_SYSTEM_OR_PATH"
    assert _resolution("vcomp140.dll", set(), ()) == "MICROSOFT_SIGNED_PREREQUISITE"
    assert _resolution("api-ms-win-core.dll", set(), ()) == "WINDOWS_API_SET"
    assert _resolution("missing_dependency.dll", set(), ()) == "UNRESOLVED"
    assert is_windows_runtime_dll("vcomp140.dll")
    assert _OPTIONAL_EXCLUDED_DLLS == {"open3d_torch_ops.dll"}


def test_open3d_dependency_probe_emits_only_path_free_failure_codes(tmp_path: Path):
    from tools.packaging.open3d_pe_dependency_probe import inspect_open3d_imports

    report = inspect_open3d_imports(tmp_path)

    assert report == {
        "schema_version": 1,
        "status": "FAIL",
        "error_code": "open3d_directory_missing",
    }
