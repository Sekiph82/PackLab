# PL-0124 — ChatGPT Audit Criteria V01

All criteria mandatory.

1. M05-BATCH-001 / READY / CODEX authorization exists before material work.
2. M03/M04 remain accepted and PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Accepted PackScan/session architecture is reused rather than duplicated.
5. PL-0124 satisfies the frozen task scope.
6. Implement persisted receiver-side transfer state using `.part` data plus an atomic sidecar/checkpoint keyed by transfer ID.
7. Support chunk/range upload with a deterministic next-required byte offset and idempotent retransmission of already-confirmed bytes.
8. Sender must query receiver status after reconnect/restart and resume from the authoritative confirmed offset rather than restart blindly.
9. Receiver restart and sender cancellation must not publish a completed package or lose already-verified resumable bytes.
10. Detect conflicting bytes/offsets/package identity and fail closed instead of splicing incompatible content.
11. Add tests for mid-transfer disconnect, sender restart, receiver restart, duplicate chunk, out-of-order chunk, conflicting chunk, cancel/retry and multi-chunk large-package completion.
12. Tests exercise the production-used transfer/finalization/UI seam, not only a disconnected helper.
13. Security/privacy claims are truthful and secrets never enter Git/logs/package evidence.
14. Full locked suite, relevant project checks and git diff --check pass truthfully.
15. Child log records exact commits/files/results/limitations, uses full GitHub URLs, and ends READY_FOR_INDEPENDENT_AUDIT.
16. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
