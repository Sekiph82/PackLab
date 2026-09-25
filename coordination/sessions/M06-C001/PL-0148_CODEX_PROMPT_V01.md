# PL-0148 — Codex Work Order V01

Task: **PL-0148 — Interrupted-processing project recovery**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0148_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0148_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0148_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

For PL-0151/0152, use measured local evidence and a single viewport adapter boundary. Do not hard-code the rest of Studio to an experimental backend before the spike decision is frozen.

## Mandatory implementation

1. Persist project-scoped recovery markers/checkpoints for in-progress jobs and editable state without treating incomplete derived output as authoritative.
2. On reopen after abnormal termination, classify interrupted jobs/artifacts as resumable, restart-required or invalid according to explicit metadata.
3. Recovery must never mutate raw evidence and must quarantine/delete only PackLab-owned temporary/partial derived artifacts according to policy.
4. Expose recovery summary/actions to the shell through ProjectManager/JobManager services, not modal logic embedded in widgets.
5. Add tests for clean close, crash marker, resumable job, invalid partial artifact, recovery accept/discard and repeated reopen idempotency.

## Validation

Use deterministic filesystem/offscreen tests and reproducible benchmark commands. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Declare/lock any viewport dependency and record license impact. Create one implementation/evidence commit and separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
