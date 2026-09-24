# PL-0094 — ChatGPT Remediation Audit Criteria V03

All criteria mandatory.

1. M04-BATCH-003 / READY / CODEX authorization exists before material work.
2. All 16 accepted M04 children remain unregressed; M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing production M04 integration is preserved.
5. PL-0094_CHATGPT_AUDIT_V02.md is fully addressed.
6. Preserve the current production M04CandidateQualityRuntime integration and corrected sharpness reason codes.
7. Add deterministic candidate-frame fixtures that make SharpnessAnalyzer return WARN and REJECT bands, not only ACCEPT/unavailable.
8. Add exact analyzer equality tests at acceptMinimum and warnMinimum using a production-used injectable metric/fixture seam if exact image construction is impractical.
9. Keep provisional calibration truthfulness and do not claim physical iPhone calibration.
10. Tests exercise the actual production-used seam/state boundary.
11. Full declared suite, relevant project checks and git diff --check pass truthfully.
12. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
