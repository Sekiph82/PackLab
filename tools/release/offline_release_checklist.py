"""Validate release-candidate checklist evidence without authorizing release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.release.offline_version_inventory import release_train_identity  # noqa: E402

_TASK_ID = re.compile(r"PL-[0-9]{4,}\Z")
_TASK_LINE = re.compile(r"^- \[(?P<checked>[ xX])\] \*\*(?P<task>PL-[0-9]{4,})\*\*", re.MULTILINE)
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_RUN_ID = re.compile(r"[0-9]{1,20}\Z")
_LIMITATION = re.compile(r"[a-z][a-z0-9_]{1,63}\Z")
_GATE_NAMES = (
    "windows_ci_build_package_smoke",
    "redistribution_notice_inventory",
    "ios_swift_simulator_tests",
    "ios_unsigned_device_archive",
    "secrets_scan",
    "windows_artifact_provenance",
    "ios_artifact_provenance",
)
_ARTIFACT_GATES = {
    "windows_artifact_provenance",
    "ios_artifact_provenance",
    "signed_ipa",
}
_VERSIONS = {"studio", "capture", "capture_build", "packscan_schema"}
_REQUIRED_LIMITATIONS = {
    "PENDING": {"physical_validation_pending"},
    "ACCEPTED_WITH_LIMITATIONS": set(),
    "PASS": set(),
}


def _repo_file(root: Path, value: Any, prefix: str) -> Path | None:
    if not isinstance(value, str) or not value.startswith(prefix) or "\\" in value:
        return None
    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        return None
    relative = PurePosixPath(value)
    if relative.is_absolute():
        return None
    current = root
    try:
        for part in relative.parts:
            current = current / part
            if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
                return None
        root_resolved = root.resolve(strict=True)
        resolved = current.resolve(strict=True)
        resolved.relative_to(root_resolved)
    except (OSError, ValueError):
        return None
    return resolved if resolved.is_file() else None


def _tracker_tasks(root: Path) -> tuple[dict[str, bool], list[str]]:
    try:
        text = (root / "TASKS.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {}, ["CANONICAL_TRACKER_UNAVAILABLE"]
    result: dict[str, bool] = {}
    errors: list[str] = []
    for match in _TASK_LINE.finditer(text):
        task_id = match.group("task")
        if task_id in result:
            errors.append("CANONICAL_TRACKER_TASK_ID_DUPLICATE")
        else:
            result[task_id] = match.group("checked").lower() == "x"
    if not result:
        errors.append("CANONICAL_TRACKER_TASKS_MISSING")
    return result, errors


def _audit_candidates(root: Path, task_id: str) -> list[tuple[int, Path]]:
    audit_root = root / "coordination/sessions"
    if not audit_root.is_dir() or audit_root.is_symlink():
        return []
    result: list[tuple[int, Path]] = []
    for path in audit_root.rglob("*"):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            return []
        if not path.is_file():
            continue
        match = re.fullmatch(re.escape(task_id) + r"_CHATGPT_AUDIT_V([0-9]+)\.md", path.name)
        if match is None:
            continue
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root.resolve(strict=True))
        except (OSError, ValueError):
            continue
        result.append((int(match.group(1)), resolved))
    return result


def _latest_task_audit(root: Path, task_id: str) -> Path | None:
    candidates = _audit_candidates(root, task_id)
    if not candidates:
        return None
    latest_version = max(version for version, _ in candidates)
    paths = {path for version, path in candidates if version == latest_version}
    return next(iter(paths)) if len(paths) == 1 else None


def _accepted_audit_text(path: Path, task_id: str) -> str | None:
    if not path.name.startswith(f"{task_id}_CHATGPT_AUDIT_"):
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    decisions = _decision_values(text)
    if len(decisions) != 1:
        return None
    final = decisions[0]
    if not re.fullmatch(r"AUDITED_PASS(?:_[A-Z0-9]+)*", final):
        return None
    task_fields = _field_values(text, "Task")
    return text if task_fields == [task_id] else None


def _field_values(text: str, label: str) -> list[str]:
    pattern = re.compile(rf"(?im)^{re.escape(label)}:\s*(.*?)\s*$")
    return [match.group(1).strip().strip("`*_ ") for match in pattern.finditer(text)]


def _decision_values(text: str) -> list[str]:
    pattern = re.compile(r"(?im)^\s*(?:Decision|Verdict):\s*[*`_ ]*([A-Z][A-Z0-9_]+)[*_` ]*\s*$")
    return [match.group(1).upper() for match in pattern.finditer(text)]


def _accepted_milestone_audit_text(path: Path, milestone: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    decisions = _decision_values(text)
    if len(decisions) != 1 or not re.fullmatch(r"AUDITED_PASS(?:_[A-Z0-9]+)*", decisions[0]):
        return None
    milestone_fields = _field_values(text, "Milestone")
    return text if milestone_fields == [milestone] else None


def _evidence_fields(artifact: bool) -> set[str]:
    fields = {"audit_task_id", "audit_ref", "source_commit", "result"}
    if artifact:
        fields.update({"artifact_sha256", "artifact_bytes", "workflow_run_id"})
    return fields


def _validate_evidence(
    root: Path,
    gate_name: str,
    evidence: Any,
    source_commit: str,
    accepted_tasks: dict[str, bool],
) -> list[str]:
    errors: list[str] = []
    artifact = gate_name in _ARTIFACT_GATES
    if not isinstance(evidence, dict) or set(evidence) != _evidence_fields(artifact):
        return [f"{gate_name.upper()}_EVIDENCE_FIELDS_INVALID"]
    task_id = evidence["audit_task_id"]
    if not isinstance(task_id, str) or not _TASK_ID.fullmatch(task_id):
        return [f"{gate_name.upper()}_AUDIT_ID_INVALID"]
    if task_id not in accepted_tasks:
        errors.append(f"{gate_name.upper()}_AUDIT_ID_UNKNOWN")
    elif not accepted_tasks[task_id]:
        errors.append(f"{gate_name.upper()}_AUDIT_TASK_NOT_ACCEPTED")
    if (
        evidence["source_commit"] != source_commit
        or not isinstance(evidence["source_commit"], str)
        or not _COMMIT.fullmatch(evidence["source_commit"])
    ):
        errors.append(f"{gate_name.upper()}_SOURCE_COMMIT_STALE")
    if evidence["result"] != "PASS":
        errors.append(f"{gate_name.upper()}_RESULT_NOT_PASS")

    audit_path = _repo_file(root, evidence["audit_ref"], "coordination/sessions/")
    latest = _latest_task_audit(root, task_id)
    if audit_path is None or latest is None or audit_path != latest:
        errors.append(f"{gate_name.upper()}_AUDIT_MISSING_OR_STALE")
        audit_text = None
    else:
        audit_text = _accepted_audit_text(audit_path, task_id)
        if audit_text is None:
            errors.append(f"{gate_name.upper()}_AUDIT_NOT_ACCEPTED")
    if audit_text is not None:
        if _field_values(audit_text, "Source commit") != [source_commit]:
            errors.append(f"{gate_name.upper()}_AUDIT_SOURCE_COMMIT_MISMATCH")
        if _field_values(audit_text, "Gate Coverage") != [gate_name]:
            errors.append(f"{gate_name.upper()}_AUDIT_SCOPE_MISMATCH")

    if artifact:
        digest = evidence["artifact_sha256"]
        length = evidence["artifact_bytes"]
        run_id = evidence["workflow_run_id"]
        if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
            errors.append(f"{gate_name.upper()}_ARTIFACT_DIGEST_INVALID")
        if isinstance(length, bool) or not isinstance(length, int) or length < 1:
            errors.append(f"{gate_name.upper()}_ARTIFACT_LENGTH_INVALID")
        if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id) or int(run_id) < 1:
            errors.append(f"{gate_name.upper()}_WORKFLOW_RUN_INVALID")
        if audit_text is not None:
            if _field_values(audit_text, "Artifact SHA-256") != [digest]:
                errors.append(f"{gate_name.upper()}_AUDIT_ARTIFACT_DIGEST_MISMATCH")
            if _field_values(audit_text, "Artifact bytes") != [str(length)]:
                errors.append(f"{gate_name.upper()}_AUDIT_ARTIFACT_LENGTH_MISMATCH")
            if _field_values(audit_text, "Workflow run ID") != [run_id]:
                errors.append(f"{gate_name.upper()}_AUDIT_WORKFLOW_RUN_MISMATCH")
    return errors


def _milestone_audit(root: Path, audit_ref: Any, source_commit: str) -> bool:
    path = _repo_file(root, audit_ref, "coordination/sessions/")
    if path is None or not re.fullmatch(r"M17-C[0-9]{3,}_CHATGPT_AUDIT_V[0-9]+\.md", path.name):
        return False
    name = path.name
    cycle_match = re.search(r"M17-C([0-9]{3,})_CHATGPT", name)
    version_match = re.search(r"_V([0-9]+)\.md\Z", name)
    if cycle_match is None or version_match is None:
        return False
    cycle = int(cycle_match.group(1))
    version = int(version_match.group(1))
    latest: set[Path] = set()
    audit_root = root / "coordination/sessions"
    for candidate in audit_root.rglob("*"):
        if candidate.is_symlink() or getattr(candidate, "is_junction", lambda: False)():
            return False
        if not candidate.is_file():
            continue
        cm = re.search(r"M17-C([0-9]{3,})_CHATGPT", candidate.name)
        vm = re.search(r"_V([0-9]+)\.md\Z", candidate.name)
        if cm and vm:
            if any(
                part.is_symlink() or getattr(part, "is_junction", lambda: False)()
                for part in (candidate, *candidate.parents)
                if part != root and part != root.parent
            ):
                return False
            pair = (int(cm.group(1)), int(vm.group(1)))
            if pair > (cycle, version):
                return False
            if pair == (cycle, version):
                try:
                    if candidate.resolve(strict=True) == path:
                        latest.add(path)
                    else:
                        latest.add(candidate.resolve(strict=True))
                except OSError:
                    return False
    if latest != {path}:
        return False
    text = _accepted_milestone_audit_text(path, "M17")
    return bool(
        text
        and _field_values(text, "Source commit") == [source_commit]
        and _field_values(text, "Milestone") == ["M17"]
    )


def _validate_evidence_fields(root: Path, candidate: Any) -> dict[str, Any]:
    """Check evidence fields only; this result is not source/train acceptance."""
    if not isinstance(candidate, dict):
        return {"status": "BLOCKED", "errors": ["CHECKLIST_CANDIDATE_INVALID"]}
    required = {
        "source_commit",
        "release_train_id",
        "versions",
        "release_intent",
        "gates",
        "m17_acceptance",
        "legal_review",
        "physical_validation",
        "known_limitations",
    }
    if set(candidate) != required:
        return {"status": "BLOCKED", "errors": ["CHECKLIST_CANDIDATE_FIELDS_INVALID"]}
    errors: set[str] = set()
    source_commit = candidate["source_commit"]
    if not isinstance(source_commit, str) or not _COMMIT.fullmatch(source_commit):
        return {"status": "BLOCKED", "errors": ["SOURCE_COMMIT_INVALID"]}
    versions = candidate["versions"]
    if not isinstance(versions, dict) or set(versions) != _VERSIONS:
        errors.add("VERSION_TUPLE_INVALID")
    if not isinstance(candidate["release_intent"], str) or candidate["release_intent"] not in (
        "INTERNAL_UNSIGNED",
        "SIGNED_DISTRIBUTION",
    ):
        errors.add("RELEASE_INTENT_INVALID")

    accepted_tasks, tracker_errors = _tracker_tasks(root)
    errors.update(tracker_errors)
    gates = candidate["gates"]
    gate_keys = {*_GATE_NAMES, "signed_ipa"}
    if not isinstance(gates, dict) or set(gates) != gate_keys:
        errors.add("REQUIRED_GATE_SET_INVALID")
    else:
        for gate_name in _GATE_NAMES:
            errors.update(
                _validate_evidence(root, gate_name, gates[gate_name], source_commit, accepted_tasks)
            )
        signed = gates["signed_ipa"]
        if candidate["release_intent"] == "SIGNED_DISTRIBUTION":
            errors.update(
                _validate_evidence(root, "signed_ipa", signed, source_commit, accepted_tasks)
            )
        elif signed is not None:
            errors.add("SIGNED_IPA_MUST_BE_OMITTED_FOR_UNSIGNED_INTENT")

    m17 = candidate["m17_acceptance"]
    if not isinstance(m17, dict) or set(m17) != {"status", "audit_ref"}:
        errors.add("M17_ACCEPTANCE_FIELDS_INVALID")
    elif m17["status"] == "ACCEPTED":
        if not _milestone_audit(root, m17["audit_ref"], source_commit):
            errors.add("M17_ACCEPTANCE_AUDIT_MISSING_OR_STALE")
    elif m17["status"] == "NOT_ACCEPTED":
        if m17["audit_ref"] is not None:
            errors.add("M17_AUDIT_MUST_BE_EMPTY_WHEN_NOT_ACCEPTED")
        errors.add("M17_ACCEPTANCE_REQUIRED_BEFORE_PL0368")
    else:
        errors.add("M17_ACCEPTANCE_STATUS_INVALID")

    legal = candidate["legal_review"]
    if not isinstance(legal, dict) or set(legal) != {
        "status",
        "approval_id",
        "approval_ref",
        "evidence_sha256",
    }:
        errors.add("LEGAL_REVIEW_FIELDS_INVALID")
    elif legal["status"] == "PENDING":
        if any(
            legal[key] is not None for key in ("approval_id", "approval_ref", "evidence_sha256")
        ):
            errors.add("LEGAL_REVIEW_PENDING_EVIDENCE_CONTRADICTION")
        errors.add("FORMAL_LEGAL_REVIEW_PENDING")
    else:
        errors.add("LEGAL_REVIEW_STATUS_INVALID")

    physical = candidate["physical_validation"]
    if not isinstance(physical, dict) or set(physical) != {"status", "evidence"}:
        errors.add("PHYSICAL_VALIDATION_FIELDS_INVALID")
    elif physical["status"] == "PENDING":
        if physical["evidence"] is not None:
            errors.add("PHYSICAL_VALIDATION_PENDING_EVIDENCE_CONTRADICTION")
    elif physical["status"] == "ACCEPTED":
        errors.update(
            _validate_evidence(
                root,
                "physical_validation",
                physical["evidence"],
                source_commit,
                accepted_tasks,
            )
        )
    else:
        errors.add("PHYSICAL_VALIDATION_STATUS_INVALID")

    limitations = candidate["known_limitations"]
    if (
        not isinstance(limitations, list)
        or not limitations
        or any(not isinstance(item, str) or not _LIMITATION.fullmatch(item) for item in limitations)
    ):
        errors.add("KNOWN_LIMITATIONS_INVALID")
    elif len(set(limitations)) != len(limitations):
        errors.add("KNOWN_LIMITATIONS_DUPLICATE")
    else:
        limitation_set = set(limitations)
        if (
            isinstance(m17, dict)
            and m17.get("status") == "NOT_ACCEPTED"
            and "m17_acceptance_not_granted" not in limitation_set
        ):
            errors.add("M17_LIMITATION_NOT_SURFACED")
        if (
            isinstance(physical, dict)
            and physical.get("status") == "PENDING"
            and "physical_validation_pending" not in limitation_set
        ):
            errors.add("PHYSICAL_LIMITATION_NOT_SURFACED")
        if (
            isinstance(legal, dict)
            and legal.get("status") == "PENDING"
            and "formal_legal_review_pending" not in limitation_set
        ):
            errors.add("LEGAL_LIMITATION_NOT_SURFACED")
        if (
            isinstance(m17, dict)
            and m17.get("status") == "ACCEPTED"
            and "m17_acceptance_not_granted" in limitation_set
        ):
            errors.add("M17_LIMITATION_CONTRADICTS_ACCEPTANCE")
        if (
            isinstance(physical, dict)
            and physical.get("status") == "ACCEPTED"
            and "physical_validation_pending" in limitation_set
        ):
            errors.add("PHYSICAL_LIMITATION_CONTRADICTS_ACCEPTANCE")

    result_errors = sorted(errors)
    return {
        "status": "BLOCKED"
        if result_errors
        else "EVIDENCE_VALIDATION_PASS_SOURCE_TRAIN_NOT_CHECKED",
        "errors": result_errors,
        "source_commit": source_commit,
        "versions": versions,
        "release_intent": candidate["release_intent"],
        "gates": gates if isinstance(gates, dict) else {},
        "m17_acceptance": m17 if isinstance(m17, dict) else {},
        "legal_review": legal if isinstance(legal, dict) else {},
        "physical_validation": physical if isinstance(physical, dict) else {},
        "known_limitations": limitations if isinstance(limitations, list) else [],
    }


def _clean_source_commit(root: Path) -> str:
    try:
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("SOURCE_REPOSITORY_UNAVAILABLE") from exc
    if status:
        raise ValueError("SOURCE_CHECKOUT_NOT_CLEAN")
    if not _COMMIT.fullmatch(commit):
        raise ValueError("SOURCE_COMMIT_INVALID")
    return commit


def render_checklist(validation: dict[str, Any], train_id: str) -> str:
    versions = validation.get("versions")
    if not isinstance(versions, dict):
        versions = {}
    gates = validation.get("gates")
    if not isinstance(gates, dict):
        gates = {}
    m17 = validation.get("m17_acceptance")
    if not isinstance(m17, dict):
        m17 = {}
    legal = validation.get("legal_review")
    if not isinstance(legal, dict):
        legal = {}
    physical = validation.get("physical_validation")
    if not isinstance(physical, dict):
        physical = {}
    limitations = validation.get("known_limitations")
    if not isinstance(limitations, list):
        limitations = []
    errors = validation.get("errors")
    if not isinstance(errors, list):
        errors = ["CHECKLIST_VALIDATION_FAILED"]
    source_commit = validation.get("source_commit")
    if not isinstance(source_commit, str) or not _COMMIT.fullmatch(source_commit):
        source_commit = "INVALID"
    if not isinstance(train_id, str) or not re.fullmatch(r"packlab-rt-v1-[0-9a-f]{64}", train_id):
        train_id = "UNKNOWN"
    safe_versions = {
        key: value
        if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9._+-]{1,64}", value)
        else "UNKNOWN"
        for key, value in versions.items()
    }
    status = validation.get("status")
    if status not in ("BLOCKED", "CHECKLIST_PASS_NOT_RELEASE_AUTHORIZATION"):
        status = "BLOCKED"
    intent = validation.get("release_intent")
    if intent not in ("INTERNAL_UNSIGNED", "SIGNED_DISTRIBUTION"):
        intent = "INVALID"
    error_codes = {error for error in errors if isinstance(error, str)}
    lines = [
        "# PackLab Release Candidate Checklist",
        "",
        f"- Status: `{status}`",
        "- Release authorization: `NOT_GRANTED`",
        "- M17 acceptance is an explicit PL-0368 prerequisite.",
        f"- Source commit: `{source_commit}`",
        f"- Release train: `{train_id}`",
        f"- Studio: `{safe_versions.get('studio', 'UNKNOWN')}`",
        f"- Capture: `{safe_versions.get('capture', 'UNKNOWN')}` (build `{safe_versions.get('capture_build', 'UNKNOWN')}`)",
        f"- PackScan schema: `{safe_versions.get('packscan_schema', 'UNKNOWN')}`",
        f"- Release intent: `{intent}`",
        "",
        "## Required evidence gates",
        "",
    ]
    for gate_name in (*_GATE_NAMES, "signed_ipa"):
        evidence = gates.get(gate_name)
        if gate_name == "signed_ipa" and evidence is None and intent == "INTERNAL_UNSIGNED":
            lines.append("- Signed IPA: `NOT_REQUIRED_UNSIGNED_INTERNAL`")
        elif gate_name == "signed_ipa" and evidence is None:
            lines.append(
                "- Signed IPA: `BLOCKED` — required for signed distribution or intent is invalid"
            )
        elif evidence is None:
            lines.append(f"- {gate_name}: `BLOCKED` — evidence missing")
        elif any(error.startswith(f"{gate_name.upper()}_") for error in error_codes):
            lines.append(f"- {gate_name}: `BLOCKED` — referenced evidence failed validation")
        elif (
            isinstance(evidence, dict)
            and isinstance(evidence.get("audit_task_id"), str)
            and _TASK_ID.fullmatch(evidence["audit_task_id"])
        ):
            artifact_digest = evidence.get("artifact_sha256", "not-applicable")
            if gate_name in _ARTIFACT_GATES and (
                not isinstance(artifact_digest, str) or not _DIGEST.fullmatch(artifact_digest)
            ):
                artifact_digest = "invalid"
            lines.append(
                f"- {gate_name}: `PASS` — `{evidence['audit_task_id']}`; "
                f"artifact SHA-256 `{artifact_digest}`"
            )
        else:
            lines.append(f"- {gate_name}: `BLOCKED` — evidence malformed")
    lines.extend(
        [
            "",
            "## External and future gates",
            "",
            f"- M17 acceptance: `{('BLOCKED' if 'M17_ACCEPTANCE_AUDIT_MISSING_OR_STALE' in error_codes else m17.get('status')) if m17.get('status') in ('ACCEPTED', 'NOT_ACCEPTED') else 'MISSING'}`",
            f"- Formal legal review: `{legal.get('status') if legal.get('status') == 'PENDING' else 'MISSING'}`",
            f"- Physical validation: `{('BLOCKED' if any(error.startswith('PHYSICAL_VALIDATION_') for error in error_codes) else physical.get('status')) if physical.get('status') in ('PENDING', 'ACCEPTED') else 'MISSING'}`",
            "",
            "## Known limitations",
            "",
        ]
    )
    lines.extend(
        f"- `{item}`"
        for item in sorted(
            item for item in limitations if isinstance(item, str) and _LIMITATION.fullmatch(item)
        )
    )
    lines.append("")
    lines.extend(["## Blockers", ""])
    lines.extend(f"- `{error}`" for error in errors if isinstance(error, str))
    if not errors:
        lines.append(
            "- No checklist blocker reported; release publication still requires separate authorization."
        )
    return "\n".join(lines).rstrip() + "\n"


def _write_new_output(root: Path, target: Path, content: str) -> None:
    root = root.resolve(strict=True)
    output = target.absolute()
    if output.exists() or output.is_symlink() or getattr(output, "is_junction", lambda: False)():
        raise ValueError("CHECKLIST_OUTPUT_ALREADY_EXISTS_OR_LINKED")
    for parent in (output.parent, *output.parent.parents):
        if parent.is_symlink() or getattr(parent, "is_junction", lambda: False)():
            raise ValueError("CHECKLIST_OUTPUT_PARENT_LINKED")
    try:
        output.resolve(strict=False).relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("CHECKLIST_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
    try:
        output.parent.resolve(strict=True)
    except OSError as exc:
        raise ValueError("CHECKLIST_OUTPUT_PARENT_UNAVAILABLE") from exc
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, help="UTF-8 JSON candidate evidence")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output", type=Path, required=True, help="Output path outside the repository"
    )
    args = parser.parse_args(argv)
    try:
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        root = args.repo.resolve(strict=True)
        validation = _validate_evidence_fields(root, candidate)
        source_commit = _clean_source_commit(root)
        if not isinstance(candidate, dict):
            raise ValueError("CHECKLIST_CANDIDATE_INVALID")
        if candidate.get("source_commit") != source_commit:
            raise ValueError("SOURCE_COMMIT_MISMATCH")
        train = release_train_identity(root, source_commit)
        if candidate.get("release_train_id") != train["release_train"]["id"]:
            raise ValueError("RELEASE_TRAIN_ID_MISMATCH")
        if candidate.get("versions") != train["release_train"]["versions"]:
            raise ValueError("VERSION_TUPLE_MISMATCH")
        if validation["status"] != "BLOCKED":
            validation["status"] = "CHECKLIST_PASS_NOT_RELEASE_AUTHORIZATION"
        markdown = render_checklist(validation, train["release_train"]["id"])
        _write_new_output(root, args.output, markdown)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        reason = str(exc) if str(exc).isupper() else "CHECKLIST_INPUT_UNREADABLE"
        print(json.dumps({"status": "BLOCKED", "errors": [reason]}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "status": validation["status"],
                "errors": validation["errors"],
                "output_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
            },
            sort_keys=True,
        )
    )
    return 0 if validation["status"] != "BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
