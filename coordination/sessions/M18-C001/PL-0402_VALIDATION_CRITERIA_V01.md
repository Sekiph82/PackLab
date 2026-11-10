# PL-0402 — Validation Criteria V01

1. Inspect and explicitly align with current PackLab ID validation and Packaging Asset/SKU/component concepts; do not create conflicting runtime contracts or claim code integration.
2. Asset ID identifies a physical/intended package design, not a SKU, supplier, mutable material, nominal size, status, revision, capture, or geometry hash. Reuse one asset across SKUs when design/geometry is the same; create component/assembly identities for independently reusable parts/configurations.
3. Define an ASCII-safe human-readable ID pattern compatible with existing validation limits, uniqueness/allocation rules, immutable non-reuse, explicit synthetic namespace and semantic metadata/display names separate from canonical IDs. Keep location, brand, customer, dates and other potentially identifying data out of public IDs/filenames; bound filename components and total length.
4. Explain immutable content-derived Packaging Asset revisions remain distinct from stable asset ID; accurately distinguish current SKU/component/assembly/imported-component version contracts. Define separate capture/source evidence IDs and safe deterministic filename convention without inventing a current PackLab capture API.
5. Define handling of unknown supplier/material/provenance, variants, artwork-only changes, geometry changes, duplicate geometry and migration/legacy IDs without destroying lineage.
6. Do not place private supplier/customer/package/production details in public IDs or filenames. No actual Kenya IDs/inventory, no real scans or PII.
7. Documentation-only; no code/test changes or physical/hosted acceptance claimed. Independent source/security reviews inspect actual content; log precise limitations and task handoff.
