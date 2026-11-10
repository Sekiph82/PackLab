# PL-0413 — Physical package sample to PackLab library

**Planning SOP draft — not approved for production operation.** This workflow is a proposed control sequence for a future site. PL-0401 station repeatability and physical-metrology validation have not occurred. Site roles, emergency procedures, numeric acceptance limits, storage technology and process timings must be reviewed locally before use.

## Roles and evidence rule

- **Sample custodian:** verifies source, permission, custody and safe package handling.
- **Capture operator:** performs only approved preparation/capture and records actual settings.
- **Reconstruction engineer:** preserves source data, runs the declared processing lane and reports defects/limitations.
- **Independent technical reviewer:** checks lineage, measurements, quality and disposition without treating the builder's result as independent proof.
- **Owner/product/EHS approvers:** resolve owner-priority, package-use, safety, supplier/license and physical acceptance decisions within their authority.

Use one internal work record per sample lifecycle and link permanent asset/capture/revision IDs per PL-0402 only after an authorized allocator exists. Never replace unknown fields with guesses. Preserve the status vocabulary actually supported by the PackLab record schema (`UNKNOWN`, `DRAFT`, `ACTIVE`, `ARCHIVED`, `RETIRED` where applicable); do not invent an `ACCEPTED` status. Keep software implementation state distinct from physical or commercial acceptance.

## 1. Receive, identify and authorize

**Entry:** an authorized custodian presents an actual physical package and can establish why PackLab may inspect/capture it.

1. Record temporary intake ID, source/owner authorization, date, custody, intended use/contents-contact status, known material/supplier facts with source evidence, condition and where the sample will be secured.
2. Assign a permanent package ID only through the approved unique allocator; otherwise retain a temporary internal intake reference. Do not put customer/supplier names or confidential lot details into filenames/public IDs.
3. Record the intended deliverable: visual reference, relative geometry, metric-unverified model, or a future independently measured reference. Do not promise manufacturing-grade use.

**Stop:** unknown ownership/permission, filled/pressurized/leaking/contaminated sample, unknown contents/use with unresolved safety implications, unsafe handling, or restricted confidential material. Isolate under the site procedure and request the responsible owner/EHS decision; do not open, clean or scan.

**Exit record:** authorization, custody, safe-to-handle decision, use class, condition images and explicit unknown fields.

## 2. Inspect and decide whether to clean or treat

Follow the PL-0400 inspection checklist. Photograph labels/artwork and surface condition in place. Preserve seals, print, closure and sample geometry; do not peel labels or apply targets over them. Do not clean by default. Cleaning requires an owner-approved method validated for the exact surface stack and intended use, and is prohibited for packages intended for food, medicine, cosmetics or other regulated contents under the current PL-0400 rule. For those packages, do not clean, open or apply any treatment; only empty, safe-to-handle exterior imaging may proceed with explicit owner/site authorization. An owner-approved method does not override this restriction.

Prefer non-contact capture remedies first: stable diffuse lights, background choice, camera viewpoint and exposure. Cross-polarization is a separately recorded optional comparison. A scanning spray/coating is prohibited unless every PL-0399 gate passes, including current exact-product SDS/TDS, actual use/site approval, EHS, matched sacrificial coupon, stop/incident/disposition plan and validated dimensional treatment plan. Unknown or food/contents-contact use is never presumed safe. If treatment/cleaning changes a label, finish, color, tack or geometry, stop, preserve before/after evidence, quarantine and obtain owner disposition.

**Exit record:** untreated baseline images, condition notes, approved cleaning/treatment decision (`NONE` by default), method and source/approval evidence if exceptional.

## 3. Check station, calibration and reference measurements

Do not use this workflow for production capture until the proposed PL-0396/0397 station is physically assembled, locally reviewed for load/clearance and safety, and PL-0401 repeatability evidence meets owner-approved criteria. A printable target is not automatically a calibrated metrology artifact.

Before each session: record station/configuration version; table/turntable/fixture IDs and ratings; camera/lens/zoom; light positions/output; background; ambient condition; calibration-board ID/dimensions/print verification; and independent scale/reference instrument ID and current verification/calibration status. Take calibration-board images in a separate calibration-only set with the object area empty, then remove it. Measure key dimensions with suitable instruments using an approved measurement plan, retaining units, tool, operator, repeat observations, uncertainty/accuracy limits and raw results. Mark image-derived scale `RELATIVE` or `METRIC_UNVERIFIED` unless independent evidence justifies a stronger status.

**Stop:** failed calibration check, expired/unknown reference status where the planned claim needs it, station repeatability gate not passed, or sample outside verified support envelope. Reconfigure/revalidate or downgrade purpose; do not hide the limitation.

## 4. Capture and preserve source evidence

For the standard COLMAP image lane, keep the package fixed in one orientation while moving the camera through overlapping viewpoints; keep illumination, focus/exposure, zoom and white balance stable within each set. Avoid severe glare, blur, clipping, moving background and missing/occluded surfaces. See PL-0400 checklist. Treat cross-polarized sets, rotated-object/turntable sets, and any approved treatment sets as separate experiments unless the exact combination has been validated.

Record source file names/hashes, capture set ID, device/software/settings, actual measured view positions if known, lighting, scale/calibration references, material/finish claims and provenance, operator/site authorization and any deviations. Keep raw originals immutable and access-controlled; do not put private Kenya scans or confidential supplier data in GitHub, public fixtures or CI artifacts.

**Exit check:** images open, cover planned surface regions with overlap, belong to one coherent capture mode, calibration and sample IDs link correctly, hashes recorded, and deviations/failed conditions preserved. Otherwise document recapture or no-go; never silently discard a failed set.

## 5. Reconstruct and assess geometry

Use only a supported, version-pinned processing lane. Record software/engine versions, config, input hashes, environment, warnings/errors and output hashes. The operator must not edit raw inputs or silently combine different motion/lighting/treatment modes. Keep original source session and all failed runs linked to the candidate revision.

Check registered views, image coverage, feature/match distribution, reprojection residuals, outliers, holes, duplicated surfaces, floating geometry, background contamination, thin-wall/handle/cap/tube/sachet defects and occluded internals. A green process exit alone does not prove geometry completeness. If reconstruction fails required checks, label it `DRAFT`/`UNKNOWN` as appropriate, record affected regions and either recapture via a justified decision or stop; do not promote a polished-looking mesh as complete.

## 6. Fit, dimensions and representation authority

Bind any fitted Design Model to the exact Scan Master/source revision and preserve parent authority. Record which fields come from supplier documents, owner reports, independent measurement, reconstruction, PackLab estimate or unknown source. Compare dimensions only against independent suitable reference measurements with traceable tool evidence and uncertainty limits. An image-derived scale, synthetic fixture, estimated mesh, or mm coordinate alone is not physical truth.

Log target dimensions, observed values, units, method, uncertainty/tolerance basis, residuals, excluded regions, coating/treatment caveats and reviewer disposition. If thresholds are not approved or uncertainty exceeds the use case, leave metric authority deferred/unverified. CAD/BREP fit, rendering, export or acceptable local tests do not grant mold or production authority; follow `docs/development/V1_LIMITATIONS_AND_MANUFACTURING_BOUNDARY.md` and obtain separate qualified engineering, supplier, compliance and owner decisions.

## 7. Independent review and library disposition

Reviewer checks sample/source authority, privacy/license, IDs/revisions, capture completeness, calibration/measurement provenance, reconstruction defects, exact parent links, treatment status, uncertainty and known limitations. Builder validation, independent review, owner/product acceptance, physical acceptance and hosted evidence are distinct records.

If required checks are incomplete, preserve a non-active draft/status supported by the schema and list exact blockers. Promotion to an active reusable library entry requires the current library contract to accept all provenance/revision fields and the designated owner/reviewer approval under a future site policy. Preserve prior revisions; corrections create new immutable content-derived revisions without reusing IDs. Keep the original capture and old library entry traceable. Never promote synthetic or AI visual-reference geometry to a physical Scan Master.

## 8. Backup, handoff and closeout

Before handoff, verify source and derived data are stored in approved internal locations, checksums/manifests are recorded, backup policy is met, and a separate restore test has passed for the relevant backup scope (PL-0412). Record library path/ID, access controls, backup version, restore evidence, open limitations, owner decision, reviewer decision and next action. If backup or restore fails, keep irreplaceable originals under custody and block library promotion.

## Non-goals and validation state

This document is a proposed lifecycle, not a validated site SOP. No physical sample, Kenya facility, calibration, measurement, reconstruction, fit, library promotion, backup/restore or production cycle was performed for PL-0413. PL-0401, PL-0403/0404, PL-0410/0412 and other real-sample tasks remain separate gates. Test suites and software evidence do not establish physical acceptance or manufacturing readiness.

## References

- PackLab PL-0396–0404 planning documents and [PL-0400 operator checklist](PL-0400_OPERATOR_CAPTURE_CHECKLIST.md).
- PackLab [V1 limitations and manufacturing boundary](V1_LIMITATIONS_AND_MANUFACTURING_BOUNDARY.md).
- PackLab `core/src/packlab_core/packaging_asset.py`, `apps/windows-studio/src/packlab_studio/packaging_library_audit.py`, and existing reconstruction/scale authority contracts.
- COLMAP, [Tutorial — image capture and reconstruction](https://colmap.github.io/tutorial.html), for overlapping views, consistent illumination and viewpoint movement.
