from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
UPLOAD_ACTION = "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"

GUARDED_UPLOADS = (
    (
        ".github/workflows/windows-studio-build.yml",
        "retained-sdk-inspection",
        "guard_precompile_diagnostics",
        "Guard precompile diagnostic artifact inputs",
        "Upload noncompiling SDK and native runtime diagnostic evidence",
        "3",
    ),
    (
        ".github/workflows/windows-studio-build.yml",
        "controlled-ocp-runtime",
        "guard_ocp_quarantine",
        "Guard OCP quarantine artifact inputs",
        "Upload post-link OCP quarantine before any downstream failure can discard it",
        "7",
    ),
    (
        ".github/workflows/windows-studio-build.yml",
        "build-studio",
        "guard_studio_smoke_diagnostics",
        "Guard packaged Studio smoke diagnostic inputs",
        "Upload packaged Studio smoke diagnostics",
        "3",
    ),
    (
        ".github/workflows/windows-studio-build.yml",
        "build-studio",
        "guard_preclearance_evidence",
        "Guard pre-clearance evidence artifact inputs",
        "Upload text-only pre-clearance evidence",
        "1",
    ),
    (
        ".github/workflows/pl0350-fmt-dependency-probe.yml",
        "dependency-probe",
        "guard_fmt_probe_artifact",
        "Guard dependency probe artifact input",
        "Upload dependency probe evidence",
        "14",
    ),
)


def _load_workflow(relative: str) -> dict[str, Any]:
    # BaseLoader keeps GitHub's `on` key as a string and still builds real
    # YAML mappings/sequences for jobs and steps.
    document = yaml.load((ROOT / relative).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(document, dict)
    assert "on" in document
    assert isinstance(document.get("jobs"), dict)
    return document


def _job_steps(workflow: dict[str, Any], job_id: str) -> list[dict[str, Any]]:
    steps = workflow["jobs"][job_id]["steps"]
    assert isinstance(steps, list)
    return steps


def _workflow_paths() -> list[Path]:
    workflow_dir = ROOT / ".github" / "workflows"
    return sorted((*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")))


def _step(steps: list[dict[str, Any]], name: str) -> tuple[int, dict[str, Any]]:
    matches = [(index, step) for index, step in enumerate(steps) if step.get("name") == name]
    assert len(matches) == 1
    return matches[0]


def _condition_succeeds(condition: str, outcomes: dict[str, str]) -> bool:
    """Evaluate the small status-expression subset used by guarded uploads."""
    for expression in (part.strip() for part in condition.split("&&")):
        if expression == "always()":
            continue
        match = re.fullmatch(r"steps\.([A-Za-z0-9_-]+)\.outcome\s*(==|!=)\s*'([a-z]+)'", expression)
        if not match:
            raise AssertionError(f"Unexpected guarded-upload condition term: {expression}")
        step_id, operator, expected = match.groups()
        actual = outcomes.get(step_id)
        matches = (
            actual == expected if operator == "==" else actual is not None and actual != expected
        )
        if not matches:
            return False
    return True


@pytest.mark.parametrize(
    "workflow_path,job_id,guard_id,guard_name,upload_name,retention_days", GUARDED_UPLOADS
)
def test_upload_is_immediately_gated_by_its_unique_successful_guard(
    workflow_path: str,
    job_id: str,
    guard_id: str,
    guard_name: str,
    upload_name: str,
    retention_days: str,
) -> None:
    workflow = _load_workflow(workflow_path)
    steps = _job_steps(workflow, job_id)
    guard_index, guard = _step(steps, guard_name)
    upload_index, upload = _step(steps, upload_name)

    assert guard_index + 1 == upload_index
    assert guard.get("id") == guard_id
    assert guard.get("if") is not None and "always()" in guard["if"]
    assert sum(step.get("id") == guard_id for step in steps) == 1
    assert upload.get("uses") == UPLOAD_ACTION
    assert upload.get("if") is not None
    assert f"steps.{guard_id}.outcome == 'success'" in upload["if"]
    assert upload["with"]["retention-days"] == retention_days


@pytest.mark.parametrize(
    "workflow_path,job_id,guard_id,guard_name,upload_name,_retention_days", GUARDED_UPLOADS
)
def test_guarded_upload_outcomes_fail_closed_but_allow_prior_unrelated_failure(
    workflow_path: str,
    job_id: str,
    guard_id: str,
    guard_name: str,
    upload_name: str,
    _retention_days: str,
) -> None:
    workflow = _load_workflow(workflow_path)
    steps = _job_steps(workflow, job_id)
    guard_index, guard = _step(steps, guard_name)
    upload_index, upload = _step(steps, upload_name)
    assert guard_index + 1 == upload_index
    condition = upload["if"]

    outcomes = {guard_id: "success", "unrelated_stage": "failure"}
    # Existing prerequisite conditions remain part of the complete expression.
    for term in condition.split("&&"):
        match = re.search(r"steps\.([A-Za-z0-9_-]+)\.outcome", term)
        if match:
            outcomes.setdefault(match.group(1), "success")
    assert _condition_succeeds(condition, outcomes)

    for rejected_outcome in ("failure", "skipped"):
        rejected = dict(outcomes, **{guard_id: rejected_outcome})
        assert not _condition_succeeds(condition, rejected)

    missing_guard = dict(outcomes)
    missing_guard.pop(guard_id)
    assert not _condition_succeeds(condition, missing_guard)


def test_every_status_overridden_artifact_upload_has_an_explicit_guard_success_gate() -> None:
    expected = {(workflow, upload) for workflow, _, _, _, upload, _ in GUARDED_UPLOADS}
    discovered: set[tuple[str, str]] = set()
    for workflow_path in _workflow_paths():
        relative = workflow_path.relative_to(ROOT).as_posix()
        workflow = _load_workflow(relative)
        for job_id, job in workflow["jobs"].items():
            steps = job.get("steps") or []
            by_id = {step["id"]: step for step in steps if step.get("id")}
            for index, upload in enumerate(steps):
                if not str(upload.get("uses", "")).startswith("actions/upload-artifact@"):
                    continue
                condition = str(upload.get("if", ""))
                if not any(
                    status in condition for status in ("always()", "failure()", "cancelled()")
                ):
                    continue
                discovered.add((relative, upload["name"]))
                matches = re.findall(
                    r"steps\.([A-Za-z0-9_-]+)\.outcome\s*==\s*'success'", condition
                )
                assert matches, f"Status-overridden upload lacks a success gate: {job_id}"
                for guard_id in matches:
                    assert guard_id in by_id
                    guard_index, _ = _step(steps, by_id[guard_id]["name"])
                    assert guard_index < index
    assert discovered == expected


def test_optional_missing_file_uploads_still_require_an_immediately_preceding_guard() -> None:
    """warn/ignore controls missing paths, not guard rejection or skip outcomes."""
    expected_optional = {
        "Upload noncompiling SDK and native runtime diagnostic evidence",
        "Upload post-link OCP quarantine before any downstream failure can discard it",
        "Upload packaged Studio smoke diagnostics",
        "Upload dependency probe evidence",
    }
    discovered_optional: set[str] = set()
    for workflow_path in _workflow_paths():
        workflow = _load_workflow(workflow_path.relative_to(ROOT).as_posix())
        for job in workflow["jobs"].values():
            steps = job.get("steps") or []
            for index, upload in enumerate(steps):
                if not str(upload.get("uses", "")).startswith("actions/upload-artifact@"):
                    continue
                missing_policy = upload.get("with", {}).get("if-no-files-found", "error")
                if missing_policy not in {"warn", "ignore"}:
                    continue
                assert index > 0
                previous = steps[index - 1]
                assert str(previous.get("name", "")).startswith("Guard ")
                assert previous.get("id")
                assert f"steps.{previous['id']}.outcome == 'success'" in upload.get("if", "")
                discovered_optional.add(upload["name"])
    assert discovered_optional == expected_optional
