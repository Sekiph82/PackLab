# PL-0090 — ChatGPT Remediation Audit Criteria V02

Task: **PL-0090 — Session resume workflow remediation**
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0090_CHATGPT_AUDIT_V01.md

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
10. Discover incomplete sessions from canonical storage on app launch and present deterministic Resume / Discard / blocked-corrupt behavior.
11. Reopen and validate persisted metadata/state/per-photo/source records including stale-temp/incomplete-write handling.
12. Reconstruct sequence, accepted/rejected/replacement history and localization epoch into one resumable session model.
13. Add filesystem restart tests for clean termination, simulated crash, missing record/source, stale temp and version mismatch.
14. New tests are behavior-bearing and cover success, failure and boundary/state transitions.
15. Existing relevant M01/M02/M03 accepted contracts are unregressed.
16. Available validation is run truthfully; unavailable native execution is not claimed.
17. git diff --check and protected TASKS/audit checks pass.
18. Remediation log records exact commits/files/commands/results and maps prior failed criteria to evidence.
19. Actual GitHub source/diff/tests/log are mutually consistent and no material audit finding remains.

Closure requires independent ChatGPT AUDITED_PASS.
