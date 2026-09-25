# PL-0131 — Codex Work Order V01

Task: **PL-0131 — Immutable raw-ingest copy**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0131_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0131_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0131_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03/M04 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Reuse `packlab_core.packscan` as the package validation authority and keep the Windows receiver/import layer headless/testable so M06 can later provide the full PySide6 shell without rewriting ingest logic.

## Mandatory implementation

1. After validation and before derived processing, create an immutable-by-policy raw ingest copy of the original `.packscan` bytes in a content-addressed or otherwise collision-safe raw store.
2. Record package SHA-256, capture_id, original source channel and ingest timestamp in adjacent immutable ingest metadata.
3. Never perform later extraction/processing by modifying the raw package in place; working/derived data must use separate locations.
4. If filesystem permissions support it, mark raw evidence read-only as defense in depth, but digest verification remains the authoritative immutability check.
5. On existing identical raw digest, reuse/idempotently reference the existing evidence; on conflicting identity, fail closed according to PL-0133.
6. Add tests for byte-for-byte raw copy, digest verification, attempted mutation detection, idempotent same-digest ingest and no overwrite on conflict.

## Validation

Add behavior-bearing filesystem/network/application tests for success, failure, restart, corruption and exact conflict cases. Run focused tests, the full declared locked suite, Ruff/project/static checks, `git diff --check`, protected-file and privacy/secret checks. Do not claim physical iPhone/Windows LAN validation unless actually executed.

Create one implementation/evidence commit and a separate child log-only commit. User-facing repository links must be full GitHub URLs only.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
