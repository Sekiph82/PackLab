# PL-0304 - Codex Work Order V01

Task: **Generate section views at user-selected heights/planes**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0304_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0304_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. Re-read M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical deferral and this criteria. Synchronize safely; preserve owner-local work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0303_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0294_CODEX_PROMPT_V01.md

## Frozen scope

Implement deterministic technical-drawing section views from validated CAD/BREP solids at explicit user-selected canonical heights/planes. Record plane definition, intersected components/features, section curves, hatching regions where safely derivable, and empty/no-intersection cases. Section view geometry is drawing evidence derived from CAD representation; it does not alter Design Model or BREP. Bound work and reject invalid/non-finite planes.

## Drawing authority rules

- Technical drawing/vector/PDF artifacts are derived from exact Design Model/CAD representation revisions.
- Numerical dimension values come from source geometry, never rendered pixels.
- RELATIVE never silently becomes mm.
- mm_unverified may display/encode numerical mm only with explicit unverified disclaimer.
- Drawing consistency validation is software/numerical evidence, not physical metrology or mold/manufacturing approval.
- Shared drawing/vector model remains source truth; PDF is presentation export.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: horizontal/vertical section; empty section; multi-component assembly section; deterministic curve ordering; invalid plane; feature/part provenance; optional hatch metadata; no source mutation.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green continue directly to PL-0305 under the M13 master batch without intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
