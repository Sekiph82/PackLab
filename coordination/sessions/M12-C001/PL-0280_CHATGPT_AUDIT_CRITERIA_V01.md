# PL-0280 - ChatGPT Audit Criteria V01

Task: **Add assembly collision/basic interference diagnostics**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Implement bounded deterministic collision/interference diagnostics across Design Model assembly components and dip tube using derived proxy geometry where necessary. Report candidate overlaps, clearance estimates and unsupported/unknown cases. This is diagnostic only, not certified fit or manufacturing interference analysis. Preserve exact component revisions/placements.
3. Tests/evidence cover at minimum: separated components, known overlap, near-clearance boundary, proxy/unsupported case, deterministic pair ordering, exact parent placements, no certified fit claim.
4. Scan Master/Design Model/assembly/library/flexible-pack authority boundaries and inherited scale/deferred-validation state remain explicit; no hidden physical/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private/unlicensed asset/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0280_CODEX_PROMPT_V01.md
