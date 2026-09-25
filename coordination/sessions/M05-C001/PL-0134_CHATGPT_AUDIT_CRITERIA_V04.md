# PL-0134 — ChatGPT Remediation Audit Criteria V04

All criteria mandatory.

1. M05-BATCH-004 / READY / CODEX authorization exists before material work.
2. All 10 accepted M05 children remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan/transfer/ingest authority is preserved.
5. PL-0134_CHATGPT_AUDIT_V03.md is fully addressed.
6. Preserve the real HTTPS receiver, shared V1 fixture, test TLS material, invalid-package quarantine matrix and exactly-once ingest assertions.
7. Make the executable harness genuinely simulate sender restart: write sender state, destroy the first sender object, create a fresh sender, read/validate persisted transfer ID + package digest + receiver identity, and derive all resumed requests from that restored state rather than hard-coded literals.
8. Verify the restored package digest and receiver identity before querying status; conflicting persisted state must fail closed.
9. Apply the same completion acceptance rules as production Swift: transfer ID match, package digest match, authenticated=true, verified=true and terminal verified/complete state.
10. Explicitly verify the live receiver certificate fingerprint equals the paired offer fingerprint before authenticated transfer operations.
11. Keep partial upload, receiver restart, cancel/resume, verified completion and exactly-once raw/index/report assertions in one coherent executable chain.
12. Tests exercise the actual production-used seam and exact failure/state boundaries.
13. Full locked suite and relevant project/static checks pass truthfully.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
