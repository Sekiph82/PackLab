# PL-0284 - Codex Work Order V02

Task: **Implement tube fitting from scan/reference dimensions under explicit authority provenance**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001-R02
Branch: `main`

Master continuation prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_AUTHORITY_RESOLUTION_CONTINUATION_CODEX_PROMPT_V03.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0284_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0284_CODEX_LOG_V02.md

Architecture decision:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001-R02 / PL-0284 V02 continuation / CODEX. Re-read M12 partial audit V02, ADR-0005, M11 accepted audit, M09 physical-validation deferral and this V02 criteria. Synchronize safely; preserve owner-local work; no reset/clean/rebase/force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0283_CODEX_PROMPT_V02.md
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/measurement_report.py

## Frozen scope

Fit the tube family from either:
(a) exact Scan Master evidence, producing/retaining a CAPTURED_SCAN_MASTER parent; or
(b) explicitly supplied reference/user dimensions under STANDALONE_DESIGN_GEOMETRY authority.
For mixed evidence, keep captured measurements, reference dimensions and modeled parameters separately labeled and choose the parent authority explicitly. Never silently convert reference dimensions into captured evidence. Missing flexible-wall regions remain uncertain; do not infer hidden wall thickness/material deformation.

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

At minimum cover: scan-bound fit; standalone reference-dimension fit; mixed source provenance; explicit parent authority selection; no fake scan lineage; contradictory/missing evidence; mm_unverified semantics; captured-only comparison rejection for standalone; no wall thickness/material deformation inference.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed V02 log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green, continue directly to PL-0285 V02 under the R02 master continuation without intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
