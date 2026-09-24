# PL-0080 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorized.
2. PL-0068 and accepted M03 truth preserved.
3. No TASKS/audit edits by Codex; no M04.
4. Batch-004 passing behavior preserved.
5. Previous V04 audit fully addressed.
6. Wire the real accepted-still orchestration to ScanSessionStore.storeAcceptedCapture(still:...) so pose evidence is bound and persisted for actual captures, not only exposed as an unused overload.
7. Use the still's monotonic capture timestamp and explicit fallback bridge semantics only when needed.
8. Add integrated tests for accepted still→PoseBuffer→AcceptedCaptureRecord.poseBinding→reopen persistence, including available/stale/unavailable/out-of-order cases.
9. Do not silently omit pose status when evidence is unavailable.
10. Tests exercise the actual production-used seam/authoritative schema.
11. Validation and git diff --check are clean/truthful.
12. Log uses GitHub URLs, records exact evidence, ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are consistent.
