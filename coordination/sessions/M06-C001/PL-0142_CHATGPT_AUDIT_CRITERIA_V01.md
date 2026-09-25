# PL-0142 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M06-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03–M05 remain accepted; PL-0068 remains OWNER_REQUIRED; M07 is not started.
3. Codex does not edit TASKS.md/ChatGPT audits.
4. M05 raw-ingest authority and M06 service/UI separation are preserved.
5. PL-0142 satisfies the frozen scope.
6. Add an About/Version screen showing PackLab Studio version, Python version, Qt/PySide6 version, PackScan schema support and build/revision metadata when available.
7. Show update information only from local/static build metadata or a manually supplied release manifest; no online service is required.
8. Distinguish current version, available-local-manifest version, unsupported/malformed manifest and no-manifest states.
9. Do not implement auto-download/install in M06.
10. Add tests for version rendering, local manifest comparison, malformed manifest, no-network requirement and privacy-safe output.
11. Tests exercise production-used project/shell seams and real filesystem boundaries.
12. No operation mutates accepted raw evidence or leaks secrets/private paths into portable state.
13. Full locked suite plus Ruff/mypy/compileall/project checks pass truthfully.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
