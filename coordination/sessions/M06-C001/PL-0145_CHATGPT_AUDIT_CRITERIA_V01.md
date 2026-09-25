# PL-0145 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. M05 raw-ingest authority and M06 service/UI separation are preserved.
5. PL-0145 satisfies the frozen scope.
6. Define versioned project metadata with immutable project UUID, human name, created/updated timestamps, schema version and monotonically advancing revision identifiers.
7. Revision identifiers must change only on authoritative editable-state commits, not mere UI navigation.
8. Persist metadata atomically and validate identity/revision on reopen.
9. Do not expose secrets/private absolute source paths in portable metadata.
10. Add tests for creation, revision increment, reopen identity, stale revision conflict and malformed metadata.
11. Tests exercise production-used project/shell seams and real filesystem boundaries.
12. No operation mutates accepted raw evidence or leaks secrets/private paths into portable state.
13. Full locked suite plus Ruff/mypy/compileall/project checks pass truthfully.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
