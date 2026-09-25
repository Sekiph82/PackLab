# PL-0132 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0132_CHATGPT_AUDIT_V01.md is fully addressed.
6. Preserve ImportReport and atomic ImportReportStore.
7. Add deterministic golden/report tests for both manual/drop and network imports.
8. Cover calibration present and absent, optional mask present/absent, optional diagnostics present/absent, payload counts and deterministic warning ordering.
9. Verify network report accepts only non-secret receiver/transfer provenance, portable locations remain relative, and private absolute paths/secrets are redacted.
10. Prove invalid packages never receive a successful import report.
11. Tests exercise the actual production-used seam rather than only a disconnected helper.
12. Invalid/incomplete/untrusted data never reaches normal import authority.
13. Security/privacy claims are truthful and no secrets/private keys enter Git/logs/package data.
14. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
