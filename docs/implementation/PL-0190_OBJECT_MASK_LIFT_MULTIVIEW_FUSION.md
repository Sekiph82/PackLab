# PL-0190 Implementation Spec — Object Mask Lift and Multiview Fusion

Mandatory pre-reads:

https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md

## Objective

Extend mask-aware reconstruction into an explicit PackLab object-extraction stage that converts real multiview reconstruction observations into OBJECT_CAPTURE_GEOMETRY.

This task is inspired by OpenReality's mask-to-world-point lifting, but PackLab requires multiview consensus and its own provenance/invalidation rules.

## Inputs

- reconstruction revision;
- world-space dense points or mesh vertices/surface samples;
- solved cameras;
- per-frame intrinsics;
- versioned target-object masks;
- optional reconstruction confidence;
- optional per-view depth.

## Camera convention gate

Before lifting any mask, validate the declared camera convention with a synthetic known point.

The adapter must normalize to one PackLab convention before projection. Never guess whether a matrix is camera-to-world or world-to-camera.

## Per-view projection

For every candidate point and view:

1. transform world point to camera coordinates;
2. reject behind-camera points;
3. project using the normalized intrinsics;
4. reject out-of-frame points as not observed;
5. perform visibility test;
6. sample the mask only if visible;
7. record support/reject/not-observed.

## Visibility

A point that projects behind the front visible surface must not count as a reject merely because its pixel is outside the mask.

Implement a deterministic z/depth visibility policy. An initial implementation may use a coarse z-buffer generated from the reconstruction. Persist the tolerance and raster scale in provenance.

## Multiview vote record

For every retained/rejected candidate make the decision reproducible from aggregate evidence:

- observed view count;
- support view count;
- reject view count;
- support ratio;
- confidence-weighted support if used;
- threshold profile ID;
- source mask-set revision.

Do not persist giant per-point per-frame matrices when a bounded aggregate plus optional debug sampling is sufficient. The exact storage representation is an implementation decision, but provenance must remain auditable.

## Initial threshold policy

The first research default may begin with:

- minimum visible observations: 2;
- support ratio: 0.70.

These are not metrology constants. PL-0185/PL-0197/PL-0199 benchmark evidence may change them through a versioned profile.

## Outlier cleanup

After vote selection, a conservative outlier pass may remove isolated points. The unfiltered object subset must remain reproducible or regenerable from the parent reconstruction and mask revisions.

Do not perform aggressive smoothing or hole filling here; M10 owns geometric cleanup.

## OBB

Generate a preliminary oriented bounding box for viewport and QA only.

If gravity/up evidence exists, a gravity-aware PCA OBB is permitted. The OBB is not metric authority until M09 scale is verified.

## COLMAP/OpenMVS mask use

Where supported and benchmarked, masks may additionally be supplied earlier to feature/dense stages. This is an optimization/reconstruction-quality path, not a replacement for the explicit post-reconstruction multiview lift.

The default principle remains:
- full image may assist camera solving;
- object masks determine final object ownership.

## Outputs

`ObjectCaptureGeometryManifest` must include:
- parent reconstruction revision;
- parent mask-set revision;
- source camera-solution revision;
- point/primitive counts before and after voting;
- threshold profile;
- visibility policy;
- outlier policy;
- preliminary OBB;
- scale state inherited from reconstruction;
- `generated=false`;
- `authority_class=OBJECT_CAPTURE_GEOMETRY`.

## Invalidation

Invalidate/regenerate when any of these change:
- reconstruction revision;
- camera solution;
- source image identity;
- mask-set revision;
- projection convention;
- visibility policy version;
- voting profile version.

## Mandatory tests

Use synthetic cameras/geometry:
1. visible foreground point inside mask -> support;
2. visible background/outside point -> reject;
3. occluded point -> not observed;
4. behind-camera point -> not observed;
5. out-of-frame point -> not observed;
6. two-view threshold boundary;
7. deterministic result independent of iteration order;
8. mask revision invalidates output;
9. camera/reconstruction revision invalidates output;
10. RAW_CAPTURE bytes unchanged;
11. output generated flag is false;
12. object geometry cannot claim metric verification before M09.
