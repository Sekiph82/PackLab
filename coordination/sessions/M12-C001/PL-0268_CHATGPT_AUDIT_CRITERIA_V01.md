# PL-0268 - ChatGPT Audit Criteria V01

Task: **Fit asymmetric/symmetric jerrycan body from stacked cross-sections**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Implement a jerrycan body fitting service over the M11 parametric kernel using ordered Scan Master cross-sections. Support symmetric and asymmetric stacked-section loft strategies, explicit side/front/back constraints and review-required ambiguity. Preserve exact Scan Master parent binding, stable feature IDs and inherited units/deferred physical validation. Do not model handles/voids in this child.
3. Tests/evidence cover at minimum: rectangular/rounded jerrycan sections, asymmetric case, symmetric case, missing/sparse sections, deterministic loft graph, stable body feature IDs, mm_unverified/deferred state, no handle modeling.
4. Scan Master remains immutable; Design Model/freeform/preview layers preserve exact parent/unit/deferred authority and never become captured or physical manufacturing truth.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0268_CODEX_PROMPT_V01.md
