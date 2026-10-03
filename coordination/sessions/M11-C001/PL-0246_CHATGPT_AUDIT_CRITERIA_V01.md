# PL-0246 - ChatGPT Audit Criteria V01

Task: **Implement parameter validation and impossible-geometry rejection**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0246_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement centralized Design Model validation for numeric bounds, unit consistency, feature relationships and obvious impossible packaging geometry. Reject non-finite/negative forbidden dimensions, neck/body/base ordering contradictions, invalid profile/cross-section references, self-inconsistent symmetry/operation inputs and stale parents. Keep validation explicit/versioned; do not silently clamp engineering parameters into acceptance.
3. Tests/evidence cover at minimum: finite/bound checks, neck/body/base contradictions, stale references, invalid unit mixing, impossible revolve/loft relationships, deterministic diagnostics, no silent clamping.
4. Scan Master remains immutable parent authority; Design Model is separate parametric truth; preview meshes remain derived proxies; inherited scale/deferred-validation state cannot become physical/mold authority.
5. No unreviewed dependency/CAD backend/model/hosted/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
