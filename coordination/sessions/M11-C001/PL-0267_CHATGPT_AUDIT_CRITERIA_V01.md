# PL-0267 - ChatGPT Audit Criteria V01

Task: **Validate bottle/cap assembly transforms on export**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0267_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Implement deterministic validation/export metadata for bottle+closure Design Model assembly transforms. Check mating reference IDs/axes/planes, component revisions, transform rigidity and unit/scale consistency before export handoff. This child validates assembly transforms and produces export-ready metadata/preview relationships only; actual CAD/STEP export remains M13. Reject stale/incompatible components and preserve deferred physical-validation limits.
3. Tests cover at minimum: identity/known valid transform, stale component, non-rigid transform, axis/plane mismatch, unit mismatch, deterministic assembly metadata, mm_unverified/deferred disclaimer, no STEP/CAD implementation.
4. Scan Master remains immutable; parametric closure/assembly truth remains separate; scale/deferred status is preserved; no hidden internal/thread/seal/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log commits are separate; completed log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects source/diff/evidence; builder validation is not acceptance.
