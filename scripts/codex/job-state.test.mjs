import test from "node:test";
import assert from "node:assert/strict";
import { transitionJob, validateJobState } from "./job-state.mjs";

const initial = {
  taskId: "PL-0435",
  title: "Implement isolated visual-reference boundary",
  stage: "SPEC",
  updatedAt: "2026-10-22T00:00:00.000Z",
};
const digest = "a".repeat(64);

test("job moves through local evidence stages without independent-review claims", () => {
  const build = transitionJob(initial, "BUILD", {}, new Date("2026-10-22T01:00:00Z"));
  const verify = transitionJob(build, "VERIFY", {
    validationEvidence: { path: "coordination/sessions/M19-C001/VALIDATION_CRITERIA_V01.md", sha256: digest, result: "passed" },
  }, new Date("2026-10-22T02:00:00Z"));
  const done = transitionJob(verify, "LOCAL_COMPLETE", {
    logEvidence: { path: "coordination/sessions/M19-C001/PL-0435_CODEX_LOG_V01.md", sha256: digest },
  }, new Date("2026-10-22T03:00:00Z"));
  assert.equal(done.stage, "LOCAL_COMPLETE");
  assert.equal(done.updatedAt > verify.updatedAt, true);
  assert.equal(done.independentReview, undefined);
});

test("verification and completion require local evidence", () => {
  assert.throws(() => transitionJob(initial, "VERIFY"), /one step/);
  const build = transitionJob(initial, "BUILD");
  assert.throws(() => transitionJob(build, "VERIFY"), /validation evidence/);
});

test("blocked work needs a reason and an explicit resume change", () => {
  const blocked = transitionJob(initial, "BLOCKED", { blockedReason: "PySide6 is unavailable" });
  assert.throws(() => transitionJob(blocked, "BUILD"), /explicit environment\/state change/);
  const resumed = transitionJob(blocked, "BUILD", { resumeReason: "Existing supported environment became available" });
  assert.equal(resumed.stage, "BUILD");
  assert.equal(resumed.blockedReason, undefined);
});

test("local metadata rejects hosted, independent-review, and release claims", () => {
  assert.throws(() => validateJobState({ ...initial, hostedVerification: true }), /cannot claim hosted/);
  assert.throws(() => validateJobState({ ...initial, independentReview: "pass" }), /cannot claim hosted/);
  assert.throws(() => validateJobState({ ...initial, releaseReady: true }), /cannot claim hosted/);
});
