# PL-0125 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Accepted PackScan/session architecture is reused rather than duplicated.
5. PL-0125 satisfies the frozen task scope.
6. Use the whole-package SHA-256 declared at transfer creation as the end-to-end package identity.
7. After all bytes arrive, receiver must independently hash the completed `.part` file before any final publication/import acknowledgement.
8. A checksum mismatch must retain/quarantine diagnostic evidence according to policy but must never mark transfer/export complete or publish the file as a valid inbox package.
9. Sender may mark network export complete only after an authenticated receiver acknowledgement that includes the matching transfer/package digest.
10. Persist verification result and bytes/expected/actual digest metadata without leaking private paths or secrets.
11. Add tests for matching digest, final-byte corruption, wrong declared digest, retry after mismatch, and sender state not completing before verified acknowledgement.
12. Tests exercise the production-used transfer/finalization/UI seam, not only a disconnected helper.
13. Security/privacy claims are truthful and secrets never enter Git/logs/package evidence.
14. Full locked suite, relevant project checks and git diff --check pass truthfully.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
