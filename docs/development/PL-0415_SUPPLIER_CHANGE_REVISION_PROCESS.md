# PL-0415: Supplier-change revision process (old geometry stays traceable)

**Planning SOP draft — not approved for production operation.** No real supplier, Kenya package or physical comparison has been used; examples and tests are synthetic. Equivalence tolerances are not yet defined and must come from PL-0401/PL-0220-0221 physical evidence.

## Principle

A supplier change never edits an existing record. `PackagingAsset` revisions are content-addressed (`packaging-asset:<sha256>`), so changing `supplier_id`/`supplier_name` produces a **new revision with the same `asset_id`**; the prior revision, its supplier facts and its Scan Master / Design Model links remain readable. SKU revisions pin an exact asset revision, so an existing SKU keeps pointing at the old revision until someone migrates it explicitly.

## Steps

1. **Intake.** Record the change request: new supplier identity, the supplier's evidence reference (quote, specification, drawing), effective date and which SKUs are affected. Supplier facts use provenance class `SUPPLIER_FACT` with a `source_reference_id`; never mark them as verified.
2. **Physical sample.** Obtain a sample from the new supplier through the PL-0413 intake (authorization, custody, safety). Without a physical sample the change stays `DRAFT` and only metadata may be recorded.
3. **Geometry equivalence decision** (independent reviewer):
   - Compare the new sample against the current Scan Master/Design Model using the same station and capture recipe (PL-0400/PL-0397) and record the deviation report.
   - **Equivalent within the locally approved tolerance** → continue at step 4 and reuse the existing geometry links.
   - **Not equivalent, unknown or not measurable** → use the PL-0417 geometry-change process instead. Do not reuse geometry on assumption, and do not infer equivalence from a matching neck finish or volume.
4. **New asset revision.** Apply `with_field_update` for `supplier_id` and `supplier_name` (both, with `SUPPLIER_FACT` provenance). Keep `scan_master_link`, `design_model_links` and raw-scan links unchanged. Attach the equivalence evidence ID to the work record.
5. **SKU migration.** For each affected SKU create a new SKU revision on the new asset revision (`PackagingSkuCatalog.with_revision`). SKUs still sourced from the old supplier stay on the old revision. History (`skus_for_geometry(..., include_history=True)`) shows both.
6. **Retention.** Never delete the old asset revision while any SKU revision or document references it: `validate_targets` fails (`packaging_sku_asset_target_stale_or_missing`) when it is missing, which is the intended guard. Nothing refuses the deletion itself, so the reviewer runs that validation before removing any revision. Archive with status `ARCHIVED`, never by deletion.

## No-go cases

Missing supplier evidence; geometry not compared; comparison done on a different station setup; supplier claims replacing a measured value; any request to overwrite the old revision; any claim that supplier certification, physical accuracy or mould use is established (`supplier_certification_inferred`, `physical_accuracy_verified`, `manufacturing_authorized` stay `false`).

## Synthetic dry-run

`tests/core/test_m18_change_processes.py::test_pl0415_*` — supplier change yields a new revision with the same asset ID and identical geometry links; old supplier remains readable; old and migrated SKU revisions coexist in history; dropping the old asset revision breaks validation. No Kenya, supplier or physical evidence is claimed.
