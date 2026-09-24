# PL-0104 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits; no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Compose GuidedAutoCaptureService into the production M04 runtime with live pose eligibility, target coverage sector, QualityDecision, duplicate/overlap permission and the existing health-gated still capture service.
7. Ensure auto capture cannot issue duplicate/in-flight requests and define deterministic cooldown/rearm after accepted and rejected attempts.
8. On accepted still, route through the existing immutable source/session transaction and authoritative coverage/quality logging updates.
9. Add integrated tests for every gate reason, quality reject, missing target, pose ineligible, overlap blocked, health hard stop, in-flight, cooldown boundary, rejected rearm and accepted capture.
10. Tests hit the production-used quality/coverage/capture seam.
11. Validation/git diff/privacy checks are truthful and clean.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
