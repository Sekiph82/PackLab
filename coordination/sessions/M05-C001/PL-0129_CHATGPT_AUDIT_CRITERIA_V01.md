# PL-0129 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan validation/session authority is reused rather than duplicated.
5. PL-0129 satisfies the frozen scope.
6. Make existing `packlab_core.packscan.validate_packscan` the authoritative validation gate for every manual/network ingest.
7. Validate ZIP safety, manifest schema/version, required entries, payload declarations, payload sizes, manifest SHA-256 values and checksums.json before any extraction/publication.
8. Unsupported future schema and malformed/corrupt packages must produce stable structured ingest error codes.
9. Extraction must occur only after validation succeeds and must retain the existing safe-path/atomic extraction guarantees.
10. Do not partially expose extracted payloads when validation fails.
11. Add integration tests proving validation precedes extraction for valid, future-version, checksum mismatch, unsafe path, missing required payload and corrupt ZIP packages.
12. Tests exercise the production-used ingest/receiver/raw-store seam, not only isolated helpers.
13. Invalid/incomplete/untrusted data never reaches normal imported authority.
14. Privacy/secrets/private paths are handled truthfully and safely.
15. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
16. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
17. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
