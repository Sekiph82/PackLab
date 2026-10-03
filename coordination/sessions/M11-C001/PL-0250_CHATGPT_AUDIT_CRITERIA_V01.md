# PL-0250 - ChatGPT Audit Criteria V01

Task: **Detect rotational/symmetry characteristics and choose bottle fitting strategy**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0250_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, accepted M10 predecessor and M09 deferral were read and synchronization was safe.
2. Deterministic PackLab-owned implementation is limited to: Analyze the selected Scan Master plus M10/M09 profile/cross-section evidence to produce a deterministic fitting-strategy recommendation: axisymmetric revolve, symmetric stacked-section loft, or review-required. Record evidence metrics/thresholds, parent Scan Master binding and uncertainty. This is strategy selection only, not Design Model fitting, and no symmetry may be treated as physical truth without evidence.
3. Tests cover at minimum: synthetic rotational body, non-circular symmetric body, asymmetric/review-required case, threshold boundaries, stale parent, deterministic strategy/evidence, mm_unverified/deferred status.
4. Exact Scan Master parent remains immutable; Design Model is separate parametric authority; derived preview/deviation evidence does not become Scan Master or manufacturing truth; scale/deferred status is preserved.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ work is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation and log publication are separate; log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects actual source/diff/evidence; builder validation is not acceptance.
