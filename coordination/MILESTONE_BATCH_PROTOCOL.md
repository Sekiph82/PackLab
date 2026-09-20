# PackLab Milestone Batch Execution Protocol

Status: owner-authorized coordination protocol.

Canonical repository: https://github.com/Sekiph82/PackLab
Canonical branch: `main`
Canonical live tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

## Purpose

PackLab may execute a whole milestone through one ChatGPT-authored master Codex work order when root `TASKS.md` explicitly authorizes a milestone batch.

The batch model improves throughput without weakening task-level auditability.

## Invariants

1. Permanent `PL-xxxx` task IDs remain unchanged.
2. Root `TASKS.md` remains the only live H!veAI/project-status tracker.
3. ChatGPT remains the only actor that may mark a task complete or update task lifecycle state.
4. Codex may execute multiple child tasks sequentially only when the current root tracker explicitly names the milestone master prompt.
5. Every child task must have its own frozen Codex prompt and matching ChatGPT audit criteria before Codex begins the batch.
6. Every child task must produce its own Codex log.
7. Every child task must have a distinct implementation/evidence commit boundary.
8. Codex does not self-audit and does not create ChatGPT audit artifacts.
9. Codex does not edit root `TASKS.md`.
10. ChatGPT later audits each child task independently, then writes one milestone-level audit after all child audits are closed.

## Execution sequence

For each child task in the master prompt order:

1. read the child prompt and matching frozen criteria;
2. verify the repository still satisfies the master batch authorization;
3. implement only the child scope;
4. run every child validation;
5. run exact changed-file and protected-file checks;
6. commit the child implementation/evidence;
7. create the matching child `CODEX_LOG`;
8. commit/push the child log;
9. verify remote visibility;
10. continue to the next child only when the child implementation validations are green and no STOP condition exists.

Codex is allowed to continue from one child to the next without a ChatGPT audit in between only because the owner explicitly authorized milestone-batch execution. This does not mean any child task is accepted before ChatGPT audit.

## Stop conditions

Codex must stop the entire batch immediately if any child task encounters:

- repository/task authorization mismatch;
- tracked local divergence that cannot be fast-forwarded safely;
- a frozen mandatory validation failure that cannot be corrected within that child scope;
- an architecture contradiction requiring an ADR outside the authorized child scope;
- a privacy/security risk;
- a dependency or owner decision that blocks the task;
- any need to modify root `TASKS.md`;
- scope that would require starting a future milestone.

When stopped, Codex writes the current child log and the master log with `BATCH_STOPPED`, pushes only authorized evidence, returns `AWAITING_MILESTONE_AUDIT`, and stops.

## Commit discipline

Preferred topology for each child:

1. one implementation/evidence commit;
2. one child-log-only commit.

A child that requires no substantive file change may have one log-only evidence commit if the frozen child prompt explicitly permits evidence-only closure.

After the final child log, Codex creates exactly one master-log-only publication commit.

## Logging

Each child log must include:

- child task ID;
- child prompt full GitHub URL;
- child criteria full GitHub URL;
- synchronized starting commit for that child;
- implementation/evidence commit;
- files read;
- files changed;
- exact validation commands;
- expected result and failure condition for material checks;
- actual results;
- failures and fixes;
- scope/privacy/security review;
- push/remote evidence;
- known limitations;
- `READY_FOR_INDEPENDENT_AUDIT`.

The master log must index every child task, implementation commit, child log commit, child log full GitHub URL, and whether the batch completed or stopped.

The master log ends with `AWAITING_MILESTONE_AUDIT`.

## Audit

ChatGPT performs:

1. one strict independent audit per child task against that task's frozen criteria;
2. actual GitHub diff/source/commit inspection for every child;
3. root tracker updates only after audit decisions;
4. a milestone audit only after all child audits have closed;
5. milestone closure only when every mandatory child task is independently accepted.

A batch run is therefore execution batching, not audit batching.


## Audit checkpoint persistence

For milestone-batch audits, ChatGPT must persist each child audit before beginning the next child audit.

Required sequence for every child:

1. read the current canonical GitHub state;
2. independently audit exactly one child against its frozen criteria;
3. create and push that child's `PL-xxxx_CHATGPT_AUDIT_VNN.md`;
4. verify the audit file is visible on GitHub `main`;
5. only then begin the next child audit.

ChatGPT must not hold multiple completed child verdicts only in conversation or temporary working context while continuing deeper into the milestone. GitHub is the durable audit checkpoint after every child.

If a long audit session is interrupted, resumes must start from current GitHub `main` and the already-published child audit artifacts. Previously published child audits are not recomputed unless new evidence invalidates them.

After all child audits are persisted, ChatGPT may write the milestone-level audit and update root `TASKS.md`.
