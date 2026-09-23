# PL-0085 — ChatGPT Remediation Audit Criteria V04

1. M03-BATCH-004 / READY / CODEX authorization exists.
2. PL-0068 remains OWNER_REQUIRED; PL-0070 remains accepted.
3. No TASKS/audit edits by Codex and no M04 work.
4. Batch-003 passing behavior is preserved.
5. Previous audit PL-0085_CHATGPT_AUDIT_V03.md is fully closed.
6. Preserve CaptureRuntimeViewModel's lifecycle-bounded refresh loop.
7. Use injected tracking/motion services in tests to prove pose, motion and epoch published values change across refresh ticks and the overlay reflects the newest values.
8. Prove stop cancels further updates and simulator/unavailable inputs remain explicitly unavailable.
9. Keep update cadence bounded and avoid per-frame unbounded diagnostics/memory growth.
10. Tests hit the actual production-used seam or authoritative contract source.
11. Relevant regression/static checks and git diff --check pass truthfully.
12. Child log is complete and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
