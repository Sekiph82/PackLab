# PL-0288 - Codex Work Order V02

Task: **Add package-family conversion safeguards across both parent authority modes**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M12-C001-R02
Branch: `main`

Master continuation prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_AUTHORITY_RESOLUTION_CONTINUATION_CODEX_PROMPT_V03.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0288_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0288_CODEX_LOG_V02.md

Architecture decision:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md

## Authorization and synchronization

Live `TASKS.md` must authorize M12-C001-R02 / PL-0288 V02 continuation / CODEX. Re-read M12 partial audit V02, ADR-0005, M11 accepted audit, M09 physical-validation deferral and this V02 criteria. Synchronize safely; preserve owner-local work; no reset/clean/rebase/force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0283_CODEX_PROMPT_V02.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0285_CODEX_PROMPT_V02.md

## Frozen scope

Implement intentional versioned family conversion across bottle/jar, jerrycan, tube and flexible-pack families. Conversions preserve the original revision and exact parent-authority mode. Semantic mapping must be explicit; unsupported features are reported and never silently discarded. Converting a standalone model must not invent Scan Master ancestry; converting a scan-bound model must not drop its exact captured parent. Cross-authority conversion/rebinding is out of scope unless an explicit reviewed operation exists.

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

At minimum cover: same-family no-op; explicit semantic mapping; unsupported feature report; original preservation; scan-bound parent preserved; standalone root preserved; cross-authority silent conversion rejected; deterministic conversion revision.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed V02 log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green, complete the M12 master/continuation handoff as BATCH_COMPLETED, confirm M13 not started, and stop for independent milestone audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
