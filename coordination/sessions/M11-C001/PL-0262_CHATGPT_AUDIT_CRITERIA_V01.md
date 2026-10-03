# PL-0262 - ChatGPT Audit Criteria V01

Task: **Fit basic cylindrical screw-cap exterior**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0262_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Implement an editable parametric exterior fit for simple cylindrical screw-cap geometry using accepted closure candidate/profile/cross-section evidence. Model only visible exterior body/rim/gross knurl envelope parameters needed by V1; do not infer thread standard, internal thread geometry, seal performance or manufacturing dimensions not observed. Record residual/support evidence and review-required ambiguity.
3. Tests cover at minimum: cylindrical cap fit, diameter/height evidence, sparse/ambiguous scan, residuals, stable feature IDs, no internal/thread-standard inference, deterministic graph.
4. Scan Master remains immutable; parametric closure/assembly truth remains separate; scale/deferred status is preserved; no hidden internal/thread/seal/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log commits are separate; completed log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects source/diff/evidence; builder validation is not acceptance.
