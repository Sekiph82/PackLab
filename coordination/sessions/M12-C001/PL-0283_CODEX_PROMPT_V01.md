# PL-0283 - Codex Work Order V01

Task: **Define tube parametric family**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0283_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0283_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001 / PL-0268 through PL-0288 / READY / CODEX. Re-read M12 master, M11 audit, M09 physical deferral and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_model.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_operations.py

## Frozen scope

Define a PackLab Design Model package family for collapsible/squeeze tubes with body, shoulder, neck, cap and crimp features plus stable references and backend-neutral parametric operations. Preserve exact Scan Master parent where fitted; support model-only creation only with explicit design-geometry authority. Do not claim flexible-wall physical deformation accuracy.

## Authority rules

Exact captured Scan Master remains immutable where present. Design Model/assembly/library/flexible-pack authorities remain explicitly separated. `METRIC_UNVERIFIED` stays unverified. Flexible-pack geometry is design/visualization geometry, not mold-grade. No M13 CAD/BREP/STEP implementation. No private/raw data or unlicensed library asset may be silently imported.

## Required tests/evidence

At minimum cover: tube family graph, body/shoulder/neck/cap/crimp stable features, valid parameter relationships, impossible dimension rejection, unit/deferred state, deterministic serialization/preview.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green continue directly to PL-0284 under the M12 master batch without intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
