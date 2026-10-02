# PL-0232 - ChatGPT Audit Criteria V01

Task: **Compute M10 geometric statistics**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0232_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, clean synchronization, accepted M09 partial frontier and owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement deterministic geometry statistics needed by later fitting/review: point/vertex/face counts, bounds, surface/edge statistics where applicable, connected-component summary, hole summary linkage, density/spacing proxies and any explicitly documented topology indicators. Metrics must state units/assumptions and remain diagnostics, not physical-accuracy claims. Bind exact geometry revision and scale state.
3. Tests/evidence cover at minimum: point-cloud and mesh stats, empty/degenerate rejection, relative/mm_unverified labeling, deterministic metrics, linkage to component/hole reports, no physical accuracy claim.
4. Parent captured evidence remains immutable; child/proxy/repair revisions preserve exact ancestry, inherited scale state and `DEFERRED_OWNER_VALIDATION` where applicable. No METRIC_VERIFIED, physical accuracy, mold/manufacturing or AI-authority claim is invented.
5. No unreviewed dependency/model/hosted service/private evidence/later-child or M11+ implementation is introduced. PL-0225 dependency changes require exact lock/license/capability evidence.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
