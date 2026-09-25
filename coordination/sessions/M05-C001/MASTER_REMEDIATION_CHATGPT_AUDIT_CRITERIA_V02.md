# M05-BATCH-003 — Master Remediation Audit Criteria V02

All criteria mandatory.

1. TASKS.md authorizes M05-BATCH-003 / READY / CODEX before material work.
2. Authorized children are exactly PL-0119, PL-0121–PL-0126, PL-0132 and PL-0134.
3. PL-0120, PL-0127, PL-0128, PL-0129, PL-0130, PL-0131 and PL-0133 remain accepted/unregressed.
4. M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
5. Codex does not edit TASKS.md or ChatGPT audits and does not start M06.
6. Actual production finalization uses CanonicalFinalizationSource and passes the complete rollback/failure matrix.
7. Swift and Python consume one authoritative golden Transfer Protocol V1 fixture/derived contract and fail closed on unsupported versions.
8. Real manual pairing is functional in the user workflow.
9. QR scanner ownership is tied to the actual production camera lifecycle; concurrent capture/scanner operation is impossible.
10. Network TLS/auth tests execute in the locked environment without relying on an unavailable external OpenSSL executable.
11. Wrong pin, expired/replayed pairing, wrong receiver and missing auth fail at the actual HTTPS boundary.
12. Production sender persists and restores the same transfer ID across retry and runtime/app restart.
13. Retry resumes from receiver-confirmed next_offset and never silently creates a second transfer.
14. Production Swift completion requires matching transfer ID, digest, authenticated=true, verified=true and terminal verified/complete state.
15. Transfer UI cancel/retry/failure/completion behavior is proven through an injected production-client seam.
16. Report tests separately prove manual and network reports plus mask/diagnostics/calibration present/absent combinations and invalid-no-report behavior.
17. Executable cross-language/production-contract transport evidence drives pairing/auth/partial upload/same-ID sender resume/receiver restart/verified ingest exactly once.
18. Static source-string inspection is supplemental only, never the sole end-to-end evidence.
19. Invalid/incomplete/untrusted content never reaches normal raw authority.
20. No insecure fallback, custom crypto, committed production private key or leaked bearer/session credential exists.
21. Full locked suite and relevant project/static checks pass truthfully.
22. No mandatory deterministic integration/security test remains skipped solely due missing external OpenSSL.
23. Every child has one implementation/evidence boundary and one separate V03 log-only boundary.
24. Child logs end READY_FOR_INDEPENDENT_AUDIT.
25. User-facing repository references are full GitHub URLs only.
26. Master log ends AWAITING_MILESTONE_AUDIT.
27. M05 closes only after independent ChatGPT re-audit of all nine children.
