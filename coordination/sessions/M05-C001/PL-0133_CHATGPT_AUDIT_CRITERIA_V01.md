# PL-0133 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan validation/session authority is reused rather than duplicated.
5. PL-0133 satisfies the frozen scope.
6. Implement an ingest index keyed by manifest `capture_id` plus whole-package SHA-256.
7. Same capture_id + same digest must be idempotent and return the existing import rather than creating duplicate raw copies/projects.
8. Same capture_id + different digest is an identity conflict and must never overwrite the existing import; return/quarantine a stable conflict result with both non-secret digests.
9. Different capture_id + same digest must be treated according to an explicit fail-closed policy and never silently create ambiguous duplicate authority.
10. The index must be crash-safe/atomic and reconstructable or verifiable against raw ingest metadata.
11. Add tests for same/same idempotency, same-ID/different-digest conflict, different-ID/same-digest ambiguity, index restart/reload and concurrent duplicate attempts.
12. Tests exercise the production-used ingest/receiver/raw-store seam, not only isolated helpers.
13. Invalid/incomplete/untrusted data never reaches normal imported authority.
14. Privacy/secrets/private paths are handled truthfully and safely.
15. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
16. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
17. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
