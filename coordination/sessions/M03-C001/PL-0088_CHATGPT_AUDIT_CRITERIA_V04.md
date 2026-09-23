# PL-0088 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. Codex does not edit TASKS.md/audits or start M04.
4. Batch-003 passing behavior is preserved.
5. Previous audit PL-0088_CHATGPT_AUDIT_V03.md is fully addressed.
6. Redesign accepted-capture transaction recovery so source, canonical record and state move as one recoverable transaction across every crash point.
7. On reopen, either complete all three final publications from staged data or roll back all partial final/staged artifacts; never leave source/record committed with old state.
8. Handle crashes after source final move, after record final move, before/after state replacement, and malformed/missing transaction markers deterministically.
9. Add filesystem failure-injection tests for every transaction stage and prove reopen yields either the fully accepted capture or a clean pre-capture state.
10. Filesystem/UI tests cover both success and injected partial/crash failure at the real production seam.
11. Relevant regressions and git diff --check are clean/truthful.
12. Child log records exact evidence and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
