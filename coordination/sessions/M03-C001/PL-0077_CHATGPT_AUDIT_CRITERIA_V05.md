# PL-0077 — ChatGPT Remediation Audit Criteria V05

1. M03-BATCH-005 / READY / CODEX authorized.
2. PL-0068 and accepted M03 truth preserved.
3. No TASKS/audit edits by Codex; no M04.
4. Batch-004 passing behavior preserved.
5. Previous V04 audit fully addressed.
6. Make preview/session restart, permission state, runtime errors and still-capture cancellation use one production CameraRecoveryOwner rather than separate preview/private and capture/runtime owners.
7. Bind the unified owner's onStateChange into CaptureRuntimeViewModel/UI and its cancellation hook into the production still adapter.
8. Ensure interruptionEnded/runtime-error retries restart the one active session owner with bounded/idempotent observer registration.
9. Add injected notification/session tests for permission, interruption/end, retry success/failure, in-flight cancellation and UI state propagation.
10. Tests exercise the actual production-used seam/authoritative schema.
11. Validation and git diff --check are clean/truthful.
12. Log uses GitHub URLs, records exact evidence, ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are consistent.
