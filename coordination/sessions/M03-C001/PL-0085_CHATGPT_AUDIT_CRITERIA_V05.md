# PL-0085 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorized.
2. PL-0068 and all accepted M03 children preserved.
3. No TASKS/audit edits by Codex; no M04.
4. Batch-004 passing behavior preserved.
5. Previous V04 audit fully addressed.
6. Use injected ARTrackingService and MotionService sequences to prove CaptureRuntimeViewModel.pose, motion and epoch change across refresh ticks, not only tracking eligibility.
7. Verify PoseOverlayModel reflects the newest runtime values and that stop prevents subsequent updates.
8. Preserve the bounded refresh cadence and simulator/unavailable truthfulness.
9. Add assertions for pose timestamp/epoch/motion changes and post-stop stability.
10. Tests cover actual production-used service/persistence/failure boundaries.
11. Validation and git diff --check clean/truthful.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
