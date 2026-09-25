# PL-0134 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan validation/session authority is reused rather than duplicated.
5. PL-0134 satisfies the frozen scope.
6. Build end-to-end integration fixtures/tests spanning iOS-transfer protocol artifacts and Windows ingest services without requiring physical devices.
7. Cover interrupted network transfer followed by resume, corrupt ZIP, missing photo/image payload, malformed/bad manifest, checksum mismatch, unsupported future schema and unsafe ZIP path.
8. Assert invalid/incomplete transfers never reach normal import/raw store and are quarantined or left resumable according to state.
9. Assert successful resumed transfer passes checksum verification, validation, immutable raw copy, dedupe index and import-report generation exactly once.
10. Include cancellation/retry and receiver restart during a resumable transfer.
11. Keep fixtures deterministic, bounded in size and safe for the normal locked test suite; no real network/internet dependency.
12. Tests exercise the production-used ingest/receiver/raw-store seam, not only isolated helpers.
13. Invalid/incomplete/untrusted data never reaches normal imported authority.
14. Privacy/secrets/private paths are handled truthfully and safely.
15. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
16. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
17. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
