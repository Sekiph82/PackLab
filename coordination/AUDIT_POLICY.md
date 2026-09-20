# PackLab Audit Policy

Canonical repository: https://github.com/Sekiph82/PackLab

## Tracking authority

Root `TASKS.md` is the only live project-status tracker and H!veAI current-state surface.

**ChatGPT is the sole writer of root `TASKS.md` lifecycle/progress/task-closure state.**

Codex must not edit root `TASKS.md` during implementation, validation, or handoff. Codex communicates implementation state only through the matching `CODEX_LOG_VNN.md` and its required `AWAITING_AUDIT` response.

ChatGPT independently audits GitHub state, writes the matching `CHATGPT_AUDIT_VNN.md`, then updates root `TASKS.md` after every audit cycle.

## Separation of duties

### Codex responsibilities

1. Read the active prompt and matching audit criteria.
2. Verify the task is still authorized by root `TASKS.md`.
3. Implement only the frozen scope.
4. Run all required tests/checks.
5. Record exact evidence in `CODEX_LOG_VNN.md`.
6. Commit and push authorized implementation/evidence changes.
7. Return `AWAITING_AUDIT` and stop.

Codex must not:
- self-audit;
- create `CHATGPT_AUDIT_VNN.md`;
- declare `AUDITED_PASS`;
- edit `TASKS.md`;
- invent completion state;
- silently broaden scope;
- continue to the next task.

### ChatGPT responsibilities

1. Read current root `TASKS.md` and relevant session/history.
2. Freeze each implementation pass in a versioned Codex prompt and matching criteria.
3. After a Codex log arrives, inspect the actual GitHub commit/diff/files.
4. Treat Codex-run tests as implementer evidence, not independent proof.
5. Independently cross-check or rerun checks where available.
6. Inspect negative paths, boundary behavior, false-positive test risk, architecture, security and scope leakage.
7. Write a versioned `CHATGPT_AUDIT_VNN.md`.
8. Update `coordination/AUDIT_INDEX.md` with reusable learnings when relevant.
9. Update root `TASKS.md` after every audit, whether PASS, FAIL, CHANGES_REQUIRED, BLOCKED or OWNER_REQUIRED.
10. On correction, publish the next versioned `CODEX_PROMPT_VNN.md` and matching criteria before handing work back.

## Owner-authorized milestone batch execution

Root `TASKS.md` may explicitly authorize a milestone batch governed by:

https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md

This is an execution-throughput exception only. It does not weaken independent audit.

During an authorized batch:

1. every child PL task has its own frozen Codex prompt and matching ChatGPT criteria before execution;
2. every child produces its own implementation/evidence boundary and Codex log;
3. Codex may continue sequentially only while the current child is validation-green and no STOP condition exists;
4. Codex must stop the entire batch on a failed child validation, blocker, owner gate, architecture contradiction, unsafe divergence, privacy/security issue, or task-state mismatch;
5. Codex still cannot edit `TASKS.md`, create ChatGPT audit artifacts, assign audit verdicts, or start the next milestone;
6. the batch ends with a master Codex log and `AWAITING_MILESTONE_AUDIT`;
7. ChatGPT independently audits every child, writes child audit artifacts, updates `TASKS.md` to audited truth, and writes a milestone audit only after child audits close.

A child implementation being validation-green is not equivalent to `AUDITED_PASS`.

## Evidence levels

### E0 - Claim

An assertion without reproducible proof. Examples: "implemented", "looks correct", "tests should pass". E0 can never establish audit PASS.

### E1 - Codex-run check

Codex actually runs a command/check and records the result. Useful implementer evidence, but not independent audit proof.

### E2 - Reproducible Codex evidence

Codex records:
- exact command;
- starting/current commit state;
- expected result;
- explicit failure condition;
- actual result;
- affected task/criterion;
- relevant file/output evidence.

E2 is strong implementation evidence but remains correlated with the implementer.

### E3 - ChatGPT independent audit evidence

ChatGPT inspects actual GitHub state, source, diffs, logs and tests and independently cross-checks where possible.

Only ChatGPT audit artifacts may assign:
- `AUDITED_PASS`;
- `AUDITED_FAIL`;
- `CHANGES_REQUIRED`;
- `NOT_INDEPENDENTLY_VERIFIED`;
- `BLOCKED`;
- `OWNER_REQUIRED`.

### E4 - Owner decision

Human-controlled product/design/physical acceptance decisions remain owner-controlled until explicitly decided by the owner.

## Codex log contract

For prompt:

`CODEX_PROMPT_VNN.md`

Codex must create exactly:

`CODEX_LOG_VNN.md`

The log must include at minimum:
- cycle ID and version;
- prompt URL/path;
- criteria URL/path;
- starting commit;
- final implementation commit;
- repository synchronization result;
- inputs read;
- files changed/added/deleted;
- implementation details;
- every required command/test individually;
- expected result and explicit failure condition for material checks;
- actual results;
- negative/boundary/regression coverage;
- failures encountered and fixes made;
- known limitations/unverified assumptions;
- secrets/privacy check;
- scope check;
- commit/push evidence;
- final handoff `AWAITING_AUDIT`.

A green aggregate test count does not substitute for a missing prompt-mandated command.

## Strict audit standard

`AUDITED_PASS` means only that no material defect was found under the frozen criteria and available evidence. It does not mean bug-free or production-perfect.

For every material audit ChatGPT must check:

1. **Prompt compliance** — every mandatory item is implemented or explicitly blocked.
2. **Criteria closure** — every numbered criterion has a disposition.
3. **Actual diff** — audit the GitHub commit/diff, not merely the Codex summary.
4. **Architecture** — ownership/layering/contracts are respected.
5. **Negative paths** — invalid, missing, interrupted, corrupt and boundary inputs are considered where relevant.
6. **Test sensitivity** — tests would fail if the intended behavior were broken; tautological or implementation-mirroring tests are not sufficient.
7. **Regression** — existing behavior required by earlier tasks remains intact.
8. **Security/privacy** — no credentials, signing material, private scans, confidential supplier material or inappropriate generated data enters the public repo.
9. **Determinism/provenance** — dimensional/reconstruction/export behavior records units, versions and provenance when relevant.
10. **Scope control** — no opportunistic future-task implementation is accepted merely because it is useful.
11. **H!veAI truth** — root `TASKS.md` is updated by ChatGPT to exactly reflect the audit outcome and next actor/action.

## Audit verdict rules

### AUDITED_PASS

All mandatory frozen criteria are satisfied, no unresolved material defect remains, and any unrerun runtime evidence is explicitly disclosed.

### CHANGES_REQUIRED / AUDITED_FAIL

Any mandatory criterion is false, materially incomplete, unsafe, untested in a required way, or contradicted by actual code/diff.

ChatGPT must:
- keep the task unchecked;
- update `TASKS.md` to correction state;
- write exact findings in `CHATGPT_AUDIT_VNN.md`;
- issue the next remediation prompt/criteria version.

### BLOCKED

Required dependency/environment/input prevents implementation or audit. `TASKS.md` must show the blocker and required actor/action.

### OWNER_REQUIRED

A physical/product/design decision needs the owner. AI must not manufacture approval.

## Continuous audit learning

`coordination/AUDIT_INDEX.md` is ChatGPT-owned reusable audit memory.

Feedback loop:

`ChatGPT finding -> AUDIT_INDEX learning -> TASKS update -> next prompt/criteria -> Codex implementation/log -> next ChatGPT audit`

`AUDIT_INDEX.md` is evidence memory only and never a live tracker.

## First-sync exception

The owner has explicitly declared GitHub `main` correct for the initial local alignment of `C:\Users\sekip\Desktop\PackLab`.

A prompt may authorize `git reset --hard origin/main` and `git clean -fd` only for that verified first bootstrap, after checking Git root and remote identity. It must not use `git clean -fdx`.

After bootstrap is proven complete, default synchronization returns to fetch/compare/fast-forward-only behavior and unexpected divergence must stop the session unless the owner explicitly authorizes replacement.
