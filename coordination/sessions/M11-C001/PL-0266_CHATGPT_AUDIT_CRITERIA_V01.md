# PL-0266 - ChatGPT Audit Criteria V01

Task: **Add closure dimensions to measurement report**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0266_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Extend the existing measurement/report layer with Design Model closure dimensions that are explicitly sourced from the parametric closure revision and exact Scan Master/scale parent. Keep captured measurements distinct from modeled dimensions. Use inherited units and uncertainty/fit evidence; while physical validation is deferred, never label closure dimensions certified/mold-ready.
3. Tests cover at minimum: cylindrical/flip-top dimension summaries, parametric-vs-captured source labeling, parent/scale binding, stale model rejection, mm_unverified semantics, deterministic report, no certified claim.
4. Scan Master remains immutable; parametric closure/assembly truth remains separate; scale/deferred status is preserved; no hidden internal/thread/seal/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log commits are separate; completed log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects source/diff/evidence; builder validation is not acceptance.
