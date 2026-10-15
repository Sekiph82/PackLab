from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest
from tools.ci.ci_data_safety import (
    TAINTED_ENVIRONMENT,
    check_environment,
    check_workflow_sources,
    scan_paths,
    tracked_and_untracked_paths,
)

ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_FIXTURES = ROOT / "tests" / "fixtures" / "ci-safe-synthetic"


def _codes(findings: list[object]) -> set[str]:
    return {finding.code for finding in findings}  # type: ignore[attr-defined]


def test_tracked_checkout_allows_only_hash_pinned_small_synthetic_media() -> None:
    findings = scan_paths(ROOT, tracked_and_untracked_paths(ROOT))

    assert findings == []
    assert {path.suffix for path in SYNTHETIC_FIXTURES.iterdir() if path.suffix != ".md"} == {
        ".png",
        ".jpg",
        ".stl",
        ".ply",
        ".step",
        ".dxf",
    }


@pytest.mark.parametrize(
    "relative",
    [
        "customer-data/frame.png",
        "supplier/drawing.step",
        "POVU/logo.png",
        "OneDrive/private/synthetic.png",
        "Dropbox/exports/synthetic.stl",
        "raw/synthetic.ply",
        "captures/view.step",
        "private-sample-scans/frame.png",
    ],
)
def test_private_data_path_family_is_rejected(tmp_path: Path, relative: str) -> None:
    candidate = tmp_path / relative
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(b"synthetic canary only")

    assert "PRIVATE_DATA_PATH_FAMILY" in _codes(scan_paths(ROOT, [candidate]))


def test_unapproved_image_and_scan_format_are_rejected(tmp_path: Path) -> None:
    image = tmp_path / "unreviewed.png"
    image.write_bytes(b"synthetic canary only")
    scan = tmp_path / "synthetic.packscan"
    scan.write_bytes(b"synthetic canary only")

    codes = _codes(scan_paths(ROOT, [image, scan]))
    assert codes == {"UNAPPROVED_SENSITIVE_PAYLOAD", "PRIVATE_OR_RAW_SCAN_FORMAT"}


@pytest.mark.parametrize("name", ["unreviewed.pdf", "povu-artwork.svg", "supplier-sheet.xlsx"])
def test_unreviewed_supplier_document_or_artwork_is_rejected(tmp_path: Path, name: str) -> None:
    candidate = tmp_path / name
    candidate.write_bytes(b"synthetic canary only")

    assert "UNAPPROVED_SENSITIVE_PAYLOAD" in _codes(scan_paths(ROOT, [candidate]))


def test_large_unknown_raw_payload_is_rejected_without_reading_content(tmp_path: Path) -> None:
    payload = tmp_path / "unknown.bin"
    with payload.open("wb") as stream:
        stream.truncate(1024 * 1024 + 1)

    assert "OVERSIZED_UNKNOWN_RAW_PAYLOAD" in _codes(scan_paths(ROOT, [payload]))


def test_large_structured_payload_and_missing_input_fail_closed(tmp_path: Path) -> None:
    payload = tmp_path / "point-cloud.json"
    with payload.open("wb") as stream:
        stream.truncate(16 * 1024 * 1024 + 1)

    assert "OVERSIZED_STRUCTURED_DATA" in _codes(scan_paths(ROOT, [payload]))
    assert "INPUT_MISSING" in _codes(scan_paths(ROOT, [tmp_path / "missing.stl"]))


def test_changed_bytes_under_a_safe_fixture_name_fail_the_hash_allowlist(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    policy = repository / "tools" / "ci"
    candidate = repository / "tests" / "fixtures" / "ci-safe-synthetic" / "synthetic-white.png"
    policy.mkdir(parents=True)
    candidate.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "tools/ci/ci_safe_data_policy.json", policy / "ci_safe_data_policy.json")
    candidate.write_bytes(
        (ROOT / "tests/fixtures/ci-safe-synthetic/synthetic-white.png").read_bytes()
        + b" synthetic canary"
    )

    assert "UNAPPROVED_SENSITIVE_PAYLOAD" in _codes(scan_paths(repository, [candidate]))


@pytest.mark.parametrize(
    "relative",
    [
        "assets/calibration/a3-packlab-calibration-mat.svg",
        "assets/calibration/a4-packlab-calibration-mat.svg",
        "tests/fixtures/ci-safe-synthetic/synthetic-box.step",
        "tests/fixtures/ci-safe-synthetic/synthetic-line.dxf",
        "tests/fixtures/ci-safe-synthetic/synthetic-triangle.ply",
        "tests/fixtures/ci-safe-synthetic/synthetic-triangle.stl",
    ],
)
def test_allowlisted_text_payloads_are_stable_across_windows_and_linux_line_endings(
    tmp_path: Path, relative: str
) -> None:
    repository = tmp_path / "repository"
    policy = repository / "tools" / "ci"
    candidate = repository / relative
    policy.mkdir(parents=True)
    candidate.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "tools/ci/ci_safe_data_policy.json", policy / "ci_safe_data_policy.json")
    source = (ROOT / relative).read_bytes()
    candidate.write_bytes(source.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))

    assert scan_paths(repository, [candidate]) == []


def test_archive_with_scan_member_is_rejected_without_extraction(tmp_path: Path) -> None:
    archive_path = tmp_path / "generated-fixture.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("ordinary.txt", "safe synthetic fixture")
        archive.writestr("supplier/part.packscan", "synthetic canary only")

    assert "ARCHIVE_CONTAINS_UNSAFE_MEMBER" in _codes(scan_paths(ROOT, [archive_path]))


def test_symlink_escape_is_rejected_when_supported(tmp_path: Path) -> None:
    boundary = tmp_path / "upload"
    boundary.mkdir()
    outside = tmp_path / "outside-data"
    outside.mkdir()
    (outside / "synthetic.stl").write_text("synthetic canary only", encoding="ascii")
    link = boundary / "linked-data"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        if os.name == "nt":
            try:
                subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except (OSError, subprocess.CalledProcessError):
                pytest.skip("host cannot create a filesystem symlink or junction")
        else:
            pytest.skip("host cannot create a filesystem symlink")

    assert "SYMLINK_ESCAPE" in _codes(scan_paths(ROOT, [boundary]))


@pytest.mark.parametrize("name", TAINTED_ENVIRONMENT)
def test_environment_injection_is_rejected_without_echoing_values(name: str) -> None:
    assert check_environment({}) == []
    canary = "synthetic-owner-root-canary"
    findings = check_environment({name: canary})
    assert _codes(findings) == {"AMBIENT_DEVELOPER_RUNTIME_INJECTION"}
    assert canary not in str(findings)


def test_workflow_owner_path_canary_is_rejected(tmp_path: Path) -> None:
    workflow_root = tmp_path / ".github" / "workflows"
    workflow_root.mkdir(parents=True)
    (workflow_root / "quality.yml").write_text(
        "run: pytest --data-root 'C:\\Users\\canary\\private scans'\n", encoding="utf-8"
    )

    assert "OWNER_SPECIFIC_WORKFLOW_ROOT" in _codes(check_workflow_sources(tmp_path))


def test_environment_check_does_not_mutate_process_environment() -> None:
    before = os.environ.get("PYTHONPATH")
    check_environment({"PYTHONPATH": "synthetic-canary"})
    assert os.environ.get("PYTHONPATH") == before


def test_uploaded_text_diagnostic_rejects_owner_root_but_accepts_runner_workspace(
    tmp_path: Path,
) -> None:
    diagnostic = tmp_path / "diagnostic.json"
    diagnostic.write_text('{"workspace":"D:\\\\a\\\\PackLab\\\\PackLab"}', encoding="utf-8")
    assert scan_paths(ROOT, [diagnostic], scan_text=True) == []
    diagnostic.write_text('{"workspace":"C:\\\\Users\\\\canary\\\\private"}', encoding="utf-8")

    assert "OWNER_PATH_IN_TEXT_ARTIFACT" in _codes(scan_paths(ROOT, [diagnostic], scan_text=True))


def test_corresponding_source_notice_text_is_an_allowed_artifact_input() -> None:
    notice = ROOT / "tools/packaging/windows_licenses/RELINKING_AND_SOURCE_GUIDE.txt"

    assert scan_paths(ROOT, [notice], scan_text=True) == []
