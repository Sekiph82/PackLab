# PL-0184 Implementation Spec — Segmentation Backend Contract

Mandatory pre-read:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

## Objective

Define segmentation as a replaceable service. No mask consumer may import model-specific APIs directly.

## Required concepts

- `SegmentationBackend`
- `SegmentationCapabilityReport`
- `SegmentationRequest`
- `SegmentationResult`
- `MaskArtifact`
- `MaskSetRevision`
- `PromptEvidence`

A backend may support:
- automatic object segmentation;
- point prompt;
- box prompt;
- prior-mask refinement;
- batch segmentation.

Capabilities must be probed rather than assumed.

## Mask coordinates

Every mask artifact records:
- source image asset ID;
- source digest;
- exact width/height;
- origin convention: top-left;
- pixel-index convention;
- whether mask was resized;
- any transform between model input and source-image pixel grid.

All downstream geometry lifting must operate in the source-image coordinate system or apply a recorded transform.

## Provenance

Persist:
- backend ID;
- model/checkpoint/version/hash;
- runtime version;
- prompt kind;
- confidence if available;
- post-processing pipeline version;
- parent mask revision if manually edited;
- manual/editor provenance;
- generated timestamp.

## Immutable source rule

Segmentation never rewrites source photos. Preprocessed model inputs and masks live in working/derived project storage.

## Model selection

PL-0185 owns benchmark-based model selection for bottle, jerrycan, cap, transparent and glossy examples.

OpenReality's use of SAM-family models is reference evidence only. PL-0184 must not silently select SAM 3 or another model.

## Downstream contract

PL-0190 consumes `MaskArtifact` and must not know which ML model produced it.

Required relation:

```text
RAW_CAPTURE image
      ↓
MaskArtifact revision
      ↓
Object mask lift
      ↓
ObjectCaptureGeometry
```

Changing a mask revision invalidates downstream object geometry.

## Tests

- fake backend replacement needs no downstream code change;
- coordinate metadata round-trips;
- resized model input maps correctly to source pixels;
- source bytes remain immutable;
- manual mask edit creates a new revision;
- model/checkpoint change produces distinct provenance;
- downstream invalidation occurs when mask revision changes.
