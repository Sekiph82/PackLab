# PL-0107 — ChatGPT Audit Criteria V01

1. M04-BATCH-001 / READY / CODEX authorization exists.
2. M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Existing M03 camera/sensor/session ownership is reused.
5. PL-0107 satisfies the frozen scope.
6. Define a detail-pass model for closure, neck and shoulder coverage using elevated viewpoints compatible with non-LiDAR iPhone capture.
7. Keep detail-pass captures part of the same session/quality/pose pipeline and mark them with explicit pass metadata.
8. Require quality and duplicate checks while allowing tighter framing appropriate for closure detail.
9. Expose explicit guidance for missing neck/top sectors.
10. Add tests for pass activation, sector completion, framing policy and unavailable pose.
11. Tests exercise the production-used coverage/auto-capture/session seam.
12. No unavailable/synthetic pose is represented as physical coverage.
13. Relevant regressions/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
