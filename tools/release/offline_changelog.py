"""Validate offline draft notes against accepted IDs and cited source text.

This tool does not infer notes from Git history or commit messages and does
not publish a changelog.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

_TASK_ID = re.compile(r"PL-[0-9]{4,}\Z")
_ACCEPTED_TASK = re.compile(r"^- \[x\] \*\*(PL-[0-9]{4,})\*\*", re.MULTILINE)


def _repo_file(root: Path, value: Any) -> Path | None:
    if not isinstance(value, str):
        return None
    rel = PurePosixPath(value)
    if rel.is_absolute() or ".." in rel.parts or "\\" in value:
        return None
    candidate = root.joinpath(*rel.parts)
    if candidate.is_symlink() or getattr(candidate, "is_junction", lambda: False)():
        return None
    try:
        root_resolved = root.resolve(strict=True)
        resolved_candidate = candidate.resolve(strict=True)
        resolved_candidate.relative_to(root_resolved)
    except (OSError, ValueError):
        return None
    return resolved_candidate if resolved_candidate.is_file() else None


def _audit_is_accepted(path: Path, task_id: str) -> bool:
    if not path.name.startswith(f"{task_id}_CHATGPT_AUDIT_"):
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    has_accepted_verdict = any(
        re.search(r"(?i)(?:verdict|decision)\s*:", line)
        and re.search(r"\bAUDITED_PASS(?:_[A-Z0-9_]+)?\b", line)
        and "AUDITED_PARTIAL" not in line
        and not re.search(r"(?i)\bNOT\s+AUDITED_PASS\b", line)
        for line in text.splitlines()
    )
    return task_id in text and has_accepted_verdict


def validate_entries(root: Path, entries: Any) -> dict[str, Any]:
    """Check notes are unique, accepted, source-bound, and audit-cited."""
    errors: set[str] = set()
    if not isinstance(entries, list) or not entries:
        return {"status": "BLOCKED", "errors": ["CHANGELOG_ENTRIES_MISSING"]}
    try:
        tracker = (root / "TASKS.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {"status": "BLOCKED", "errors": ["CANONICAL_TRACKER_UNAVAILABLE"]}
    accepted = set(_ACCEPTED_TASK.findall(tracker))
    seen: set[str] = set()
    for entry in entries:
        fields = {"task_id", "summary", "audit_ref", "source_ref", "source_sha256"}
        if not isinstance(entry, dict) or set(entry) != fields:
            errors.add("CHANGELOG_ENTRY_FIELDS_MISSING_OR_UNEXPECTED")
            continue
        task_id = entry["task_id"]
        if not isinstance(task_id, str) or not _TASK_ID.fullmatch(task_id):
            errors.add("CHANGELOG_TASK_ID_INVALID")
            continue
        if task_id in seen:
            errors.add("CHANGELOG_TASK_ID_DUPLICATE")
        seen.add(task_id)
        if task_id not in accepted:
            errors.add("CHANGELOG_TASK_NOT_ACCEPTED")
        summary = entry["summary"]
        if not isinstance(summary, str) or not summary.strip() or "\n" in summary:
            errors.add("CHANGELOG_SUMMARY_INVALID")
        audit_path = _repo_file(root, entry["audit_ref"])
        if (
            audit_path is None
            or not audit_path.as_posix().startswith(
                (root.resolve() / "coordination").resolve().as_posix() + "/"
            )
            or not _audit_is_accepted(audit_path, task_id)
        ):
            errors.add("CHANGELOG_AUDIT_CITATION_UNACCEPTED")
        source_path = _repo_file(root, entry["source_ref"])
        expected = entry["source_sha256"]
        if source_path is None:
            errors.add("CHANGELOG_SOURCE_FRAGMENT_UNAVAILABLE")
        else:
            try:
                content = source_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                errors.add("CHANGELOG_SOURCE_FRAGMENT_UNREADABLE")
                continue
            try:
                actual = hashlib.sha256(source_path.read_bytes()).hexdigest()
            except OSError:
                errors.add("CHANGELOG_SOURCE_FRAGMENT_UNREADABLE")
                continue
            if (
                not isinstance(expected, str)
                or not re.fullmatch(r"[0-9a-f]{64}", expected)
                or expected != actual
            ):
                errors.add("CHANGELOG_SOURCE_DIGEST_MISMATCH")
            if isinstance(summary, str) and summary.strip() and summary not in content:
                errors.add("CHANGELOG_SUMMARY_NOT_IN_SOURCE_FRAGMENT")
    return {
        "status": "OFFLINE_CHANGELOG_INPUT_VALIDATION_ONLY" if not errors else "BLOCKED",
        "errors": sorted(errors),
        "entry_count": len(entries),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path, help="UTF-8 JSON array of draft notes")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        draft = json.loads(args.draft.read_text(encoding="utf-8"))
        result = validate_entries(args.repo.resolve(), draft)
    except (OSError, UnicodeError, json.JSONDecodeError):
        result = {"status": "BLOCKED", "errors": ["CHANGELOG_DRAFT_UNREADABLE"]}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] != "BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
