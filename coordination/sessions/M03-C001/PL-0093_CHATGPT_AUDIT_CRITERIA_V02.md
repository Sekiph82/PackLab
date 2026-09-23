# PL-0093 — ChatGPT Remediation Audit Criteria V02

Task: **PL-0093 — Safe deletion workflow remediation**
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0093_CHATGPT_AUDIT_V01.md

All criteria mandatory.

1. M03-BATCH-002 / READY / CODEX authorization exists before material work.
2. PL-0068 remains unchecked / OWNER_REQUIRED.
3. PL-0070 accepted state is not regressed.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts.
5. No M04 work starts.
6. No secrets/signing/private assets/caches enter public Git.
7. Child scope remains bounded to this remediation plus justified adjacent tests/project files.
8. Previously passing child behavior is preserved.
9. The previous independent audit is fully addressed.
10. Bind deletion to a validated canonical PackLab session/history identity rather than an arbitrary in-root URL.
11. Add real confirmation UI that clearly identifies the scan/session being destroyed.
12. Coordinate cleanup of session files, derivatives/temp data and authoritative history/index references with detailed partial-failure diagnostics.
13. Add temporary-filesystem tests for successful deletion, cancellation, missing session, injected partial failure, path traversal and symlink escape; stop before M04.
14. New tests are behavior-bearing and cover success, failure and boundary/state transitions.
15. Existing relevant M01/M02/M03 accepted contracts are unregressed.
16. Available validation is run truthfully; unavailable native execution is not claimed.
17. git diff --check and protected TASKS/audit checks pass.
18. Remediation log records exact commits/files/commands/results and maps prior failed criteria to evidence.
19. Actual GitHub source/diff/tests/log are mutually consistent and no material audit finding remains.

Closure requires independent ChatGPT AUDITED_PASS.
