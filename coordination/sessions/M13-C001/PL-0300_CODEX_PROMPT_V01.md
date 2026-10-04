# PL-0300 - Codex Work Order V01

Task: **Add export manifest for source project, revision, scale and software versions**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0300_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0300_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. Re-read M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical deferral and this criteria. Synchronize safely; preserve owner work; no reset/clean/rebase/force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0289_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0298_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CODEX_PROMPT_V01.md

## Frozen scope

Implement one canonical machine-readable export manifest contract shared by M13 STEP/STL/OBJ/GLB exports. Record project ID, export ID, format, exact Design Model revision, parent-authority kind/root or Scan Master binding, CAD representation revision/digest, source coordinate unit/scale state, any export-space scaling transform, topology-validation result, tessellation settings where applicable, selected Python binding version, observed OCCT/kernel version, PackLab version/commit, file digests, component/part names, named-feature mapping status, physical-validation status and limitations. Manifest identity must be deterministic over export content/provenance, excluding ambient paths/timestamps where inappropriate.

## Export authority rules

- Export artifacts are derived from exact source revisions and never replace Scan Master, Design Model or CAD/BREP truth.
- `mm_unverified` may be encoded numerically as millimetres only when explicitly permitted by the child contract and must remain physically unverified.
- `RELATIVE` / `reconstruction_units` must never silently become millimetres.
- Successful export/round-trip is numerical/software evidence, not physical/mold/manufacturing validation.
- PL-0220 through PL-0224 remain DEFERRED_OWNER_VALIDATION.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: STEP/STL/OBJ/GLB manifest variants; file SHA-256; parent authority; unit/scale transform; software/kernel versions; topology/tessellation metadata; privacy-safe path handling; deterministic manifest ID; no physical validation escalation.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0301; stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
