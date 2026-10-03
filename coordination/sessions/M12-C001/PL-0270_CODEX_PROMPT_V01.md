# PL-0270 - Codex Work Order V01

Task: **Model handle opening as editable constrained feature**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0270_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0270_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001 / PL-0268 through PL-0288 / READY / CODEX. Re-read the M12 master, accepted M11 audit, M09 physical-validation deferral and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0269_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_model.py

## Frozen scope

Create an editable parametric handle-opening feature from an accepted PL-0269 candidate. Represent opening profile/path/clearance envelope and relationship to jerrycan body as versioned Design Model parameters/features. The opening is modeling geometry, not copied scan triangles. Apply explicit constraints to keep it inside supported body regions and reject impossible/self-intersecting states.

## Authority rules

- Exact Scan Master remains immutable captured reference.
- DESIGN_MODEL remains separate editable parametric authority.
- Derived previews/deformations are not Scan Master or physical truth.
- PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`; `METRIC_UNVERIFIED`/ `mm_unverified` stays unverified.
- No M13 CAD/BREP/STEP implementation or manufacturing/mold claims.
- No private/raw scan evidence may be embedded in reusable fixtures/presets.

## Required tests/evidence

At minimum cover: valid opening feature, move/resize edit, body-bound constraints, self-intersection/out-of-body rejection, stable feature identity, undo/redo compatibility, no Scan Master mutation.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0271; stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
