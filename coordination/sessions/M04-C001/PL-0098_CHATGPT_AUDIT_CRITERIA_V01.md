# PL-0098 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M04-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03 remains accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits or start M05.
4. Existing M03 capture/sensor/session ownership is reused rather than duplicated.
5. PL-0098 implements the frozen task scope.
6. Implement a deterministic object/framing score estimating how much of the image the package occupies and whether margins are usable for reconstruction.
7. Return explicit too-small, acceptable and too-large/cropped states rather than a single opaque score.
8. Keep the design compatible with later package segmentation/masking work without starting M08.
9. Expose framing metrics/reasons to the live capture UI and logging pipeline.
10. Add tests for small, centered-good, edge-touching/cropped and oversized cases.
11. Tests exercise the actual production-used quality/runtime/persistence seam, not only a disconnected helper.
12. Thresholds/physical claims are truthful about whether owner/iPhone calibration occurred.
13. Relevant regression/project checks and git diff --check pass truthfully.
14. Privacy/signing/secret boundaries remain clean.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
