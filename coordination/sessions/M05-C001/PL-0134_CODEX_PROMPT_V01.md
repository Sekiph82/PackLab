# PL-0134 — Codex Work Order V01

Task: **PL-0134 — Ingest resilience integration tests**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03/M04 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Reuse `packlab_core.packscan` as the package validation authority and keep the Windows receiver/import layer headless/testable so M06 can later provide the full PySide6 shell without rewriting ingest logic.

## Mandatory implementation

1. Build end-to-end integration fixtures/tests spanning iOS-transfer protocol artifacts and Windows ingest services without requiring physical devices.
2. Cover interrupted network transfer followed by resume, corrupt ZIP, missing photo/image payload, malformed/bad manifest, checksum mismatch, unsupported future schema and unsafe ZIP path.
3. Assert invalid/incomplete transfers never reach normal import/raw store and are quarantined or left resumable according to state.
4. Assert successful resumed transfer passes checksum verification, validation, immutable raw copy, dedupe index and import-report generation exactly once.
5. Include cancellation/retry and receiver restart during a resumable transfer.
6. Keep fixtures deterministic, bounded in size and safe for the normal locked test suite; no real network/internet dependency.

## Validation

Add behavior-bearing filesystem/network/application tests for success, failure, restart, corruption and exact conflict cases. Run focused tests, the full declared locked suite, Ruff/project/static checks, `git diff --check`, protected-file and privacy/secret checks. Do not claim physical iPhone/Windows LAN validation unless actually executed.

Create one implementation/evidence commit and a separate child log-only commit. User-facing repository links must be full GitHub URLs only.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
