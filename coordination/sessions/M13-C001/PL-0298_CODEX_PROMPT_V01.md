# PL-0298 - Codex Work Order V01

Task: **Export printable STL with explicit unit handling and mesh-quality options**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0298_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0298_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. Re-read M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical deferral and this criteria. Synchronize safely; preserve owner work; no reset/clean/rebase/force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0296_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CODEX_PROMPT_V01.md

## Frozen scope

Implement deterministic STL export from a validated CAD/BREP representation via controlled tessellation. STL has no reliable embedded unit metadata, so printable STL export must require `mm_unverified` source coordinates and produce a mandatory sidecar/export manifest declaring numerical coordinates are interpreted as millimetres but remain physically unverified. RELATIVE sources must fail closed for printable STL. Expose bounded mesh-quality options (deflection/angular tolerance or named presets) that map to explicit tessellation parameters; preserve source revision and topology-validation status. Do not call the STL production-ready or physically accurate.

## Export authority rules

- Export artifacts are derived from exact source revisions and never replace Scan Master, Design Model or CAD/BREP truth.
- `mm_unverified` may be encoded numerically as millimetres only when explicitly permitted by the child contract and must remain physically unverified.
- `RELATIVE` / `reconstruction_units` must never silently become millimetres.
- Successful export/round-trip is numerical/software evidence, not physical/mold/manufacturing validation.
- PL-0220 through PL-0224 remain DEFERRED_OWNER_VALIDATION.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: binary or explicitly selected STL mode; coarse/fine bounded presets; deterministic triangle output; mm_unverified sidecar; RELATIVE rejection; invalid BREP rejection; triangle/normal sanity; exact source revision; no print-fit/manufacturing claim.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0299; stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
