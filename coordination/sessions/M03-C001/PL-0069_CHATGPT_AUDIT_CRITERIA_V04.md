# PL-0069 — ChatGPT Remediation Audit Criteria V04

Task: **PL-0069 — Preview lifecycle and authorization remediation**
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CHATGPT_AUDIT_V03.md

All criteria mandatory.

1. M03-BATCH-003 / READY / CODEX authorization exists before material work.
2. PL-0068 remains unchecked / OWNER_REQUIRED.
3. PL-0070 remains accepted and unregressed.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts.
5. No M04 work starts.
6. No secrets/signing/private assets/caches enter public Git.
7. Previous passing behavior is preserved.
8. The prior independent audit is fully addressed.
9. Move authorization evaluation ahead of lifecycle start bookkeeping so denied/restricted first launch cannot leave the preview lifecycle falsely marked started.
10. Handle Settings-return/authorization changes so a newly authorized camera can attach and start without recreating the app.
11. Keep preview attach/start/stop/detach symmetric and idempotent across repeated appear/disappear cycles.
12. Add behavior-bearing tests for denied→authorized, start failure/error mapping, and disappear→reappear actual bridge/lifecycle transitions.
13. New tests exercise the actual integrated seam, not a disconnected helper only.
14. Relevant M01/M02/M03 contracts remain unregressed.
15. Available validation is run truthfully.
16. git diff --check and protected-file checks pass.
17. Child log maps each prior failure to code/tests and records exact commits/results.
18. Actual GitHub source/diff/tests/log are consistent and no material finding remains.

Closure requires independent ChatGPT AUDITED_PASS.
