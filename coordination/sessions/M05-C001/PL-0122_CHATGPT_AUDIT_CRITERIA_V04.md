# PL-0122 — ChatGPT Remediation Audit Criteria V04

All criteria mandatory.

1. M05-BATCH-004 / READY / CODEX authorization exists before material work.
2. All 10 accepted M05 children remain accepted/unregressed; M03/M04 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. Codex does not edit TASKS.md/ChatGPT audits and does not start M06.
4. Existing PackScan/transfer/ingest authority is preserved.
5. PL-0122_CHATGPT_AUDIT_V03.md is fully addressed.
6. Preserve functional manual pairing, persisted reconnect identity, QR scanner gating and ProductionCaptureCameraLifecycle stop/restore registration.
7. Represent the real production camera lifecycle with enough state to distinguish: active-and-stoppable, active-but-stop-failed, and already-released/idle.
8. QR acquisition must succeed when the production camera is already safely released; it must fail only when an active camera cannot be released.
9. Restore production capture only when pairing actually displaced an active production camera; do not spuriously restart an already-idle camera.
10. Add Swift tests for wrong-version PairingOffer rejection, active stop success, active stop refusal, already-idle success, no concurrent scanner/capture ownership and correct conditional hand-back.
11. Tests exercise the actual production-used seam and exact failure/state boundaries.
12. Full locked suite and relevant project/static checks pass truthfully.
13. Child log uses full GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
14. Final source/tests/log are mutually consistent.

Closure requires independent ChatGPT AUDITED_PASS.
