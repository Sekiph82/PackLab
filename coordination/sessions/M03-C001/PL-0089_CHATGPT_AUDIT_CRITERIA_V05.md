# PL-0089 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorized.
2. PL-0068 and all accepted M03 children preserved.
3. No TASKS/audit edits by Codex; no M04.
4. Batch-004 passing behavior preserved.
5. Previous V04 audit fully addressed.
6. Preserve the real AcceptedFrameGalleryView retake callback and rollback-oriented SessionGalleryStore implementation.
7. Add behavior tests that invoke the real retake action/callback path and verify persisted replacement state, files and gallery audit.
8. Inject failures at multiple mutation stages, including source/record/state/audit publication for delete and retake, and prove rollback leaves one coherent old/new state with no orphan files.
9. Retain ordering, missing preview/source and corrupt-record behavior.
10. Filesystem/UI tests cover the actual production mutation/recovery/destructive boundary.
11. Validation and git diff --check clean/truthful.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
