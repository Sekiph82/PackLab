# PL-0117 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits and no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Insert CaptureProtocolView into the real New Scan flow after preset selection and before preflight/start; remove the generic toggle as a substitute for preset-specific protocol presentation.
7. Drive protocol content from versioned preset data and retain acknowledgement state only where required.
8. Make protocol guidance accessible from the active scan without corrupting session state.
9. Add navigation/view-model tests for all presets, transparent acknowledgement requirement, continue/cancel behavior and persisted acknowledgement.
10. Tests exercise the production preset/protocol/preflight/session seam.
11. No unsupported physical/reconstruction capability is claimed.
12. Validation/git diff/privacy checks clean and truthful.
13. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
14. Final source/tests/log consistent.
