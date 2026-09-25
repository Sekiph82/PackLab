# PL-0128 — Codex Work Order V01

Task: **PL-0128 — Windows network receiver for paired iPhone transfers**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0128_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0128_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0128_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03/M04 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Reuse `packlab_core.packscan` as the package validation authority and keep the Windows receiver/import layer headless/testable so M06 can later provide the full PySide6 shell without rewriting ingest logic.

## Mandatory implementation

1. Implement a headless PackLab Studio receiver service using the PL-0121 V1 protocol, PL-0122 pairing identity, PL-0123 TLS/auth and PL-0124 resumable transfer store.
2. Receiver must bind only to configured local-network interfaces/port, advertise its receiver instance identity, and expose lifecycle start/stop/status without requiring the future M06 shell.
3. Completed verified packages must enter a dedicated Capture Inbox staging directory and then the same ingest service used by PL-0127.
4. Never extract/import an unauthenticated, incomplete or checksum-unverified transfer.
5. Support clean shutdown/restart while preserving resumable transfer checkpoints.
6. Add loopback integration tests for paired transfer, unpaired rejection, shutdown/restart resume, verified inbox handoff and concurrent distinct transfer IDs.

## Validation

Add behavior-bearing filesystem/network/application tests for success, failure, restart, corruption and exact conflict cases. Run focused tests, the full declared locked suite, Ruff/project/static checks, `git diff --check`, protected-file and privacy/secret checks. Do not claim physical iPhone/Windows LAN validation unless actually executed.

Create one implementation/evidence commit and a separate child log-only commit. User-facing repository links must be full GitHub URLs only.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
