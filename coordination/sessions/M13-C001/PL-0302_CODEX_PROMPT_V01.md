# PL-0302 - Codex Work Order V01

Task: **Add export UI distinguishing Scan Mesh from editable Design Model**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0302_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0302_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. Re-read M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical deferral and this criteria. Synchronize safely; preserve owner work; no reset/clean/rebase/force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0298_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/apps/windows-studio/src/packlab_studio/project.py

## Frozen scope

Implement Windows Studio export UI/workflow that clearly separates Scan Mesh/Scan Master export from editable Design Model/CAD export. The UI must show the selected source authority, revision, units/scale status, physical-validation disclaimer and available formats before export. Domain services remain authoritative; UI must not bypass CAD validation, RELATIVE->mm guards, or export manifest creation. Scan Mesh export must route only through accepted scan export services; Design Model export must route through M13 CAD/export services. No ambiguous single 'Export' action that hides source type.

## Export authority rules

- Export artifacts are derived from exact source revisions and never replace Scan Master, Design Model or CAD/BREP truth.
- `mm_unverified` may be encoded numerically as millimetres only when explicitly permitted by the child contract and must remain physically unverified.
- `RELATIVE` / `reconstruction_units` must never silently become millimetres.
- Successful export/round-trip is numerical/software evidence, not physical/mold/manufacturing validation.
- PL-0220 through PL-0224 remain DEFERRED_OWNER_VALIDATION.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: source-type selector/summary; Scan Mesh vs Design Model labels; format gating; RELATIVE mm-export disabled/rejected; mm_unverified disclaimer; exact revision display; domain-service delegation; cancel/error path; no authority mutation.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0303; stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
