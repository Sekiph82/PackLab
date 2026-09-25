# PL-0141 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. M05 raw-ingest authority and M06 service/UI separation are preserved.
5. PL-0141 satisfies the frozen scope.
6. Create a crash/diagnostic bundle service that collects bounded application logs, version/build info, OS/Python/Qt info, active project/job summaries and recent structured errors.
7. Exclude secrets, bearer tokens, pairing codes, private keys, signing material and raw/private package payloads; redact absolute user paths where practical.
8. Bundle creation must be explicit and local, deterministic, bounded in size and safe if some sources are missing/corrupt.
9. Write bundles atomically to a user-selected or app diagnostics location without requiring network upload.
10. Add tests for normal bundle, missing logs, bounded truncation, redaction, no-secret content and atomic publication.
11. Tests exercise production-used project/shell seams and real filesystem boundaries.
12. No operation mutates accepted raw evidence or leaks secrets/private paths into portable state.
13. Full locked suite plus Ruff/mypy/compileall/project checks pass truthfully.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
