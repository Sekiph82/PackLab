# PL-0326 - ChatGPT Audit Criteria V02

Task: **Real Blender scene construction with truthful fused-geometry binding and exact label overlays**

All criteria are mandatory.

1. Live tracker authorization, M14 partial audit V03, PL-0326 V01 blocker and accepted PL-0313→PL-0325 contracts/audits are read.
2. The fused GLB receives a component material only through an explicit `WHOLE_SOLID_SINGLE_COMPONENT` binding proven from exact BREP source feature lineage to exactly one stable component ID.
3. Zero/multiple component lineage or partition-required material assignments fail closed. No triangle subsets, primitive splits or component material slots are invented.
4. Artwork uses a separate deterministic Label Render Overlay Binding derived from exact Model/BREP/digest + PL-0312 analysis + PL-0313 metric binding + placement + artwork chain.
5. Host-surface resolution is recomputed against the exact BREP and must be unique. No native face index, traversal order, transient topology ID or base-mesh UV identity is persisted as authority.
6. PLANAR_RECTANGULAR overlay reconstructs exact front/back zone geometry in the accepted frame. CYLINDRICAL_WRAP reconstructs exact cylinder center/axis/radius/seam/angular/axial zone parameters. Unsupported/freeform cases fail closed.
7. Blender creates separate overlay geometry with UVs; it does not fabricate authoritative UVs on the fused base mesh. Any anti-z-fighting offset is deterministic, bounded, recorded and presentation-only.
8. PNG artwork is proven in a real Blender 5.2.2 headless smoke. SVG either uses an already-present safe local Blender path or fails closed without new download/dependency.
9. Exact material/PBR metadata is applied only to the proven component; material/PCR/certification semantics remain visual/non-certified.
10. Real Blender smoke proves package validation, GLB import, material assignment, planar and cylindrical overlays, PNG texture load and UV presence. No render is required yet.
11. Exact source/package/artwork/material revisions/digests and source-to-render transform are preserved in deterministic scene-result provenance. Source geometry authority is not mutated.
12. No auto-download, network dependency, unreviewed dependency, ambient path leakage, tracker edit, PL-0327+ implementation or M15+ work is introduced.
13. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and V02 log publication are distinct; V02 log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0326_CODEX_PROMPT_V02.md
