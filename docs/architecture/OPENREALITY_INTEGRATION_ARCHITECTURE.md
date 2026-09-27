# PackLab OpenReality-Derived Object-Centric Reconstruction Architecture

Status: architecture contract  
Date: 2026-09-27  
Owner: PackLab  
Reference upstream inspected at commit: `4d93d5f5b75166a43f0fd64b7d44acc12a56907f`

## 1. Purpose

This document records which ideas PackLab adopts from the public OpenReality architecture and, equally importantly, which ideas PackLab does **not** adopt as authority.

OpenReality reference:
https://github.com/reality-opened/openreality

Pinned reference commit:
https://github.com/reality-opened/openreality/commit/4d93d5f5b75166a43f0fd64b7d44acc12a56907f

The useful pattern is not "reconstruct a room and keep the room." The useful pattern is:

1. solve camera geometry from the capture;
2. segment the target package in image space;
3. project reconstructed world geometry into the source cameras;
4. retain only points supported by the package masks and visibility tests;
5. fuse support across multiple views;
6. create an object-only captured geometry asset;
7. clean, scale and promote that asset through PackLab's existing Scan Master workflow.

PackLab remains a packaging-engineering application. Room navigation, robot-training export, scene agents and general indoor-scene product features are outside the V1 scope.

## 2. Source ideas adopted

The following OpenReality files informed this architecture:

- dense/video reconstruction concepts:
  https://github.com/reality-opened/openreality/blob/4d93d5f5b75166a43f0fd64b7d44acc12a56907f/core/docs/overview.md
- 2D mask to world-point lifting, visibility filtering, outlier rejection and OBB fitting:
  https://github.com/reality-opened/openreality/blob/4d93d5f5b75166a43f0fd64b7d44acc12a56907f/server/server/oreos/segment_geometry.py
- captured-vs-generated object provenance separation:
  https://github.com/reality-opened/openreality/blob/4d93d5f5b75166a43f0fd64b7d44acc12a56907f/server/server/oreos/routes_sam3d.py
- open-set object detection and mask-aware 3D localization:
  https://github.com/reality-opened/openreality/blob/4d93d5f5b75166a43f0fd64b7d44acc12a56907f/core/vggt_slam/object_detector.py
- self-host capability and licensing caveats:
  https://github.com/reality-opened/openreality/blob/4d93d5f5b75166a43f0fd64b7d44acc12a56907f/server/docs/self-hosting.md

PackLab adopts the architecture patterns, not an implicit dependency on the repository.

## 3. Non-negotiable geometry authority hierarchy

PackLab must persist the authority class of every 3D asset. The classes are ordered by meaning, not by visual quality.

### RAW_CAPTURE

Immutable source evidence: PackScan stills, video if present, intrinsics, ARKit/CoreMotion metadata, calibration observations and capture metadata.

### RECONSTRUCTION_OBSERVATION

A reconstruction backend's direct output before object isolation. It may include cameras, sparse points, dense points, mesh, confidence and temporary world geometry. It is evidence derived from RAW_CAPTURE, but it is not yet a Scan Master.

### OBJECT_CAPTURE_GEOMETRY

Geometry supported by real captured observations after mask-to-3D lifting and multi-view consensus. It may still contain holes, noise and uncertain areas. It remains derived from real captured evidence.

### SCAN_MASTER

An explicitly promoted, normalized, cleaned and provenance-complete reference asset. This is the measurement/fitting reference when M09/M10 acceptance requirements are satisfied.

### AI_VISUAL_REFERENCE

A generated completion or reconstruction whose unseen surfaces may be inferred by a model. Examples include future SAM 3D Objects or TRELLIS outputs. This class is **never** measurement authority and can never be promoted directly to Scan Master.

### DESIGN_MODEL

PackLab's editable parametric/engineering model. It may be fitted against Scan Master, but it has its own revision/provenance authority.

No code path may silently convert AI_VISUAL_REFERENCE into OBJECT_CAPTURE_GEOMETRY or SCAN_MASTER.

## 4. V1 reconstruction strategy

V1 remains anchored on the planned local photogrammetry path:

`PackScan -> COLMAP -> OpenMVS -> reconstruction observations`

This is the first production backend because the existing M07 plan already isolates executable engines and preserves intermediate evidence.

M07 must nevertheless implement a backend-neutral contract so future reconstruction engines can be added without changing project authority, UI semantics or downstream M08-M10 logic.

Required abstraction:

```text
ReconstructionBackend
  probe()
  prepare_inputs()
  run()
  cancel()
  collect_outputs()
  describe_provenance()
```

Normalized output must include, where available:

- registered source image IDs;
- camera intrinsics and extrinsics with explicit convention;
- sparse point cloud;
- dense point cloud;
- mesh;
- texture assets;
- per-output coordinate system;
- scale state: relative / metric-unverified / metric-verified;
- confidence/quality metadata;
- backend name/version/build/license record;
- exact inputs and configuration digest;
- logs and exit/stage states.

The concrete COLMAP/OpenMVS implementation may use two executables internally while presenting one PackLab reconstruction job contract.

See:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0163_RECONSTRUCTION_BACKEND_CONTRACT.md

## 5. Future neural reconstruction seam

OpenReality uses a VGGT-family pipeline. PackLab does not adopt OpenReality's default self-host model stack as a V1 dependency.

The official VGGT repository now distinguishes the original non-commercial checkpoint from `VGGT-1B-Commercial`:

https://github.com/facebookresearch/vggt

PackLab rules:

1. no neural reconstruction model may become a dependency merely because its code can run;
2. a specific checkpoint, license, hash, runtime and redistribution/deployment path must be reviewed separately;
3. the original `facebook/VGGT-1B` checkpoint is forbidden for commercial PackLab use;
4. a commercially eligible checkpoint may only enter an experimental backend after its license terms are accepted and recorded;
5. neural reconstruction remains non-authoritative until PackLab's own physical benchmark demonstrates acceptable repeatability and geometry accuracy;
6. the backend must implement the same normalized ReconstructionBackend contract.

Future task:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0436_COMMERCIAL_NEURAL_RECONSTRUCTION_RESEARCH.md

## 6. Segmentation architecture

M08 segmentation must use a replaceable PackLab-owned interface rather than binding domain logic to a specific model.

Required conceptual API:

```text
SegmentationBackend
  probe()
  segment(image, prompts?)
  batch_segment(frames)
  describe_provenance()
```

A `MaskArtifact` must carry:

- source frame identity and immutable source digest;
- pixel width/height and coordinate origin;
- backend/model/checkpoint/version;
- prompt type and prompt data where applicable;
- probability/confidence information where available;
- post-processing version;
- mask revision;
- generated timestamp;
- manual-edit ancestry;
- quality flags.

Masks are derived data and version independently from RAW_CAPTURE.

See:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md

## 7. Object extraction: mask-to-3D lifting

This is the highest-value OpenReality-derived pattern for PackLab.

Given:

- reconstructed world points `P_world`;
- camera intrinsics `K_i`;
- camera transform `T_i`;
- target object mask `M_i`;

PackLab projects each candidate world point into each camera that can observe it.

For camera `i`:

1. transform world point into camera coordinates;
2. reject points behind camera or outside the image;
3. project with the camera intrinsics;
4. test the projected pixel against the object mask;
5. apply visibility/occlusion logic using a depth or z-buffer tolerance;
6. record a support vote, reject vote or not-observed state.

A single mask must not be the final authority for a multiview object.

For point `p`, persist:

- `observed_views`;
- `support_views`;
- `reject_views`;
- `support_ratio`;
- optional confidence-weighted support;
- source mask IDs;
- source reconstruction revision.

The default classification contract must be configurable but deterministic. Example initial research threshold:

`support_views >= 2 AND support_ratio >= 0.70`

This number is not frozen as a production threshold until M08 benchmark evidence supports it.

Visibility must be evaluated before a reject vote. A point hidden behind another surface in a camera must be `not-observed`, not a negative object vote.

The output is `ObjectCaptureGeometry`, not Scan Master.

See:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0190_OBJECT_MASK_LIFT_MULTIVIEW_FUSION.md

## 8. Background handling

PackLab must not erase the background before camera solving unless a backend-specific benchmark demonstrates that this is safe.

Default strategy:

```text
full image -> camera solving / feature geometry
object masks -> dense-object restriction and/or post-reconstruction lifting
```

Reason: glossy, transparent and low-texture consumer packaging can contain too few stable visual features. Background features can improve camera registration even when background geometry is discarded later.

Where COLMAP/OpenMVS safely support masks, M08 may use masks to suppress unwanted feature/dense geometry, but source images remain immutable.

## 9. PackScan advantage over generic phone video

PackLab must prefer structured PackScan evidence over degrading it into a generic video-only input.

Available/expected PackScan evidence includes:

- high-resolution source stills;
- camera metadata;
- known intrinsics where valid;
- ARKit/CoreMotion observations where available;
- capture ordering;
- guided orbit/ring coverage;
- calibration observations;
- quality metadata.

ReconstructionBackend may use these as priors. It must record whether a camera was:

- solved entirely by the backend;
- initialized from capture metadata;
- fixed from trusted metadata;
- refined from a prior;
- rejected as inconsistent.

No capture pose is silently treated as metrology-grade truth.

## 10. Turntable distinction

A turntable capture violates the ordinary static-world/moving-camera assumption.

PackLab must distinguish:

- `guided_orbit`: object/world fixed, camera moves;
- `turntable`: camera fixed or nearly fixed, object rotates.

For turntable datasets, known turntable angles should be represented as object transforms or equivalent virtual-camera transforms. A generic SLAM backend must not be fed rotating-object footage and allowed to interpret it as a static scene without an explicit turntable adapter.

Existing/future turntable tasks remain responsible for synchronizing angle evidence into PackScan metadata.

## 11. Metric scale and units

Monocular geometry can be internally consistent without having reliable absolute scale.

PackLab rule:

**No reconstructed length is millimetres merely because a backend emits a number.**

M09 owns metric authority.

Metric promotion requires explicit scale evidence such as validated calibration markers or another approved physical reference. Scale provenance and uncertainty must travel with normalized geometry.

See:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md

## 12. Scan Master gate

Only captured geometry can feed Scan Master promotion.

Allowed ancestry:

`RAW_CAPTURE -> RECONSTRUCTION_OBSERVATION -> OBJECT_CAPTURE_GEOMETRY -> normalized/cleaned captured geometry -> SCAN_MASTER`

Forbidden ancestry:

`AI_VISUAL_REFERENCE -> SCAN_MASTER`

If an AI completion is visually overlaid to help an operator understand a hole, the missing region remains missing in the authoritative Scan Master unless it is reconstructed or explicitly modeled in the later Design Model layer.

See:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0233_SCAN_MASTER_AUTHORITY.md

## 13. AI object completion lane

OpenReality demonstrates a useful honesty pattern: generated completion is marked generated and carries caveats.

PackLab may later add SAM 3D Objects, TRELLIS or another generator strictly as AI_VISUAL_REFERENCE.

Potential uses:

- visualizing an occluded back side;
- assisting recapture planning;
- giving the user a fast "likely complete object" preview;
- suggesting geometry-family candidates;
- visual comparison with captured geometry.

Prohibited uses:

- measurement;
- calibration;
- Scan Master promotion;
- engineering acceptance;
- thread/neck/base dimensions;
- mold-manufacturing claims;
- replacing a failed scan without explicit non-authoritative labeling.

Future task:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0435_AI_VISUAL_REFERENCE_LANE.md

## 14. Storage contract

Suggested project layout additions:

```text
raw/
  packscan/

working/
  reconstruction/<revision>/
    manifest.json
    cameras/
    sparse/
    dense/
    mesh/
    logs/
  masks/<mask-set-revision>/
    manifest.json
    frames/
  object_geometry/<revision>/
    manifest.json
    points.ply
    support.npz
    obb.json

derived/
  scan_master/<revision>/
  previews/
  ai_visual_reference/<revision>/
```

Actual paths must follow the accepted M06 project-layout/versioning authority. These names are architecture guidance, not permission to bypass existing ProjectManager APIs.

## 15. Provenance minimum

Every reconstruction/object geometry artifact must record:

- project UUID;
- input PackScan digest;
- source photo digests;
- reconstruction backend ID/version;
- exact backend settings digest;
- segmentation backend/model/checkpoint;
- mask-set revision;
- camera convention and units state;
- object-extraction algorithm version;
- support-vote thresholds;
- cleanup steps;
- parent artifact IDs;
- creation timestamp;
- generated flag;
- authority class.

`generated=true` assets may never claim `authority_class=SCAN_MASTER`.

## 16. Testing strategy

The architecture must be testable without private Kenya scans.

Repository-safe test assets should include:

- synthetic calibrated cameras and known 3D points;
- synthetic foreground/background point clouds;
- masks with known projection truth;
- explicit occlusion cases;
- points outside the mask;
- transparent/glossy benchmark placeholders using public/synthetic data;
- turntable transform fixtures;
- generated AI reference fixtures that prove authority isolation.

Mandatory mask-lift tests:

1. a foreground point projects inside the mask and survives;
2. a background point projects inside the mask but is occluded and does not produce a reject/support error;
3. a visible outside-mask point produces a reject vote;
4. a hidden outside-mask point produces no vote;
5. multiview support threshold is deterministic;
6. changing mask revision invalidates object geometry;
7. changing reconstruction revision invalidates object geometry;
8. source RAW_CAPTURE remains byte-identical;
9. AI_VISUAL_REFERENCE cannot pass the Scan Master gate.

## 17. Roadmap mapping

- PL-0163: reconstruction backend contract.
- PL-0166/0167: preserve source images and consume camera priors safely.
- PL-0184: segmentation backend contract.
- PL-0189: independent mask revision authority.
- PL-0190: mask-aware reconstruction plus multiview mask-to-3D object extraction.
- PL-0197/0199/0200: object-geometry coverage/quality gates.
- PL-0209: metric scale provenance and uncertainty.
- PL-0233/0238: Scan Master authority and explicit promotion.
- PL-0435: optional AI visual-reference lane.
- PL-0436: commercial-license-cleared neural reconstruction research backend.
- PL-0437: controlled reconstruction-backend benchmark before any neural backend can become a production default.

## 18. Dependency policy

OpenReality itself is a BSD-2-Clause reference repository, but its self-host stack fetches separately licensed models. PackLab must evaluate code and model licenses independently.

Relevant sources:

- OpenReality license:
  https://github.com/reality-opened/openreality/blob/4d93d5f5b75166a43f0fd64b7d44acc12a56907f/LICENSE
- VGGT license and commercial-checkpoint distinction:
  https://github.com/facebookresearch/vggt/blob/main/LICENSE.txt
  https://github.com/facebookresearch/vggt/blob/main/README.md
- SAM 3D Objects custom SAM License:
  https://github.com/facebookresearch/sam-3d-objects/blob/main/LICENSE
- TRELLIS MIT project license, with separately licensed submodules noted upstream:
  https://github.com/microsoft/TRELLIS/blob/main/LICENSE
  https://github.com/microsoft/TRELLIS/blob/main/README.md

No future task may infer model commercial eligibility from the repository code license alone.
