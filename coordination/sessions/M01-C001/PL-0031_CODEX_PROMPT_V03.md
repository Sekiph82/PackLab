# PL-0031 — Codex Remediation Work Order V03

Task: **PL-0031 — Strict-marker documentation alignment remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_PROMPT_V03.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_LOG_V03.md

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

- `docs/development/TESTING.md`

Use only minimal adjacent files if technically unavoidable and justify them in the log.

## Mandatory requirements

1. Do not change the working pytest behavior unless a new defect is found.
2. Correct TESTING.md so it explicitly states strict unknown-marker validation is enabled by the --strict-markers addopt.
3. Remove any claim that the canonical configuration sets strict_markers = true.
4. Preserve unit/integration/slow registration, default not-slow behavior and explicit slow selection wording.
5. Re-run the marker tests and full Python regression suite; record evidence without editing prior audit/log artifacts.

## Validation

Re-run the still-valid original/V02 criteria, focused regression tests, full relevant M01 regression, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review, protected-file review and privacy/secrets review.

For unavailable native platform evidence, state the limitation rather than fabricating a pass.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_LOG_V03.md with synchronized start, implementation/evidence commit, exact files, defect mapping, commands/results, failures/fixes, scope/privacy, limitations and push evidence.

End with `AWAITING_AUDIT`. Do not self-audit.
