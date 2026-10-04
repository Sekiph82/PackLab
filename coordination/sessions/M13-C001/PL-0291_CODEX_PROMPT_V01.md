# PL-0291 - Codex Work Order V01

Task: **Convert profile/revolve Design Models into BREP solids**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0291_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0291_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 batch / READY / CODEX. Re-read the M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical-validation deferral, repository rules and this child criteria. Fetch and fast-forward only if clean and behind-only. Preserve owner-local work; never reset, clean, rebase or force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0290_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_operations.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_profile.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_model.py

## Frozen scope

Implement deterministic conversion of accepted M11/M12 revolve-based Design Models into BREP solids through the PackLab CAD adapter. Consume explicit profile/revolve operation, stable feature references, exact model revision and parent-authority metadata. Validate profile closure/axis/orientation and reject invalid/self-intersecting/degenerate inputs. Output is a new CAD representation revision linked to the exact Design Model, never a replacement for Design Model or Scan Master. Coordinates remain in the Design Model's coordinate unit; do not silently treat RELATIVE as mm. For mm_unverified models, the CAD representation may carry millimetre-like numerical units only with explicit unverified authority metadata.

## CAD authority and physical-validation rules

- CAD/BREP is a derived engineering representation of exact Design Model revision truth.
- CAD never replaces Scan Master or Design Model authority.
- CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY parent modes remain explicit.
- `METRIC_UNVERIFIED` / `mm_unverified` remains unverified; `RELATIVE` must never silently become mm.
- Topology validity, STEP/STL validity or successful export is not evidence of physical accuracy, mold readiness or manufacturing suitability.
- PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: cylinder/bottle revolve; axis/profile validation; deterministic BREP digest/revision; scan-bound and standalone parent propagation; RELATIVE vs mm_unverified units; degenerate/self-intersecting profile rejection; Design Model immutability; no physical/mold claim.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, dependency/license/privacy/secrets/generated/binary/scope/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green and no real stop condition exists, continue directly to PL-0292 under the master batch without waiting for intermediate ChatGPT audit. Stop only on FAILED/BLOCKED/OWNER_REQUIRED/master stop.
