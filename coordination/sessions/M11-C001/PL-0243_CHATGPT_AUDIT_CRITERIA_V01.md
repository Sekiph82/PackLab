# PL-0243 - ChatGPT Audit Criteria V01

Task: **Implement spline/profile primitives with explicit coordinate units**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0243_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement deterministic editable 2D profile/spline primitives for Design Model geometry. Coordinates and dimensions must carry the Design Model unit state: RELATIVE/reconstruction_units or METRIC_UNVERIFIED/mm_unverified while M09 physical validation is deferred. Do not label unverified values as verified millimetres. Define control-point ordering, interpolation/evaluation policy, endpoint/tangent constraints and bounded sampling without tying the primitive to a CAD backend.
3. Tests/evidence cover at minimum: line/curve fixtures, interpolation endpoints, control-point validation, monotonic parameter evaluation, relative/mm_unverified units, deterministic evaluation/sampling, degenerate/duplicate point rejection, no verified-mm claim.
4. Scan Master remains immutable parent authority; Design Model is separate parametric truth; preview meshes remain derived proxies; inherited scale/deferred-validation state cannot become physical/mold authority.
5. No unreviewed dependency/CAD backend/model/hosted/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
