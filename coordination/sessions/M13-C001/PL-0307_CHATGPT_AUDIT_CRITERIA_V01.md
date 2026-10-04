# PL-0307 - ChatGPT Audit Criteria V01

Task: **Export technical drawing to SVG and DXF**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic implementation is limited to: Implement deterministic vector export of M13 technical drawing views, section curves, dimension annotations and title block to SVG and DXF. The shared drawing model remains source truth. SVG must preserve vector primitives/text metadata and explicit viewBox/units. DXF must use a documented version/subset and layers for geometry, sections, dimensions, annotations/title block where supported. RELATIVE drawings must not masquerade as mm; mm_unverified drawings may encode millimetre numerical units only with explicit unverified metadata/disclaimer. Include output digests and drawing/source revisions.
3. Tests/evidence cover at minimum: SVG parse/vector primitives; DXF parse/basic entities; view/section/dimension/title layers; deterministic bytes where format permits or deterministic normalized content; unit metadata; special character escaping; no raster source; digests/provenance.
4. Exact Design Model/CAD parent revisions and units remain explicit; no pixel-derived dimensions, RELATIVE->mm promotion or physical/mold/manufacturing claim occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced; PL-0308 must block rather than silently add a PDF dependency.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0307_CODEX_PROMPT_V01.md
