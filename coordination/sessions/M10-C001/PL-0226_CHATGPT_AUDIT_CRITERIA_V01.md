# PL-0226 - ChatGPT Audit Criteria V01

Task: **Remove isolated floating components with configurable safeguards**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0226_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, clean synchronization, accepted M09 partial frontier and owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement non-destructive component analysis/removal over captured or M10-derived geometry through the PackLab adapter. Component connectivity/distance policy, minimum support thresholds and maximum removable fraction must be explicit/versioned. Preserve the largest/main component unless an explicit safe rule says otherwise. Produce a child revision with removed-component evidence, never overwrite the parent, and retain deferred physical-validation/scale state.
3. Tests/evidence cover at minimum: synthetic main-plus-floaters, threshold boundaries, all-small/ambiguous case, removal fraction safeguard, deterministic component ordering, parent immutability, provenance, METRIC_UNVERIFIED preservation.
4. Parent captured evidence remains immutable; child/proxy/repair revisions preserve exact ancestry, inherited scale state and `DEFERRED_OWNER_VALIDATION` where applicable. No METRIC_VERIFIED, physical accuracy, mold/manufacturing or AI-authority claim is invented.
5. No unreviewed dependency/model/hosted service/private evidence/later-child or M11+ implementation is introduced. PL-0225 dependency changes require exact lock/license/capability evidence.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
