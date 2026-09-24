# PL-0110 — ChatGPT Audit Criteria V01

1. M04-BATCH-001 / READY / CODEX authorization exists.
2. M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing M03 camera/sensor/session ownership is reused.
5. PL-0110 satisfies the frozen scope.
6. Add a manual capture action that can request a still even when auto-capture conditions are not met, while preserving hard safety/admission gates.
7. Show and persist quality warnings/reasons when the user manually accepts a candidate that would not auto-capture.
8. Define which conditions are never overridable, such as health hard-stop, camera/session failure or unusable source capture.
9. Manual override must not bypass immutable-source, metadata, pose/motion or session transaction rules.
10. Add tests for warning override, non-overridable failures, accepted manual capture logging and interaction with auto-capture cooldown/state.
11. Tests exercise the production-used coverage/auto-capture/session seam.
12. No unavailable/synthetic pose is represented as physical coverage.
13. Relevant regressions/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
