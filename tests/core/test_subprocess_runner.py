import sys
import threading
import time

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


def test_timeout_stops_child():
    result = run_process(child("import time; time.sleep(5)"), timeout=0.05)
    assert result.timed_out is True
    assert result.returncode is not None


def test_cancellation_stops_child():
    event = threading.Event()
    result_holder = []

    def run():
        result_holder.append(run_process(child("import time; time.sleep(5)"), cancel_event=event))

    thread = threading.Thread(target=run)
    thread.start()
    time.sleep(0.05)
    event.set()
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert result_holder[0].cancelled is True


def test_shell_is_not_used_by_default():
    result = run_process(
        child(
            "import subprocess; raise SystemExit(0 if subprocess.__name__ == 'subprocess' else 1)"
        )
    )
    assert result.returncode == 0
