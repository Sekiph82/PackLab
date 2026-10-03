# PL-0268 - Codex Work Order V01

Task: **Fit asymmetric/symmetric jerrycan body from stacked cross-sections**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0268_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0268_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001 / PL-0268 through PL-0288 / READY / CODEX. Re-read the M12 master, accepted M11 audit, M09 physical-validation deferral and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/symmetric_section_loft.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_model.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/scan_master.py

## Frozen scope

Implement a jerrycan body fitting service over the M11 parametric kernel using ordered Scan Master cross-sections. Support symmetric and asymmetric stacked-section loft strategies, explicit side/front/back constraints and review-required ambiguity. Preserve exact Scan Master parent binding, stable feature IDs and inherited units/deferred physical validation. Do not model handles/voids in this child.

## Authority rules

- Exact Scan Master remains immutable captured reference.
- DESIGN_MODEL remains separate editable parametric authority.
- Derived previews/deformations are not Scan Master or physical truth.
- PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`; `METRIC_UNVERIFIED`/ `mm_unverified` stays unverified.
- No M13 CAD/BREP/STEP implementation or manufacturing/mold claims.
- No private/raw scan evidence may be embedded in reusable fixtures/presets.

## Required tests/evidence

At minimum cover: rectangular/rounded jerrycan sections, asymmetric case, symmetric case, missing/sparse sections, deterministic loft graph, stable body feature IDs, mm_unverified/deferred state, no handle modeling.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0269; stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
