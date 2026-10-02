# PL-0239 - ChatGPT Audit Criteria V01

Task: **Prevent downstream Design Model from silently retargeting after reconstruction changes**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0239_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M09 partial frontier and owner deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement a PackLab-owned parent-binding/staleness contract for future Design Models so a design revision pins one exact Scan Master ID/digest. New reconstruction or Scan Master revisions must not silently change that parent. Provide explicit stale/available-newer status and an intentional rebind seam that creates a new revision rather than mutating the old one. Do not implement the M11 Design Model kernel itself.
3. Tests/evidence cover at minimum: pinned parent survives newer reconstruction, stale/newer-available status, explicit rebind creates new identity, missing parent rejection, deterministic binding, no M11 geometry implementation.
4. RAW_CAPTURE/reconstruction/original captured geometry remain immutable; revision/proxy/repair/export ancestry is explicit, inherited scale state is preserved and `DEFERRED_OWNER_VALIDATION` cannot become physical/mold authority.
5. Generated/AI_VISUAL_REFERENCE cannot become Scan Master authority. No unreviewed dependency/model/hosted/private evidence/later-child or M11+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not acceptance.
