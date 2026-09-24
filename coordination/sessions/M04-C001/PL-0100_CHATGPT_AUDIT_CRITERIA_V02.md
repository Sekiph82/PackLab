# PL-0100 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits; no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Fix QualityDecisionEngine so `rejectUnavailableClipping == true` actually produces a hard reject for unavailable highlight/shadow metrics.
7. Make QualityDecisionEngine the authoritative decision used by the production M04 candidate runtime after all six metric inputs are computed.
8. Preserve stable reason ordering/deduplication and deterministic unavailable/warning/hard-reject precedence.
9. Add table-driven tests for all hard/warning/unavailable combinations, policy switches and equality at every relevant threshold.
10. Tests hit the production-used quality/coverage/capture seam.
11. Validation/git diff/privacy checks are truthful and clean.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
