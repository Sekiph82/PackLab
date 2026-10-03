# PL-0259 - ChatGPT Audit Criteria V01

Task: **Allow direct profile and cross-section control-point editing**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0259_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, accepted M10 predecessor and M09 deferral were read and synchronization was safe.
2. Deterministic PackLab-owned implementation is limited to: Implement command-based direct editing of profile and cross-section control points with stable feature references, constraint enforcement and undo/redo. Each edit must validate resulting geometry and create a new immutable Design Model revision. Preview regeneration is derived; Scan Master and prior model revisions remain unchanged.
3. Tests cover at minimum: profile point move/add/remove where allowed, cross-section edit, symmetry constraints, invalid self-intersection/ordering rejection, undo/redo, deterministic revision/preview.
4. Exact Scan Master parent remains immutable; Design Model is separate parametric authority; derived preview/deviation evidence does not become Scan Master or manufacturing truth; scale/deferred status is preserved.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ work is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation and log publication are separate; log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects actual source/diff/evidence; builder validation is not acceptance.
