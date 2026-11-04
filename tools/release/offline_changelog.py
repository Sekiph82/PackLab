"""Generate a deterministic, preparation-only changelog from audited task notes.

The tool never reads Git commit messages or builder logs as release truth.
Every entry must bind to an accepted task, its final ChatGPT audit, and a
hash-verified curated release-note fragment. Output is not release authority.
"""

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
_MILESTONE = re.compile(r"^# M(?P<number>[0-9]+) - .+$")
_COMMIT_SHA = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_CATEGORIES = ("Added", "Changed", "Fixed", "Security")
_PRIVATE_OR_PATH = re.compile(
    r"(?:[A-Za-z]:[\\/]|\\\\[^\\\\]+[\\\\]|(?:^|\s)/(?:Users|home|private|tmp)/|"
    r"\b(?:https?|file)://\S+|(?<![A-Za-z0-9_.-])(?:\.\.?/|[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*)(?=$|[^A-Za-z0-9_.-])|"
    r"(?<![A-Za-z0-9_.-])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+(?=$|[^A-Za-z0-9_.-])|"
    r"\b[^\s/@]+@[^\s/@]+\.[A-Za-z]{2,}\b|"
    r"\b(?:ghp_|github_pat_|sk-[A-Za-z0-9]{8,}|AKIA[A-Z0-9]{12,})|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)",
    re.IGNORECASE,
)


def _repo_file(root: Path, value: Any, prefix: str) -> Path | None:
    """Resolve a strict repository-relative file under one approved prefix."""
    if not isinstance(value, str):
        return None
    rel = PurePosixPath(value)
    if (
        rel.is_absolute()
        or not rel.parts
        or ".." in rel.parts
        or "" in rel.parts
        or "\\" in value
        or not value.startswith(prefix)
    ):
        return None
    candidate = root.joinpath(*rel.parts)
    current = root
    try:
        for part in rel.parts:
            current = current / part
            if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
                return None
        root_resolved = root.resolve(strict=True)
        resolved_candidate = candidate.resolve(strict=True)
        resolved_candidate.relative_to(root_resolved)
    except (OSError, ValueError):
        return None
    return resolved_candidate if resolved_candidate.is_file() else None


def _accepted_tasks(root: Path) -> tuple[dict[str, tuple[bool, str]], list[str]]:
    """Map task IDs to checked state and owning milestone from canonical TASKS."""
    try:
        lines = (root / "TASKS.md").read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return {}, ["CANONICAL_TRACKER_UNAVAILABLE"]
    records: dict[str, tuple[bool, str]] = {}
    errors: list[str] = []
    milestone = ""
    for line in lines:
        heading = _MILESTONE.fullmatch(line)
        if heading:
            milestone = f"M{int(heading.group('number')):02d}"
            continue
        task = _TASK_LINE.match(line)
        if task is None:
            continue
        task_id = task.group("task")
        if task_id in records:
            errors.append("CANONICAL_TRACKER_TASK_ID_DUPLICATE")
        else:
            records[task_id] = (task.group("checked").lower() == "x", milestone)
    if not records:
        errors.append("CANONICAL_TRACKER_TASKS_MISSING")
    return records, errors


def _audit_is_accepted(path: Path, task_id: str) -> bool:
    """Require the referenced task-specific audit's final decision to pass."""
    if not path.name.startswith(f"{task_id}_CHATGPT_AUDIT_"):
        return False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return False
    decisions = [
        match.group(1).strip("`*_ ").upper()
        for line in lines
        if (match := re.search(r"(?i)\b(?:verdict|decision)\s*:\s*[*`_ ]*([A-Z][A-Z0-9_]+)", line))
    ]
    final_decision = decisions[-1] if decisions else ""
    accepted_decision = final_decision == "AUDITED_PASS" or bool(
        re.fullmatch(r"AUDITED_PASS(?:_[A-Z0-9]+(?:_[A-Z0-9]+)*)", final_decision)
    )
    return bool(task_id in "\n".join(lines) and accepted_decision)


def _latest_task_audit(root: Path, task_id: str) -> Path | None:
    """Return the unique highest-version task-specific audit without linked paths."""
    candidates: list[tuple[int, Path]] = []
    root = root.resolve()
    audit_root = root / "coordination/sessions"
    if not audit_root.is_dir() or audit_root.is_symlink():
        return None
    for path in audit_root.rglob(f"{task_id}_CHATGPT_AUDIT_V*.md"):
        if any(
            part.is_symlink() or getattr(part, "is_junction", lambda: False)()
            for part in (path, *path.parents)
            if part != root.parent and part != root
        ):
            continue
        match = re.fullmatch(re.escape(task_id) + r"_CHATGPT_AUDIT_V([0-9]+)\.md", path.name)
        if match is None:
            continue
        try:
            path.resolve(strict=True).relative_to(root)
        except (OSError, ValueError):
            continue
        candidates.append((int(match.group(1)), path.resolve()))
    if not candidates:
        return None
    latest_version = max(version for version, _ in candidates)
    latest = {path for version, path in candidates if version == latest_version}
    return next(iter(latest)) if len(latest) == 1 else None


def _matches_head_blob(root: Path, relative: str) -> bool:
    """Reject reviewed inputs whose worktree bytes differ from committed HEAD."""
    try:
        committed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", f"HEAD:{relative}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        working = subprocess.run(
            ["git", "-C", str(root), "hash-object", "--", str(root / relative)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return False
    return bool(committed) and committed == working


def _committed_evidence_matches_head(root: Path, entries: list[dict[str, Any]]) -> bool:
    paths = {"TASKS.md", "tools/release/offline_changelog.py"}
    for entry in entries:
        paths.add(entry["audit_ref"])
        paths.add(entry["source_ref"])
    return all(_matches_head_blob(root, relative) for relative in sorted(paths))


def _safe_note(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and value == value.strip()
        and "\\" not in value
        and len(value) <= 500
        and not any(ord(char) < 32 for char in value)
        and not _PRIVATE_OR_PATH.search(value)
    )


def _escape_markdown(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    for character in ("`", "*", "_", "[", "]", "(", ")", "<", ">", "#", "|", "!"):
        escaped = escaped.replace(character, f"\\{character}")
    return escaped


def validate_entries(root: Path, entries: Any) -> dict[str, Any]:
    """Check unique audited tasks, strict categories, and curated note evidence."""
    if not isinstance(entries, list) or not entries:
        return {"status": "BLOCKED", "errors": ["CHANGELOG_ENTRIES_MISSING"]}
    task_records, tracker_errors = _accepted_tasks(root)
    errors: set[str] = set(tracker_errors)
    seen: set[str] = set()
    validated: list[dict[str, Any]] = []
    fields = {
        "task_id",
        "category",
        "summary",
        "known_limitations",
        "audit_ref",
        "source_ref",
        "source_sha256",
    }
    for entry in entries:
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
        task_record = task_records.get(task_id)
        if task_record is None:
            errors.add("CHANGELOG_TASK_ID_UNKNOWN")
            continue
        accepted, milestone = task_record
        if not accepted:
            errors.add("CHANGELOG_TASK_NOT_ACCEPTED")

        category = entry["category"]
        if category not in _CATEGORIES:
            errors.add("CHANGELOG_CATEGORY_INVALID")
        summary = entry["summary"]
        limitations = entry["known_limitations"]
        if not _safe_note(summary):
            errors.add("CHANGELOG_SUMMARY_INVALID")
        if not isinstance(limitations, list) or any(not _safe_note(item) for item in limitations):
            errors.add("CHANGELOG_LIMITATIONS_INVALID")
            limitations = []
        if len(set(item for item in limitations if isinstance(item, str))) != len(limitations):
            errors.add("CHANGELOG_LIMITATION_DUPLICATE")

        audit_path = _repo_file(root, entry["audit_ref"], "coordination/sessions/")
        latest_audit = _latest_task_audit(root, task_id)
        if (
            audit_path is None
            or latest_audit is None
            or audit_path != latest_audit
            or not _audit_is_accepted(audit_path, task_id)
        ):
            errors.add("CHANGELOG_AUDIT_CITATION_UNACCEPTED")

        source_path = _repo_file(root, entry["source_ref"], "docs/packaging/release-notes/")
        if entry["source_ref"] != f"docs/packaging/release-notes/{task_id}.md":
            errors.add("CHANGELOG_SOURCE_TASK_ID_MISMATCH")
        expected = entry["source_sha256"]
        if source_path is None:
            errors.add("CHANGELOG_SOURCE_FRAGMENT_UNAVAILABLE")
        else:
            try:
                content = source_path.read_text(encoding="utf-8")
                actual = hashlib.sha256(source_path.read_bytes()).hexdigest()
            except (OSError, UnicodeError):
                errors.add("CHANGELOG_SOURCE_FRAGMENT_UNREADABLE")
                continue
            if (
                not isinstance(expected, str)
                or not _DIGEST.fullmatch(expected)
                or expected != actual
            ):
                errors.add("CHANGELOG_SOURCE_DIGEST_MISMATCH")
            if not _safe_note(summary) or summary not in content:
                errors.add("CHANGELOG_SUMMARY_NOT_IN_SOURCE_FRAGMENT")
            note_lines = content.splitlines()
            task_metadata = [line for line in note_lines if line.startswith("Task-ID:")]
            if (
                not note_lines
                or note_lines[0] != f"Task-ID: {task_id}"
                or task_metadata != [f"Task-ID: {task_id}"]
            ):
                errors.add("CHANGELOG_SOURCE_TASK_ID_MISMATCH")
            category_metadata = [line for line in note_lines if line.startswith("Category:")]
            if (
                category not in _CATEGORIES
                or note_lines[1:2] != [f"Category: {category}"]
                or category_metadata != [f"Category: {category}"]
            ):
                errors.add("CHANGELOG_CATEGORY_SOURCE_MISMATCH")
            for limitation in limitations:
                if limitation not in content:
                    errors.add("CHANGELOG_LIMITATION_NOT_IN_SOURCE_FRAGMENT")
        validated.append(
            {
                "task_id": task_id,
                "milestone": milestone,
                "category": category,
                "summary": summary,
                "known_limitations": limitations,
            }
        )
    result_errors = sorted(errors)
    return {
        "status": "CHANGELOG_INPUT_VALIDATION_PASS" if not result_errors else "BLOCKED",
        "errors": result_errors,
        "entry_count": len(entries),
        "entries": validated if not result_errors else [],
    }


def render_changelog(
    entries: list[dict[str, Any]], source_commit: str, train: dict[str, Any]
) -> str:
    """Render canonical Markdown with milestone/category/task numeric ordering."""
    if not _COMMIT_SHA.fullmatch(source_commit):
        raise ValueError("INVALID_SOURCE_COMMIT")
    versions = train.get("release_train", {}).get("versions")
    train_id = train.get("release_train", {}).get("id")
    if not isinstance(versions, dict) or not isinstance(train_id, str):
        raise ValueError("RELEASE_TRAIN_UNAVAILABLE")
    lines = [
        "# PackLab Offline Changelog Draft",
        "",
        "- Status: `PREPARATION_ONLY_NOT_RELEASE_AUTHORIZATION`",
        "> Preparation only. This document is not a release notice or release authorization.",
        "> M17 acceptance and PL-0368 release approval have not been granted.",
        "",
        f"- Source commit: `{source_commit}`",
        f"- Release train: `{train_id}`",
        f"- Studio: `{versions['studio']}`",
        f"- Capture: `{versions['capture']}` (build `{versions['capture_build']}`)",
        f"- PackScan schema: `{versions['packscan_schema']}`",
        "",
    ]
    milestone_ids = sorted(
        {entry["milestone"] for entry in entries}, key=lambda value: int(value[1:])
    )
    categories = (*_CATEGORIES, "Known limitations")
    for milestone in milestone_ids:
        lines.extend([f"## {milestone}", ""])
        for category in categories:
            if category == "Known limitations":
                categorized = [
                    (entry, limitation)
                    for entry in entries
                    if entry["milestone"] == milestone
                    for limitation in entry["known_limitations"]
                ]
            else:
                categorized = [
                    (entry, entry["summary"])
                    for entry in entries
                    if entry["milestone"] == milestone and entry["category"] == category
                ]
            if not categorized:
                continue
            lines.extend([f"### {category}", ""])
            categorized.sort(key=lambda pair: int(pair[0]["task_id"].split("-")[1]))
            lines.extend(
                f"- **{entry['task_id']}** — {_escape_markdown(text)}"
                for entry, text in categorized
            )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


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
    if not _COMMIT_SHA.fullmatch(commit):
        raise ValueError("INVALID_SOURCE_COMMIT")
    return commit


def _write_new_output(root: Path, target: Path, content: str) -> None:
    """Create a new draft only; never overwrite existing files or linked parents."""
    root = root.resolve(strict=True)
    output_path = target.absolute()
    if (
        output_path.exists()
        or output_path.is_symlink()
        or getattr(output_path, "is_junction", lambda: False)()
    ):
        raise ValueError("CHANGELOG_OUTPUT_ALREADY_EXISTS_OR_LINKED")
    for current in (output_path.parent, *output_path.parent.parents):
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
            raise ValueError("CHANGELOG_OUTPUT_PARENT_LINKED")
    try:
        output_path.resolve(strict=False).relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("CHANGELOG_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
    try:
        output_path.parent.resolve(strict=True)
    except OSError as exc:
        raise ValueError("CHANGELOG_OUTPUT_PARENT_UNAVAILABLE") from exc
    with output_path.open("x", encoding="utf-8", newline="\n") as output_file:
        output_file.write(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path, help="UTF-8 JSON array of curated task-note entries")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output", type=Path, required=True, help="Draft output path outside the repository"
    )
    args = parser.parse_args(argv)
    try:
        entries = json.loads(args.draft.read_text(encoding="utf-8"))
        root = args.repo.resolve(strict=True)
        validation = validate_entries(root, entries)
        if validation["status"] == "BLOCKED":
            print(json.dumps({"status": "BLOCKED", "errors": validation["errors"]}, sort_keys=True))
            return 2
        source_commit = _clean_source_commit(root)
        train = release_train_identity(root, source_commit)
        if not _committed_evidence_matches_head(root, validation["entries"]):
            raise ValueError("CHANGELOG_EVIDENCE_DIFFERS_FROM_HEAD")
        markdown = render_changelog(validation["entries"], source_commit, train)
        _write_new_output(root, args.output, markdown)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        reason = str(exc) if str(exc).isupper() else "CHANGELOG_DRAFT_UNREADABLE"
        print(json.dumps({"status": "BLOCKED", "errors": [reason]}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "status": "PREPARATION_ONLY_NOT_RELEASE_AUTHORIZATION",
                "entry_count": validation["entry_count"],
                "output_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
