# PL-0108 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 preserved; PL-0068 OWNER_REQUIRED.
3. No TASKS/audit edits and no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Integrate the base pass into the active session with explicit physically-feasible / unavailable / skipped / incomplete / complete state persisted in session diagnostics.
7. Use the same authoritative pose, quality and duplicate rules as other accepted captures when the pass is feasible.
8. Never claim base completion for unavailable/unsafe handling; preserve the explicit reason code.
9. Add tests for feasible complete/incomplete, unavailable/skipped, quality/pose failure and reopen/persistence of pass status.
10. Tests exercise the production guided-capture/session persistence seam.
11. Validation/git diff/privacy checks clean and truthful.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
