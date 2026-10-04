# PL-0308 - Codex Work Order V01

Task: **Export PDF technical drawing without compromising vector source**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0308_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0308_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. Re-read M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical deferral and this criteria. Synchronize safely; preserve owner-local work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0307_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/pyproject.toml
- https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/DEPENDENCY_LICENSE_REGISTER.md

## Frozen scope

Implement PDF technical-drawing export only through a stable, offline, vector-preserving path compatible with PackLab's existing dependency/governance model. Prefer reusing the canonical drawing/vector model and an already-reviewed capability (for example an available PySide6/Qt vector PDF path) rather than introducing a new PDF dependency silently. If a new dependency would be required, stop BLOCKED for review. PDF is a presentation/export artifact: SVG/DXF/shared drawing model remain vector source truth. Preserve line/vector text quality, page size/orientation, title block, dimensions and disclaimers. Add render/parse verification so clipped/broken output fails.

## Drawing authority rules

- Technical drawing/vector/PDF artifacts are derived from exact Design Model/CAD representation revisions.
- Numerical dimension values come from source geometry, never rendered pixels.
- RELATIVE never silently becomes mm.
- mm_unverified may display/encode numerical mm only with explicit unverified disclaimer.
- Drawing consistency validation is software/numerical evidence, not physical metrology or mold/manufacturing approval.
- Shared drawing/vector model remains source truth; PDF is presentation export.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: capability probe for vector PDF path; one-page orthographic drawing; section/dimensions/title block; PDF parse/page count; vector-preserving or explicitly evidenced path; render smoke with no clipping; relative/mm_unverified disclaimer; no new unreviewed dependency; source SVG/drawing remains authoritative.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green continue directly to PL-0309 under the M13 master batch without intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
