# PL-0241 - Codex Work Order V01

Task: **Define Design Model parameter graph separate from triangle-mesh data**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M11-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0241_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0241_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M11-C001 / ordered PL-0241 through PL-0267 batch / READY / CODEX. Re-read the M11 master prompt, accepted M10 audit, M09 physical-validation deferral, repository rules and this child criteria. Fetch/fast-forward only when safe and clean. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/design_model_binding.py
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0233_SCAN_MASTER_AUTHORITY.md

## Frozen scope

Define the PackLab-owned Design Model graph as immutable/versioned parametric truth independent of scan triangles and preview tessellation. Represent model revision identity, package family, parameter nodes, feature/component references, parent Scan Master binding, inherited scale state/provenance, deferred physical-validation status and edit ancestry. The graph must not embed Open3D/CAD backend objects or silently copy Scan Master triangles as parametric authority.

## Authority and deferred-validation rules

- Design Model is a separate editable parametric authority and never rewrites Scan Master.
- It pins an exact Scan Master parent/revision.
- PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`.
- `METRIC_UNVERIFIED` remains unverified; use `mm_unverified` where appropriate, never verified-mm/mold-ready claims.
- Preview/tessellated meshes are derived proxies, not parametric truth or Scan Master.
- M12+ and M13 CAD/BREP work are unauthorized.

## Required tests/evidence

At minimum cover: deterministic graph identity, explicit Scan Master parent binding, immutable revisions, parameter uniqueness/type validation, RELATIVE/mm_unverified semantics, no triangle-mesh authority leakage, serialization-ready values, deferred validation/mold false.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks.

Use separate implementation/evidence and child-log-only commits. Completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green and no real stop condition exists, continue directly to PL-0242 under the master batch without waiting for intermediate ChatGPT audit. Stop only on FAILED/BLOCKED/OWNER_REQUIRED or master stop condition.
