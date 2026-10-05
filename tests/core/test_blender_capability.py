from __future__ import annotations

import json
import os
import subprocess

import pytest

from packlab_core.blender_capability import (
    BLENDER_SUPPORTED_MAJOR,
    BlenderCapabilityStatus,
    discover_blender,
)


def _output(
    version: str = "5.2.2 LTS",
    *,
    build_hash: str = "abc1234",
    build_branch: str = "blender-v5.2-release",
    build_date: str = "2026-09-15",
) -> str:
    facts = {
        "version": version,
        "build_hash": build_hash,
        "build_branch": build_branch,
        "build_date": build_date,
    }
    return "startup text\nPACKLAB_BLENDER_BUILD:" + json.dumps(facts, sort_keys=True)


def _runner(output: str = _output()):
    calls: list[tuple[list[str], dict[str, object]]] = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, stdout=output, stderr="")

    return calls, run


def _binary(path, *, executable: bool = True) -> None:
    path.write_bytes(b"fixture; subprocess is injected")
    if os.name != "nt":
        path.chmod(0o755 if executable else 0o644)


def test_configured_executable_headless_probe_captures_build_facts_safely(tmp_path) -> None:
    executable = tmp_path / "Blender with spaces.exe"
    _binary(executable)
    calls, run = _runner()

    result = discover_blender(executable, runner=run, which=lambda _: None, system="win32")

    assert result.status is BlenderCapabilityStatus.READY
    assert result.version == "5.2.2 LTS"
    assert result.build_hash == "abc1234"
    assert result.build_branch == "blender-v5.2-release"
    assert result.build_date == "2026-09-15"
    assert result.discovery_source == "configured"
    assert calls[0][0] == [
        str(executable),
        "--background",
        "--factory-startup",
        "--disable-autoexec",
        "--python-expr",
        calls[0][0][-1],
    ]
    assert "import bpy" in calls[0][0][-1]
    assert calls[0][1]["shell"] is False
    assert calls[0][1]["timeout"] == 20.0
    assert calls[0][1]["stdin"] == subprocess.DEVNULL
    assert str(tmp_path) not in json.dumps(result.as_dict())
    assert result.as_dict()["detail"] == "headless_probe_passed"


def test_missing_configured_path_is_unavailable_without_path_leakage(tmp_path) -> None:
    missing = tmp_path / "private folder" / "blender.exe"
    result = discover_blender(missing, runner=lambda *_a, **_k: pytest.fail("must not launch"))

    assert result.status is BlenderCapabilityStatus.UNAVAILABLE
    assert result.detail == "configured_executable_not_found"
    assert str(tmp_path) not in json.dumps(result.as_dict())


def test_non_executable_and_wrong_binary_are_incompatible(tmp_path) -> None:
    non_executable = tmp_path / "blender.txt"
    _binary(non_executable, executable=False)
    result = discover_blender(
        non_executable,
        runner=lambda *_a, **_k: pytest.fail("non-executable must not launch"),
        system="win32",
    )
    assert result.status is BlenderCapabilityStatus.INCOMPATIBLE
    assert result.detail == "executable_not_runnable"

    wrong_binary = tmp_path / "wrong-tool.exe"
    _binary(wrong_binary)
    calls, run = _runner("not Blender output")
    wrong = discover_blender(wrong_binary, runner=run, system="win32")
    assert calls
    assert wrong.status is BlenderCapabilityStatus.INCOMPATIBLE
    assert wrong.detail == "headless_version_output_invalid"


def test_probe_timeout_and_unsupported_version_are_incompatible(tmp_path) -> None:
    executable = tmp_path / "blender.exe"
    _binary(executable)

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("blender", 20)

    timed_out = discover_blender(executable, runner=timeout, system="win32")
    assert timed_out.status is BlenderCapabilityStatus.INCOMPATIBLE
    assert timed_out.detail == "headless_probe_timed_out"

    calls, run = _runner(_output("4.2.3 LTS"))
    unsupported = discover_blender(executable, runner=run, system="win32")
    assert calls
    assert unsupported.status is BlenderCapabilityStatus.INCOMPATIBLE
    assert unsupported.version == "4.2.3 LTS"
    assert unsupported.detail == "supported_major_policy_mismatch"
    assert BLENDER_SUPPORTED_MAJOR == 5


def test_auto_discovery_checks_path_then_fixed_platform_location(tmp_path) -> None:
    program_files = tmp_path / "Program Files"
    executable = program_files / "Blender Foundation" / "Blender 5.2" / "blender.exe"
    executable.parent.mkdir(parents=True)
    _binary(executable)
    calls, run = _runner()

    found = discover_blender(
        which=lambda _: None,
        runner=run,
        system="win32",
        environ={"ProgramFiles": str(program_files)},
    )

    assert found.status is BlenderCapabilityStatus.READY
    assert found.discovery_source == "platform-standard"
    assert calls[0][0][0] == str(executable)
    assert str(tmp_path) not in json.dumps(found.as_dict())


def test_path_discovery_is_used_when_available(tmp_path) -> None:
    executable = tmp_path / "bin" / "blender"
    executable.parent.mkdir()
    _binary(executable)
    calls, run = _runner()
    found = discover_blender(
        which=lambda name: str(executable) if name == "blender" else None,
        runner=run,
        system="linux",
    )

    assert found.status is BlenderCapabilityStatus.READY
    assert found.discovery_source == "PATH"
    assert calls[0][0][0] == str(executable)


@pytest.mark.parametrize("output", ["Blender development build", _output("not-a-version")])
def test_unparseable_version_is_incompatible(tmp_path, output: str) -> None:
    executable = tmp_path / "blender.exe"
    _binary(executable)
    _, run = _runner(output)

    result = discover_blender(executable, runner=run, system="win32")

    assert result.status is BlenderCapabilityStatus.INCOMPATIBLE
    assert result.detail == "headless_version_output_invalid"


def test_invalid_probe_configuration_is_rejected(tmp_path) -> None:
    executable = tmp_path / "blender.exe"
    _binary(executable)
    with pytest.raises(ValueError, match="timeout_invalid"):
        discover_blender(executable, timeout_seconds=True)


def test_real_blender_headless_build_probe_when_available() -> None:
    result = discover_blender()
    if result.status is BlenderCapabilityStatus.UNAVAILABLE:
        pytest.skip("Blender is not installed on this machine")
    if result.status is BlenderCapabilityStatus.INCOMPATIBLE and (
        result.detail == "supported_major_policy_mismatch"
    ):
        pytest.skip("Installed Blender is outside this task's supported major policy")

    assert result.status is BlenderCapabilityStatus.READY
    assert result.version is not None
    assert result.build_hash
    assert result.build_branch
    assert result.build_date
