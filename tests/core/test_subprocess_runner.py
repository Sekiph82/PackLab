import os
import sys
import threading
import time
from pathlib import Path

from packlab_core.subprocess_runner import run_process


def child(*code: str):
    return [sys.executable, "-c", *code]


def test_success_streams_stdout_and_stderr():
    stdout, stderr = [], []
    result = run_process(
        child("import sys; print('out'); print('err', file=sys.stderr)"),
        on_stdout=stdout.append,
        on_stderr=stderr.append,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "out"
    assert result.stderr.strip() == "err"
    assert stdout == ["out"]
    assert stderr == ["err"]


def test_nonzero_exit_is_structured():
    result = run_process(child("raise SystemExit(7)"))
    assert result.returncode == 7
    assert result.timed_out is False
    assert result.cancelled is False


def _parent_with_child(marker: Path):
    return child(
        "import os, pathlib, subprocess, sys, time; "
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
        "pathlib.Path(sys.argv[1]).write_text(f'{os.getpid()} {child.pid}', encoding='ascii'); "
        "time.sleep(30)",
        str(marker),
    )


def _read_pids(marker: Path) -> tuple[int, int]:
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        if marker.exists():
            values = marker.read_text(encoding="ascii").split()
            if len(values) == 2:
                return int(values[0]), int(values[1])
        time.sleep(0.01)
    raise AssertionError("parent did not record both process IDs")


def _assert_processes_gone(pids: tuple[int, int]):
    def is_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        if not any(is_alive(pid) for pid in pids):
            return
        time.sleep(0.02)
    raise AssertionError(f"runner-owned processes remain alive: {pids}")


def test_timeout_stops_parent_and_spawned_child(tmp_path):
    marker = tmp_path / "timeout-pids.txt"
    result_holder = []

    def run():
        result_holder.append(run_process(_parent_with_child(marker), timeout=0.2))

    thread = threading.Thread(target=run)
    thread.start()
    pids = _read_pids(marker)
    thread.join(timeout=3)
    assert not thread.is_alive()
    result = result_holder[0]
    assert result.timed_out is True
    assert result.returncode is not None
    _assert_processes_gone(pids)


def test_cancellation_stops_parent_and_spawned_child(tmp_path):
    marker = tmp_path / "cancel-pids.txt"
    event = threading.Event()
    result_holder = []

    def run():
        result_holder.append(run_process(_parent_with_child(marker), cancel_event=event))

    thread = threading.Thread(target=run)
    thread.start()
    pids = _read_pids(marker)
    event.set()
    thread.join(timeout=3)
    assert not thread.is_alive()
    assert result_holder[0].cancelled is True
    _assert_processes_gone(pids)


def test_shell_is_not_used_by_default():
    result = run_process(
        child(
            "import subprocess; raise SystemExit(0 if subprocess.__name__ == 'subprocess' else 1)"
        )
    )
    assert result.returncode == 0
