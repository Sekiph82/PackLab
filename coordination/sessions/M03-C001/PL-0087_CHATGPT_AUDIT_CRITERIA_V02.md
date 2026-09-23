# PL-0087 — ChatGPT Remediation Audit Criteria V02

Task: **PL-0087 — New Scan workflow remediation**
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CHATGPT_AUDIT_V01.md

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
10. Make New Scan reachable from the actual PackLab Capture navigation/root workflow.
11. Provide visible validation state for invalid Start actions instead of silently swallowing validation failures.
12. Preserve the accepted M02 freehand/guided_orbit/turntable IDs and keep M04 guidance parameters out of this task.
13. Add behavior-bearing tests for cancellation, successful Start callback, invalid Start prevention and all capture-mode mappings.
14. New tests are behavior-bearing and cover success, failure and boundary/state transitions.
15. Existing relevant M01/M02/M03 accepted contracts are unregressed.
16. Available validation is run truthfully; unavailable native execution is not claimed.
17. git diff --check and protected TASKS/audit checks pass.
18. Remediation log records exact commits/files/commands/results and maps prior failed criteria to evidence.
19. Actual GitHub source/diff/tests/log are mutually consistent and no material audit finding remains.

Closure requires independent ChatGPT AUDITED_PASS.
