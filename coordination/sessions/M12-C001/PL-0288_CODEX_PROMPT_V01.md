# PL-0288 - Codex Work Order V01

Task: **Add package-family selection and conversion safeguards**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0288_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0288_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001 / PL-0268 through PL-0288 / READY / CODEX. Re-read M12 master, M11 audit, M09 physical deferral and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_model.py
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0283_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0285_CODEX_PROMPT_V01.md

## Frozen scope

Implement explicit package-family selection/conversion rules across supported M11/M12 families (bottle/jar, jerrycan, tube, flexible pack). Conversion must be intentional, versioned and only allowed when semantic features/parameters have an explicit mapping; unsupported features are reported, never silently discarded. Preserve original revisions and Scan Master parent binding where applicable.

## Authority rules

Exact captured Scan Master remains immutable where present. Design Model/assembly/library/flexible-pack authorities remain explicitly separated. `METRIC_UNVERIFIED` stays unverified. Flexible-pack geometry is design/visualization geometry, not mold-grade. No M13 CAD/BREP/STEP implementation. No private/raw data or unlicensed library asset may be silently imported.

## Required tests/evidence

At minimum cover: same-family no-op, supported bottle-to-jerrycan-style conversion where mapping explicit, unsupported handle/closure/flexible feature reporting, original revision preservation, exact parent binding, deterministic conversion revision.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If this final child is green, complete the M12 master log as BATCH_COMPLETED, verify clean local/origin/GitHub parity, confirm M13 was not started, end exactly `AWAITING_MILESTONE_AUDIT`, publish separately and stop.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
