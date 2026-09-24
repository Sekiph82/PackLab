# PL-0098 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorization exists.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits by Codex and no M05 work.
4. V01 correct behavior is preserved.
5. Previous V01 audit is fully addressed.
6. Wire FramingAnalyzer into the production candidate runtime and publish too-small/acceptable/cropped state plus metrics/reasons to the live capture UI.
7. Feed the same framing metric into CandidateQualityMetrics and the candidate log store.
8. Keep object-mask input as the accepted bounded contract without starting M08 segmentation.
9. Add tests for too-small, centered-good, edge-touching, oversized-by-area, unavailable mask and exact size/margin boundaries at the runtime seam.
10. Tests drive the production-used M04 candidate runtime, not only a pure helper.
11. Relevant regression/project checks and git diff --check pass truthfully.
12. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are mutually consistent.
