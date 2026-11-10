import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { applyOwnerAnswers, claimCurrentTask, writeTracker } from "./task-queue.mjs";
import { parseTaskState } from "./task-state.mjs";

function tracker({ status = "READY", marker = " ", next = "Continue the explicit task." } = {}) {
  return `# PackLab\n\n## Project Status\n- Current Milestone: M19\n- Current Sprint: M19-S01\n- Current Task: PL-0001 — First task\n- Current Task Status: ${status}\n- Next Task/Action: ${next}\n- Required Actor: CODEX\n- Tracking Repository: Sekiph82/PackLab\n- Tracking Branch: main\n\n## Tasks\n- [${marker}] **PL-0001** First task\n- [ ] **PL-0002** Second task **Mandatory pre-read:** docs/implementation/example.md\n\n## Questions for Owner\n- Q-PL-0001-1 | May the task use a local fixture? | TASK: PL-0001\n\n## Owner Decisions\n`;
}

test("claims only the explicit READY task and leaves checkbox order alone", () => {
  const source = tracker();
  const claimed = claimCurrentTask(source);
  const state = parseTaskState(claimed.source);
  assert.equal(claimed.changed, true);
  assert.equal(state.currentTask.id, "PL-0001");
  assert.equal(state.currentTaskStatus, "IN_PROGRESS");
  assert.equal(state.tasks[1].marker, " ");
  assert.equal(state.tasks[1].title, "Second task");
});

test("does not claim a blocked explicit task", () => {
  assert.throws(() => claimCurrentTask(tracker({ status: "BLOCKED", marker: "!" })), /cannot be claimed/);
});

test("applies only the exact open owner question and matching task", () => {
  const source = tracker({ status: "BLOCKED", marker: "!" });
  const result = applyOwnerAnswers(source, [
    { questionId: "Q-PL-0001-1", taskId: "PL-0002", answer: "wrong task" },
    { questionId: "Q-PL-0001-1", taskId: "PL-0001", answer: "Use an isolated local fixture." },
  ]);
  const state = parseTaskState(result.source);
  assert.deepEqual(result.applied, [{ questionId: "Q-PL-0001-1", taskId: "PL-0001" }]);
  assert.equal(state.currentTaskStatus, "READY");
  assert.equal(state.tasks[0].marker, " ");
  assert.match(result.source, /Q-PL-0001-1 \| TASK: PL-0001 \| ANSWER:/);
  assert.equal(state.questions.length, 0);
});

test("rejects blank matching answers and ignores stale answers", () => {
  const source = tracker();
  assert.throws(() => applyOwnerAnswers(source, [{ questionId: "Q-PL-0001-1", taskId: "PL-0001", answer: "  " }]), /blank/);
  const stale = applyOwnerAnswers(source, [{ questionId: "Q-OLD", taskId: "PL-0001", answer: "No longer open." }]);
  assert.deepEqual(stale.applied, []);
  assert.equal(stale.source, source);
});

test("tracker writer preserves concurrent owner edits and existing lock/temp files", async () => {
  const root = await mkdtemp(join(tmpdir(), "packlab-task-queue-test-"));
  try {
    const original = tracker();
    await writeFile(join(root, "TASKS.md"), original, "utf8");
    const newer = `${original}\nOwner edit\n`;
    await writeFile(join(root, "TASKS.md"), newer, "utf8");
    await assert.rejects(writeTracker(root, original, "queue rewrite\n"), /changed during queue processing/);
    assert.equal(await readFile(join(root, "TASKS.md"), "utf8"), newer);

    await mkdir(join(root, "TASKS.md.codex-queue.lock"));
    await assert.rejects(writeTracker(root, newer, `${newer}claimed\n`), /holds the TASKS.md lock/);
    assert.equal(await readFile(join(root, "TASKS.md"), "utf8"), newer);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
