from __future__ import annotations

import pytest

from tools.codex.task_queue import parse_task_rows, validate_queue


def tracker(current: str = "PL-0438 — Integrate autonomous queue", status: str = "IN_PROGRESS", row: str = "~") -> str:
    return f"""# PackLab

## Project Status
- Current Milestone: M16
- Current Sprint: M16-C002 — Queue
- Current Task: {current}
- Current Task Status: {status} / OWNER_AUTHORIZED
- Next Task/Action: Continue the explicit task only.
- Required Actor: CODEX implements
- Tracking Repository: https://github.com/Sekiph82/PackLab
- Tracking Branch: main

## Tasks
### Sprint M16-C002
- [{row}] **PL-0438** Integrate autonomous queue
- [ ] **FVL-11.008** Other project's task; must not be accepted here

# Execution Rules
"""


def test_accepts_packlab_ids_and_uses_only_the_explicit_current_task() -> None:
    state = validate_queue(tracker())
    assert state.task_id == "PL-0438"
    assert state.status == "IN_PROGRESS"
    assert state.task_count == 2
    assert state.completed_count == 0


def test_accepts_periodic_ids_used_by_formulab_without_confusing_project_authority() -> None:
    source = tracker("FVL-11.008 — FormuLab only", "READY", " ").replace(
        "FVL-11.008** Other project's task; must not be accepted here",
        "FVL-11.009** Other project's task; must not be accepted here",
    )
    with pytest.raises(ValueError, match="must match exactly one"):
        validate_queue(source)


def test_rejects_current_task_and_status_disagreement() -> None:
    with pytest.raises(ValueError, match="does not match its task row"):
        validate_queue(tracker(status="READY"))


def test_rejects_inferred_tasks_and_multiple_in_progress_rows() -> None:
    with pytest.raises(ValueError, match="Only the explicit Current Task"):
        validate_queue(tracker().replace("- [ ] **FVL-11.008**", "- [~] **FVL-11.008**"))


def test_rejects_duplicate_ids_and_malformed_task_rows() -> None:
    with pytest.raises(ValueError, match="must be unique"):
        parse_task_rows(tracker().replace("FVL-11.008", "PL-0438"))
    with pytest.raises(ValueError, match="Malformed canonical task row"):
        parse_task_rows(tracker().replace("- [ ] **FVL-11.008**", "- [?] **FVL-11.008**"))


def test_task_selector_cannot_override_canonical_current_task() -> None:
    with pytest.raises(ValueError, match="canonical Current Task is PL-0438"):
        validate_queue(tracker(), expected_task="PL-0437")


def test_rejects_a_repository_url_that_only_contains_packlab_as_a_substring() -> None:
    source = tracker().replace(
        "https://github.com/Sekiph82/PackLab",
        "https://github.com/attacker/Sekiph82/PackLab",
    )
    with pytest.raises(ValueError, match="must target Sekiph82/PackLab on main"):
        validate_queue(source)


def test_blocked_current_task_is_explicit_and_cannot_hide_an_in_progress_row() -> None:
    source = tracker("PL-0438 — Integrate autonomous queue", "BLOCKED", "!")
    assert validate_queue(source).status == "BLOCKED"
    with pytest.raises(ValueError, match="non-active Current Task"):
        validate_queue(source.replace("- [ ] **FVL-11.008**", "- [~] **FVL-11.008**"))
