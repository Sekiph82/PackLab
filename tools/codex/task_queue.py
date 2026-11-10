"""Read and validate PackLab's explicit TASKS.md queue without mutating it."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit

TASK_ID = r"[A-Z][A-Z0-9]*-\d+(?:\.\d+)?"
TASK_ROW = re.compile(rf"^- \[([ x~!])\] (?:\*\*)?({TASK_ID})(?:\*\*)?(?: — | )(.+)$")
CURRENT_TASK = re.compile(rf"^({TASK_ID}) — (.+)$")


@dataclass(frozen=True)
class QueueState:
    repository: str
    branch: str
    task_id: str
    title: str
    status: str
    next_action: str
    task_count: int
    completed_count: int


def _field(source: str, name: str) -> str:
    matches = re.findall(rf"^- {re.escape(name)}:\s*(.+)$", source, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"{name} must appear exactly once in TASKS.md")
    return matches[0].strip()


def parse_task_rows(source: str) -> list[tuple[str, str, str]]:
    lines = source.splitlines()
    headings = [index for index, line in enumerate(lines) if line == "## Tasks"]
    if len(headings) != 1:
        raise ValueError("TASKS.md must contain exactly one canonical ## Tasks ledger")
    end = next(
        (index for index in range(headings[0] + 1, len(lines)) if lines[index] == "# Execution Rules"),
        len(lines),
    )
    rows: list[tuple[str, str, str]] = []
    for line in lines[headings[0] + 1 : end]:
        match = TASK_ROW.fullmatch(line)
        if match:
            rows.append((match.group(1), match.group(2), match.group(3)))
        elif line.startswith("- [") and re.search(r"(?:\*\*)?[A-Z][A-Z0-9]*-\d", line):
            raise ValueError(f"Malformed canonical task row: {line}")
    if not rows:
        raise ValueError("The canonical task ledger is empty")
    identifiers = [row[1] for row in rows]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Task IDs must be unique")
    return rows


def validate_queue(source: str, expected_task: str | None = None) -> QueueState:
    current = CURRENT_TASK.fullmatch(_field(source, "Current Task"))
    if not current:
        raise ValueError("Current Task must explicitly identify one task ID and title")
    task_id, title = current.groups()
    if expected_task and task_id != expected_task:
        raise ValueError(f"Expected {expected_task}; canonical Current Task is {task_id}")

    status = _field(source, "Current Task Status").split(" / ", 1)[0]
    required_actor = _field(source, "Required Actor")
    if required_actor.split(" ", 1)[0] != "CODEX":
        raise ValueError("Required Actor must authorize CODEX")
    branch = _field(source, "Tracking Branch")
    repository = _field(source, "Tracking Repository")
    next_action = _field(source, "Next Task/Action")
    rows = parse_task_rows(source)
    matches = [row for row in rows if row[1] == task_id and row[2] == title]
    if len(matches) != 1:
        raise ValueError(f"Current Task {task_id} must match exactly one task row")

    expected_marker = {"READY": " ", "IN_PROGRESS": "~", "BLOCKED": "!"}.get(status)
    if expected_marker is None:
        raise ValueError(f"Unsupported Current Task Status: {status}")
    if matches[0][0] != expected_marker:
        raise ValueError(f"Current Task Status {status} does not match its task row")
    in_progress = [row[1] for row in rows if row[0] == "~"]
    if len(in_progress) > 1 or (status == "IN_PROGRESS" and in_progress != [task_id]):
        raise ValueError("Only the explicit Current Task may be marked in progress")
    if status != "IN_PROGRESS" and in_progress:
        raise ValueError("A non-active Current Task cannot coexist with an in-progress task row")
    parsed_repository = urlsplit(repository)
    valid_repository = repository == "Sekiph82/PackLab" or (
        parsed_repository.scheme == "https"
        and parsed_repository.hostname == "github.com"
        and parsed_repository.username is None
        and parsed_repository.password is None
        and not parsed_repository.query
        and not parsed_repository.fragment
        and parsed_repository.path.rstrip("/") in {"/Sekiph82/PackLab", "/Sekiph82/PackLab.git"}
    )
    if (
        branch != "main"
        or not valid_repository
    ):
        raise ValueError("Queue authority must target Sekiph82/PackLab on main")

    return QueueState(
        repository=repository,
        branch=branch,
        task_id=task_id,
        title=title,
        status=status,
        next_action=next_action,
        task_count=len(rows),
        completed_count=sum(row[0] == "x" for row in rows),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--task", help="Require this exact explicit Current Task ID")
    parser.add_argument("--json", action="store_true", help="Print the validated queue as JSON")
    args = parser.parse_args(argv)
    try:
        state = validate_queue((args.root / "TASKS.md").read_text(encoding="utf-8"), args.task)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(asdict(state), ensure_ascii=False, sort_keys=True))
    else:
        print(f"TASKS.md valid: {state.task_id} ({state.status}); {state.completed_count}/{state.task_count} accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
