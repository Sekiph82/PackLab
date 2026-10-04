# PL-0296 - ChatGPT Audit Criteria V01

Task: **Tessellate BREP back to preview mesh with controlled tolerance**

All criteria are mandatory.

1. M13 tracker/master authorization, safe synchronization, M12 AUDITED_PASS, ADR-0005 and M09 deferral were read.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement deterministic tessellation of accepted BREP representations into derived PREVIEW_PROXY mesh geometry through the CAD adapter. Tessellation deflection/angle/work limits must be explicit and bounded; preserve CAD/Design Model revision linkage and named-feature mapping where supported. Preview geometry is disposable and may not become CAD truth, Design Model truth or Scan Master. Compare basic bounds/counts against source CAD representation and report tessellation limitations.
3. Tests/evidence cover at minimum: coarse/fine tolerance; deterministic vertices/triangles; work bounds; BREP bounds consistency; feature-to-preview mapping; invalid BREP rejection; PREVIEW_PROXY authority; relative/mm_unverified propagation; no Scan Master promotion.
4. CAD/BREP remains derived from exact Design Model revision; parent authority, units and DEFERRED_OWNER_VALIDATION remain explicit; no RELATIVE->mm or unverified->physical/mold authority promotion occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced. PL-0289 alone owns dependency/lock/license selection.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0296_CODEX_PROMPT_V01.md
