# PL-0105 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits; no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Compose NearDuplicateDetector into the real candidate/auto-capture gate before a new still is accepted.
7. Use authoritative accepted pose evidence and optional bounded visual signatures; unavailable/stale pose must fail safe without rejecting useful captures.
8. Never mutate/delete previous accepted immutable source records.
9. Add tests for exact duplicate, useful translation parallax, same azimuth with useful elevation change, visual-signature cases, stale evidence and exact distance/elevation/signature thresholds.
10. Tests hit the production-used quality/coverage/capture seam.
11. Validation/git diff/privacy checks are truthful and clean.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
