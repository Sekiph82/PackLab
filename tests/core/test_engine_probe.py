from __future__ import annotations

from pathlib import Path

from packlab_core.engine_probe import (
    EngineProbeStatus,
    EngineVersion,
    parse_colmap_version,
    probe_colmap,
)


def _runner(output: str, returncode: int = 0):
    def run(_path: Path) -> tuple[int, str, str]:
        return returncode, output, ""

    return run


def test_colmap_parser_accepts_the_selected_banner() -> None:
    assert parse_colmap_version("COLMAP 3.12.6 -- Structure-from-Motion and Multi-View Stereo") == EngineVersion(3, 12, 6)


def test_probe_distinguishes_missing_invalid_unsupported_and_valid(tmp_path) -> None:
    missing = probe_colmap(tmp_path / "missing.exe", runner=_runner(""))
    assert missing.status is EngineProbeStatus.MISSING
    assert missing.configured is True

    executable = tmp_path / "colmap.exe"
    executable.write_bytes(b"fixture")
    invalid = probe_colmap(executable, runner=_runner("COLMAP unavailable"))
    assert invalid.status is EngineProbeStatus.INVALID

    unsupported = probe_colmap(executable, runner=_runner("COLMAP 4.0.0"))
    assert unsupported.status is EngineProbeStatus.UNSUPPORTED
    assert unsupported.version == EngineVersion(4, 0, 0)

    valid = probe_colmap(executable, runner=_runner("COLMAP 3.12.6"))
    assert valid.status is EngineProbeStatus.VALID
    assert valid.version == EngineVersion(3, 12, 6)


def test_probe_reports_unexecutable_runner_failure_without_writing(tmp_path) -> None:
    executable = tmp_path / "colmap.exe"
    executable.write_bytes(b"fixture")
    before = executable.read_bytes()
    result = probe_colmap(executable, runner=_runner("", returncode=17))
    assert result.status is EngineProbeStatus.UNEXECUTABLE
    assert executable.read_bytes() == before
