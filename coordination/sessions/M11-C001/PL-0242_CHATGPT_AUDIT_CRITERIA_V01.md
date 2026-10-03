# PL-0242 - ChatGPT Audit Criteria V01

Task: **Define stable feature IDs and references for package features**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0242_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Define deterministic stable feature identifiers and typed references for body, base, shoulder, neck, finish and cap/closure components. Feature IDs must survive ordinary parameter edits when feature semantic identity remains, reject duplicate/ambiguous references and never be derived from ephemeral preview-mesh indices. Define replacement/deletion semantics explicitly so stale references fail rather than silently retarget.
3. Tests/evidence cover at minimum: stable IDs across parameter revision, duplicate/reused ID rejection, stale/deleted feature reference, body/base/shoulder/neck/finish/cap typing, deterministic reference serialization, no mesh-index identity.
4. Scan Master remains immutable parent authority; Design Model is separate parametric truth; preview meshes remain derived proxies; inherited scale/deferred-validation state cannot become physical/mold authority.
5. No unreviewed dependency/CAD backend/model/hosted/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
