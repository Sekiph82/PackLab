# PL-0025 — Codex Remediation Work Order V02

Task: **PL-0025 — Root task-runner final M01 integration remediation**

Repository: https://github.com/Sekiph82/PackLab
Original/updated audit finding: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CHATGPT_AUDIT_V02.md
This remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CODEX_PROMPT_V02.md
Frozen remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CHATGPT_AUDIT_CRITERIA_V02.md
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CODEX_LOG_V02.md

## Authority

Root TASKS.md must authorize the M01 remediation batch and Required Actor CODEX. Read AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, coordination/AUDIT_POLICY.md, the relevant V01 prompt/criteria/log/audit history, and current files before work.

Before material work run:
- git fetch origin main --prune
- git rev-list --left-right --count HEAD...origin/main
- git status --porcelain

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md.

## Authorized files

- `tools/tasks.py`
- `tests/tools/test_tasks.py`
- `docs/development/TASK_RUNNER.md`

Minimal adjacent files are allowed only when technically necessary for the remediation and must be justified in the log.

## Mandatory remediation requirements

1. Make the root task runner the real single M01 entry point for bootstrap, test, lint, type-check, diagnostics and build-oriented commands.
2. On Windows, bootstrap must safely dispatch scripts/bootstrap_windows.ps1 using an argument-array subprocess; on unsupported platforms report a clear nonzero/deferred state until their bootstrap exists.
3. Test, lint and type-check must run through the locked uv project environment and must not depend on globally installed pytest/Ruff/mypy or shell activation.
4. Diagnostics must remain safe and direct; build remains explicitly deferred until its owning milestone.
5. Preserve shell=False/argument-array execution and child exit-code propagation.
6. Add focused tests for command construction, Windows bootstrap dispatch, uv missing/unavailable handling, exit propagation, and no global PATH dependency.

## Full regression

Re-run the original task's still-valid mandatory criteria, not only the named defect. Preserve all accepted behavior from sibling M01 tasks. Run task-relevant focused tests/checks, git diff --check, git diff -- TASKS.md, exact changed-file review, protected-file review and privacy/secrets review.

For Swift/Xcode tasks, static project/source evidence on Windows is allowed but native Xcode/simulator/device success must not be fabricated.

## Handoff

Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CODEX_LOG_V02.md. Record synchronized start, implementation/evidence commit, exact files changed, defect-to-fix mapping, validation expected/failure/actual results, regressions, privacy/scope review, platform limitations and push evidence.

End with `AWAITING_AUDIT`. Do not self-audit. Do not start M02.
