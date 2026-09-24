# PL-0099 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorization exists.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits by Codex and no M05 work.
4. V01 correct behavior is preserved.
5. Previous V01 audit is fully addressed.
6. Wire BackgroundComplexityAnalyzer into the production candidate runtime and live warning/guidance state.
7. Keep bounded background-only sampling and do not infer a new segmentation pipeline.
8. Feed the metric/reasons into CandidateQualityMetrics and candidate logs under the active preset.
9. Add tests for clean matte, moderate/boundary complexity, highly cluttered, missing/unusable mask and production runtime propagation.
10. Tests drive the production-used M04 candidate runtime, not only a pure helper.
11. Relevant regression/project checks and git diff --check pass truthfully.
12. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are mutually consistent.
