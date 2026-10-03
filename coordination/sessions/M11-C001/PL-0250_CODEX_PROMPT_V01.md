# PL-0250 - Codex Work Order V01

Task: **Detect rotational/symmetry characteristics and choose bottle fitting strategy**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M11-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0250_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0250_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M11-C001 / PL-0241 through PL-0267 batch / READY / CODEX. Re-read the M11 master, M10 audit, M09 physical-validation deferral, repository rules and this criteria. Fetch/fast-forward only when clean/safe. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/scan_master.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/geometry_statistics.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/cross_section_overlay.py

## Frozen scope

Analyze the selected Scan Master plus M10/M09 profile/cross-section evidence to produce a deterministic fitting-strategy recommendation: axisymmetric revolve, symmetric stacked-section loft, or review-required. Record evidence metrics/thresholds, parent Scan Master binding and uncertainty. This is strategy selection only, not Design Model fitting, and no symmetry may be treated as physical truth without evidence.

## Authority rules

- Pin one exact Scan Master parent via the accepted M10 binding seam.
- Design Model parametric truth is separate from Scan Master and preview triangles.
- `METRIC_UNVERIFIED`/ `mm_unverified` remains unverified while PL-0220–0224 are deferred.
- No manufacturing/mold tolerance or CAD/BREP authority claim.
- M12+ and M13 CAD implementation are unauthorized.

## Required tests/evidence

At minimum cover: synthetic rotational body, non-circular symmetric body, asymmetric/review-required case, threshold boundaries, stale parent, deterministic strategy/evidence, mm_unverified/deferred status.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected scope, dependency/license/privacy/secrets/generated/binary and remote checks.

Publish implementation/evidence commit(s), then a separate child-log-only commit ending exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0251 without intermediate audit. Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
