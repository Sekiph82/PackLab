# PL-0147 — Codex Work Order V01

Task: **PL-0147 — Non-destructive operation history**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0147_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0147_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0147_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

For PL-0151/0152, use measured local evidence and a single viewport adapter boundary. Do not hard-code the rest of Studio to an experimental backend before the spike decision is frozen.

## Mandatory implementation

1. Implement append-only logical operation history for user edits with operation ID, project revision, timestamp, operation type, parameters/reference IDs and reversible/non-reversible marker.
2. History must never store mutable raw payload copies or secrets; reference project-relative assets/state.
3. Provide undo/redo cursor semantics only for explicitly reversible operations and never rewrite prior history entries.
4. Persist history atomically and validate revision continuity on reopen.
5. Add tests for append, undo/redo, non-reversible barrier, restart/reload, revision mismatch and tamper/corrupt history.

## Validation

Use deterministic filesystem/offscreen tests and reproducible benchmark commands. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Declare/lock any viewport dependency and record license impact. Create one implementation/evidence commit and separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
