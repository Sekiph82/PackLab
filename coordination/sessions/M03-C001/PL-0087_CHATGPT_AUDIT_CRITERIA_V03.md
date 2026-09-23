# PL-0087 — ChatGPT Remediation Audit Criteria V03

Task: **PL-0087 — New Scan callback workflow remediation**
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CHATGPT_AUDIT_V02.md

All criteria mandatory.

1. M03-BATCH-003 / READY / CODEX authorization exists before material work.
2. PL-0068 remains unchecked / OWNER_REQUIRED.
3. PL-0070 remains accepted and unregressed.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts.
5. No M04 work starts.
6. No secrets/signing/private assets/caches enter public Git.
7. Previous passing behavior is preserved.
8. The prior independent audit is fully addressed.
9. Make NewScanWizard use a testable workflow/view-model seam rather than duplicating validation logic separate from NewScanWorkflowModel.
10. Prove valid Start invokes the supplied onStart callback exactly once with the normalized draft.
11. Prove invalid Start never invokes onStart and retains visible validation state; prove Cancel never invokes Start.
12. Preserve root reachability and all accepted M02 capture-mode IDs, and pass the produced draft into the real session-creation handoff instead of discarding it.
13. New tests exercise the actual integrated seam, not a disconnected helper only.
14. Relevant M01/M02/M03 contracts remain unregressed.
15. Available validation is run truthfully.
16. git diff --check and protected-file checks pass.
17. Child log maps each prior failure to code/tests and records exact commits/results.
18. Actual GitHub source/diff/tests/log are consistent and no material finding remains.

Closure requires independent ChatGPT AUDITED_PASS.
