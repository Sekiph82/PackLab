# PL-0081 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorized.
2. PL-0068 and all accepted M03 children preserved.
3. No TASKS/audit edits by Codex; no M04.
4. Batch-004 passing behavior preserved.
5. Previous V04 audit fully addressed.
6. Keep exactly one physical MotionService/CMMotionManager ownership path; CoreMotionController may only project an injected service and may not allocate its own pipeline.
7. Wire real accepted-still orchestration to persist MotionCaptureBinding derived from MotionService records using the same monotonic capture timestamp semantics as PL-0080.
8. Add integrated tests for available/stale/unavailable motion evidence, one-owner composition and AcceptedCaptureRecord.motionBinding persistence/reopen.
9. Preserve bounded buffering, quaternion attitude and rotation-rate evidence.
10. Tests cover actual production-used service/persistence/failure boundaries.
11. Validation and git diff --check clean/truthful.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
