# PL-0296 - Codex Work Order V01

Task: **Tessellate BREP back to preview mesh with controlled tolerance**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0296_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0296_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 batch / READY / CODEX. Re-read the M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical-validation deferral, repository rules and this child criteria. Fetch and fast-forward only if clean and behind-only. Preserve owner-local work; never reset, clean, rebase or force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0294_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0295_CODEX_PROMPT_V01.md

## Frozen scope

Implement deterministic tessellation of accepted BREP representations into derived PREVIEW_PROXY mesh geometry through the CAD adapter. Tessellation deflection/angle/work limits must be explicit and bounded; preserve CAD/Design Model revision linkage and named-feature mapping where supported. Preview geometry is disposable and may not become CAD truth, Design Model truth or Scan Master. Compare basic bounds/counts against source CAD representation and report tessellation limitations.

## CAD authority and physical-validation rules

- CAD/BREP is a derived engineering representation of exact Design Model revision truth.
- CAD never replaces Scan Master or Design Model authority.
- CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY parent modes remain explicit.
- `METRIC_UNVERIFIED` / `mm_unverified` remains unverified; `RELATIVE` must never silently become mm.
- Topology validity, STEP/STL validity or successful export is not evidence of physical accuracy, mold readiness or manufacturing suitability.
- PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: coarse/fine tolerance; deterministic vertices/triangles; work bounds; BREP bounds consistency; feature-to-preview mapping; invalid BREP rejection; PREVIEW_PROXY authority; relative/mm_unverified propagation; no Scan Master promotion.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, dependency/license/privacy/secrets/generated/binary/scope/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green and no real stop condition exists, continue directly to PL-0297 under the master batch without waiting for intermediate ChatGPT audit. Stop only on FAILED/BLOCKED/OWNER_REQUIRED/master stop.
