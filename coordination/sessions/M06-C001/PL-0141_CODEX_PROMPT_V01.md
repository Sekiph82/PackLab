# PL-0141 — Codex Work Order V01

Task: **PL-0141 — Crash report/log bundle**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0141_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0141_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0141_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

M06 project state must preserve M05 raw-ingest authority and keep UI separate from project/domain services.

## Mandatory implementation

1. Create a crash/diagnostic bundle service that collects bounded application logs, version/build info, OS/Python/Qt info, active project/job summaries and recent structured errors.
2. Exclude secrets, bearer tokens, pairing codes, private keys, signing material and raw/private package payloads; redact absolute user paths where practical.
3. Bundle creation must be explicit and local, deterministic, bounded in size and safe if some sources are missing/corrupt.
4. Write bundles atomically to a user-selected or app diagnostics location without requiring network upload.
5. Add tests for normal bundle, missing logs, bounded truncation, redaction, no-secret content and atomic publication.

## Validation

Use deterministic filesystem/offscreen UI tests. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Update declared/locked dependencies reproducibly if needed. Create one implementation/evidence commit and one separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
