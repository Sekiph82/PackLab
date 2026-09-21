# PL-0035 — Codex Remediation Work Order V03

Task: **PL-0035 — Non-destructive Windows process-tree proof remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_PROMPT_V03.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_LOG_V03.md

## Gate

Read AGENTS.md, TASKS.md, the blocking audit above, this prompt and its criteria. TASKS.md must authorize M01-REMEDIATION-BATCH-002 / CODEX.

Before material work:
```
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
git status --porcelain
```

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Do not start M02.

## Authorized files

- `core/src/packlab_core/subprocess_runner.py`
- `tests/core/test_subprocess_runner.py`

Use only minimal adjacent files if technically unavoidable and justify them in the log.

## Mandatory requirements

1. Keep the runner-owned Windows taskkill /PID <root> /T /F strategy unless a concrete defect requires a minimal change.
2. Replace Windows os.kill(pid, 0) liveness checking with a non-destructive Windows process query. Do not add psutil or another dependency.
3. Timeout and cancellation regressions must prove the parent and spawned child are already gone without the assertion itself terminating them.
4. Add a negative/control proof showing the liveness helper detects a live process without killing it, and that the regression would fail for parent-only cleanup.
5. Inspect taskkill completion. A nonzero/timeout/start failure must not be silently treated as successful tree cleanup; surface bounded structured cleanup error evidence while still attempting safe root cleanup.
6. Preserve POSIX process-group behavior, shell=False, argument arrays, streaming callbacks and structured ProcessResult semantics.

## Validation

Re-run the still-valid original/V02 criteria, focused regression tests, full relevant M01 regression, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review, protected-file review and privacy/secrets review.

For unavailable native platform evidence, state the limitation rather than fabricating a pass.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_LOG_V03.md with synchronized start, implementation/evidence commit, exact files, defect mapping, commands/results, failures/fixes, scope/privacy, limitations and push evidence.

End with `AWAITING_AUDIT`. Do not self-audit.
