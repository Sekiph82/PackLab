# PL-0133 — Codex Remediation Work Order V02

Task: **PL-0133 — Structured identity conflicts and index reconstruction closure**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0133_CODEX_LOG_V02.md

## Authorization

TASKS.md must authorize `M05-BATCH-002 / READY / CODEX`. Preserve accepted PL-0127, PL-0129 and PL-0131, all accepted M03/M04 behavior, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Preserve useful V01 implementation. Close only the independent-audit gaps below.

## Mandatory remediation

1. Preserve atomic IngestIndex behavior and same/same idempotency.
2. Replace string-only identity conflicts with a structured conflict containing capture ID plus existing/incoming non-secret digests and stable conflict code.
3. Define the ImportService fail-closed/quarantine disposition for same-ID/different-digest and different-ID/same-digest conflicts without overwriting raw authority.
4. Add index verification/reconstruction from immutable RawEvidenceStore metadata so missing/corrupt index state can be rebuilt or deterministically rejected.
5. Add tests for both conflict classes, digest evidence, restart/reload, concurrent duplicates, missing index reconstruction and corrupt index recovery/fail-closed behavior.

## Validation

Add behavior-bearing tests at the production-used ingest/receiver seam. Run focused tests, full locked suite, relevant static/project checks, Ruff/compileall, `git diff --check`, protected-file and privacy/secret checks.

Create one implementation/evidence commit and then one separate log-only commit. Every user-facing repository reference must be a full GitHub URL.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
