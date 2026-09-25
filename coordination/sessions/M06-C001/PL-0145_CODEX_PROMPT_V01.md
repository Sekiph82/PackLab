# PL-0145 — Codex Work Order V01

Task: **PL-0145 — Project metadata and revision identifiers**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0145_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0145_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0145_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

M06 project state must preserve M05 raw-ingest authority and keep UI separate from project/domain services.

## Mandatory implementation

1. Define versioned project metadata with immutable project UUID, human name, created/updated timestamps, schema version and monotonically advancing revision identifiers.
2. Revision identifiers must change only on authoritative editable-state commits, not mere UI navigation.
3. Persist metadata atomically and validate identity/revision on reopen.
4. Do not expose secrets/private absolute source paths in portable metadata.
5. Add tests for creation, revision increment, reopen identity, stale revision conflict and malformed metadata.

## Validation

Use deterministic filesystem/offscreen UI tests. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Update declared/locked dependencies reproducibly if needed. Create one implementation/evidence commit and one separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
