# PL-0307 - Codex Work Order V01

Task: **Export technical drawing to SVG and DXF**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0307_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0307_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. Re-read M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical deferral and this criteria. Synchronize safely; preserve owner-local work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0303_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0304_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0305_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0306_CODEX_PROMPT_V01.md

## Frozen scope

Implement deterministic vector export of M13 technical drawing views, section curves, dimension annotations and title block to SVG and DXF. The shared drawing model remains source truth. SVG must preserve vector primitives/text metadata and explicit viewBox/units. DXF must use a documented version/subset and layers for geometry, sections, dimensions, annotations/title block where supported. RELATIVE drawings must not masquerade as mm; mm_unverified drawings may encode millimetre numerical units only with explicit unverified metadata/disclaimer. Include output digests and drawing/source revisions.

## Drawing authority rules

- Technical drawing/vector/PDF artifacts are derived from exact Design Model/CAD representation revisions.
- Numerical dimension values come from source geometry, never rendered pixels.
- RELATIVE never silently becomes mm.
- mm_unverified may display/encode numerical mm only with explicit unverified disclaimer.
- Drawing consistency validation is software/numerical evidence, not physical metrology or mold/manufacturing approval.
- Shared drawing/vector model remains source truth; PDF is presentation export.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: SVG parse/vector primitives; DXF parse/basic entities; view/section/dimension/title layers; deterministic bytes where format permits or deterministic normalized content; unit metadata; special character escaping; no raster source; digests/provenance.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green continue directly to PL-0308 under the M13 master batch without intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
