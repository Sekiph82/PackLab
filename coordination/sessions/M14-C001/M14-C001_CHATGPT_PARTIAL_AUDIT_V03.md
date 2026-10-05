# M14-C001 - ChatGPT Partial Milestone Audit V03

Date: 2026-10-05
Decision: **AUDITED_PARTIAL_CHANGES_REQUIRED**
Independently accepted frontier: **PL-0310 through PL-0325**
Current blocked child: **PL-0326 V01**
Later children: **PL-0327 through PL-0331 not started**

## Newly accepted children

The following builder-green children were independently source/diff/evidence audited and accepted:

- PL-0313 V02 — metric surface binding + mm_unverified dieline
- PL-0314 V01 — safe margin / bleed print intent
- PL-0315 V01 — bounded SVG/PNG artwork ingest
- PL-0316 V01 — front/back/wrap artwork variants
- PL-0317 V01 — deterministic dieline SVG export
- PL-0318 V01 — visual-only packaging material library
- PL-0319 V01 — separate geometry material/content appearance channels
- PL-0320 V01 — bounded PBR visual parameters
- PL-0321 V01 — starter material catalog
- PL-0322 V01 — PCR declaration/visual variants
- PL-0323 V01 — per-component material project persistence
- PL-0324 V01 — real Blender capability probe
- PL-0325 V01 — deterministic Blender scene package

Individual independent audits are published beside the child logs in this session directory.

PL-0324 real capability evidence is accepted: Blender 5.2.2 LTS launched headlessly under the bounded offline probe. PL-0325 package generation is accepted as a package/manifest boundary only; actual scene construction remains PL-0326 scope.

## PL-0326 V01 blocker

The builder stop is **VALID**.

The live accepted source contracts confirm:

1. `cad_preview.py` maps an accepted coarse whole-solid feature to the entire preview triangle set. It does not establish component-specific triangle ownership.
2. `cad_mesh_export.py` emits one GLB node, one mesh and one primitive with only `POSITION`; no UV set or per-component material slots exist.
3. `blender_scene_package.py` carries exact zone/placement/artwork/material revision metadata and normalized Label Zone bounds but no exact host-surface world/render transform.
4. `LabelMetricSurfaceBinding` proves exact metric host dimensions and mapping semantics, but its accepted identity deliberately does not persist transient CAD face identity or a renderer placement transform.
5. Therefore a Blender implementation that guesses component subsets, manufactures UVs from whole-solid bounds, chooses transient face identity, or directly attaches artwork to the fused mesh would invent authority.

No PL-0326 implementation was retained. PL-0327 through PL-0331 were not started.

## Frozen PL-0326 V02 authority resolution

PL-0326 V02 may extend the renderer/package layer without weakening accepted CAD authority.

### A. Base geometry/component material binding

The existing fused GLB may receive a component material **only** through mode:

`WHOLE_SOLID_SINGLE_COMPONENT`

This mode is permitted only when all exact `CadBrepRepresentationRevision.source_feature_ids` resolve through the accepted Design Model to exactly one stable `component_id`, and the material assignment being applied is for that same component.

If source lineage spans zero or multiple component IDs, or multiple component material assignments require geometric partitioning, scene construction must fail closed with an explicit component-mesh-partition-unavailable result. PL-0326 must not infer triangle subsets or synthesize material slots.

This rule is intentionally narrower than future multi-part rendering. It allows truthful current single-component scene construction while preserving the blocker for unsupported multi-component geometry.

### B. Artwork uses a separate renderer overlay, not base-mesh UV authority

Artwork must not be projected onto the fused source mesh by guessed UVs.

Introduce a deterministic **Label Render Overlay Binding** derived from:

- exact Design Model revision;
- exact BREP revision + geometry digest;
- exact PL-0312 analysis revision/region;
- accepted PL-0313 Label Metric Surface Binding;
- exact Label Zone placement revision;
- exact artwork mapping/assignment revision.

The overlay binding is derived presentation evidence only. It must not become Design Model/CAD/Label Zone authority.

At package-build time, recompute the exact host-surface resolution from the pinned BREP and accepted analysis-region evidence. Resolution must be unique or fail closed.

For `PLANAR_RECTANGULAR`, persist renderer-only world/source coordinates sufficient to reconstruct the exact zone rectangle:
- exact host plane origin/frame compatible with PackLab front/back frame;
- U/V axes and surface normal;
- exact zone corner coordinates derived from accepted normalized boundary + metric binding.

For `CYLINDRICAL_WRAP`, persist renderer-only world/source parameters sufficient to reconstruct the exact cylindrical label patch:
- cylinder center/axis;
- radius;
- accepted seam direction and azimuth direction;
- exact zone angular start/end;
- exact axial start/end.

No native face index/topology identity is persisted.

### C. Blender presentation overlay

The real Blender scene builder may generate a **separate derived overlay mesh**:

- planar: deterministic 4-vertex quad with UV 0..1;
- cylindrical: bounded deterministic segmented cylindrical patch with UV 0..1;
- source coordinates must be transformed through the already accepted CAD-export viewer transform;
- an explicitly recorded tiny render-only outward offset may be used solely to avoid z-fighting; it must be deterministic, bounded and excluded from source/physical authority.

The source GLB mesh is never modified to create authoritative UVs.

PNG artwork may be loaded and textured onto the overlay in the real Blender smoke. SVG must either use an already-present, verified Blender-native safe path or fail closed as unsupported for real scene texturing; no new rasterizer/network/dependency may be silently added.

### D. Scene construction requirements

Real Blender 5.2.2 headless evidence must prove at minimum:

- exact manifest/assets digest validation before import;
- fused base GLB import;
- truthful single-component mapping and material/PBR assignment;
- fail-closed multi-component/partition-required case;
- FRONT/BACK planar overlay construction and artwork UV mapping;
- WRAP cylindrical overlay construction and artwork UV mapping;
- stale/mismatched overlay/artwork/metric binding rejection;
- no source geometry authority mutation;
- RELATIVE/mm_unverified metadata preservation;
- no network access;
- deterministic scene facts/output manifest.

The scene itself is a derived presentation artifact. Scene success is not print fit, material certification, physical accuracy, mold/manufacturing or regulatory evidence.

## Resume rule

Execute PL-0326 V02 under the new prompt/criteria. If builder-green, continue PL-0327 through PL-0331 under the new continuation master. PL-0328+ real render requirements remain mandatory.

## Verdict

`AUDITED_PARTIAL_CHANGES_REQUIRED`

M14 remains open. PL-0310 through PL-0325 are independently accepted. Resume at PL-0326 V02. M15 remains unauthorized.
