# PL-0107 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 preserved; PL-0068 OWNER_REQUIRED.
3. No TASKS/audit edits and no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Integrate top/neck/closure detail passes into the active guided-capture runtime with explicit CapturePassMetadata persisted alongside accepted capture/session evidence.
7. Require authoritative pose coverage, framing quality, overall QualityDecision and NearDuplicateDetector approval for detail-pass acceptance.
8. Use tighter detail framing without changing the selected main-wide camera ownership.
9. Expose missing top/neck/closure guidance live and add tests for activation, quality reject, duplicate reject, unavailable pose, framing boundaries and persisted pass metadata.
10. Tests exercise the production guided-capture/session persistence seam.
11. Validation/git diff/privacy checks clean and truthful.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
