# PL-0133 — ChatGPT Remediation Audit Criteria V02

All criteria mandatory.

1. M05-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0127, PL-0129 and PL-0131 remain accepted; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/session/ingest architecture is preserved.
5. PL-0133_CHATGPT_AUDIT_V01.md is fully addressed.
6. Preserve atomic IngestIndex behavior and same/same idempotency.
7. Replace string-only identity conflicts with a structured conflict containing capture ID plus existing/incoming non-secret digests and stable conflict code.
8. Define the ImportService fail-closed/quarantine disposition for same-ID/different-digest and different-ID/same-digest conflicts without overwriting raw authority.
9. Add index verification/reconstruction from immutable RawEvidenceStore metadata so missing/corrupt index state can be rebuilt or deterministically rejected.
10. Add tests for both conflict classes, digest evidence, restart/reload, concurrent duplicates, missing index reconstruction and corrupt index recovery/fail-closed behavior.
11. Tests exercise the actual production-used seam rather than only a disconnected helper.
12. Invalid/incomplete/untrusted data never reaches normal import authority.
13. Security/privacy claims are truthful and no secrets/private keys enter Git/logs/package data.
14. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
