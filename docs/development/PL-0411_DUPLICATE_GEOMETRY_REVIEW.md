# PL-0411 Duplicate-geometry review (software half)

Status: software implemented and tested on synthetic fixtures only. Physical acceptance stays
`PHYSICAL_EVIDENCE_PENDING`. The Kenya factory and its real package inventory do not exist yet.

Module: `core/src/packlab_core/duplicate_geometry_review.py`.
Tests: `tests/core/test_duplicate_geometry_review.py`.

## What it does

`review_duplicate_geometry(entries, policy=...)` takes Scan Master meshes and/or Design Model
tessellations (`LibraryGeometryEntry`, each bound to one or more SKUs). It proposes groups where
one physical package is shared by several SKUs that differ only in label, artwork or colour.

1. **Fail closed** when any of the following holds:
   - there are fewer than two entries, or more than `max_entries` (default 64, hard cap 256);
   - two entries share an id;
   - a scale is missing, scales are mixed, or any scale is `RELATIVE`;
   - a unit does not match its scale state (`mm_unverified` / `mm`);
   - geometry is non-finite or degenerate, or exceeds 200k vertices / 400k triangles per entry;
   - an Open3D adapter or registration error occurs (mapped to `registration_failed_closed`).

   Entry provenance is recorded per entry. `from_scan_master` checks the manifest authority,
   revision id and geometry digest (`SCAN_MASTER_MANIFEST_DIGEST`). `from_design_model` takes a
   `DesignPreview` whose model revision, root/parent lineage, scale and unit must match the
   revision (`DESIGN_PREVIEW_BOUND_TO_REVISION`). A directly constructed or
   `dataclasses.replace`d entry is always `CALLER_ASSERTED_UNVERIFIED` and can be reviewed,
   but cannot become the scan-once source of a reuse plan.
2. **Cheap screens** run only within one package family. They compare principal-frame extents,
   surface area, enclosed volume and the sorted area-weighted radii of gyration (the
   principal-axes signature).
3. **Rigid confirmation** samples each surface deterministically. Samples are area-weighted and
   seeded by the mesh digest, so the comparison is largely tessellation-independent. Faceting
   still changes the surface itself; for example the chord error of a 35 mm radius at 32
   segments is about 0.17 mm. Alignment then runs in three
   steps:
   - start from the 8 proper principal-axes poses;
   - run the same pinned Open3D point-to-point ICP that `repeat_scan_registration` uses, with no
     scaling;
   - refine once with dense clouds.

   Every transform passes `_validate_rigid_transform`, which rejects reflection and scale. The
   reported deviation is the symmetric point-to-surface RMS and maximum. These surface-deviation
   gates are the only acceptance criteria. The `RegistrationPolicy` inlier gates (minimum
   fitness, inlier count, inlier RMSE) are not applied, so they are not written to the report.
   The rigid gate is imported as the package-private `_validate_rigid_transform`; a rename in
   `repeat_scan_registration` breaks this import loudly rather than silently.
4. **Mirror check.** Mirror images (left- vs right-hand jerrycans) share every pose invariant.
   The reason `mirror_image_handedness_differs` is given only when the reflected fit is within
   tolerance and the proper fit is clearly worse (RMS above the review tolerance and at least 4x
   the reflected RMS). Otherwise the ordinary rules below apply. Either way a reflection is never
   accepted as a duplicate, because every admissible transform is a proper rotation.
5. **Decisions:**
   - `PROPOSED_DUPLICATE`: RMS and max are both within tolerance.
   - `NEEDS_HUMAN_REVIEW`: RMS is within the review tolerance, but a localized max deviation is
     too large (for example a cap or closure difference). It is also the decision for a pair
     that includes one partial-coverage scan (open boundary edges, or declared coverage below the
     minimum), unless the partial scan's largest principal extent exceeds the complete mesh's
     diameter bound sqrt(sum of its extents squared) plus tolerance. Only that case is ruled
     `DISTINCT`, because any subset of a surface is no wider than the parent's diameter. Two
     partial scans are always NEEDS_HUMAN_REVIEW.
   - `DISTINCT`: everything else.

   Groups are connected components over PROPOSED pairs. A group stays PROPOSED only if every
   member pair was independently confirmed, so duplicates are never merged transitively. A
   NEEDS_HUMAN_REVIEW pair whose two entries are not already in the same PROPOSED component
   becomes its own review group.
6. **Report.** The output is a versioned (`packlab.duplicate-geometry-review.v1`), digest-bound
   canonical JSON report. It always records:
   - `auto_merge_performed: false`, `deletion_performed: false` and `authority_changes: NONE`;
   - `physical_validation_status: PHYSICAL_EVIDENCE_PENDING`;
   - `simulation_only`, which is true if any input entry is simulated.
7. **Decisions and reuse plan.** `DuplicateDecisionRecord` captures an APPROVE or REJECT
   decision, an actor id, a UTC timestamp and a reason. Each record is bound to the report
   sha256. `build_reuse_plan` emits "scan once, reuse for SKUs X, Y, Z" only from APPROVE
   records. It fails closed in these cases:
   - the report contract or version is not `packlab.duplicate-geometry-review.v1` / 1;
   - a record's digest does not match the report;
   - a record names an unknown group;
   - two records conflict over the same group;
   - two approved groups overlap;
   - the canonical entry is not a group member;
   - the canonical entry has only partial coverage;
   - the canonical entry's authority is caller-asserted (not verified by a factory method);
   - the group contains any DISTINCT pair (including mirror images). There is no override.

   Existing Scan Master authority is preserved and nothing is upgraded.

## Synthetic fixtures (SIMULATION ONLY)

The fixtures are procedural shapes measured in mm: a 500 ml PET-style bottle (surface of
revolution) and a chiral 20 L HDPE-style jerrycan (body, off-centre handle and corner spout).
Each uses a seeded proper rigid pose and 0.05 mm Gaussian vertex noise. Ground truth:

| Fixture | Expected | Observed (default policy) |
|---|---|---|
| Same bottle, different pose, noise and artwork SKUs, plus a finer-tessellated Design Model | PROPOSED_DUPLICATE | RMS 0.09, max 0.27 |
| Bottle 2 % taller | DISTINCT | Extent/area/volume screens. With relaxed screens, rigid fit gives RMS 0.61, max 3.3 |
| Cap radius +1 mm only | DISTINCT or review | NEEDS_HUMAN_REVIEW: RMS 0.21, max 1.08 |
| Mirrored jerrycan | DISTINCT | Proper fit max about 40. Mirror fit is within tolerance, giving the mirror reason |
| Partial scan (bottom 60 mm missing, open) | NEEDS_HUMAN_REVIEW | partial_coverage_cannot_confirm_duplicate |
| Same jerrycan across 3 seeded pose pairs | PROPOSED_DUPLICATE | RMS of at most about 0.09 |
| Open 5 mm strip along the 316 mm face diagonal of a 100x100x300 column, 3 poses | NEEDS_HUMAN_REVIEW | Strip PCA extent > 300 (old sorted-extent screen would have said DISTINCT) |
| Bottle heights 1.000 / 1.003 / 1.006 (transitive chain) | no merge | a-b, b-c PROPOSED; a-c not; group NEEDS_HUMAN_REVIEW |
| Closed bottle with declared coverage 0.9 | NEEDS_HUMAN_REVIEW | partial, not registered |

## Limits

- **Alignment accuracy.** Point-to-point ICP on sampled clouds leaves an alignment bias of
  about 0.05 to 0.1 mm on the 20 L proxy. Default tolerances (RMS 0.25, max 0.75) are therefore
  synthetic-scale choices, not calibrated factory values. Point-to-plane refinement would
  remove the bias, but the adapter does not expose it yet.
- **Partial coverage.** Partial scans are never auto-confirmed or registered. They only get a
  conservative diameter screen, so almost every partial pair is routed to a human; only a partial
  wider than the complete mesh's diameter bound is ruled DISTINCT.
- **Symmetric shapes.** Principal-axes initialisation can be ambiguous for near-symmetric shapes.
  The 8-pose multi-start covers sign flips and a 90 degree in-plane turn, not every rotation.
- **What the review cannot see.** It compares geometry only. Colour, artwork and material are
  intentionally ignored, so a material change (for example PET to HDPE with the same shape) will
  be proposed as a duplicate geometry. The human decision record is the safeguard.
- **Digest portability.** The report digest includes ICP-derived floats (rounded to 6-9
  decimals). It is reproducible on the same platform with the pinned Open3D, but cross-platform
  (macOS/Linux vs Windows) byte equality has not been demonstrated.
- **Physical acceptance stays pending.** That needs a real scanned library of physical packages
  with measured ground truth, plus a factory operator's approve/reject records.
