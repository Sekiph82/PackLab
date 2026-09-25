# PL-0109 — ChatGPT Remediation Audit Criteria V04

Task: **PL-0109 — Completion resume/recomputation integrity**

All criteria are mandatory.

1. TASKS.md authorizes `M04-BATCH-004 / READY / CODEX` before material work.
2. All 24 accepted M04 children remain accepted/unregressed.
3. M03 remains accepted and PL-0068 remains unchecked / OWNER_REQUIRED.
4. Codex does not edit TASKS.md or ChatGPT audit artifacts and does not start M05.
5. Existing production M04 quality/guided-capture/session architecture is preserved.
6. https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0109_CHATGPT_AUDIT_V03.md is fully addressed.
7. Resume no longer relies on a precomputed `CompletionDiagnostics` snapshot as the sole source of truth for required detail passes.
8. The minimum authoritative detail-pass evidence/state needed to reconstruct completion is persisted or deterministically reconstructed from canonical accepted capture records.
9. A fresh runtime restores/reconstructs detail-pass state and recomputes the same completed/missing required passes and score.
10. After resume, processing one additional accepted capture/recompute must not erase a previously completed detail pass.
11. Missing/corrupt detail-pass resume evidence fails explicitly and must not manufacture completion.
12. Backward compatibility is handled truthfully for sessions created before the new persisted detail-pass state exists.
13. Optional-unavailable/skipped base semantics, asymmetric/turntable state, and previously accepted completion behavior remain unregressed.
14. Tests exercise the production-used session/context/accepted-capture seam, not a disconnected helper.
15. Full declared locked suite and relevant project/static checks pass truthfully.
16. `git diff --check`, protected-file and privacy/signing checks pass.
17. Child has one distinct implementation/evidence commit and one separate log-only commit.
18. Child log uses only full GitHub URLs in user-facing references and ends exactly `READY_FOR_INDEPENDENT_AUDIT`.
19. Final GitHub source/tests/log are mutually consistent.

Closure requires independent ChatGPT `AUDITED_PASS`.
