"""Safe, cancellable subprocess execution for future PackLab adapters."""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

LineCallback = Callable[[str], None]


@dataclass(frozen=True)
class ProcessResult:
    args: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool
    cancelled: bool
    error: str | None = None


def _stop_process(process: subprocess.Popen[str]) -> str | None:
    """Stop a process and its group where the host supports it."""

    cleanup_error: str | None = None
    if os.name == "nt" and process.pid:
        # The PID is the runner-owned root. /T limits taskkill to that process tree.
        try:
            completed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                check=False,
                shell=False,
                timeout=1.0,
            )
            if completed.returncode != 0:
                cleanup_error = f"taskkill failed with exit code {completed.returncode}"
        except subprocess.TimeoutExpired:
            cleanup_error = "taskkill timed out after 1.0 seconds"
        except OSError as exc:
            cleanup_error = f"taskkill could not start: {type(exc).__name__}"
        if cleanup_error is not None:
            process.terminate()
    elif os.name != "nt" and process.pid:
        kill_group = getattr(os, "killpg", None)
        try:
            if kill_group is not None:
                kill_group(process.pid, signal.SIGTERM)
            else:
                process.terminate()
        except ProcessLookupError:
            return None
    elif os.name == "nt":
        process.terminate()
    try:
        process.wait(timeout=1.0)
        return cleanup_error
    except subprocess.TimeoutExpired:
        pass
    process.kill()
    process.wait(timeout=1.0)
    return cleanup_error


def run_process(
    args: Sequence[str],
    *,
    timeout: float | None = None,
    cancel_event: threading.Event | None = None,
    on_stdout: LineCallback | None = None,
    on_stderr: LineCallback | None = None,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> ProcessResult:
    """Run one command with bounded ownership and no shell-string interpretation."""

    command = tuple(args)
    if not command or any(not isinstance(item, str) or not item for item in command):
        raise ValueError("args must be a non-empty sequence of non-empty strings")
    if os.name == "nt":
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            env=None if env is None else dict(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    else:
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            env=None if env is None else dict(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            start_new_session=True,
        )
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    def drain(stream, target: list[str], callback: LineCallback | None) -> None:
        for line in iter(stream.readline, ""):
            target.append(line)
            if callback:
                callback(line.rstrip("\r\n"))
        stream.close()

    stdout_thread = threading.Thread(
        target=drain, args=(process.stdout, stdout_lines, on_stdout), daemon=True
    )
    stderr_thread = threading.Thread(
        target=drain, args=(process.stderr, stderr_lines, on_stderr), daemon=True
    )
    stdout_thread.start()
    stderr_thread.start()
    started = time.monotonic()
    timed_out = False
    cancelled = False
    cleanup_error: str | None = None
    while process.poll() is None:
        if cancel_event and cancel_event.is_set():
            cancelled = True
            cleanup_error = _stop_process(process)
            break
        if timeout is not None and time.monotonic() - started >= timeout:
            timed_out = True
            cleanup_error = _stop_process(process)
            break
        time.sleep(0.01)
    returncode = process.wait(timeout=1.0)
    stdout_thread.join(timeout=1.0)
    stderr_thread.join(timeout=1.0)
    return ProcessResult(
        command,
        returncode,
        "".join(stdout_lines),
        "".join(stderr_lines),
        timed_out,
        cancelled,
        cleanup_error,
    )
