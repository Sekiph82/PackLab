# PL-0244 - ChatGPT Audit Criteria V01

Task: **Implement editable cross-section primitive with symmetry options**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0244_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement an editable parametric cross-section primitive independent of scan mesh topology and CAD backend. Support explicit symmetry modes appropriate for packaging (none, left-right, front-back, both where valid), deterministic control points/axes, unit state and constraint propagation. Symmetry is an editable modeling constraint, not inferred physical truth unless later fitting evidence says so.
3. Tests/evidence cover at minimum: circle/ellipse/general section, symmetry toggles, mirrored edit propagation, asymmetric mode preservation, invalid self-intersecting/degenerate control sets, unit propagation, deterministic serialization.
4. Scan Master remains immutable parent authority; Design Model is separate parametric truth; preview meshes remain derived proxies; inherited scale/deferred-validation state cannot become physical/mold authority.
5. No unreviewed dependency/CAD backend/model/hosted/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
