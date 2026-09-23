# PL-0081 — ChatGPT Remediation Audit Criteria V03

Task: **PL-0081 — Unified CoreMotion service remediation**
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_V02.md

All criteria mandatory.

1. M03-BATCH-003 / READY / CODEX authorization exists before material work.
2. PL-0068 remains unchecked / OWNER_REQUIRED.
3. PL-0070 remains accepted and unregressed.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts.
5. No M04 work starts.
6. No secrets/signing/private assets/caches enter public Git.
7. Previous passing behavior is preserved.
8. The prior independent audit is fully addressed.
9. Remove or subsume the parallel CoreMotionController so the existing MotionService is the single physical motion pipeline.
10. Make the physical MotionService provide the required attitude/quaternion and rotation-rate samples, not acceleration-only data.
11. Bind actual MotionService samples to accepted captures through the same explicit timestamp-domain/tolerance rules.
12. Add tests for single ownership, unavailable/error states, attitude/rotation-rate recording, bounded buffering and accepted-capture alignment.
13. New tests exercise the actual integrated seam, not a disconnected helper only.
14. Relevant M01/M02/M03 contracts remain unregressed.
15. Available validation is run truthfully.
16. git diff --check and protected-file checks pass.
17. Child log maps each prior failure to code/tests and records exact commits/results.
18. Actual GitHub source/diff/tests/log are consistent and no material finding remains.

Closure requires independent ChatGPT AUDITED_PASS.
