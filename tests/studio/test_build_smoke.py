from __future__ import annotations

from packlab_studio import app as studio_app


def test_app_build_smoke_constructs_and_closes_the_real_window(monkeypatch) -> None:
    events: list[str] = []
    created_argv: list[str] = []

    class FakeApplication:
        def processEvents(self) -> None:
            events.append("process")

        def quit(self) -> None:
            events.append("quit")

    class FakeWindow:
        def show(self) -> None:
            events.append("show")

        def close(self) -> bool:
            events.append("close")
            return True

    def create_application(argv: list[str] | None) -> FakeApplication:
        created_argv.extend(argv or [])
        return FakeApplication()

    monkeypatch.setattr(studio_app, "create_application", create_application)
    monkeypatch.setattr(studio_app, "StudioMainWindow", FakeWindow)

    assert (
        studio_app.run(["PackLabStudio", studio_app.BUILD_SMOKE_ARGUMENT])
        == studio_app.EXIT_SUCCESS
    )
    assert created_argv == ["PackLabStudio"]
    assert events == ["show", "process", "close", "process", "quit"]


def test_app_build_smoke_records_startup_exception(monkeypatch, tmp_path) -> None:
    log_path = tmp_path / "studio-smoke.log"
    monkeypatch.setenv("PACKLAB_BUILD_SMOKE_LOG", str(log_path))
    monkeypatch.setattr(studio_app, "create_application", lambda _argv: object())

    def fail_to_create_window() -> None:
        raise RuntimeError("packaged startup detail")

    monkeypatch.setattr(studio_app, "StudioMainWindow", fail_to_create_window)

    assert (
        studio_app.run(["PackLabStudio", studio_app.BUILD_SMOKE_ARGUMENT])
        == studio_app.EXIT_STARTUP_FAILURE
    )
    assert "RuntimeError: packaged startup detail" in log_path.read_text(encoding="utf-8")
