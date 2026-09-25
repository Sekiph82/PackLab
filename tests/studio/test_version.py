from __future__ import annotations

import json

from packlab_studio.version import ManifestStatus, version_report


def test_version_report_without_network_or_manifest(tmp_path) -> None:
    report = version_report(tmp_path / "missing.json")
    assert report.status is ManifestStatus.NO_MANIFEST
    assert report.current.packscan_schema == "1.0.0"
    assert "C:\\" not in report.current.build_revision


def test_local_manifest_comparison_and_malformed_states(tmp_path) -> None:
    path = tmp_path / "release.json"
    path.write_text(json.dumps({"schema_version": 1, "version": "9.9.9", "revision": "local"}), encoding="utf-8")
    assert version_report(path).status is ManifestStatus.AVAILABLE
    path.write_text(json.dumps({"schema_version": 99, "version": "9.9.9"}), encoding="utf-8")
    assert version_report(path).status is ManifestStatus.UNSUPPORTED
    path.write_text("broken", encoding="utf-8")
    assert version_report(path).status is ManifestStatus.MALFORMED


def test_about_view_renders_local_report(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from packlab_studio.app import create_application
    from packlab_studio.version import AboutView

    app = create_application(["packlab-version-test"])
    view = AboutView(version_report())
    assert view.findChildren(type(view.findChildren(object)[0]))
    view.close()
    app.processEvents()
