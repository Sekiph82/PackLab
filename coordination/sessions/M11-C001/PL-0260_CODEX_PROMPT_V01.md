# PL-0260 - Codex Work Order V01

Task: **Save fitting preset and parameters independently of raw scan**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M11-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0260_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0260_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M11-C001 / PL-0241 through PL-0267 batch / READY / CODEX. Re-read the M11 master, M10 audit, M09 physical-validation deferral, repository rules and this criteria. Fetch/fast-forward only when clean/safe. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0248_CODEX_PROMPT_V01.md

## Frozen scope

Define deterministic versioned fitting presets containing strategy, fitting algorithm parameters, constraints and reusable package-family defaults without embedding raw scan bytes or project-private geometry. Applying a preset to a different Scan Master creates new project-specific fitting evidence and does not copy parent IDs or claim identical fit quality.

## Authority rules

- Pin one exact Scan Master parent via the accepted M10 binding seam.
- Design Model parametric truth is separate from Scan Master and preview triangles.
- `METRIC_UNVERIFIED`/ `mm_unverified` remains unverified while PL-0220–0224 are deferred.
- No manufacturing/mold tolerance or CAD/BREP authority claim.
- M12+ and M13 CAD implementation are unauthorized.

## Required tests/evidence

At minimum cover: preset round-trip, canonical serialization, apply to new parent, no raw scan/geometry bytes, parameter/version validation, stale/unsupported preset rejection, no copied fit-quality claim.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected scope, dependency/license/privacy/secrets/generated/binary and remote checks.

Publish implementation/evidence commit(s), then a separate child-log-only commit ending exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0261 without intermediate audit. Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
