# PL-0082 — ChatGPT Remediation Audit Criteria V03

Task: **PL-0082 — Coordinate golden-contract remediation**
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CHATGPT_AUDIT_V02.md

All criteria mandatory.

1. M03-BATCH-003 / READY / CODEX authorization exists before material work.
2. PL-0068 remains unchecked / OWNER_REQUIRED.
3. PL-0070 remains accepted and unregressed.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts.
5. No M04 work starts.
6. No secrets/signing/private assets/caches enter public Git.
7. Previous passing behavior is preserved.
8. The prior independent audit is fully addressed.
9. Add real golden X/Y/Z axis-rotation matrices with expected numeric outputs, not only 16-element shape checks.
10. Add the authoritative PackScan basis_conversion constant arkit_to_packscan_identity_shared_right_handed_basis_v1 alongside the coordinate convention and metre unit.
11. Cross-check the coordinate/basis/unit constants against schemas/packscan/pose.schema.json in deterministic tests.
12. Preserve fail-closed invalid-matrix and inverse/round-trip behavior.
13. New tests exercise the actual integrated seam, not a disconnected helper only.
14. Relevant M01/M02/M03 contracts remain unregressed.
15. Available validation is run truthfully.
16. git diff --check and protected-file checks pass.
17. Child log maps each prior failure to code/tests and records exact commits/results.
18. Actual GitHub source/diff/tests/log are consistent and no material finding remains.

Closure requires independent ChatGPT AUDITED_PASS.
