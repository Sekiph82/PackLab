# PL-0134 — Codex Remediation Work Order V02

Task: **PL-0134 — True cross-language transfer-to-ingest integration closure**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_LOG_V02.md

## Authorization

TASKS.md must authorize `M05-BATCH-002 / READY / CODEX`. Preserve accepted PL-0127, PL-0129 and PL-0131, all accepted M03/M04 behavior, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Preserve useful V01 implementation. Close only the independent-audit gaps below.

## Mandatory remediation

1. Preserve the existing deterministic M05 integration fixtures and Windows ingest assertions.
2. After PL-0121–PL-0126 remediation, drive the authoritative iOS/cross-language transfer client/protocol seam into the real HTTPS receiver rather than calling receiver methods with token_authenticated=True.
3. Exercise pairing, pinned/authenticated transport, partial transfer, sender/receiver restart/resume, cancel/retry, checksum verification and exactly-once ingest through raw/index/report.
4. Add an invalid PackScan fixture with valid controls/checksum index structure but the declared image/photo payload specifically missing, so missing-image failure is isolated rather than masked by missing checksums.json.
5. Retain corrupt ZIP, bad manifest, internal checksum mismatch, future schema and unsafe path quarantine tests; invalid/untrusted data must never reach raw authority.

## Validation

Add behavior-bearing tests at the production-used ingest/receiver seam. Run focused tests, full locked suite, relevant static/project checks, Ruff/compileall, `git diff --check`, protected-file and privacy/secret checks.

Create one implementation/evidence commit and then one separate log-only commit. Every user-facing repository reference must be a full GitHub URL.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
