from __future__ import annotations

import ctypes
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from ctypes import wintypes
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools" / "dev" / "run_packlab_tests.ps1"
CONTRACT_PARENT = Path(tempfile.gettempdir()) / "PackLab" / "runner-contract"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


pytestmark = pytest.mark.skipif(
    os.name != "nt" or POWERSHELL is None, reason="Windows PowerShell integration"
)


def _new_contract_root() -> Path:
    CONTRACT_PARENT.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f"case-{uuid.uuid4().hex}-", dir=CONTRACT_PARENT))


def _run_wrapper(
    contract_root: Path,
    scenario: str,
    *,
    base_limit: int = 16_384,
    fixture_limit: int = 16_384,
    disposable_limit: int = 32_768,
    inject_measurement_failure: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [
        str(POWERSHELL),
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(RUNNER),
        "-ContractTestMode",
        "-ContractRoot",
        str(contract_root),
        "-ContractScenario",
        scenario,
        "-ContractPython",
        os.sys.executable,
        "-ContractMaxBaseTempBytes",
        str(base_limit),
        "-ContractMaxFixtureBytes",
        str(fixture_limit),
        "-ContractMaxDisposableBytes",
        str(disposable_limit),
    ]
    if inject_measurement_failure:
        command.append("-ContractInjectMeasurementFailure")
    return subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
        check=False,
    )


def _run_root(output: str) -> Path:
    match = re.search(r"^packlab_run_root=(.+)$", output, re.MULTILINE)
    assert match, output
    return Path(match.group(1))


def _child_pids(output: str) -> list[int]:
    match = re.search(r"^contract_child_process_ids=([0-9,]+)$", output, re.MULTILINE)
    assert match, output
    return [int(pid) for pid in match.group(1).split(",")]


def _process_exists(pid: int) -> bool:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    open_process = kernel32.OpenProcess
    open_process.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    open_process.restype = wintypes.HANDLE
    get_exit_code = kernel32.GetExitCodeProcess
    get_exit_code.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    get_exit_code.restype = wintypes.BOOL
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL
    handle = open_process(0x1000, False, pid)
    if not handle:
        return False
    try:
        exit_code = wintypes.DWORD()
        if not get_exit_code(handle, ctypes.byref(exit_code)):
            return False
        return exit_code.value == 259  # STILL_ACTIVE
    finally:
        close_handle(handle)


def test_runner_handles_quiet_and_asymmetric_stream_eof() -> None:
    for scenario, expected_output in (
        ("quiet", ""),
        ("stdout-eof", "PACKLAB_TEST_STDERR_REMAINS_OPEN"),
    ):
        root = _new_contract_root()
        try:
            result = _run_wrapper(root, scenario)
            assert result.returncode == 0, result.stdout + result.stderr
            assert expected_output in result.stdout
            assert not _run_root(result.stdout).exists()
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_runner_propagates_healthy_child_failure_code() -> None:
    root = _new_contract_root()
    try:
        result = _run_wrapper(root, "nonzero")
        assert result.returncode == 17, result.stdout + result.stderr
        assert "PACKLAB_TEST_NONZERO_CHILD" in result.stdout
        assert not _run_root(result.stdout).exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    (
        "scenario",
        "base_limit",
        "fixture_limit",
        "disposable_limit",
        "expected_code",
        "expected_message",
    ),
    [
        ("base-over", 1024, 16_384, 32_768, 42, "PYTEST_DISK_BUDGET_EXCEEDED"),
        ("fixture-over", 16_384, 1024, 32_768, 43, "TEST_FIXTURE_DISK_BUDGET_EXCEEDED"),
        ("staging-over", 16_384, 16_384, 1024, 44, "PACKLAB_DISPOSABLE_DISK_BUDGET_EXCEEDED"),
    ],
)
def test_runner_stops_owned_child_tree_for_tiny_budget(
    scenario: str,
    base_limit: int,
    fixture_limit: int,
    disposable_limit: int,
    expected_code: int,
    expected_message: str,
) -> None:
    root = _new_contract_root()
    unrelated = subprocess.Popen([os.sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        assert unrelated.poll() is None
        result = _run_wrapper(
            root,
            scenario,
            base_limit=base_limit,
            fixture_limit=fixture_limit,
            disposable_limit=disposable_limit,
        )
        assert result.returncode == expected_code, result.stdout + result.stderr
        assert expected_message in result.stdout
        assert not _run_root(result.stdout).exists()
        child_pids = _child_pids(result.stdout)
        assert len(child_pids) == 2
        for pid in child_pids:
            deadline = time.monotonic() + 3
            while _process_exists(pid) and time.monotonic() < deadline:
                time.sleep(0.05)
            assert not _process_exists(pid), f"PackLab-owned child process {pid} is still alive"
        assert unrelated.poll() is None, "the unrelated sentinel process must remain running"
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=5)
        shutil.rmtree(root, ignore_errors=True)


def test_runner_fails_closed_and_cleans_after_measurement_exception() -> None:
    root = _new_contract_root()
    try:
        result = _run_wrapper(root, "measurement-failure", inject_measurement_failure=True)
        assert result.returncode == 45, result.stdout + result.stderr
        assert "PACKLAB_DISPOSABLE_MEASUREMENT_FAILED" in result.stdout
        assert not _run_root(result.stdout).exists()
        for pid in _child_pids(result.stdout):
            deadline = time.monotonic() + 3
            while _process_exists(pid) and time.monotonic() < deadline:
                time.sleep(0.05)
            assert not _process_exists(pid), f"PackLab-owned child process {pid} is still alive"
    finally:
        shutil.rmtree(root, ignore_errors=True)
