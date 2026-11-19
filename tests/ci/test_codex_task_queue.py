from __future__ import annotations

import pytest
from tools.codex.task_queue import parse_task_rows, validate_queue


def tracker(
    current: str = "PL-0438 — Integrate autonomous queue",
    status: str = "IN_PROGRESS",
    row: str = "~",
) -> str:
    return f"""# PackLab

## Project Status
- Current Milestone: M16
- Current Sprint: M16-C002 — Queue
- Current Task: {current}
- Current Task Status: {status} / OWNER_AUTHORIZED
- Next Task/Action: Continue the explicit task only.
- Required Actor: CLAUDE_CODE implements
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


def test_idle_tracker_is_valid_without_inferring_a_task() -> None:
    state = validate_queue(
        tracker("none dependency-ready; all open tasks externally gated", "X", " ")
    )
    assert state.task_id is None and state.title is None
    assert state.status == "IDLE"
    with pytest.raises(ValueError, match="canonical Current Task is None"):
        validate_queue(tracker("none dependency-ready", "X", " "), expected_task="PL-0438")


def test_idle_tracker_cannot_hide_an_in_progress_row() -> None:
    with pytest.raises(ValueError, match="idle tracker cannot have an in-progress"):
        validate_queue(tracker("none dependency-ready", "X", "~"))


def test_only_claude_is_an_authorized_actor() -> None:
    for actor in ("CODEX implements", "CLAUDEX", "OWNER", "CLAUDE-CODEX", "CLAUDE; CODEX"):
        source = tracker().replace("CLAUDE_CODE implements", actor)
        with pytest.raises(ValueError, match="must authorize CLAUDE"):
            validate_queue(source)


@pytest.mark.parametrize(
    "current",
    ["none PL-0438 — Integrate autonomous queue", "None-of-the-above", "NONE", "nonexistent"],
)
def test_idle_marker_is_strict_and_cannot_name_a_task(current: str) -> None:
    with pytest.raises(ValueError, match="explicitly identify one task"):
        validate_queue(tracker(current, "X", " "))


def test_current_task_title_must_match_the_row_exactly() -> None:
    with pytest.raises(ValueError, match="must match exactly one task row"):
        validate_queue(tracker("PL-0438 — Integrate autonomous queues"))


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("- Tracking Branch: main", "- Tracking Branch: dev"),
        ("https://github.com/Sekiph82/PackLab", "https://user@github.com/Sekiph82/PackLab"),
        ("https://github.com/Sekiph82/PackLab", "https://github.com:443/Sekiph82/PackLab"),
        ("https://github.com/Sekiph82/PackLab", "http://github.com/Sekiph82/PackLab"),
    ],
)
def test_repository_and_branch_authority_is_exact(old: str, new: str) -> None:
    with pytest.raises(ValueError, match="must target Sekiph82/PackLab on main"):
        validate_queue(tracker().replace(old, new))


@pytest.mark.parametrize(
    "row",
    [
        "- [X] **FVL-11.008** Upper-case marker",
        "  - [~] **FVL-11.008** Indented in-progress row",
        "- [~]**FVL-11.008** Missing space",
        "* [~] **FVL-11.008** Star bullet",
    ],
)
def test_malformed_or_indented_rows_are_rejected_not_ignored(row: str) -> None:
    source = tracker().replace(
        "- [ ] **FVL-11.008** Other project's task; must not be accepted here", row
    )
    with pytest.raises(ValueError, match="Malformed canonical task row"):
        parse_task_rows(source)


def test_ledger_ends_at_a_suffixed_execution_rules_heading() -> None:
    source = tracker().replace(
        "# Execution Rules", "# Execution Rules (owner-revised)\n- [ ] **PL-9999** after the ledger"
    )
    assert [row[1] for row in parse_task_rows(source)] == ["PL-0438", "FVL-11.008"]
