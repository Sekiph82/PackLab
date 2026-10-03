# PL-0276 - ChatGPT Audit Criteria V01

Task: **Define assembly graph for body, closure, trigger/pump and dip tube**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Define an immutable versioned parametric assembly graph that composes bottle/body, closure, trigger/pump and dip-tube component revisions through stable feature/reference relationships. Assembly graph truth is metadata/parametric authority only; components retain their own revision identities and exact Scan Master/Design Model ancestry. Reject duplicate roles, stale component revisions, incompatible units/scale state and implicit retargeting.
3. Tests/evidence cover at minimum: body+closure+trigger+dip-tube graph, missing/duplicate role, stale component, unit/scale mismatch, deterministic assembly identity, component parent preservation, deferred-validation status.
4. Scan Master/Design Model/assembly/library/flexible-pack authority boundaries and inherited scale/deferred-validation state remain explicit; no hidden physical/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private/unlicensed asset/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0276_CODEX_PROMPT_V01.md
