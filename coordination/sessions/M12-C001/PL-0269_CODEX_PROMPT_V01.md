# PL-0269 - Codex Work Order V01

Task: **Detect handle-void candidate from captured evidence**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0269_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0269_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001 / PL-0268 through PL-0288 / READY / CODEX. Re-read the M12 master, accepted M11 audit, M09 physical-validation deferral and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/scan_master.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/cross_section_overlay.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_model.py

## Frozen scope

Detect a handle/opening void candidate from selected Scan Master and jerrycan Design Model silhouette/cross-section evidence. Produce evidence-bound candidate metadata only: region, support, confidence/ambiguity, parent feature IDs and coverage limitations. Do not subtract geometry or create a handle opening yet. Hidden/unobserved void extent must remain unknown.

## Authority rules

- Exact Scan Master remains immutable captured reference.
- DESIGN_MODEL remains separate editable parametric authority.
- Derived previews/deformations are not Scan Master or physical truth.
- PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`; `METRIC_UNVERIFIED`/ `mm_unverified` stays unverified.
- No M13 CAD/BREP/STEP implementation or manufacturing/mold claims.
- No private/raw scan evidence may be embedded in reusable fixtures/presets.

## Required tests/evidence

At minimum cover: clear handle opening candidate, no-void case, ambiguous/multiple voids, incomplete coverage, deterministic region identity, stale parent rejection, no destructive boolean/hidden completion.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0270; stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
