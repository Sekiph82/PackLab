# PL-0273 - Codex Work Order V01

Task: **Constrain cage edits to preserve key dimensions and symmetry**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0273_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0273_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001 / PL-0268 through PL-0288 / READY / CODEX. Re-read the M12 master, accepted M11 audit, M09 physical-validation deferral and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0272_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_dimensions.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_symmetry_constraints.py

## Frozen scope

Add constraints for cage/freeform edits so selected key dimensions, mating references and enabled symmetry relationships remain preserved within exact numerical rules. Reject edits that violate protected dimensions or impossible constraints; never silently relax them. Record constrained/unconstrained degrees of freedom and residual diagnostics.

## Authority rules

- Exact Scan Master remains immutable captured reference.
- DESIGN_MODEL remains separate editable parametric authority.
- Derived previews/deformations are not Scan Master or physical truth.
- PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`; `METRIC_UNVERIFIED`/ `mm_unverified` stays unverified.
- No M13 CAD/BREP/STEP implementation or manufacturing/mold claims.
- No private/raw scan evidence may be embedded in reusable fixtures/presets.

## Required tests/evidence

At minimum cover: protected height/width/depth, symmetry on/off, valid local deformation, violating deformation rejection, mating-reference preservation, deterministic residuals, undo/redo compatibility.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0274; stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
