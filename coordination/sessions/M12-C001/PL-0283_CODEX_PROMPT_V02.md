# PL-0283 - Codex Work Order V02

Task: **Define tube parametric family with explicit standalone Design Geometry root**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001-R02
Branch: `main`

Master continuation prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_AUTHORITY_RESOLUTION_CONTINUATION_CODEX_PROMPT_V03.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0283_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0283_CODEX_LOG_V02.md

Architecture decision:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001-R02 / PL-0283 V02 continuation / CODEX. Re-read M12 partial audit V02, ADR-0005, M11 accepted audit, M09 physical-validation deferral and this V02 criteria. Synchronize safely; preserve owner-local work; no reset/clean/rebase/force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_model.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_model_binding.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_serialization.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_history.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_validation.py

## Frozen scope

First implement the ADR-0005 authority foundation required for truthful model-only Design Models, then define the tube family.

Authority foundation may modify shared Design Model parent/binding/serialization/history/validation/preview contracts as necessary, but must be backward compatible for existing scan-bound revisions. Introduce an immutable versioned standalone Design Geometry root and explicit parent discrimination. No fake scan lineage is allowed.

Then define the collapsible/squeeze tube family with body, shoulder, neck, cap and crimp stable features and backend-neutral parametric operations. Support:
(a) scan-bound tube Design Models using the existing exact Scan Master parent path; and
(b) model-only tube creation from an explicit standalone Design Geometry root.
Do not claim flexible-wall physical deformation accuracy.

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

At minimum cover: standalone root deterministic identity/digest/provenance; no fake scan fields; scan-bound revision/serialization regression stability; standalone serialization/history/validation/preview; captured-only service rejection of standalone; tube graph for both parent modes; body/shoulder/neck/cap/crimp stable features; impossible dimensions; RELATIVE/mm_unverified semantics; deterministic preview.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed V02 log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green, continue directly to PL-0284 V02 under the R02 master continuation without intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
