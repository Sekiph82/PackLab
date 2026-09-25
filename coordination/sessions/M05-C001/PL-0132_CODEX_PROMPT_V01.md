# PL-0132 — Codex Work Order V01

Task: **PL-0132 — Import report generation**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03/M04 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Reuse `packlab_core.packscan` as the package validation authority and keep the Windows receiver/import layer headless/testable so M06 can later provide the full PySide6 shell without rewriting ingest logic.

## Mandatory implementation

1. Generate a structured import report after successful validated ingest using authoritative manifest/photo/calibration data.
2. Report must include capture_id, schema version, source channel, package SHA-256, image count/bytes, photo metadata count, capture mode, device summary, calibration profile/reference availability, optional payload counts, warnings and ingest/raw-store locations expressed without private absolute-path leakage in portable report content.
3. Include transfer verification/pairing provenance only as non-secret receiver/transfer identifiers when network imported.
4. Persist the report atomically next to the ingest record and make it serializable for later M06 Capture Inbox UI.
5. Warnings must distinguish owner-required calibration, optional missing data and actual validation errors; successful report generation must not relabel invalid packages as imported.
6. Add golden/report tests for manual and network imports, calibration present/absent, optional diagnostics/masks, warning ordering and privacy redaction.

## Validation

Add behavior-bearing filesystem/network/application tests for success, failure, restart, corruption and exact conflict cases. Run focused tests, the full declared locked suite, Ruff/project/static checks, `git diff --check`, protected-file and privacy/secret checks. Do not claim physical iPhone/Windows LAN validation unless actually executed.

Create one implementation/evidence commit and a separate child log-only commit. User-facing repository links must be full GitHub URLs only.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
