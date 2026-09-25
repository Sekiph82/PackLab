# PL-0130 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan validation/session authority is reused rather than duplicated.
5. PL-0130 satisfies the frozen scope.
6. Implement a dedicated quarantine store outside normal imported/raw evidence directories.
7. On corrupt/unsupported ingest, atomically preserve the original package when safely readable plus a structured quarantine record containing stable error code, source channel, capture ID if safely known, package digest if computable, timestamp and redacted diagnostics.
8. Never partially extract quarantined packages into the normal ingest tree.
9. Quarantine filenames/paths must be collision-safe and must not trust package-provided path fragments.
10. Repeated quarantine of the same bytes must be deterministic/idempotent enough to avoid uncontrolled duplicates while retaining event history as appropriate.
11. Add tests for corrupt ZIP, future schema, checksum mismatch, malicious filename/path, repeated quarantine and no-normal-import-artifacts.
12. Tests exercise the production-used ingest/receiver/raw-store seam, not only isolated helpers.
13. Invalid/incomplete/untrusted data never reaches normal imported authority.
14. Privacy/secrets/private paths are handled truthfully and safely.
15. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
16. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
17. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
