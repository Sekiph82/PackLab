# PL-0103 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits; no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Present CoverageGridView in the real guided-capture UI and drive it from the authoritative active-session OrbitCoverageModel.
7. Update coverage immediately after accepted captures and expose the currently targeted/missing sector; unavailable evidence must render unavailable rather than synthetic missing/captured state.
8. Keep the view independent from AR ownership and add accessible text fallback.
9. Add runtime/view-model tests for empty, partial, complete, targeted, unavailable and accepted-capture update transitions.
10. Tests hit the production-used quality/coverage/capture seam.
11. Validation/git diff/privacy checks are truthful and clean.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
