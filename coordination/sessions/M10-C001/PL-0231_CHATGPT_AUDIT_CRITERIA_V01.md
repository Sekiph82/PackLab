# PL-0231 - ChatGPT Audit Criteria V01

Task: **Create viewport/proxy decimation while preserving full reference geometry**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0231_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, clean synchronization, accepted M09 partial frontier and owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement deterministic proxy decimation with explicit target policy and quality evidence. The full cleaned geometry remains the authoritative candidate reference; proxy outputs are authority_class PREVIEW_PROXY and must carry a back-reference to their exact full parent. Never replace or relabel a proxy as Scan Master. Preserve textures/UV references where supported or report unavailable truthfully.
3. Tests/evidence cover at minimum: target triangle/point reduction, no-op threshold, proxy parent binding, deterministic identity, full parent byte/digest preservation, texture/UV limitation reporting, proxy authority rejection.
4. Parent captured evidence remains immutable; child/proxy/repair revisions preserve exact ancestry, inherited scale state and `DEFERRED_OWNER_VALIDATION` where applicable. No METRIC_VERIFIED, physical accuracy, mold/manufacturing or AI-authority claim is invented.
5. No unreviewed dependency/model/hosted service/private evidence/later-child or M11+ implementation is introduced. PL-0225 dependency changes require exact lock/license/capability evidence.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
