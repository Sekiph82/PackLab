# PL-0076 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. Codex does not edit TASKS.md/audits or start M04.
4. Prior passing behavior is preserved.
5. Previous audit PL-0076_CHATGPT_AUDIT_V03.md is fully addressed.
6. Add a test utility/fixture that validates the encoded Swift PackScan photo metadata document against the authoritative schemas/packscan/photo-metadata.schema.json contract or a mechanically generated equivalent fixture, so schema drift cannot pass local Swift-only checks.
7. Fix ISO mapping so numeric value/source/unit are permitted only for schema-allowed available/estimated states; unavailable/not_recorded must reject all forbidden evidence.
8. Exercise available, estimated, unavailable and not_recorded for focal length, exposure, ISO and white balance, including all minimum/maximum numeric boundaries.
9. Keep app-only lens/timestamp fields outside the strict photo wire object.
10. Tests exercise the actual production seam or its injected driver, not only a neighboring helper.
11. Regressions and git diff --check are clean/truthful.
12. Log records exact commits/files/results and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
