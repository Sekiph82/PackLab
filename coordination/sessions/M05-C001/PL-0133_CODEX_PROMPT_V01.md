# PL-0133 — Codex Work Order V01

Task: **PL-0133 — Deduplicate imports by capture ID and checksum**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03/M04 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Reuse `packlab_core.packscan` as the package validation authority and keep the Windows receiver/import layer headless/testable so M06 can later provide the full PySide6 shell without rewriting ingest logic.

## Mandatory implementation

1. Implement an ingest index keyed by manifest `capture_id` plus whole-package SHA-256.
2. Same capture_id + same digest must be idempotent and return the existing import rather than creating duplicate raw copies/projects.
3. Same capture_id + different digest is an identity conflict and must never overwrite the existing import; return/quarantine a stable conflict result with both non-secret digests.
4. Different capture_id + same digest must be treated according to an explicit fail-closed policy and never silently create ambiguous duplicate authority.
5. The index must be crash-safe/atomic and reconstructable or verifiable against raw ingest metadata.
6. Add tests for same/same idempotency, same-ID/different-digest conflict, different-ID/same-digest ambiguity, index restart/reload and concurrent duplicate attempts.

## Validation

Add behavior-bearing filesystem/network/application tests for success, failure, restart, corruption and exact conflict cases. Run focused tests, the full declared locked suite, Ruff/project/static checks, `git diff --check`, protected-file and privacy/secret checks. Do not claim physical iPhone/Windows LAN validation unless actually executed.

Create one implementation/evidence commit and a separate child log-only commit. User-facing repository links must be full GitHub URLs only.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
