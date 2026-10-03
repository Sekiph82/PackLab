# PL-0255 - ChatGPT Audit Criteria V01

Task: **Fit non-circular symmetric body using stacked cross-sections and lofting**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0255_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, accepted M10 predecessor and M09 deferral were read and synchronization was safe.
2. Deterministic PackLab-owned implementation is limited to: Fit a symmetric non-circular bottle/jar body from stacked Scan Master cross-sections into editable cross-section primitives and a loft operation. Require explicit section heights/order and symmetry evidence. Preserve observed asymmetry when constraints are disabled and reject sparse/contradictory section sets. Output remains parametric Design Model truth plus derived preview.
3. Tests cover at minimum: elliptical/rounded-rect stacked sections, section order, symmetry on/off, sparse/missing sections, deterministic loft graph, Scan Master parent binding, preview-only mesh.
4. Exact Scan Master parent remains immutable; Design Model is separate parametric authority; derived preview/deviation evidence does not become Scan Master or manufacturing truth; scale/deferred status is preserved.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ work is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation and log publication are separate; log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects actual source/diff/evidence; builder validation is not acceptance.
