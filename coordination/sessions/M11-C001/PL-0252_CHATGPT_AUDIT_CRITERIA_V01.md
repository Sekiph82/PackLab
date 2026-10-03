# PL-0252 - ChatGPT Audit Criteria V01

Task: **Fit smoothed profile while preserving shoulder/base transitions**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0252_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, accepted M10 predecessor and M09 deferral were read and synchronization was safe.
2. Deterministic PackLab-owned implementation is limited to: Fit an editable parametric profile to PL-0251 evidence with explicit smoothing/regularization parameters and feature-preservation constraints around shoulder/base transitions. Record residuals and rejected evidence. The fitted profile is Design Model data, not a replacement Scan Master. Excessive smoothing or unsupported gaps must fail or remain review-required.
3. Tests cover at minimum: noisy smooth body, sharp shoulder/base preservation, regularization boundary, missing-gap handling, residual evidence, deterministic fit, parent profile/Scan Master binding.
4. Exact Scan Master parent remains immutable; Design Model is separate parametric authority; derived preview/deviation evidence does not become Scan Master or manufacturing truth; scale/deferred status is preserved.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ work is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation and log publication are separate; log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects actual source/diff/evidence; builder validation is not acceptance.
