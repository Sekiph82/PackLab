# PL-0084 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorized.
2. PL-0068 and all accepted M03 children preserved.
3. No TASKS/audit edits by Codex; no M04.
4. Batch-004 passing behavior preserved.
5. Previous V04 audit fully addressed.
6. Preserve the current SharedARSessionOwner reset/recovery implementation.
7. Add conditional/injected tests using ARSessionLifecycleDriver that exercise reset→relocalizing→recovered, reset→failed, repeated reset, degradation-threshold reset and interruption reset on the real owner.
8. Verify old-epoch pose rejection and ResetDiagnosticEvent reason/epoch/result from the real owner path.
9. Do not add another AR owner.
10. Tests cover actual production-used service/persistence/failure boundaries.
11. Validation and git diff --check clean/truthful.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
