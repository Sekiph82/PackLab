# PL-0119 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. TASKS.md authorizes M05-BATCH-003 / READY / CODEX before material work.
2. Accepted PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing accepted PackScan/transfer/ingest authority is preserved.
5. PL-0119_CHATGPT_AUDIT_V02.md is fully addressed.
6. Keep CanonicalFinalizationSource and the existing PackScanWriter/SessionFinalizer rollback design.
7. Route the actual production finalization call through SessionFinalizer.finalize(source:manifest:payloads:destination:) so authoritative accepted records + immutable source/metadata bytes are required in the real app flow.
8. Add deterministic tests for CanonicalFinalizationSource success and missing authoritative source/metadata rejection.
9. Add real filesystem/injected failure tests for package write/move failure, finalization-record publication failure, destination-already-exists, checksum failure and no-partial destination/finalization/temp artifacts.
10. After every injected failure prove the session remains resumable and any pre-existing valid exported package/finalization record is preserved or restored truthfully.
11. Tests exercise the actual production-used seam and prove the relevant restart/failure boundaries.
12. No untrusted/incomplete data reaches normal import authority and no security control is weakened.
13. Full locked suite and relevant project/static checks pass truthfully.
14. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
15. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
