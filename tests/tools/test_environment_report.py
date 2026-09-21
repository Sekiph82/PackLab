import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[2] / "tools" / "environment_report.py"
SPEC = importlib.util.spec_from_file_location("environment_report", MODULE_PATH)
assert SPEC and SPEC.loader
environment_report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(environment_report)


def fake_runner(args, timeout):
    if args[0] == "powershell":
        return {
            "status": "available",
            "output": '["Intel(R) Iris(R) Xe Graphics"]',
            "detail": "Intel(R) Iris(R) Xe Graphics",
        }
    return {"status": "missing", "version": None, "detail": "not found"}


def test_report_is_structured_and_redacted():
    report = environment_report.collect_report(fake_runner)
    assert report["schema"] == "packlab.environment-report.v1"
    assert report["gpu"]["adapters"] == [{"name": "Intel(R) Iris(R) Xe Graphics"}]
    assert report["gpu"]["cuda"]["status"] == "unknown"
    assert report["privacy"] == {
        "identifiers": "omitted",
        "paths": "omitted",
        "credentials": "omitted",
    }
    assert "username" not in str(report).lower()


def test_windows_non_nvidia_adapter_is_discoverable(monkeypatch):
    monkeypatch.setattr(environment_report.platform, "system", lambda: "Windows")
    report = environment_report.collect_report(fake_runner)
    assert report["gpu"]["adapters"] == [{"name": "Intel(R) Iris(R) Xe Graphics"}]
    assert report["gpu"]["driver"]["status"] == "missing"


def test_nvidia_metadata_does_not_prove_cuda(monkeypatch):
    monkeypatch.setattr(environment_report.platform, "system", lambda: "Windows")

    def nvidia_runner(args, timeout):
        if args[0] == "powershell":
            return {"status": "available", "output": '["NVIDIA RTX Example"]'}
        if args[0] == "nvidia-smi":
            return {"status": "available", "output": "NVIDIA RTX Example, 4096"}
        return {"status": "missing", "version": None, "detail": "not found"}

    report = environment_report.collect_report(nvidia_runner)
    assert report["gpu"]["adapters"] == [{"name": "NVIDIA RTX Example"}]
    assert report["gpu"]["driver"]["status"] == "available"
    assert report["gpu"]["cuda"]["status"] == "unknown"


def test_missing_tools_are_deterministic():
    report = environment_report.collect_report(
        lambda args, timeout: {"status": "missing", "version": None, "detail": "not found"}
    )
    assert report["external_tools"]["colmap"]["status"] == "missing"
    assert report["gpu"]["adapter_probe"]["status"] in {"missing", "unsupported"}
    assert report["gpu"]["cuda"]["status"] == "unknown"


def test_command_probe_never_uses_shell():
    result = environment_report.run_command(["definitely-not-a-packlab-tool"], 0.01)
    assert result["status"] == "missing"
