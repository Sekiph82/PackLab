# PL-0132 — Codex Remediation Work Order V03

Task: **PL-0132 — Complete manual/network mask/diagnostics report matrix**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0132_CODEX_LOG_V03.md

## Authorization

TASKS.md must authorize `M05-BATCH-003 / READY / CODEX`. Preserve accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 plus accepted M03/M04. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Read the V02 audit first. Preserve useful implementation and close exactly these remaining gaps.

## Mandatory remediation

1. Preserve ImportReport, safe provenance filtering and atomic ImportReportStore.
2. Use separate fixtures/imports/assertions for manual/drop and network reports so one digest-keyed network report does not overwrite the only evidence for the manual report before it is inspected.
3. Add a valid PackScan with an optional mask payload and verify optional_payload_counts plus absence of optional_mask_missing warning.
4. Retain mask-absent, diagnostics-present, diagnostics-absent, calibration-present and calibration-absent coverage with deterministic warning ordering.
5. Assert network provenance keeps only receiver_id/transfer_id and strips secrets/private paths.
6. Add an invalid-package case proving no successful report file/state is created.

## Validation

Tests must drive production-used seams, not a disconnected helper/static grep. Run focused tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and secrets/privacy checks.

Create one implementation/evidence commit and one separate V03 log-only commit. All user-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
