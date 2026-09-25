# M05-BATCH-005 — Full-Suite Validation Gate Stabilization

Milestone: **M05 — Transfer & Ingest**
Purpose: **Clear the final mandatory locked-suite blocker without reopening product logic**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Canonical tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
Previous master audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_VALIDATION_GATE_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_VALIDATION_GATE_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_VALIDATION_GATE_CODEX_LOG_V01.md

## Authorization gate

TASKS.md must show:
- Current Milestone: M05
- Current Sprint: M05-BATCH-005
- Current Task: M05-BATCH-005
- Current Task Status: READY
- Required Actor: CODEX
- the final six M05 children still unchecked: PL-0119, PL-0121, PL-0122, PL-0125, PL-0126, PL-0134
- all other 10 M05 children checked
- M03/M04 accepted
- PL-0068 unchecked / OWNER_REQUIRED
- M06 not started
- Next Task/Action pointing to this prompt

Otherwise stop `TASK_STATE_MISMATCH`.

Before work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Fast-forward only if safe. Never reset, rebase, force-push, destructively clean or stash owner work.

Never edit TASKS.md or ChatGPT audit artifacts. Never start M06. Never fabricate PL-0068 evidence.

## Scope

The six remaining M05 product remediations were independently found functionally acceptable in:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_V03.md

Do **not** rewrite those product surfaces unless a regression is discovered.

The only known blocker is the exact full locked test command:

`PYTHONPATH=core/src;apps/windows-studio/src python -m pytest -q`

Codex reported one aggregate-only failure:

`tests/core/test_subprocess_runner.py::test_windows_liveness_query_is_non_destructive`

The same test passes in isolation.

## Required diagnosis

Inspect:
- `tests/core/test_subprocess_runner.py`
- `core/src/packlab_core/subprocess_runner.py`
- full-suite ordering/load/environment around the liveness test

The current test helper runs Windows `tasklist` with a hard 1.0-second timeout and converts `TimeoutExpired` into `False`, which can misclassify a still-running process as dead under aggregate load.

Determine the actual failure trace before changing anything.

## Acceptable remediation

Make the Windows liveness proof deterministic and still non-destructive.

Preferred properties:
- do not kill, signal or mutate the queried process;
- do not hide genuine dead-process detection;
- do not simply skip the test;
- do not mark the test xfail;
- do not delete the assertion;
- do not globally weaken timeouts without evidence;
- do not introduce shell=True;
- do not change M05 transfer/ingest product behavior.

A bounded retry/query strategy, a direct non-destructive Windows process-state query, or another deterministic Windows-native proof is acceptable if well tested.

If production subprocess code must change because the same underlying race exists there, make the smallest safe change and add focused evidence. Otherwise keep the fix test-infrastructure-only.

## Required validation

1. Run the failing test repeatedly, not once:
   - at least 10 consecutive executions or an equivalent repeated pytest invocation.
2. Run the surrounding file:
   - `python -m pytest -q tests/core/test_subprocess_runner.py`
3. Run the focused M05 transfer/TLS/wire command from Batch-004 and keep it green.
4. Run the **exact full locked suite**:
   - `PYTHONPATH=core/src;apps/windows-studio/src python -m pytest -q`
   - it must exit 0 with **zero failures**.
5. Run Ruff/compileall for any changed Python files.
6. Run `git diff --check`.
7. Verify TASKS.md and ChatGPT audits untouched.
8. Review secrets/private keys/signing/private scans.
9. Verify no accepted M05 behavior regressed.

Do not use “passes isolated” as final evidence. The aggregate suite itself must be green.

## Publication

Create:
- one implementation/evidence commit for the liveness stabilization;
- one separate master log-only commit.

No new per-child product implementation is required unless a regression is actually found.

The master log must include:
- exact failure traceback observed before the fix;
- root cause;
- exact changed files;
- repeated-test evidence;
- exact full-suite zero-failure result;
- focused M05 regression result;
- exact implementation commit;
- exact log commit;
- explicit statement that the six product task surfaces were not rewritten unless applicable.

All user-facing repository references must be full GitHub URLs.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not self-audit.
