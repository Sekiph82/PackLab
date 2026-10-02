# PL-0234 - ChatGPT Audit Criteria V01

Task: **Implement repeat-scan geometry registration service**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0234_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M09 partial frontier and owner deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement deterministic rigid point-cloud/mesh registration for comparing two captured/Scan Master revisions through the PackLab geometry adapter. Record initialization, convergence policy, transform, residuals/inlier statistics and both immutable parent revisions. Reject generated/AI inputs and incompatible/stale coordinate/scale states. Synthetic tests may prove algorithm behavior, but this child must not claim physical repeat-scan reproducibility because PL-0222 is deferred.
3. Tests/evidence cover at minimum: identity/known-transform synthetic registration, poor-overlap/non-convergence, deterministic transform, parent binding, relative/mm_unverified compatibility, generated input rejection, no physical reproducibility claim.
4. RAW_CAPTURE/reconstruction/original captured geometry remain immutable; revision/proxy/repair/export ancestry is explicit, inherited scale state is preserved and `DEFERRED_OWNER_VALIDATION` cannot become physical/mold authority.
5. Generated/AI_VISUAL_REFERENCE cannot become Scan Master authority. No unreviewed dependency/model/hosted/private evidence/later-child or M11+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not acceptance.
