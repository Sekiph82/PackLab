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
    assert statuses == {
        "job-resume": RecoveryStatus.RESUMABLE,
        "job-restart": RecoveryStatus.RESTART_REQUIRED,
        "job-invalid": RecoveryStatus.INVALID,
    }
    recovery.accept("job-resume")
    recovery.discard("job-restart")
    assert not restart.exists()
    assert recovery.inspect()[0].job_id == "job-invalid"


def test_reconstruction_checkpoint_digest_mismatch_is_not_resumable(tmp_path) -> None:
    layout = ProjectLayout.create(tmp_path / "project")
    recovery = RecoveryManager(layout)
    recovery.mark_start()
    checkpoint = layout.path("derived", "reconstruction/sparse.bin")
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"validated sparse checkpoint")
    recovery.checkpoint(
        "reconstruction-1",
        area="derived",
        relative_path="reconstruction/sparse.bin",
        resumable=True,
    )
    assert recovery.inspect()[0].status is RecoveryStatus.RESUMABLE

    checkpoint.write_bytes(b"changed after checkpoint")
    item = recovery.inspect()[0]
    assert item.job_id == "reconstruction-1"
    assert item.status is RecoveryStatus.INVALID


def test_unclean_session_checkpoints_survive_restart_until_resolved(tmp_path) -> None:
    layout = ProjectLayout.create(tmp_path / "project")
    first = RecoveryManager(layout)
    first.mark_start()
    draft = layout.path("temp", "draft.json")
    draft.write_bytes(b"{}")
    first.checkpoint("draft", area="temp", relative_path="draft.json", resumable=True)
    # Crash: no mark_clean_close. The next session starts and still sees the item.
    second = RecoveryManager(layout)
    second.mark_start()
    assert [item.job_id for item in second.inspect()] == ["draft"]
    assert second.discard("draft") is not None and not draft.exists()
    second.mark_clean_close()
    third = RecoveryManager(layout)
    third.mark_start()
    assert third.inspect() == ()
