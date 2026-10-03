# PL-0284 - Codex Work Order V01

Task: **Implement tube fitting from scan/reference dimensions**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0284_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0284_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001 / PL-0268 through PL-0288 / READY / CODEX. Re-read M12 master, M11 audit, M09 physical deferral and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0283_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/measurement_report.py

## Frozen scope

Fit the M12 tube parametric family from an exact Scan Master when available and/or explicitly supplied reference dimensions with source authority labels. Keep captured measurements, user/reference dimensions and modeled parameters distinct. Missing flexible-wall regions remain uncertain; no hidden wall-thickness or material deformation inference.

## Authority rules

Exact captured Scan Master remains immutable where present. Design Model/assembly/library/flexible-pack authorities remain explicitly separated. `METRIC_UNVERIFIED` stays unverified. Flexible-pack geometry is design/visualization geometry, not mold-grade. No M13 CAD/BREP/STEP implementation. No private/raw data or unlicensed library asset may be silently imported.

## Required tests/evidence

At minimum cover: scan-bound fit, explicit reference-dimension fit, mixed source provenance, missing/contradictory evidence, mm_unverified semantics, no wall-thickness/material inference.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green continue directly to PL-0285 under the M12 master batch without intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
