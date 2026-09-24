# PL-0113 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits and no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Add a transparent-packaging preparation flow in New Scan/Capture Protocol with an explicit TransparentTreatmentMode selector.
7. Require acknowledgement and record the selected treatment mode truthfully; `.none` must not be silently represented as treated.
8. Persist treatment/acknowledgement in M04ScanContext and use it in ScanSuitabilityPreflight warnings/blockers without claiming physical verification.
9. Add tests for every treatment option, no acknowledgement, acknowledgement, context persistence/reopen and no-false-suitability behavior.
10. Tests exercise the production preset/protocol/preflight/session seam.
11. No unsupported physical/reconstruction capability is claimed.
12. Validation/git diff/privacy checks clean and truthful.
13. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
14. Final source/tests/log consistent.
