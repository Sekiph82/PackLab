# PL-0071 — ChatGPT Remediation Audit Criteria V03

Task: **PL-0071 — Selected-camera still capture remediation**
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0071_CHATGPT_AUDIT_V02.md

All criteria mandatory.

1. M03-BATCH-003 / READY / CODEX authorization exists before material work.
2. PL-0068 remains unchecked / OWNER_REQUIRED.
3. PL-0070 remains accepted and unregressed.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts.
5. No M04 work starts.
6. No secrets/signing/private assets/caches enter public Git.
7. Previous passing behavior is preserved.
8. The prior independent audit is fully addressed.
9. Remove unscoped NextLevel.shared capture ownership from the still adapter and bind capture to the deterministic PL-0070 selected main-wide camera/session owner.
10. Implement session-stop/cancellation cleanup so any pending continuation/delegate completes exactly once and cannot leak across session restart.
11. Keep original full-resolution bytes/dimensions and preserve overlap/duplicate-callback rejection.
12. Test the real injected delegate/adapter seam for success, failure, duplicate callback, overlap, cancellation and session stop.
13. New tests exercise the actual integrated seam, not a disconnected helper only.
14. Relevant M01/M02/M03 contracts remain unregressed.
15. Available validation is run truthfully.
16. git diff --check and protected-file checks pass.
17. Child log maps each prior failure to code/tests and records exact commits/results.
18. Actual GitHub source/diff/tests/log are consistent and no material finding remains.

Closure requires independent ChatGPT AUDITED_PASS.
