# PL-0131 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan validation/session authority is reused rather than duplicated.
5. PL-0131 satisfies the frozen scope.
6. After validation and before derived processing, create an immutable-by-policy raw ingest copy of the original `.packscan` bytes in a content-addressed or otherwise collision-safe raw store.
7. Record package SHA-256, capture_id, original source channel and ingest timestamp in adjacent immutable ingest metadata.
8. Never perform later extraction/processing by modifying the raw package in place; working/derived data must use separate locations.
9. If filesystem permissions support it, mark raw evidence read-only as defense in depth, but digest verification remains the authoritative immutability check.
10. On existing identical raw digest, reuse/idempotently reference the existing evidence; on conflicting identity, fail closed according to PL-0133.
11. Add tests for byte-for-byte raw copy, digest verification, attempted mutation detection, idempotent same-digest ingest and no overwrite on conflict.
12. Tests exercise the production-used ingest/receiver/raw-store seam, not only isolated helpers.
13. Invalid/incomplete/untrusted data never reaches normal imported authority.
14. Privacy/secrets/private paths are handled truthfully and safely.
15. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
16. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
17. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
