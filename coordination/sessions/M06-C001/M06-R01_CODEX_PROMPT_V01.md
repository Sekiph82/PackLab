# M06-R01 — Codex Remediation Work Order V01

Tasks: **PL-0138, PL-0140, PL-0141, PL-0144, PL-0145, PL-0146, PL-0147, PL-0148, PL-0149**

Repository:
https://github.com/Sekiph82/PackLab

Branch: `main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Source audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/CHATGPT_AUDIT_V01.md

Remediation audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/M06-R01_CHATGPT_AUDIT_CRITERIA_V01.md

This prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/M06-R01_CODEX_PROMPT_V01.md

Required remediation log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/M06-R01_CODEX_LOG_V01.md

Original master work order:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md

Original master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization

Root TASKS.md must authorize M06-R01 / CHANGES_REQUIRED / CODEX and point to this prompt and its criteria.

Do not edit:
- https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/CHATGPT_AUDIT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/M06-R01_CHATGPT_AUDIT_CRITERIA_V01.md
- any other ChatGPT audit artifact.

Do not start PL-0150 through PL-0157.
Do not start M07.
Keep PL-0068 OWNER_REQUIRED.
Preserve accepted M03–M05 behavior.

## Phase 0 — Recover the publication boundary safely

The last builder handoff reported:

- local `main`: `fea9830505e457cb777dc6885ba06453fbc17478`
- then-remote `origin/main`: `0442a3fea64d5133f9ccdac788444fbe0407caf4`
- worktree clean
- local branch three commits ahead
- the three local-only commits contain the missing PL-0145 log, PL-0149 log and master batch-stop log.

Since that handoff, ChatGPT has legitimately advanced remote `main` with independent audit/coordination artifacts. Therefore a simple push or fast-forward may no longer be possible.

First run:

`git fetch origin main --prune`

`git status --porcelain`

`git rev-list --left-right --count HEAD...origin/main`

`git log --oneline --decorate --graph --max-count=20 --all`

Rules:

1. Worktree must be clean before reconciliation.
2. Never reset, rebase, force-push, destructively clean or discard commits.
3. Verify the local-only commits are the expected publication artifacts and that remote-only commits are ChatGPT audit/criteria/prompt/tracker commits.
4. If and only if the divergence is exactly that expected safe shape, merge `origin/main` into local `main` with a normal non-destructive merge commit.
5. Resolve only trivial non-overlapping coordination-file conflicts. If any source-code conflict, TASKS.md ownership conflict, or unexpected commit is present, stop and report `REPOSITORY_DIVERGENCE_STOP`.
6. Push the reconciled `main`.
7. Verify these URLs resolve on remote before remediation:
   - https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0145_CODEX_LOG_V01.md
   - https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0149_CODEX_LOG_V01.md
   - https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_LOG_V01.md

Do not rewrite those logs just to change audit outcome. Preserve truthful existing evidence.

## Phase 1 — Read before editing

Read in full:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/CHATGPT_AUDIT_V01.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/M06-R01_CHATGPT_AUDIT_CRITERIA_V01.md

Then re-read the frozen criteria for every affected task:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0138_CHATGPT_AUDIT_CRITERIA_V01.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0140_CHATGPT_AUDIT_CRITERIA_V01.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0141_CHATGPT_AUDIT_CRITERIA_V01.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0144_CHATGPT_AUDIT_CRITERIA_V01.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0145_CHATGPT_AUDIT_CRITERIA_V01.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0146_CHATGPT_AUDIT_CRITERIA_V01.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0147_CHATGPT_AUDIT_CRITERIA_V01.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0148_CHATGPT_AUDIT_CRITERIA_V01.md

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0149_CHATGPT_AUDIT_CRITERIA_V01.md

PL-0145 requires publication verification only unless reinspection finds a real source defect. Do not churn accepted source without evidence.

## Phase 2 — Remediate exact audit findings

### PL-0138

Fix production preference restore so saved window geometry is sanitized against the current available screen/work area before `setGeometry`. Add a production-seam offscreen test that stores an unreachable window position and proves Studio restores to a usable location.

### PL-0140

Keep `packlab_core.subprocess_runner` as the only process-tree cancellation authority. Add deterministic tests through `OwnedSubprocessJob` and the production cancellation seam. Prove cancellation affects the PackLab-owned process only and does not terminate an unrelated process.

### PL-0141

Integrate diagnostic bundle creation through the real Studio/project service seam. Include bounded/privacy-safe build/runtime info, current project summary when present, active jobs and structured errors. Do not include raw payloads, secrets, pairing codes, signing material or private absolute paths. Add production-seam tests rather than service-only tests.

### PL-0144

Bind route/workspace availability to `ProjectManager` open/closed state with stable service-driven state, not widget-local shadow authority. Also make switching/new-project behavior failure-safe: an active-job close veto must be checked before a replacement project destination is published on disk.

### PL-0146

Make authoritative editable-state + project-revision publication transactionally crash-safe. The previous valid state/revision must remain authoritative, or recovery must be deterministic, if a failure occurs between staged state and metadata publication. Add injected-failure tests that prove no silent state/revision mismatch becomes authoritative.

### PL-0147

Preserve append-only logical history semantics while making persistence atomically publish a complete valid history state. Add tests for partial/injected write failure, reopen, revision gaps, tamper and non-reversible barriers.

### PL-0148

Wire recovery into `ProjectManager` and Studio lifecycle. Opening/starting a project must establish recovery authority; abnormal reopen must expose recovery classification/actions; clean close must mark recovery clean. Accept/discard must remain limited to PackLab-owned temp/derived artifacts and never mutate raw evidence. Add production-seam lifecycle tests.

### PL-0149

Add stale-state reopen persistence coverage and an explicit deterministic query API suitable for UI badges/job planning. Preserve direct/transitive invalidation, unrelated-input isolation, parameter invalidation and missing/tampered upstream detection. Do not mutate raw evidence.

## Phase 3 — Validation

Run focused tests for every remediated task, then the exact full locked suite.

Also run all repository-required checks including:
- Ruff
- mypy where configured/relevant
- compileall
- project/static checks
- `git diff --check`
- protected-file review
- secrets/privacy review
- dependency/lock/license review
- generated/binary/signing-material review

Do not claim native/GPU behavior that was not executed.

## Phase 4 — Commit and publish

Keep remediation changes reviewable. Do not squash away the recovered pre-existing local log commits.

Publish the remediation implementation/evidence commits, then create a separate log-only commit containing:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/M06-R01_CODEX_LOG_V01.md

The log must include:
- publication-recovery result and reconciliation commit SHA if one was required;
- exact status for each affected task PL-0138, PL-0140, PL-0141, PL-0144, PL-0145, PL-0146, PL-0147, PL-0148 and PL-0149;
- changed files;
- focused test commands/results;
- exact full-suite result;
- static/project check results;
- implementation/evidence commit SHAs;
- log-only commit SHA when available;
- residual limitations;
- full GitHub URLs only.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Stop. Do not edit TASKS.md. Do not self-audit. Do not continue to PL-0150.
