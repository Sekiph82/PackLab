# PL-0080 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. Codex does not edit TASKS.md/audits or start M04.
4. Prior passing behavior is preserved.
5. Previous audit PL-0080_CHATGPT_AUDIT_V03.md is fully addressed.
6. Call the pose binder from the real accepted-still flow after capture and persist PoseCaptureBinding with the accepted photo/session evidence.
7. Use a capture-time monotonic timestamp sourced as close as possible to the actual photo event; if fallback wall-clock bridging is required, record which timestamp path was used and its alignment semantics.
8. Ensure stale/unavailable/invalid tracking yields explicit non-available pose evidence, not omission or invented pose.
9. Add integrated accepted-still→timestamp bridge→PoseBuffer→persisted binding tests including exact tolerance and out-of-order samples.
10. Tests exercise the actual production seam or its injected driver, not only a neighboring helper.
11. Regressions and git diff --check are clean/truthful.
12. Log records exact commits/files/results and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
