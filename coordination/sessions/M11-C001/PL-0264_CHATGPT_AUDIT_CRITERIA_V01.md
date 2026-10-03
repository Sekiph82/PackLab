# PL-0264 - ChatGPT Audit Criteria V01

Task: **Define neck/closure mating reference planes and axes**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0264_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Define stable parametric mating reference entities between bottle neck/finish and closure: canonical axis, neck/closure reference planes and explicit offsets. Bind references to stable feature IDs and current Design Model revision. Validate coaxial/alignment assumptions and expose mismatches; do not claim sealing/thread compatibility.
3. Tests cover at minimum: coaxial reference creation, offset plane, stale feature rejection, non-coaxial mismatch, deterministic IDs, edit persistence, no compatibility/seal claim.
4. Scan Master remains immutable; parametric closure/assembly truth remains separate; scale/deferred status is preserved; no hidden internal/thread/seal/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log commits are separate; completed log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects source/diff/evidence; builder validation is not acceptance.
