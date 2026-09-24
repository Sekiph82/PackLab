# PL-0116 — ChatGPT Audit Criteria V01

1. M04-BATCH-001 / READY / CODEX authorization exists.
2. M03 remains accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M05.
4. Shared M03/M04 capture, quality, coverage and session architecture is reused.
5. PL-0116 satisfies the frozen scope.
6. Implement a deterministic turntable capture mode with angle-indexed sectors and explicit assumptions about static camera/background versus rotating object.
7. Keep turntable pose/angle evidence distinct from freehand AR world-pose evidence and record the evidence source truthfully.
8. Define duplicate/coverage/completion rules for expected turntable angles, including missed and repeated angles.
9. Keep object/background masking assumptions as metadata/guidance only; do not start M08 segmentation implementation.
10. Add tests for angle indexing, wrap-around, missing/repeated angles, completion and evidence-source labeling.
11. Preset/mode behavior is config-driven and persisted with session context.
12. No unsupported physical/reconstruction capability is claimed.
13. Tests exercise the production-used preflight/preset/session seam.
14. Relevant regression/project checks and git diff --check pass truthfully.
15. Privacy/signing/secret boundaries remain clean.
16. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
17. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
