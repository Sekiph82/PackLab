# PL-0417: Packaging-geometry change process (new scan and design revision required)

**Planning SOP draft — not approved for production operation.** No real mould change, Kenya package or physical measurement is used; tests are synthetic. Deviation thresholds remain pending PL-0220/PL-0221 physical evidence.

## When it applies

Any change that can alter the physical shape: mould/tooling change, wall or shoulder redesign, different neck finish or closure interface, volume change, a supplier package that failed or skipped the PL-0415 equivalence check, or a label size/wrap change that moves the label zone.

## Steps

1. **Classify.** Same package line with a new shape (same `asset_id`, new revision) **or** a different physical package (new `asset_id`, allocated per PL-0402). A SKU cannot switch to a different `asset_id`; the contract rejects it (`packaging_sku_geometry_identity_change_forbidden`), so a different package means a new or successor SKU record.
2. **New capture.** Capture the changed sample through PL-0413/PL-0400 and run the PL-0414 decision tree until it reaches `proceed_to_reconstruction_review`. The new raw capture is an immutable new `RawScanLink`.
3. **New Scan Master and Design Model.** Reconstruct and promote a new Scan Master revision. Fit a new Design Model revision whose parent is that Scan Master. Never edit the prior Scan Master or Design Model; they stay linked from the prior asset revision.
4. **New asset revision.** `with_source_links(...)` with the new raw scan, Scan Master and Design Model links. Scale stays `METRIC_UNVERIFIED` or `RELATIVE`, and `mold_use_authorized` stays `false`.
5. **Downstream review.** Re-check label zones, closure interfaces (mating references), assemblies and technical drawings that referenced the old geometry; each gets a new revision or is marked as still bound to the old revision.
6. **Explicit SKU migration.** A new asset revision alone never moves any SKU. Migrate each SKU deliberately with a new SKU revision after the reviewer signs off; the rest stay on the old revision.
7. **Retention.** Archive (never delete) the old geometry revisions while anything references them.

## No-go cases

Reusing old geometry for a changed package; editing a Scan Master in place; migrating SKUs implicitly; skipping the QA decision tree; claiming physical accuracy or mould suitability.

## Synthetic dry-run

`tests/core/test_m18_change_processes.py::test_pl0417_*` — a rescan creates a new asset revision with a different Scan Master while the old revision keeps its geometry; the SKU stays pinned until explicitly migrated; moving a SKU to a different package identity is rejected; all links keep `mold_use_authorized: false`. No Kenya, mould or physical evidence is claimed.
