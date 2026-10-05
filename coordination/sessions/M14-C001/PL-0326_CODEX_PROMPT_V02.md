# PL-0326 - Codex Prompt V02

Task: **Construct real Blender scene with truthful fused-geometry material binding and exact label render overlays**
Milestone: **M14 - Labels, Materials & Rendering**
Cycle: **M14-C001-R03**

This V02 supersedes PL-0326 V01 after the independently accepted authority stop.

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/M14-C001_CHATGPT_PARTIAL_AUDIT_V03.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0326_CHATGPT_AUDIT_CRITERIA_V02.md

## Start rule

Synchronize the execution checkout non-destructively with latest `origin/main`, preserve owner-local work, and verify live root `TASKS.md` authorizes M14-C001-R03 / PL-0326 V02.

Read before implementation:

- M14 partial audit V03;
- accepted PL-0313 through PL-0325 contracts and independent audits;
- PL-0326 V01 blocker log;
- current `cad_preview.py`, `cad_mesh_export.py`, `label_metric_surface_binding.py`, `blender_scene_package.py`;
- M13 final audit, M09 physical-validation deferral and ADR-0005.

Do not edit root `TASKS.md`.

## Frozen authority resolution

The current exported GLB is one fused presentation mesh. PL-0326 V02 must not invent per-component triangle partitions or base-mesh UVs.

### 1. Whole-solid single-component geometry binding

Introduce an immutable deterministic renderer-only geometry binding mode:

`WHOLE_SOLID_SINGLE_COMPONENT`

It is valid only when:

- the exact BREP revision/digest matches the accepted CAD export;
- every `source_feature_id` in the exact BREP resolves through the accepted Design Model;
- all resolved source features belong to exactly one stable `component_id`;
- the geometry material assignment applied in the scene is for that same component.

If zero/multiple component IDs are present, or multiple component material assignments require a mesh partition, fail closed. Do not synthesize triangle subsets, primitive splits or material slots.

The fused imported mesh may receive the exact single component's visual material/PBR metadata only under this proven mode.

### 2. Label Render Overlay Binding

Do not attach artwork to the fused base mesh using guessed UVs.

Introduce a deterministic immutable `LabelRenderOverlayBinding` derived from exact:

- Design Model revision;
- BREP revision + geometry digest;
- PL-0312 surface-analysis revision + analysis region;
- PL-0313 Label Metric Surface Binding;
- Label Zone placement revision;
- artwork mapping + assignment + asset revision/digest.

Recompute the exact host-surface resolution from the pinned BREP and accepted analysis-region evidence. It must resolve uniquely or fail closed.

The renderer binding is presentation evidence only. It must never become CAD/Design Model/Label Zone authority and must not persist native face index, traversal order or transient topology identity.

#### PLANAR_RECTANGULAR overlay binding

Persist enough exact source/world coordinates to reconstruct the zone rectangle:

- host frame/origin compatible with accepted PackLab front/back frame;
- U axis, V axis and surface normal;
- exact zone corner coordinates derived from accepted normalized zone boundary and metric surface binding;
- source coordinate unit and exact source-to-GLB viewer transform.

#### CYLINDRICAL_WRAP overlay binding

Persist enough exact source/world parameters to reconstruct the zone patch:

- cylinder center/axis;
- radius;
- accepted seam direction and azimuth direction;
- exact angular start/end for the selected zone boundary;
- exact axial start/end;
- source coordinate unit and exact source-to-GLB viewer transform.

No generic freeform overlay mapping is authorized.

### 3. Blender presentation overlay geometry

In the real Blender scene:

- import the exact digest-validated base GLB;
- preserve it as derived presentation geometry;
- create a separate overlay object rather than rewriting base-mesh UVs;
- planar overlay: deterministic quad with UV 0..1;
- cylindrical overlay: deterministic bounded segmented patch with UV 0..1;
- use the accepted CAD-export viewer transform so overlay and imported GLB share the same render coordinate space;
- a tiny deterministic renderer-only outward offset may be used to prevent z-fighting; it must be bounded, recorded in scene provenance, and explicitly non-physical.

The source GLB mesh must not be modified to claim an authoritative UV layout.

### 4. Artwork media handling

PNG must be supported by the real Blender headless scene-construction smoke.

SVG may be used only if Blender 5.2.2 provides an already-present safe local import path that requires no network, hidden extension download or new dependency. Otherwise SVG scene texturing must fail closed with an explicit unsupported-media reason. Do not silently rasterize through an unreviewed library/service.

### 5. Scene material rules

Apply exact accepted visual material/PBR values only under the proven single-component binding. Keep PCR/material/certification semantics as metadata only.

No scene material value may imply measured resin properties, environmental certification, manufacturing approval or regulatory authority.

## Required implementation

Implement scene construction from the accepted PL-0325 package plus the new exact renderer bindings.

The package/runner contract may be versioned forward as needed, but:

- previously accepted source authority must remain intact;
- exact source revisions/digests remain pinned;
- assets remain project-relative and digest-bound;
- no arbitrary user code execution;
- no ambient absolute path identity in canonical outputs;
- no auto-download/network;
- no Blender binary committed.

The real scene builder must produce a deterministic scene-result manifest containing at minimum:

- scene/package contract versions;
- exact Blender capability facts;
- exact source model/CAD/package/material/artwork revisions/digests;
- geometry binding mode + component ID;
- overlay binding IDs and mapping modes;
- imported base object identifier;
- material assignment result;
- overlay object facts and UV-presence facts;
- source/render coordinate transform;
- renderer-only offset value if used;
- explicit authority/limitation flags.

## Required validation

### Source/geometry binding
- proven single-component BREP lineage succeeds;
- multi-component lineage fails closed;
- stale CAD export/BREP/model digest or revision rejects;
- no triangle-subset/per-component slot is fabricated.

### Materials
- exact single-component geometry material/PBR assignment reaches imported Blender object;
- stale/wrong-component material assignment rejects;
- content/PCR metadata does not mutate geometry authority.

### Artwork overlays
- FRONT planar PNG overlay succeeds with deterministic quad + UV;
- BACK planar orientation succeeds;
- WRAP cylindrical PNG overlay succeeds with deterministic segmented geometry + UV;
- exact overlay binding is tied to metric/analysis/placement/artwork revisions;
- stale/tampered binding or asset rejects;
- unsupported/freeform host fails closed;
- unsupported SVG path fails closed if no safe built-in path exists;
- no base-mesh UV fabrication.

### Real Blender smoke
Use the approved real Blender 5.2.2 headless executable. Unit fakes may supplement but cannot replace this smoke.

The smoke must prove actual:
- package validation;
- GLB import;
- material creation/application;
- planar overlay creation;
- cylindrical overlay creation;
- image texture load for PNG;
- UV data on overlays;
- deterministic scene/result facts;
- no network access.

A render image is not required by PL-0326; PL-0328 remains the first required render child.

### Global checks
Run focused predecessor/regression tests, locked full suite, changed-file Ruff/format, targeted mypy/compile, dependency/lockfile, privacy/security/scope checks, and publication parity.

## Stop conditions

Stop if:

- exact component lineage is ambiguous;
- required overlay host cannot resolve uniquely;
- only a guessed face/triangle/UV mapping would make the task pass;
- real Blender fails;
- a new dependency/network download would be required;
- M15+ work is needed.

## Handoff

Publish implementation/evidence commit(s), then publish:

`coordination/sessions/M14-C001/PL-0326_CODEX_LOG_V02.md`

in a separate log-only commit.

The log must record the V01 blocker resolution, exact supported/unsupported scene modes, real Blender facts, focused/full results, changed files, limitations, and final local/origin/GitHub parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
