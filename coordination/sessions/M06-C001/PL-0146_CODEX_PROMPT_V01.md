# PL-0146 — Codex Work Order V01

Task: **PL-0146 — Autosave editable project state**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0146_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0146_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0146_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

M06 project state must preserve M05 raw-ingest authority and keep UI separate from project/domain services.

## Mandatory implementation

1. Implement debounced/transactional autosave for editable project state using ProjectManager/revision contracts.
2. Autosave must never write into raw evidence and must be atomic with crash-safe temp/replace behavior.
3. Concurrent/stale writes must be detected using project revision/base revision rather than silently overwriting newer state.
4. Expose save status/error state to the shell without blocking the GUI thread.
5. Add tests for debounce/coalescing, atomic save, stale conflict, write failure, shutdown flush policy and raw-store non-mutation.

## Validation

Use deterministic filesystem/offscreen UI tests. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Update declared/locked dependencies reproducibly if needed. Create one implementation/evidence commit and one separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
