# PL-0261 - ChatGPT Audit Criteria V01

Task: **Separate cap/closure from body when scan evidence allows**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0261_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Implement deterministic evidence-driven cap/closure separation candidates from the selected Scan Master and accepted neck/finish/profile evidence. Separation must be conservative, preserve captured parent geometry, expose ambiguity/support evidence and create Design Model component candidates only when evidence is sufficient. Do not destructively split Scan Master or invent hidden closure geometry.
3. Tests cover at minimum: clear cap/body separation, ambiguous/no-separation case, support thresholds, stale parent, stable feature/component IDs, no Scan Master mutation, unit/deferred status.
4. Scan Master remains immutable; parametric closure/assembly truth remains separate; scale/deferred status is preserved; no hidden internal/thread/seal/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log commits are separate; completed log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects source/diff/evidence; builder validation is not acceptance.
