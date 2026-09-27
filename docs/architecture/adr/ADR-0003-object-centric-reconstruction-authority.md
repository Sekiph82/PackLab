# ADR-0003 — Object-Centric Reconstruction and Geometry Authority

Status: accepted  
Date: 2026-09-27

## Context

PackLab digitizes packaging rather than rooms. A reviewed OpenReality architecture demonstrates two useful patterns:

1. retain full-scene camera/reconstruction evidence while extracting an object-specific 3D subset by lifting image masks into world geometry;
2. explicitly distinguish captured geometry from AI-generated completion.

Reference:
https://github.com/reality-opened/openreality/commit/4d93d5f5b75166a43f0fd64b7d44acc12a56907f

PackLab already plans COLMAP/OpenMVS reconstruction, segmentation, scale calibration, Open3D processing and Scan Master promotion. Replacing those foundations with a room-oriented SLAM product would create unnecessary coupling and licensing risk.

## Decision

PackLab adopts an **object-centric, backend-neutral reconstruction architecture**.

### Production V1

- COLMAP/OpenMVS remains the first production reconstruction lane.
- M07 creates a PackLab-owned ReconstructionBackend contract.
- M08 creates a PackLab-owned SegmentationBackend contract.
- M08 adds mask-to-3D lifting plus multiview support voting to produce OBJECT_CAPTURE_GEOMETRY.
- M09 remains the sole metric scale authority.
- M10 remains the Scan Master promotion/cleanup authority.

### Future neural lane

A neural reconstruction backend may be researched behind the same contract only after model-specific commercial licensing and physical benchmark gates are satisfied.

The original non-commercial VGGT checkpoint is not eligible for commercial PackLab use. A commercial checkpoint or successor must be reviewed as a separate dependency before installation or distribution.

### Generated completion

SAM 3D Objects, TRELLIS or any successor may only produce AI_VISUAL_REFERENCE.

Generated or hallucinated geometry cannot become:
- metric evidence;
- Scan Master;
- measurement authority;
- engineering acceptance evidence.

## Consequences

Positive:
- PackLab can use background features for robust camera solving but discard background geometry afterward.
- object extraction works with COLMAP/OpenMVS today and can work with a future neural backend later.
- provenance remains explicit across captured and generated assets.
- model/vendor replacement does not rewrite project authority.

Costs:
- additional normalized data contracts;
- multiview projection/visibility implementation;
- separate artifact provenance and invalidation;
- additional benchmark and licensing work for optional neural/generative models.

## Mandatory implementation references

Master architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

Reconstruction backend:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0163_RECONSTRUCTION_BACKEND_CONTRACT.md

Segmentation backend:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md

Mask lift:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0190_OBJECT_MASK_LIFT_MULTIVIEW_FUSION.md

Metric provenance:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md

Scan Master:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0233_SCAN_MASTER_AUTHORITY.md
