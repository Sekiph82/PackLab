# PL-0109 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 preserved; PL-0068 OWNER_REQUIRED.
3. No TASKS/audit edits and no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Make CompletionDiagnostics the authoritative active-session completion state derived from ring/detail/base evidence.
7. Publish score, mandatory missing areas, optional unavailable areas and guidance to the live UI; percentage must never hide mandatory missing coverage.
8. Persist completion diagnostics with the M04 session context or a dedicated atomic session sidecar and restore it on resume/recompute deterministically.
9. Add tests for complete/incomplete/unavailable states, optional pass behavior, mixed required passes, persistence/reopen and UI/view-model propagation.
10. Tests exercise the production guided-capture/session persistence seam.
11. Validation/git diff/privacy checks clean and truthful.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
