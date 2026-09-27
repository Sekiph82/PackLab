# PL-0233 Implementation Spec — Scan Master Authority

Mandatory pre-read:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

## Objective

Create an explicit promoted Scan Master whose ancestry is captured evidence only.

## Allowed ancestry

```text
RAW_CAPTURE
 -> RECONSTRUCTION_OBSERVATION
 -> OBJECT_CAPTURE_GEOMETRY
 -> M09 scale/alignment
 -> M10 conservative cleanup
 -> SCAN_MASTER
```

## Forbidden ancestry

No asset with `generated=true` or `authority_class=AI_VISUAL_REFERENCE` may be promoted to Scan Master.

A visual-reference overlay can coexist in the viewport, but it cannot patch holes in the authority geometry.

## Promotion manifest

Persist:
- Scan Master revision ID;
- project UUID;
- parent object-geometry revision;
- reconstruction revision;
- mask-set revision;
- scale provenance ID;
- alignment transform;
- cleanup operation list and parameters;
- hole report;
- decimation relationship if proxy assets exist;
- source geometry digest;
- output geometry digest;
- promoted timestamp;
- promotion actor;
- authority class;
- known limitations/coverage gaps.

## Source preservation

Promotion never overwrites:
- RAW_CAPTURE;
- original reconstruction;
- original object geometry.

Cleanup stages create revisions.

## Proxy rule

Viewport-decimated meshes are `PREVIEW_PROXY`, never Scan Master. The Scan Master remains the full accepted reference.

## Downstream contract

Parametric Design Model fitting consumes a selected Scan Master revision and pins that parent ID. Rerunning reconstruction or creating a new Scan Master must not silently move an existing Design Model to the new parent.

## Tests

- generated asset promotion rejected;
- preview proxy promotion rejected unless it refers back to an eligible full captured asset and promotion selects the full asset;
- promotion manifest complete;
- original assets byte-identical;
- reopening project preserves selected Scan Master;
- newer reconstruction does not silently retarget downstream design model;
- provenance graph is traversable to immutable PackScan input.
