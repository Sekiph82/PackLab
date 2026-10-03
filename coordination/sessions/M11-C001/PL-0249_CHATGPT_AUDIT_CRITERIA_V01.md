# PL-0249 - ChatGPT Audit Criteria V01

Task: **Generate tessellated preview mesh from Design Model parameters**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0249_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement deterministic tessellation of supported M11 parametric primitives/operations into PREVIEW_PROXY geometry for interactive viewport use. Tessellation parameters/tolerance must be explicit and bounded. Preview mesh is derived and disposable: it cannot become Design Model parametric truth or Scan Master authority. Preserve feature-to-preview mapping where practical for selection, and inherited unit/deferred-validation metadata.
3. Tests/evidence cover at minimum: revolve/loft preview fixtures, tessellation tolerance/work bounds, deterministic vertices/triangles, feature mapping, invalid graph rejection, PREVIEW_PROXY authority, no Scan Master promotion, unit/deferred state.
4. Scan Master remains immutable parent authority; Design Model is separate parametric truth; preview meshes remain derived proxies; inherited scale/deferred-validation state cannot become physical/mold authority.
5. No unreviewed dependency/CAD backend/model/hosted/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
