# PL-0240 - ChatGPT Audit Criteria V01

Task: **Export Scan Master as PLY/OBJ/GLB with provenance manifest**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0240_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M09 partial frontier and owner deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement deterministic Scan Master export for supported PLY/OBJ/GLB paths plus original/eligible texture assets where available. Export only a selected eligible Scan Master, never AI/generated/proxy authority. Preserve geometry/texture relationships and write a machine-readable export manifest with Scan Master revision, source/output digests, units, scale state, scale provenance, deferred physical-validation status and limitations. Do not relabel mm_unverified as mm and do not claim manufacturing readiness. Unsupported texture/format capability must fail or degrade explicitly, never silently.
3. Tests/evidence cover at minimum: PLY/OBJ/GLB deterministic export, manifest digests, selected revision binding, texture-present/absent paths, generated/proxy rejection, mm_unverified preservation, deferred-validation disclaimer, round-trip/basic parse where practical.
4. RAW_CAPTURE/reconstruction/original captured geometry remain immutable; revision/proxy/repair/export ancestry is explicit, inherited scale state is preserved and `DEFERRED_OWNER_VALIDATION` cannot become physical/mold authority.
5. Generated/AI_VISUAL_REFERENCE cannot become Scan Master authority. No unreviewed dependency/model/hosted/private evidence/later-child or M11+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not acceptance.
