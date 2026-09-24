# PL-0118 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits and no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Replace hard-coded `cameraReady`, `sessionReady` and `storageAvailable` values in NewScanWizard with production readiness supplied from CaptureRuntimeViewModel/session storage/camera binding.
7. Evaluate real health admission, camera readiness, session/storage readiness, selected preset preparation state and PL-0068 calibration availability before scan start.
8. Persist the exact preflight result and acknowledgements in NewScanDraft/M04ScanContext and block Start only for deterministic blocker reasons.
9. Add integrated New Scan tests for actual readiness transitions, hard health stop, unavailable camera/storage/session, ownerRequired calibration warning, all presets and exact start eligibility.
10. Tests exercise the production preset/protocol/preflight/session seam.
11. No unsupported physical/reconstruction capability is claimed.
12. Validation/git diff/privacy checks clean and truthful.
13. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
14. Final source/tests/log consistent.
