# PL-0275 - Codex Work Order V01

Task: **Validate 2 L/5 L style jerrycan benchmark geometry synthetically/publicly**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0275_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0275_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001 / PL-0268 through PL-0288 / READY / CODEX. Re-read the M12 master, accepted M11 audit, M09 physical-validation deferral and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0268_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0270_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0271_CODEX_PROMPT_V01.md

## Frozen scope

Create a reproducible non-private synthetic/public geometry benchmark for representative 2 L and 5 L style jerrycan Design Models covering body, handle opening and grip/indent behavior. This is a software/geometry benchmark only, not a physical dimensional-accuracy benchmark and not a substitute for deferred PL-0220–PL-0224. Record fixtures, expected parametric invariants, deviation diagnostics and limitations.

## Authority rules

- Exact Scan Master remains immutable captured reference.
- DESIGN_MODEL remains separate editable parametric authority.
- Derived previews/deformations are not Scan Master or physical truth.
- PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`; `METRIC_UNVERIFIED`/ `mm_unverified` stays unverified.
- No M13 CAD/BREP/STEP implementation or manufacturing/mold claims.
- No private/raw scan evidence may be embedded in reusable fixtures/presets.

## Required tests/evidence

At minimum cover: 2L-style and 5L-style synthetic fixtures, deterministic fitting/edit invariants, handle feature retention, invalid fixture negative case, no owner/private evidence, explicit non-physical benchmark disclaimer.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0276; stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
