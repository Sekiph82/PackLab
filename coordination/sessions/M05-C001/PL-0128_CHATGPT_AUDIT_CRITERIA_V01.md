# PL-0128 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan validation/session authority is reused rather than duplicated.
5. PL-0128 satisfies the frozen scope.
6. Implement a headless PackLab Studio receiver service using the PL-0121 V1 protocol, PL-0122 pairing identity, PL-0123 TLS/auth and PL-0124 resumable transfer store.
7. Receiver must bind only to configured local-network interfaces/port, advertise its receiver instance identity, and expose lifecycle start/stop/status without requiring the future M06 shell.
8. Completed verified packages must enter a dedicated Capture Inbox staging directory and then the same ingest service used by PL-0127.
9. Never extract/import an unauthenticated, incomplete or checksum-unverified transfer.
10. Support clean shutdown/restart while preserving resumable transfer checkpoints.
11. Add loopback integration tests for paired transfer, unpaired rejection, shutdown/restart resume, verified inbox handoff and concurrent distinct transfer IDs.
12. Tests exercise the production-used ingest/receiver/raw-store seam, not only isolated helpers.
13. Invalid/incomplete/untrusted data never reaches normal imported authority.
14. Privacy/secrets/private paths are handled truthfully and safely.
15. Full locked suite, relevant project/static checks and git diff --check pass truthfully.
16. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
17. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
