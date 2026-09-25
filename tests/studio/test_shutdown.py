from __future__ import annotations

from PySide6.QtCore import QEventLoop, QTimer

from packlab_studio.app import create_application
from packlab_studio.jobs import JobManager, JobState
from packlab_studio.shutdown import ShutdownCoordinator, ShutdownState


def _wait(app, coordinator: ShutdownCoordinator, timeout: int = 500) -> object:
    result: list[object] = []
    coordinator.finished.connect(result.append)
    loop = QEventLoop()
    coordinator.finished.connect(loop.quit)
    QTimer.singleShot(timeout, loop.quit)
    loop.exec()
    app.processEvents()
    assert result
    return result[-1]


def test_idle_close_is_immediate(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    create_application(["packlab-shutdown-idle"])
    manager = JobManager()
    coordinator = ShutdownCoordinator(manager)
    result = coordinator.begin()
    assert result is not None and result.state is ShutdownState.COMPLETED


def test_active_jobs_cancel_without_blocking_and_multiple_hooks(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-shutdown-active"])
    manager = JobManager()
    first = manager.create("one", "owned", job_id="one")
    second = manager.create("two", "owned", job_id="two")
    manager.start(first.job_id)
    manager.start(second.job_id)
    manager.register_cancel_hook(first.job_id, lambda: True)
    manager.register_cancel_hook(second.job_id, lambda: True)
    coordinator = ShutdownCoordinator(manager)
    coordinator.begin()
    published = _wait(app, coordinator)
    assert published.state is ShutdownState.COMPLETED
    assert manager.active_jobs() == ()


def test_cleanup_failure_is_not_reported_as_success(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-shutdown-failure"])
    manager = JobManager()
    job = manager.create("broken", "owned", job_id="broken")
    manager.start(job.job_id)
    manager.register_cancel_hook(job.job_id, lambda: (_ for _ in ()).throw(RuntimeError("cleanup denied")))
    coordinator = ShutdownCoordinator(manager)
    coordinator.begin()
    result = _wait(app, coordinator)
    assert result.state is ShutdownState.FAILED
    assert "cleanup denied" in result.errors[0]


def test_bounded_timeout_and_non_cancellable_job(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-shutdown-timeout"])
    manager = JobManager()
    job = manager.create("external", "owned", cancellable=False, job_id="external")
    manager.start(job.job_id)
    coordinator = ShutdownCoordinator(manager, timeout_seconds=0.05, poll_ms=5)
    coordinator.begin()
    result = _wait(app, coordinator, timeout=500)
    assert result.state is ShutdownState.TIMED_OUT
    assert result.errors == (job.job_id,)
    assert manager.get(job.job_id).state is JobState.RUNNING
