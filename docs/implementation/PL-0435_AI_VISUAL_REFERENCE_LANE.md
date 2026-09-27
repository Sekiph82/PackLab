# PL-0435 Implementation Spec — AI Visual Reference Lane

Status: future M19 work, not authorized for early execution.

## Objective

Add an optional generated 3D reference lane for visualization only. Candidate backends may include SAM 3D Objects, TRELLIS or later models.

## Hard authority boundary

Every output must have:
- `generated=true`;
- `authority_class=AI_VISUAL_REFERENCE`;
- generator/model/checkpoint/version;
- conditioning images/masks;
- seed/settings;
- caveat that unseen geometry may be invented.

The type system/service boundary must prevent this asset from:
- becoming Scan Master;
- contributing measurement samples;
- feeding calibration;
- satisfying capture coverage;
- being exported as authoritative engineering geometry.

## Backend contract

Use a replaceable `VisualReferenceBackend` interface. Do not let model SDK types escape the adapter.

Possible inputs:
- source image + mask;
- multiview crops;
- object OBB for display placement.

OBB fitting is display alignment only. It does not confer dimensional truth.

## Candidate licensing

Before enabling any model:
- record repository/code license;
- record checkpoint license separately;
- record permitted commercial use;
- record redistribution/runtime requirements;
- pin checkpoint/version/hash.

SAM 3D Objects:
https://github.com/facebookresearch/sam-3d-objects

TRELLIS:
https://github.com/microsoft/TRELLIS

## UI

Viewport must render a strong, persistent "AI Visual Reference" state and allow hiding it independently from Scan Mesh / Scan Master / Design Model.

Screenshots/export metadata must preserve the generated label.

## Tests

- generated output cannot pass Scan Master promotion;
- generated geometry cannot be sampled by measurement tools;
- provenance persists;
- model replacement does not affect authority code;
- screenshot sidecar says generated;
- deletion of AI reference cannot alter captured geometry.
