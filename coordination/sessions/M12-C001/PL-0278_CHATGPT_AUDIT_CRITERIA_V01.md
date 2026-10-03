# PL-0278 - ChatGPT Audit Criteria V01

Task: **Align library trigger/pump component to detected neck reference**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Implement deterministic alignment of an accepted reusable trigger/pump component to explicit M11 neck/closure mating references. Validate attachment axis/plane, component unit/scale metadata and exact bottle/closure revision parents. Output a new assembly placement revision; do not deform bottle geometry or claim thread/seal compatibility.
3. Tests/evidence cover at minimum: identity/known transform, axis/plane mismatch, stale parent, unit mismatch, deterministic rigid placement, no bottle mutation, no seal/thread compatibility claim.
4. Scan Master/Design Model/assembly/library/flexible-pack authority boundaries and inherited scale/deferred-validation state remain explicit; no hidden physical/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private/unlicensed asset/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0278_CODEX_PROMPT_V01.md
