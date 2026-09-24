# PL-0110 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorized.
2. M03 and PL-0111 preserved; PL-0068 OWNER_REQUIRED.
3. No TASKS/audit edits and no M05.
4. V01 correct behavior preserved.
5. Previous V01 audit fully addressed.
6. Add a real manual capture action in the guided-capture UI/runtime that evaluates ManualCaptureCoordinator and, when allowed, invokes the same health-gated still-capture/session transaction used by auto capture.
7. Manual override may bypass auto-quality/coverage gating only as frozen; it must never bypass health hard stop, camera/session readiness, source integrity or required metadata/evidence constraints.
8. Persist manual-override warnings/reasons with the candidate/accepted quality log and accepted capture context.
9. Synchronize auto-capture cooldown/in-flight state after manual capture and add tests for warning override, hard blockers, persistence, rejected/manual success and auto/manual interaction.
10. Tests exercise the production guided-capture/session persistence seam.
11. Validation/git diff/privacy checks clean and truthful.
12. Log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log consistent.
