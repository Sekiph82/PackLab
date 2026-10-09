from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def _spawn_sleeper() -> int:
    command = [sys.executable, "-c", "import time; time.sleep(60)"]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    child = subprocess.Popen(command, creationflags=flags)
    return child.pid


def _write_payload(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def main() -> int:
    scenario, base_temp, staging_root, pid_record, *flags = sys.argv[1:]
    base_path = Path(base_temp)
    staging_path = Path(staging_root)
    record_path = Path(pid_record)
    inject_measurement_failure = "--inject-measurement-failure" in flags

    if scenario == "quiet":
        time.sleep(0.3)
        return 0
    if scenario == "stdout-eof":
        print("PACKLAB_TEST_STDOUT_BEFORE_EOF", flush=True)
        os.close(sys.stdout.fileno())
        sys.stdout = None
        print("PACKLAB_TEST_STDERR_REMAINS_OPEN", file=sys.stderr, flush=True)
        time.sleep(0.3)
        return 0
    if scenario == "nonzero":
        print("PACKLAB_TEST_NONZERO_CHILD", flush=True)
        return 17

    child_pid = _spawn_sleeper()
    record_path.write_text(f"{os.getpid()}\n{child_pid}\n", encoding="ascii")

    if scenario == "base-over":
        _write_payload(base_path / "pytest-0" / "test-base-budget" / "payload.bin", 4096)
    elif scenario == "fixture-over":
        _write_payload(base_path / "pytest-0" / "test-fixture-budget" / "payload.bin", 4096)
    elif scenario == "staging-over":
        _write_payload(staging_path / "concurrent-build" / "payload.bin", 4096)
    elif scenario == "measurement-failure" and inject_measurement_failure:
        (record_path.parent / "inject-measurement-failure").write_text(
            "fail closed", encoding="ascii"
        )
    else:
        return 18

    print("PACKLAB_TEST_CHILD_WAITING", flush=True)
    time.sleep(60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
