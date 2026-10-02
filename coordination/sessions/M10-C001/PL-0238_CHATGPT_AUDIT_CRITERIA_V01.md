# PL-0238 - ChatGPT Audit Criteria V01

Task: **Add Promote to Scan Master action with hard authority gate**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0238_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M09 partial frontier and owner deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement the Windows Studio/application action that requests domain promotion to Scan Master with explicit actor/reason/audit metadata. The UI/action must delegate eligibility and revision truth to the core Scan Master service. Hard reject generated/AI_VISUAL_REFERENCE, preview proxy as selected authority, incomplete provenance, stale parents or unauthorized authority classes. Promotion before physical validation must visibly retain DEFERRED_OWNER_VALIDATION, inherited scale state and mold_use_authorized=false.
3. Tests/evidence cover at minimum: eligible promotion, AI/generated/proxy rejection, incomplete/stale provenance, actor/reason audit metadata, UI delegation, reopen persistence, deferred-validation visibility.
4. RAW_CAPTURE/reconstruction/original captured geometry remain immutable; revision/proxy/repair/export ancestry is explicit, inherited scale state is preserved and `DEFERRED_OWNER_VALIDATION` cannot become physical/mold authority.
5. Generated/AI_VISUAL_REFERENCE cannot become Scan Master authority. No unreviewed dependency/model/hosted/private evidence/later-child or M11+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not acceptance.
