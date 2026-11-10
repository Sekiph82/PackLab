# PL-0402 — Packaging asset naming and ID convention

**Proposed convention for future PackLab library entries. No production IDs are assigned by this document.**

## Existing PackLab contract

PackLab already distinguishes the governed `Packaging Asset` identity from revision, capture, geometry, component/assembly, SKU, and artwork. The Windows Studio packaging library validates canonical IDs against `^[A-Za-z][A-Za-z0-9_.:-]{0,127}$`; asset revisions are content-derived as `packaging-asset:<64 lowercase hex SHA-256>`. The library accepts a document with contract `packlab.packaging-asset.v1`, where `document.asset_id` must equal the library entry ID. Keep those runtime contracts intact. This proposal is documentation; code/schema integration is not part of PL-0402.

## ID roles and proposed syntax

Use distinct, stable, human-readable opaque identifiers. Prefixes below are reserved categories, not proof of a real item:

| Entity | Proposed form | Meaning |
| --- | --- | --- |
| Packaging asset | `PKG-000001` | One distinct physical/intended package body design or governed package identity |
| Reusable component | `CMP-000001` | One reusable cap, trigger, pump, tube, insert or other distinct part |
| Package assembly/configuration | `ASM-000001` | A specific governed combination of component identities and mating arrangement |
| SKU | `SKU-000001` | Product presentation record linked to an asset and artwork; never the geometry identity |
| Capture session | `CAP-000001` | Source image/scan session; separate from asset and revision IDs |

All examples in this document are synthetic format examples and assert no real site, item, inventory, or captured data. The prefixes and zero-padded sequence are proposed entity-type namespace only; a future owner must reserve/approve the allocator before assigning any real record. Do not encode country, brand, supplier, date, material, nominal size, customer, or other mutable/identifying facts in canonical IDs. Keep semantic descriptions and capture timestamps in access-controlled metadata.

Store descriptive fields separately: display name, package family, nominal capacity/size, material, resin grade, color, finish, supplier/manufacturer, supplier part number, plant/site, use/contact class, provenance status, lifecycle state, and owner. Each field needs a source/evidence reference and a confidence/status (for example `VERIFIED`, `OWNER_REPORTED`, `ESTIMATED`, `UNKNOWN`, `NOT_APPLICABLE`). Never turn a guess into an ID token.

## Identity and revision rules

1. Assign a stable asset ID to one package design identity, not to every SKU that uses it. Different artwork-only SKU presentations point to the same geometry asset while keeping separate SKU/artwork IDs and revisions.
2. Create a separate asset identity when the package geometry/design differs in a controlled, material way or cannot be safely represented as a governed variant. Use explicit `VARIANT_OF` or other supported relationships where appropriate; preserve parent links and evidence. A supplier change alone is metadata unless evidence shows a design/geometry difference.
3. Give independently reusable closures, triggers, pumps, caps and tubes component IDs. Give an assembly/configuration its own ID and explicit component membership/pose/compatibility record; do not hide a changing closure under a bottle-only ID.
4. Treat `asset_id` as stable and non-reusable. For a Packaging Asset, corrections/new evidence create immutable content-derived IDs with the existing `packaging-asset:<64 lowercase hex SHA-256>` contract; never overwrite or recycle the stable asset ID. Other entity types retain their own current contracts: packaging SKU uses `packaging-sku:<digest>`, reusable packaging component uses `packaging-component:<digest>`, parametric assembly graph uses `assembly-graph:<digest>`, while imported trigger/pump components use a SemVer `component_version` plus geometry digest rather than that asset revision field. Do not unify or replace these contracts under this documentation task. Human labels such as “Rev 02” are display metadata only.
5. Separate `CAP` source-session IDs from package identity/revision. A new capture does not automatically mean a new package identity. Link source files, calibration/scale records, device/capture recipe and processing lineage explicitly to the capture/revision evidence.
6. Unknown material/supplier/provenance remain explicit `UNKNOWN` or null as allowed by schema; never infer them from appearance or code a false value into an ID. Record conflicting sources and their authority instead of silently choosing one.
7. Check suspected duplicate geometry before creating new asset IDs. Reuse only when evidence supports the same physical design; retain separate IDs for genuinely different physical designs and record their relationship. Never merge IDs destructively or lose source lineage.

## Allocation, filenames and privacy

- Allocate IDs from a single authorized registry or library transaction that checks uniqueness. Reserve a sequence before issuing it; failed or retired allocations are never reassigned. Store allocator/version and allocation timestamp in metadata. IDs are case-sensitive in stored form; normalize input to uppercase before allocation, and reject whitespace, slashes, control characters and paths. These are proposed future controls, not an implemented allocator.
- Keep `asset_id`, `revision_id`, `capture_id` and `sku_id` as separate typed fields. Do not parse identity back out of display names or filenames as the authoritative source.
- Proposed internal filename format: `{asset_id}__{capture_id}__{view_code}__{sequence:04d}.{ext}`. Example only: `SYNTHETIC-TEST-PKG-0001__SYNTHETIC-TEST-CAP-0001__VIEW-0001__0001.jpg`. Use a separate synthetic fixture prefix for all examples/test material. View code is metadata with a versioned legend; use normalized azimuth/elevation only if measured/known, otherwise use a simple ordinal such as `VIEW-0001`. Capture date, physical site, and operator belong in access-controlled metadata, not in the filename.
- Bound filename fields in any future allocator: proposed canonical IDs are 40 ASCII characters maximum each, view code 16 characters maximum, sequence is fixed-width 4 decimal digits, extension allowlisted, and the full basename is limited to 180 ASCII characters. The shorter examples conform. This conservative filename bound is proposed for future filesystem compatibility and is not implemented in PackLab today.
- Keep supplier/customer names, addresses, confidential part numbers, country/site, capture dates, personal operator names, batch/lot data and product contents out of public IDs and filenames. Treat capture/image paths as internal/private unless separately reviewed for publication. Keep sensitive manufacturing fields in access-controlled metadata, not in public source repositories or sample fixtures.
- Legacy IDs remain stored as source/alias metadata with their original values and mapping evidence. Migrate by adding a stable canonical ID and an explicit old-ID alias; do not rewrite capture files, alter published hashes or delete historical identifiers as a side effect.

## Proposed grammar (machine-checkable)

These patterns restate the rules above; `tests/ci/test_m18_station_sop_docs.py` checks the examples and negative cases against them. They are a proposal, not an implemented allocator.

- Canonical ID: `^(PKG|CMP|ASM|SKU|CAP)-[0-9]{6}$` (uppercase only; no whitespace, slash, dot segment or semantic token).
- Synthetic fixture ID: `^SYNTHETIC-TEST-(PKG|CMP|ASM|SKU|CAP)-[0-9]{4}$`.
- View code: `^VIEW-[0-9]{4}$`.
- Capture filename: `{asset_id}__{capture_id}__{view_code}__{sequence:04d}.{ext}` with an asset ID of type `PKG`, `CMP` or `ASM`, a capture ID of type `CAP`, extension in `jpg`, `png`, `heic`, `dng`, and a basename of at most 180 ASCII characters.

## Synthetic-only examples

- Synthetic package asset: `SYNTHETIC-TEST-PKG-0001` (not a real asset).
- Synthetic component: `SYNTHETIC-TEST-CMP-0001` (not a real closure).
- Synthetic assembly: `SYNTHETIC-TEST-ASM-0001` (composition and fit are simulated unless separately measured).
- Two synthetic SKU records may reference the same synthetic package asset while using different synthetic artwork revisions. This demonstrates identity separation only; it does not establish compatibility or production reuse for any real product.
- Example immutable revision shape: `packaging-asset:<64-hex-digest>`. The literal digest must be computed from the canonical serialized revision by PackLab; do not copy a placeholder as a real revision.

## References and limits

- PackLab [Glossary — Packaging Asset and Component/Assembly](../architecture/GLOSSARY.md): identity, reusable part, design and artwork boundaries.
- `apps/windows-studio/src/packlab_studio/packaging_library_audit.py` and `core/src/packlab_core/packaging_asset.py`: existing `_ID` validator, `packlab.packaging-asset.v1`, and content-derived asset revision validation.
- `core/src/packlab_core/packaging_components.py`, `packaging_sku_library.py`, `assembly_graph.py`, and `trigger_pump_library.py`: distinct component/SKU/assembly/imported-component versioning contracts summarized above.
- No Kenya inventory, assigned production ID, real supplier/material field, physical package, database migration, runtime integration or code/test result is part of this task. The registry owner, namespace collision check and operational allocator implementation remain future coordination work before creating real IDs.
