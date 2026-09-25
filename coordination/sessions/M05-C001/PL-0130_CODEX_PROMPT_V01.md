# PL-0130 — Codex Work Order V01

Task: **PL-0130 — Quarantine corrupt or unsupported scans**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0130_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0130_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0130_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03/M04 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Reuse `packlab_core.packscan` as the package validation authority and keep the Windows receiver/import layer headless/testable so M06 can later provide the full PySide6 shell without rewriting ingest logic.

## Mandatory implementation

1. Implement a dedicated quarantine store outside normal imported/raw evidence directories.
2. On corrupt/unsupported ingest, atomically preserve the original package when safely readable plus a structured quarantine record containing stable error code, source channel, capture ID if safely known, package digest if computable, timestamp and redacted diagnostics.
3. Never partially extract quarantined packages into the normal ingest tree.
4. Quarantine filenames/paths must be collision-safe and must not trust package-provided path fragments.
5. Repeated quarantine of the same bytes must be deterministic/idempotent enough to avoid uncontrolled duplicates while retaining event history as appropriate.
6. Add tests for corrupt ZIP, future schema, checksum mismatch, malicious filename/path, repeated quarantine and no-normal-import-artifacts.

## Validation

Add behavior-bearing filesystem/network/application tests for success, failure, restart, corruption and exact conflict cases. Run focused tests, the full declared locked suite, Ruff/project/static checks, `git diff --check`, protected-file and privacy/secret checks. Do not claim physical iPhone/Windows LAN validation unless actually executed.

Create one implementation/evidence commit and a separate child log-only commit. User-facing repository links must be full GitHub URLs only.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
