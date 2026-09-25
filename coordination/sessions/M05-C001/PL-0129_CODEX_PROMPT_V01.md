# PL-0129 — Codex Work Order V01

Task: **PL-0129 — Validate schema and checksums before extraction**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0129_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0129_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0129_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03/M04 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Reuse `packlab_core.packscan` as the package validation authority and keep the Windows receiver/import layer headless/testable so M06 can later provide the full PySide6 shell without rewriting ingest logic.

## Mandatory implementation

1. Make existing `packlab_core.packscan.validate_packscan` the authoritative validation gate for every manual/network ingest.
2. Validate ZIP safety, manifest schema/version, required entries, payload declarations, payload sizes, manifest SHA-256 values and checksums.json before any extraction/publication.
3. Unsupported future schema and malformed/corrupt packages must produce stable structured ingest error codes.
4. Extraction must occur only after validation succeeds and must retain the existing safe-path/atomic extraction guarantees.
5. Do not partially expose extracted payloads when validation fails.
6. Add integration tests proving validation precedes extraction for valid, future-version, checksum mismatch, unsafe path, missing required payload and corrupt ZIP packages.

## Validation

Add behavior-bearing filesystem/network/application tests for success, failure, restart, corruption and exact conflict cases. Run focused tests, the full declared locked suite, Ruff/project/static checks, `git diff --check`, protected-file and privacy/secret checks. Do not claim physical iPhone/Windows LAN validation unless actually executed.

Create one implementation/evidence commit and a separate child log-only commit. User-facing repository links must be full GitHub URLs only.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
