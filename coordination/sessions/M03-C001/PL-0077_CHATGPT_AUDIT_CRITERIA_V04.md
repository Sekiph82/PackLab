# PL-0077 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists before material work.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. Codex does not edit TASKS.md/audits or start M04.
4. Prior passing behavior is preserved.
5. Previous audit PL-0077_CHATGPT_AUDIT_V03.md is fully addressed.
6. Wire CameraRecoveryOwner.onStateChange into the real capture runtime/UI so interruption/restarting/permission/failure messages become visible state rather than owner-internal values.
7. Ensure the production still adapter is bound to the same recovery owner so interruption/runtime error cancels the exact in-flight photo request.
8. Make restart callbacks invoke the one real preview/session owner and prove observer registration/unregistration remains idempotent.
9. Add injected notification/session tests covering denied/restricted, interruption, interruptionEnded restart success/failure, runtime error retry bound, in-flight cancellation and UI state propagation.
10. Tests exercise the actual production seam or its injected driver, not only a neighboring helper.
11. Regressions and git diff --check are clean/truthful.
12. Log records exact commits/files/results and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
