# PL-0308 - ChatGPT Audit Criteria V01

Task: **Export PDF technical drawing without compromising vector source**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic implementation is limited to: Implement PDF technical-drawing export only through a stable, offline, vector-preserving path compatible with PackLab's existing dependency/governance model. Prefer reusing the canonical drawing/vector model and an already-reviewed capability (for example an available PySide6/Qt vector PDF path) rather than introducing a new PDF dependency silently. If a new dependency would be required, stop BLOCKED for review. PDF is a presentation/export artifact: SVG/DXF/shared drawing model remain vector source truth. Preserve line/vector text quality, page size/orientation, title block, dimensions and disclaimers. Add render/parse verification so clipped/broken output fails.
3. Tests/evidence cover at minimum: capability probe for vector PDF path; one-page orthographic drawing; section/dimensions/title block; PDF parse/page count; vector-preserving or explicitly evidenced path; render smoke with no clipping; relative/mm_unverified disclaimer; no new unreviewed dependency; source SVG/drawing remains authoritative.
4. Exact Design Model/CAD parent revisions and units remain explicit; no pixel-derived dimensions, RELATIVE->mm promotion or physical/mold/manufacturing claim occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced; PL-0308 must block rather than silently add a PDF dependency.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0308_CODEX_PROMPT_V01.md
