# PL-0416: Artwork-only change process (geometry reused)

**Planning SOP draft — not approved for production operation.** No real POVU artwork, Kenya SKU or printed label is used; tests are synthetic. Print/colour fidelity is out of scope and not validated.

## When it applies

Only the label/sleeve artwork changes (design, text, colour, regulatory copy, variant). The physical package, label zone geometry and its surface placement stay the same. If the label **size, position, material or wrap** changes, or the package itself changes, use PL-0417 instead.

## Steps

1. **Intake.** Record the artwork change request, owner/brand approver, artwork source and licence/permission for every element (fonts, images, logos). Unlicensed elements stop the change.
2. **Ingest.** Ingest the new artwork as a new immutable `LabelArtworkAssetRevision`; never overwrite the previous artwork file or revision.
3. **Map and assign.** Map it to the **existing** Label Zone placement already used by the SKU and create an assignment (`SkuArtworkPresentationReference.from_accepted_assignment`). A stale or mismatched zone/mapping/assignment set is rejected by the contract. The contract does **not** check that the label zone belongs to the SKU's asset Design Model, so the reviewer confirms that binding.
4. **New SKU revision.** Create a new SKU revision on the **same Packaging Asset revision** with the new artwork reference. The asset record and its Scan Master / Design Model links are not touched, and no geometry is copied (`geometry_copied: false`).
5. **Review.** A reviewer compares the rendered mockup against the approved artwork proof and confirms that the label zone still fits. Rendering is a visual reference only.
6. **Retention.** Keep the old artwork revision and old SKU revision; current lookup moves to the new revision, history keeps both.

## No-go cases

Artwork without licence/permission; the label zone does not match the actual label; a request to "just replace the file"; any geometry, dimension or material change disguised as an artwork change; any claim of print-colour or regulatory-copy validation.

## Synthetic dry-run

`tests/core/test_m18_change_processes.py::test_pl0416_*` — two SKU revisions (red → blue synthetic artwork) share the identical asset revision; asset revision unchanged; current lookup returns the new artwork, history holds both; validating against a registry missing the new artwork fails. No Kenya or physical evidence is claimed.
