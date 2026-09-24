# PL-0094 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M04-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03 remains accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits or start M05.
4. Existing M03 capture/sensor/session ownership is reused rather than duplicated.
5. PL-0094 implements the frozen task scope.
6. Implement a deterministic sharpness metric suitable for high-resolution packaging stills, with normalization that is stable across supported image dimensions.
7. Define configurable ACCEPT/WARN/REJECT sharpness thresholds and document units/interpretation; do not hard-code unexplained magic numbers.
8. Add a calibration harness/fixture workflow that can tune thresholds from labeled packaging images later without changing the algorithm contract.
9. On Windows without physical iPhone captures, treat thresholds as provisional/test-calibrated only; do not claim owner/device calibration that did not occur.
10. Add positive/negative/boundary tests for sharp, mildly blurred and strongly blurred fixtures or deterministic synthetic equivalents.
11. Tests exercise the actual production-used quality/runtime/persistence seam, not only a disconnected helper.
12. Thresholds/physical claims are truthful about whether owner/iPhone calibration occurred.
13. Relevant regression/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
