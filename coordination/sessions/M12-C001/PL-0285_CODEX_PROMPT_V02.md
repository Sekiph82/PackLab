# PL-0285 - Codex Work Order V02

Task: **Define simplified sachet/pouch Design Model with standalone design authority**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001-R02
Branch: `main`

Master continuation prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_AUTHORITY_RESOLUTION_CONTINUATION_CODEX_PROMPT_V03.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0285_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0285_CODEX_LOG_V02.md

Architecture decision:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001-R02 / PL-0285 V02 continuation / CODEX. Re-read M12 partial audit V02, ADR-0005, M11 accepted audit, M09 physical-validation deferral and this V02 criteria. Synchronize safely; preserve owner-local work; no reset/clean/rebase/force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0283_CODEX_PROMPT_V02.md
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_model.py

## Frozen scope

Define a simplified sachet/pouch parametric family focused on artwork surfaces, overall dimensions, seal zones and basic front/back shape. Model-only creation must use STANDALONE_DESIGN_GEOMETRY by default. If a scan-bound path is supported, it must remain explicitly CAPTURED_SCAN_MASTER and separate. Classify the family as visualization/design geometry rather than mold-grade captured surface authority.

## Authority rules

- Support both explicit parent modes only where this task requires them: CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY.
- Never create a placeholder/fake Scan Master or fake scan/reconstruction/digest/provenance fields.
- Existing accepted scan-bound Design Model identities/serialization must remain backward compatible.
- Standalone model-only dimensions remain RELATIVE/reconstruction_units or METRIC_UNVERIFIED/mm_unverified with explicit source provenance.
- Standalone geometry is design authority only, not captured/physical/mold/manufacturing evidence.
- Scan Master remains immutable.
- PL-0220 through PL-0224 remain DEFERRED_OWNER_VALIDATION.
- No M13 CAD/BREP/OpenCascade/STEP implementation.

## Required tests/evidence

At minimum cover: standalone rectangular pouch/sachet; optional explicit scan-bound path if implemented; overall dimensions; seal-zone parameters; stable artwork surfaces; invalid seal/dimension relationships; deterministic graph/serialization/preview; visualization-only authority flag; no fake scan ancestry.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed V02 log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green, continue directly to PL-0286 V02 under the R02 master continuation without intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
