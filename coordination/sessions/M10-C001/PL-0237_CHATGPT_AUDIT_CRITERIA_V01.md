# PL-0237 - ChatGPT Audit Criteria V01

Task: **Record reconstruction and Scan Master versions with explicit selection**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0237_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M09 partial frontier and owner deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement append-only project revision metadata for reconstruction/object-geometry/M10 cleanup/Scan Master chains and explicit active-selection switching. Switching selects an existing revision; it never mutates or retargets downstream parents. Preserve history across reopen and reject missing/stale/duplicate revisions. Physical-validation deferred status and scale state travel with each Scan Master revision.
3. Tests/evidence cover at minimum: append/reopen/switch, duplicate/missing revision rejection, active pointer, downstream parent stability, deferred-validation persistence, optimistic concurrency.
4. RAW_CAPTURE/reconstruction/original captured geometry remain immutable; revision/proxy/repair/export ancestry is explicit, inherited scale state is preserved and `DEFERRED_OWNER_VALIDATION` cannot become physical/mold authority.
5. Generated/AI_VISUAL_REFERENCE cannot become Scan Master authority. No unreviewed dependency/model/hosted/private evidence/later-child or M11+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not acceptance.
