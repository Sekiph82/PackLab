# PL-0235 - ChatGPT Audit Criteria V01

Task: **Implement scan-to-design distance heatmap contract**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0235_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M09 partial frontier and owner deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement a deterministic deviation/heatmap service between a selected Scan Master revision and an explicitly supplied fitted Design Model geometry reference. M11 fitting itself is out of scope; use a narrow PackLab-owned comparison input contract and synthetic fixtures. Record signed/unsigned distance policy, sampling, thresholds, scale state, parents and color-bin metadata. If physical validation is deferred or scale is unverified, report geometry deviation in inherited units and do not label results manufacturing tolerance.
3. Tests/evidence cover at minimum: zero deviation, known offset, mixed positive/negative distances where supported, sampling/bin thresholds, stale parent rejection, deterministic output, mm_unverified labeling, no M11 implementation.
4. RAW_CAPTURE/reconstruction/original captured geometry remain immutable; revision/proxy/repair/export ancestry is explicit, inherited scale state is preserved and `DEFERRED_OWNER_VALIDATION` cannot become physical/mold authority.
5. Generated/AI_VISUAL_REFERENCE cannot become Scan Master authority. No unreviewed dependency/model/hosted/private evidence/later-child or M11+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not acceptance.
