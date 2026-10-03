# PL-0241 - ChatGPT Audit Criteria V01

Task: **Define Design Model parameter graph separate from triangle-mesh data**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0241_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Define the PackLab-owned Design Model graph as immutable/versioned parametric truth independent of scan triangles and preview tessellation. Represent model revision identity, package family, parameter nodes, feature/component references, parent Scan Master binding, inherited scale state/provenance, deferred physical-validation status and edit ancestry. The graph must not embed Open3D/CAD backend objects or silently copy Scan Master triangles as parametric authority.
3. Tests/evidence cover at minimum: deterministic graph identity, explicit Scan Master parent binding, immutable revisions, parameter uniqueness/type validation, RELATIVE/mm_unverified semantics, no triangle-mesh authority leakage, serialization-ready values, deferred validation/mold false.
4. Scan Master remains immutable parent authority; Design Model is separate parametric truth; preview meshes remain derived proxies; inherited scale/deferred-validation state cannot become physical/mold authority.
5. No unreviewed dependency/CAD backend/model/hosted/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
