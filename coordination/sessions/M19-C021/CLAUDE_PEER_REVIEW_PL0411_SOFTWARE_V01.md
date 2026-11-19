# CLAUDE_PEER_REVIEW: PL-0411 duplicate-geometry review (software half), V01

Reviewer: independent Claude Code peer reviewer (non-implementing). Findings below are my own; they
are not the builder or tester report and not a CHATGPT_AUDIT / CODEX_PEER_REVIEW.
Base: HEAD 8e8c11470c04007dc9addb3b5eb85a1ffcb6449e, main. The files under review are untracked
working-tree additions:
- core/src/packlab_core/duplicate_geometry_review.py (879 lines)
- tests/core/test_duplicate_geometry_review.py (536 lines)
- docs/development/PL-0411_DUPLICATE_GEOMETRY_REVIEW.md (95 lines)
I made no edits to the source or the tests, and no git writes. The PL-0412 files were not touched.

## Verdict: SOFTWARE_PASS_WITH_NOTES

Scope: SOFTWARE COMPLETE / PHYSICAL VALIDATION PENDING only. There are no P1 findings. Fix the two
P2 findings, or explicitly accept them, before marking the task [x]. P2-1 is a doc-accuracy fix
plus an optional one-line screen fix.

## Commands run (local, Windows, .venv)
- pytest on test_duplicate_geometry_review, test_repeat_scan_registration,
  test_packaging_sku_library, test_scan_master, test_design_model and test_geometry_adapter:
  69 passed in 31 s.
- ruff check core apps tools tests: All checks passed.
- ruff format --check (line-ending auto) on the two new .py files: already formatted.
- mypy core apps tools (as CI runs it): Success, no issues in 296 source files.
- Mutation testing on temp copies only. A conftest override loaded the mutated module in the
  scratchpad; the repository was untouched. The unmutated baseline passed 18/18.

| Mutant | Result |
|---|---|
| M1 remove the mirror-fit branch | KILLED |
| M2 group all(...) -> any(...) (transitive merge) | SURVIVED |
| M3 union-find also joins NEEDS_HUMAN_REVIEW pairs | KILLED |
| M4 disable invariant screens | KILLED |
| M5 drop coverage_fraction from the partial criterion | SURVIVED |
| M6 from_design_model labels the entry SCAN_MASTER | SURVIVED |
| M7 drop the approved-group overlap check | KILLED |
| M8 REJECT treated as approve | KILLED |
| M9 improper (det -1) candidate initial poses | KILLED (fails closed: registration_failed_closed) |
| M10 allow a partial canonical entry | KILLED |
| M11 drop the review_rms >= rms policy check | SURVIVED |
| M12 disable the human-review band | KILLED |
| M13 gate on RMS only (ignore max) | KILLED |
| M14 mirror fit -> PROPOSED_DUPLICATE | KILLED |
| M15 remove _validate_rigid_transform in _evaluate | SURVIVED (Open3D with_scaling=False is already proper; this is defence in depth) |
| M16 simulation_only any -> all | SURVIVED |

Behaviour probes that I wrote myself (scratchpad, not committed):
- Transitive chain: bottles at height scale 1.0, 1.003 and 1.006. A-B and B-C come out
  PROPOSED, A-C comes out NEEDS_HUMAN_REVIEW (max 1.09). The group {a,b,c} is NEEDS_HUMAN_REVIEW
  with group_not_fully_confirmed_pairwise, so the code is correct. However, no committed test
  covers this (see M2). An owner can still APPROVE that NHR group; the plan records
  review_decision NEEDS_HUMAN_REVIEW.
- Partial containment: a genuine open sliver cut from the side face of a 100x100x300 column
  (running along the face diagonal), over 3 seeded poses. Every pose returned
  DISTINCT / partial_extents_exceed_complete_geometry, because the PCA extent of the sliver is 316
  and the sorted column extents are 300. This is P2-1.
- Separately, a 0.3-0.35 % taller bottle (0.7-0.8 mm over 225 mm) is PROPOSED_DUPLICATE under the
  default policy. That is consistent with the doc statement that tolerances are synthetic-scale
  choices, and the owner decision record is the safeguard.

## Verified OK
- Proper rotations only. _CANDIDATE_TURNS (duplicate_geometry_review.py:499-506) are
  diag(sx, sy, sx*sy)*turn, det +1, 8 poses. Every ICP initial transform (:563), every output in
  _evaluate (:519) and the refined transform (:592 -> :519) passes _validate_rigid_transform,
  which checks orthonormality and det = 1 +/-1e-4 (repeat_scan_registration.py:79-99). The adapter
  uses TransformationEstimationPointToPoint(with_scaling=False) (geometry_adapter.py:565).
  A reflection can never be accepted. The mirror branch (:636-643) only ever yields DISTINCT, and
  the mirror fit is a proper fit of an explicitly mirrored copy (_mirror, :459-463, flips x and the
  winding).
- Inverse transform for the reverse distance (:526-531): p_src = R^T p - R^T t is correct.
  _symmetric_eigen forces a right-handed basis (:341-343). The rotation init A_t*turn*A_s^T (:576)
  is correct for column-eigenvector bases.
- Invariants (:379-456). The area-weighted first and second moments use the exact triangle
  second-moment formula. Volume is taken only when the mesh is closed. Non-manifold edges
  (count != 2) count as boundary and therefore as partial (fail-safe).
- Groups (:718-764). Only PROPOSED pairs union. A NHR pair only becomes its own group when its
  ends lie in different components, so partial pairs cannot absorb confirmed groups (M3 is killed).
  A component is PROPOSED only when it is complete and every pair is PROPOSED. The probe confirms
  that no transitive merge happens.
- Fail-closed paths. These are checked before any geometry work: entry bound (max_entries <= 256),
  typed entries, duplicate ids, missing/mixed/RELATIVE scale, unit vs scale. The vertex bound is
  200k. Non-finite and degenerate geometry is rejected. The sample count is bounded by the
  RegistrationPolicy point cap, and the default 1500x12 = 18000 <= 20000.
- Authority honesty. from_design_model labels DESIGN_MODEL using the scale and unit of the
  revision itself. Nothing is labelled captured, nothing is upgraded, and no ScanMaster or
  DesignModel object is mutated. The report and the plan both carry authority_changes NONE,
  auto_merge_performed false, deletion_performed false and PHYSICAL_EVIDENCE_PENDING.
- Reuse plan (:816-879). Records are digest-bound to review.sha256. Unknown groups, duplicate
  decisions per group, overlapping approvals, non-member canonical entries and partial canonical
  entries all fail closed. Only APPROVE records produce approved_reuse. The output is sorted and
  plan_sha256 is computed over the canonical body.
- Determinism. The sampling RNG is seeded from mesh_sha256, entries are sorted by id, and output is
  canonical JSON with sort_keys. The order-independence test passes.
- Direct-adapter choice. This is acceptable and the honest option. RegistrationRevision
  (repeat_scan_registration.py:131-136) rejects non-captured authority and METRIC_VERIFIED, so
  routing a Design Model tessellation through register_repeat_scans would require mislabelling it
  as captured. The review modifies no geometry, so allowing METRIC_VERIFIED here does not conflict
  with the rule in that module against registering verified scans.

## Findings

### P1
None.

### P2
- P2-1. The partial containment screen is not a valid necessary condition, and the doc
  overclaims. At duplicate_geometry_review.py:473-481, the sorted PCA extents of a partial scan
  are compared to the sorted PCA extents of the complete mesh. The principal frame of a subset can
  rotate (for example a diagonal strip), so its extent along that frame can exceed the sorted
  extents of the parent. My probe showed a genuine subset classified DISTINCT. The consequence is
  safe for merging (no false merge), but the pair is silently removed from human review. The doc
  contradicts this behaviour:
  - PL-0411_DUPLICATE_GEOMETRY_REVIEW.md:40-42 says NEEDS_HUMAN_REVIEW also applies to any pair
    that includes a partial-coverage scan;
  - doc :87-88 says partials are routed to a human.

  Fix: either correct the doc wording, or use a sound bound. For example, compare the largest
  partial extent against the diameter bound of the complete mesh, sqrt(sum(ext^2)). The subset
  diameter is at most the parent diameter, which is at most the norm of the parent PCA extents.
- P2-2. The SCAN_MASTER label is caller-asserted on the direct constructor.
  LibraryGeometryEntry(...) (:82-130) accepts authority_kind=SCAN_MASTER with any
  authority_revision_id and no ScanMasterRevision manifest check. Only from_scan_master (:148-153)
  verifies the authority class, the revision id and the geometry digest. The reuse plan then emits
  scan_once_authority_kind / scan_once_authority_revision_id (:855-856) as though they were
  verified. Most test entries use this unverified path (test :132-146). Likewise,
  from_design_model (:172-193) does not bind the tessellation to the Design Model revision: any
  mesh can be attached to any revision id. The report records the tessellation sha256, but not its
  provenance.

  This does not upgrade authority, because everything is proposal-only. Even so, either add a
  field such as authority_verified (true only via the factory paths) to the summary and the plan,
  or make the factories the only public constructors. Mutant M6 survives, so add a test asserting
  authority_kind == DESIGN_MODEL for bottle-a-nominal.

### P3
- P3-1. Test gaps found by the surviving mutants:
  - M2: there is no transitive-chain test. My 1.0/1.003/1.006 bottle probe could serve as a
    seeded fixture.
  - M5: no test where a closed mesh with coverage_fraction < 0.98 is partial.
  - M11: the policy_tolerances_inconsistent check is untested.
  - M16: no test with a mixed simulation flag.
  - M15: defence in depth only, acceptable.
- P3-2. At :712-713 only RegistrationError is mapped to registration_failed_closed. Adapter
  InvalidGeometry / GeometryAdapterError (for example the 1M-triangle surface-distance bound at
  geometry_adapter.py:604) propagate unmapped. The behaviour is still fail-closed, but the error
  type is inconsistent.
- P3-3. There is no triangle-count bound on the entry (:116-119 bounds only vertices), so the
  pure-Python moment loop (:388-409) runs before the 1M-triangle cap in the adapter. Add a triangle
  bound next to _MAX_VERTICES.
- P3-4. build_reuse_plan (:821) does not check report contract == REPORT_CONTRACT or version.
  DuplicateGeometryReview can be built from arbitrary bytes; the digest binds content, not origin.
- P3-5. APPROVE is permitted for a NEEDS_HUMAN_REVIEW component that contains a DISTINCT pair,
  including in principle a mirror_image_handedness_differs pair. That is a human decision, and the
  plan records review_decision. Consider rejecting approval when any inside pair carries the
  mirror reason.
- P3-6. Reason labelling at :636-643. If the proper fit misses because of a poor ICP basin on an
  achiral shape, a successful mirror fit reports mirror_image_handedness_differs even though the
  parts are not mirror images. The outcome is safe (DISTINCT), but the reason can mislead.
- P3-7. RegistrationPolicy.maximum_inlier_rmse / minimum_inlier_count are serialized into the
  report policy (:271) but not enforced in _align. The surface-deviation gate is the real
  criterion. Either document this or drop the fields from the report.
- P3-8. Doc wording:
  - :24-25 says tessellation does not matter. Faceting changes the surface itself: the chord
    error for a 35 mm radius at 32 segments is about 0.17 mm. Largely tessellation-independent
    would be more accurate.
  - :47 says each NEEDS_HUMAN_REVIEW pair becomes its own review group. That holds only when the
    pair is not inside a PROPOSED component.
- P3-9. The private import of _validate_rigid_transform (:36) is acceptable within the package,
  but brittle. Consider a public alias in repeat_scan_registration.
- P3-10. The report digest includes ICP-derived floats. It is reproducible on the same
  platform/Open3D pin, but cross-platform byte equality is not demonstrated (Windows local only).

## Not verified
- GitHub Actions results for this change (the files are untracked; there is no CI run).
- macOS/Linux determinism of the report digest.
- Any physical or factory accuracy. All fixtures are synthetic, and physical acceptance stays
  PHYSICAL_EVIDENCE_PENDING.
