# PL-0293 - Codex Work Order V01

Task: **Implement boolean feature support for handle openings and simple indentations**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0293_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0293_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 batch / READY / CODEX. Re-read the M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical-validation deferral, repository rules and this child criteria. Fetch and fast-forward only if clean and behind-only. Preserve owner-local work; never reset, clean, rebase or force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0291_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0292_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/jerrycan_handle_opening.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/jerrycan_grip_indent.py

## Frozen scope

Implement a narrow, deterministic boolean feature layer needed by existing parametric handle openings and simple grip/indent features. Boolean operations must be driven by explicit Design Model feature parameters/reference geometry, not raw scan triangles. Record operation type, tool/body feature IDs, adapter/kernel result, topology status and failure diagnostics. Limit scope to subtraction/cut operations required by current M12 features; no arbitrary CAD modeling suite. Boolean failure must remain explicit and must not silently drop the feature.

## CAD authority and physical-validation rules

- CAD/BREP is a derived engineering representation of exact Design Model revision truth.
- CAD never replaces Scan Master or Design Model authority.
- CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY parent modes remain explicit.
- `METRIC_UNVERIFIED` / `mm_unverified` remains unverified; `RELATIVE` must never silently become mm.
- Topology validity, STEP/STL validity or successful export is not evidence of physical accuracy, mold readiness or manufacturing suitability.
- PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: handle opening cut; simple indent cut where representable; tool outside body; nonintersecting boolean; invalid tool; deterministic operation provenance; stable feature linkage; failure leaves parent BREP/model unchanged; no raw scan boolean.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, dependency/license/privacy/secrets/generated/binary/scope/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green and no real stop condition exists, continue directly to PL-0294 under the master batch without waiting for intermediate ChatGPT audit. Stop only on FAILED/BLOCKED/OWNER_REQUIRED/master stop.
