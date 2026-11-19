import test from "node:test";
import assert from "node:assert/strict";
import { parseTaskRows, parseTaskState } from "./task-state.mjs";

function tracker({ current = "PL-0001 — First task", status = "READY", marker = " ", actor = "CLAUDE_CODE_SOLE_ORCHESTRATOR" } = {}) {
  return `# PackLab\n\n## Project Status\n- Current Milestone: M19\n- Current Sprint: M19-S01\n- Current Task: ${current}\n- Current Task Status: ${status}\n- Next Task/Action: Continue the explicit task.\n- Required Actor: ${actor}\n- Tracking Repository: Sekiph82/PackLab\n- Tracking Branch: main\n\n## Tasks\n- [${marker}] **PL-0001** First task\n- [ ] **PL-0002** Second task **Mandatory pre-read:** docs/implementation/example.md\n\n# Execution Rules (revised)\n- [ ] **PL-0003** not part of the ledger\n`;
}

test("an explicit READY task validates and is matched by exact title", () => {
  const state = parseTaskState(tracker());
  assert.deepEqual(state.currentTask, { id: "PL-0001", title: "First task" });
  assert.equal(state.currentTaskStatus, "READY");
  assert.equal(state.totalTasks, 2);
  assert.throws(() => parseTaskState(tracker({ current: "PL-0001 — First tasks" })), /exactly one canonical task row/);
});

test("an idle tracker validates, names no task, and cannot hide an in-progress row", () => {
  const state = parseTaskState(tracker({ current: "none dependency-ready", status: "anything" }));
  assert.equal(state.currentTask, null);
  assert.equal(state.currentTaskStatus, "IDLE");
  assert.throws(() => parseTaskState(tracker({ current: "none dependency-ready", marker: "~" })), /idle tracker/);
  for (const current of ["none PL-0001 — First task", "NONE", "None-of-the-above", "nonexistent"]) {
    assert.throws(() => parseTaskState(tracker({ current })), /must identify one PL task/);
  }
});

test("only CLAUDE is an authorized actor", () => {
  for (const actor of ["CODEX", "CLAUDEX", "OWNER", "CLAUDE-CODEX", "CLAUDE; CODEX", "CLAUDE_CODEX_RUNNER"]) {
    assert.throws(() => parseTaskState(tracker({ actor })), /must authorize CLAUDE/);
  }
});

test("repository and branch authority are exact", () => {
  assert.throws(() => parseTaskState(tracker().replace("Sekiph82/PackLab", "attacker/PackLab")), /Sekiph82\/PackLab on main/);
  assert.throws(() => parseTaskState(tracker().replace("Tracking Branch: main", "Tracking Branch: dev")), /Sekiph82\/PackLab on main/);
});

test("malformed or indented task rows are rejected, not ignored", () => {
  for (const row of ["- [X] **PL-0002** Upper", "  - [~] **PL-0002** Indented", "- [~]**PL-0002** Tight", "* [~] **PL-0002** Star"]) {
    const source = tracker().replace("- [ ] **PL-0002** Second task **Mandatory pre-read:** docs/implementation/example.md", row);
    assert.throws(() => parseTaskRows(source), /Malformed canonical task row/);
  }
});
