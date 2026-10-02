# PL-0227 - ChatGPT Audit Criteria V01

Task: **Implement normal estimation and orientation repair**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0227_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, clean synchronization, accepted M09 partial frontier and owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement deterministic, bounded normal estimation/orientation repair for M10 geometry revisions. Record neighborhood/search parameters, orientation strategy and unresolved/ambiguous normals. Never mutate the parent geometry or infer physical orientation from normals. Preserve captured ancestry, scale state and deferred-validation status.
3. Tests/evidence cover at minimum: plane/sphere synthetic normals, neighborhood boundaries, orientation consistency, sparse/degenerate points, deterministic output, parent immutability, provenance.
4. Parent captured evidence remains immutable; child/proxy/repair revisions preserve exact ancestry, inherited scale state and `DEFERRED_OWNER_VALIDATION` where applicable. No METRIC_VERIFIED, physical accuracy, mold/manufacturing or AI-authority claim is invented.
5. No unreviewed dependency/model/hosted service/private evidence/later-child or M11+ implementation is introduced. PL-0225 dependency changes require exact lock/license/capability evidence.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and completed child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
