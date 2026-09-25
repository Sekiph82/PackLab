# PL-0132 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan validation/session authority is reused rather than duplicated.
5. PL-0132 satisfies the frozen scope.
6. Generate a structured import report after successful validated ingest using authoritative manifest/photo/calibration data.
7. Report must include capture_id, schema version, source channel, package SHA-256, image count/bytes, photo metadata count, capture mode, device summary, calibration profile/reference availability, optional payload counts, warnings and ingest/raw-store locations expressed without private absolute-path leakage in portable report content.
8. Include transfer verification/pairing provenance only as non-secret receiver/transfer identifiers when network imported.
9. Persist the report atomically next to the ingest record and make it serializable for later M06 Capture Inbox UI.
10. Warnings must distinguish owner-required calibration, optional missing data and actual validation errors; successful report generation must not relabel invalid packages as imported.
11. Add golden/report tests for manual and network imports, calibration present/absent, optional diagnostics/masks, warning ordering and privacy redaction.
12. Tests exercise the production-used ingest/receiver/raw-store seam, not only isolated helpers.
13. Invalid/incomplete/untrusted data never reaches normal imported authority.
14. Privacy/secrets/private paths are handled truthfully and safely.
15. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
16. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
17. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
