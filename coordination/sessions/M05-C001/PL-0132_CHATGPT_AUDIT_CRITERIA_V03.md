# PL-0132 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. TASKS.md authorizes M05-BATCH-003 / READY / CODEX before material work.
2. Accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/transfer/ingest authority is preserved.
5. PL-0132_CHATGPT_AUDIT_V02.md is fully addressed.
6. Preserve ImportReport, safe provenance filtering and atomic ImportReportStore.
7. Use separate fixtures/imports/assertions for manual/drop and network reports so one digest-keyed network report does not overwrite the only evidence for the manual report before it is inspected.
8. Add a valid PackScan with an optional mask payload and verify optional_payload_counts plus absence of optional_mask_missing warning.
9. Retain mask-absent, diagnostics-present, diagnostics-absent, calibration-present and calibration-absent coverage with deterministic warning ordering.
10. Assert network provenance keeps only receiver_id/transfer_id and strips secrets/private paths.
11. Add an invalid-package case proving no successful report file/state is created.
12. Tests exercise actual production-used behavior and exact failure/restart boundaries.
13. No untrusted/incomplete data reaches normal import authority and no security control is weakened.
14. Full locked suite and relevant project/static checks pass truthfully.
15. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
