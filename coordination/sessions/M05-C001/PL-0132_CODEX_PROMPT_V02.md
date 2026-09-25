# PL-0132 — Codex Remediation Work Order V02

Task: **PL-0132 — Complete import-report golden matrix**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CODEX_LOG_V02.md

## Authorization

TASKS.md must authorize `M05-BATCH-002 / READY / CODEX`. Preserve accepted PL-0127, PL-0129 and PL-0131, all accepted M03/M04 behavior, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Preserve useful V01 implementation. Close only the independent-audit gaps below.

## Mandatory remediation

1. Preserve ImportReport and atomic ImportReportStore.
2. Add deterministic golden/report tests for both manual/drop and network imports.
3. Cover calibration present and absent, optional mask present/absent, optional diagnostics present/absent, payload counts and deterministic warning ordering.
4. Verify network report accepts only non-secret receiver/transfer provenance, portable locations remain relative, and private absolute paths/secrets are redacted.
5. Prove invalid packages never receive a successful import report.

## Validation

Add behavior-bearing tests at the production-used ingest/receiver seam. Run focused tests, full locked suite, relevant static/project checks, Ruff/compileall, `git diff --check`, protected-file and privacy/secret checks.

Create one implementation/evidence commit and then one separate log-only commit. Every user-facing repository reference must be a full GitHub URL.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
