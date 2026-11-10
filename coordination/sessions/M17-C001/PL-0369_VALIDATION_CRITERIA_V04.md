# PL-0369 — Validation Criteria V04

V04 supersedes V03 scope using the owner's 2026-11-04 dataset direction.

1. All committed fixtures are small and license-eligible; large/downloaded datasets remain outside Git.
2. A reproducible manifest binds every local sample's identity, source, license/attribution, bytes/hash, real-vs-synthetic provenance, measurement authority, camera/render data and expected software use.
3. The actual downloaded source object(s) match official URLs, verified byte lengths and SHA-256 values; archive content is inspected before derived samples are accepted.
4. Blender generator deterministically produces all eight required package families, multiple views/lighting/material appearances, masks, calibrated virtual camera metadata, expected geometry dimensions, controlled optical effects and explicit synthetic tolerance assumptions.
5. Synthetic dimensions and tolerances are labeled simulated; any public-source dimensional data is attributed to the source and never upgraded to independent physical ground truth.
6. Internal-use dataset notice reflects the owner's exact scope and does not purport to modify root/dependency licensing or grant third-party clearance. Preserve third-party trademark/product-right caveats.
7. Add regression tests for manifest, integrity, synthetic/real provenance boundaries and failure cases; schedule the grouped test run at M17 end per V04 prompt.
8. Keep future Kenya field scans, physical measurements, reconstruction accuracy, material validation, and release acceptance open until real evidence exists.
9. Matching V04 log records exact commands/results, data footprint, checksums, privacy/licensing review, local-only publication status and known limits.

