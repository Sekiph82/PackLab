# PL-0248 - ChatGPT Audit Criteria V01

Task: **Serialize Design Model parameters in versioned human-readable format**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0248_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement deterministic human-readable versioned serialization/deserialization for the Design Model graph, features, parametric operations, units, Scan Master parent binding and edit metadata. Use canonical ordering and integrity digest/version checks. Reject duplicate JSON keys, unsupported versions, malformed/stale authority and silent defaults that could change geometry. Do not serialize preview mesh as parametric truth.
3. Tests/evidence cover at minimum: round-trip equality, canonical bytes, duplicate-key rejection, version rejection, digest tamper, unit/parent preservation, feature/reference integrity, no preview mesh embedded.
4. Scan Master remains immutable parent authority; Design Model is separate parametric truth; preview meshes remain derived proxies; inherited scale/deferred-validation state cannot become physical/mold authority.
5. No unreviewed dependency/CAD backend/model/hosted/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
