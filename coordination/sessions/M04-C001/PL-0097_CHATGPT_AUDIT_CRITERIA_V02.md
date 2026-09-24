# PL-0097 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorization exists.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits by Codex and no M05 work.
4. V01 correct behavior is preserved.
5. Previous V01 audit is fully addressed.
6. Apply the same explicit clipping-band semantics to shadow analysis, including the configured warning threshold.
7. Wire shadow analysis into the production candidate quality runtime using object-region evidence when available and truthful fallback when unavailable.
8. Expose raw shadow metrics/reasons in live quality state and candidate logs.
9. Add tests for normal exposure, localized dark region, warning, broad reject, no-mask fallback and exact threshold boundaries.
10. Tests drive the production-used M04 candidate runtime, not only a pure helper.
11. Relevant regression/project checks and git diff --check pass truthfully.
12. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are mutually consistent.
