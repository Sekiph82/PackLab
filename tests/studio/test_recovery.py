from __future__ import annotations

from packlab_studio.project_layout import ProjectLayout
from packlab_studio.recovery import RecoveryManager, RecoveryStatus


def test_clean_close_and_repeated_reopen_are_idempotent(tmp_path) -> None:
    layout = ProjectLayout.create(tmp_path / "project")
    recovery = RecoveryManager(layout)
    recovery.mark_start()
    assert recovery.inspect() == ()
    recovery.mark_clean_close()
    assert recovery.inspect() == ()
    assert recovery.inspect() == ()


def test_resumable_restart_invalid_and_accept_discard(tmp_path) -> None:
    layout = ProjectLayout.create(tmp_path / "project")
    recovery = RecoveryManager(layout)
    recovery.mark_start()
    resumable = layout.path("derived", "resume.bin")
    resumable.write_bytes(b"resume")
    recovery.checkpoint("job-resume", area="derived", relative_path="resume.bin", resumable=True)
    restart = layout.path("temp", "restart.part")
    restart.write_bytes(b"restart")
    recovery.checkpoint("job-restart", area="temp", relative_path="restart.part", resumable=False)
    recovery.checkpoint("job-invalid", area="derived", relative_path="missing.bin", resumable=True)
    statuses = {item.job_id: item.status for item in recovery.inspect()}
    assert statuses == {"job-resume": RecoveryStatus.RESUMABLE, "job-restart": RecoveryStatus.RESTART_REQUIRED, "job-invalid": RecoveryStatus.INVALID}
    recovery.accept("job-resume")
    recovery.discard("job-restart")
    assert not restart.exists()
    assert recovery.inspect()[0].job_id == "job-invalid"
