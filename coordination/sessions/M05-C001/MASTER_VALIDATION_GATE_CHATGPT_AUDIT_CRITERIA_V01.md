# M05-BATCH-005 — Validation Gate Audit Criteria V01

All criteria mandatory.

1. TASKS.md authorizes M05-BATCH-005 / READY / CODEX before material work.
2. The six remaining children stay PL-0119, PL-0121, PL-0122, PL-0125, PL-0126 and PL-0134; the 10 accepted M05 children remain accepted/unregressed.
3. M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED; M06 is not started.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts.
5. The pre-fix aggregate failure is reproduced or its exact prior traceback/evidence is captured truthfully.
6. Root cause is identified rather than masked.
7. The Windows liveness proof remains non-destructive and still distinguishes live vs dead process state.
8. The test is not skipped, xfailed, deleted or weakened into a meaningless assertion.
9. Any timeout/retry change is bounded and evidence-based.
10. The failing liveness test passes repeatedly under stress/repetition.
11. tests/core/test_subprocess_runner.py passes.
12. The focused M05 transfer/TLS/wire regression command remains green.
13. The exact full locked suite exits 0 with zero failures.
14. Ruff/compileall for changed Python files pass.
15. git diff --check passes.
16. No accepted M05 product behavior regresses.
17. No insecure subprocess behavior, shell=True regression, secret/private-key leakage or signing/private-scan contamination is introduced.
18. One implementation/evidence commit and one separate master log-only commit are published.
19. User-facing repository references are full GitHub URLs only.
20. Master log ends AWAITING_MILESTONE_AUDIT.
21. The final six M05 children close only after independent ChatGPT re-audit using this green batch-level validation evidence plus their V04 functional audits.
