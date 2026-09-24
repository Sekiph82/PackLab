# PL-0096 — ChatGPT Remediation Audit Criteria V02

1. M04-BATCH-002 / READY / CODEX authorization exists.
2. M03 and PL-0111 remain accepted; PL-0068 remains OWNER_REQUIRED.
3. No TASKS/audit edits by Codex and no M05 work.
4. V01 correct behavior is preserved.
5. Previous V01 audit is fully addressed.
6. Define and implement explicit semantics for `toleratedFraction`, `warningFraction` and `rejectFraction`; `warningFraction` must no longer be dead configuration.
7. Wire highlight analysis into the production candidate quality runtime and use the active persisted preset's highlight thresholds.
8. Expose raw clipped fractions/reasons in live quality state and candidate logs.
9. Add tests for zero clipping, tolerated localized specular clipping, warning band, reject band, exact thresholds and Glossy/PET policy propagation.
10. Tests drive the production-used M04 candidate runtime, not only a pure helper.
11. Relevant regression/project checks and git diff --check pass truthfully.
12. Child log uses GitHub URLs and ends READY_FOR_INDEPENDENT_AUDIT.
13. Final source/tests/log are mutually consistent.
