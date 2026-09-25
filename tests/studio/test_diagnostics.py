from __future__ import annotations

import json

from packlab_studio.diagnostics import DiagnosticsBundleService


def test_bundle_is_atomic_bounded_and_redacted(tmp_path) -> None:
    service = DiagnosticsBundleService(tmp_path, max_log_bytes=1024)
    bundle = service.create_bundle(
        logs="bearer: TOPSECRET C:\\Users\\private\\raw.packscan " + "x" * 10_000,
        build_info={"version": "0.1.0", "api_key": "SECRET"},
        active_jobs=[{"job_id": "job-1", "status": "running"}],
        structured_errors=[{"message": "C:\\Users\\private\\failure"}],
    )
    value = json.loads(bundle.path.read_text(encoding="utf-8"))
    text = bundle.path.read_text(encoding="utf-8")
    assert bundle.bytes_written == bundle.path.stat().st_size
    assert len(value["logs"].encode("utf-8")) <= 1024
    assert "TOPSECRET" not in text and "SECRET" not in text
    assert "C:\\Users" not in text
    assert not list(tmp_path.glob("*.tmp"))


def test_missing_sources_and_explicit_destination_are_safe(tmp_path) -> None:
    service = DiagnosticsBundleService(tmp_path)
    destination = tmp_path / "nested" / "report.json"
    bundle = service.create_bundle(destination, logs="", build_info=None)
    assert bundle.path == destination
    assert json.loads(destination.read_text(encoding="utf-8"))["structured_errors"] == []

