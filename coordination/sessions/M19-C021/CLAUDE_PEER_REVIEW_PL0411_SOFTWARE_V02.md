# CLAUDE_PEER_REVIEW: PL-0411 duplicate-geometry review (software half), V02

Reviewer: independent Claude Code peer reviewer (non-implementing). This is a re-review of the
V01 findings (CLAUDE_PEER_REVIEW_PL0411_SOFTWARE_V01.md). The findings below are my own. They
are not the implementer report and not a CHATGPT_AUDIT / CODEX_PEER_REVIEW.
Base: HEAD 2bcf0edc49250e83dbdcca68ec9248a05c9f4e0c, main. The files are still untracked:
- core/src/packlab_core/duplicate_geometry_review.py (953 lines)
- tests/core/test_duplicate_geometry_review.py (759 lines)
- docs/development/PL-0411_DUPLICATE_GEOMETRY_REVIEW.md (125 lines)
I made no source edits and no git writes.

## Verdict: SOFTWARE_PASS_WITH_NOTES

Both V01 P2 findings are resolved. There are no open P1 or P2 findings. The remaining notes are
P3 and do not block marking the task SOFTWARE COMPLETE / PHYSICAL VALIDATION PENDING.

## Commands run (local, Windows, .venv)
- pytest on test_duplicate_geometry_review, test_repeat_scan_registration,
  test_packaging_sku_library, test_scan_master, test_design_model, test_geometry_adapter and
  test_design_preview: 87 passed in 27 s. The module alone has 33 tests, which matches the
  implementer claim. I did not reproduce the 140-test figure; my suite set differs.
- ruff check core apps tools tests: All checks passed.
- ruff format --check (line-ending auto) on the two .py files: already formatted.
- mypy core apps tools: Success, no issues in 296 source files.
- Mutation testing on scratch copies only. A conftest override loaded the mutated module; the
  repository was untouched. The unmutated baseline passed 33/33.

| Mutant | V01 | V02 | Killing test |
|---|---|---|---|
| M1 remove mirror branch | KILLED | KILLED | test_mirrored_jerrycan_is_never_merged |
| M2 group all -> any (transitive) | SURVIVED | KILLED | test_transitive_chain_is_not_merged |
| M3 union also joins NHR pairs | KILLED | KILLED | test_same_bottle_... |
| M4 invariant screens off | KILLED | KILLED | test_two_percent_taller_bottle_is_distinct |
| M5 coverage dropped from partial | SURVIVED | KILLED | test_partial_larger_than_complete_diameter_is_distinct |
| M6 Design Model labelled SCAN_MASTER | SURVIVED | KILLED | test_authority_kind_and_provenance_are_reported |
| M7 overlap check off | KILLED | KILLED | test_reuse_plan_fails_closed |
| M8 REJECT treated as approve | KILLED | KILLED | test_reuse_plan_only_from_approved_records |
| M9 improper start poses | KILLED | KILLED | fails closed in the module fixture |
| M10 partial canonical allowed | KILLED | KILLED | test_reuse_plan_fails_closed |
| M11 review_rms >= rms check off | SURVIVED | KILLED | test_review_tolerance_below_rms_tolerance_is_rejected |
| M12 review band off | KILLED | KILLED | test_reuse_plan_fails_closed |
| M13 RMS-only gate | KILLED | KILLED | test_same_bottle_... |
| M14 mirror -> PROPOSED | KILLED | KILLED | test_mirrored_jerrycan_is_never_merged |
| M15 rigid validation in _evaluate removed | SURVIVED | SURVIVED | none (defence in depth; accepted in V01) |
| M16 simulation flag any -> all | SURVIVED | KILLED | test_simulation_flag_is_true_if_any_entry_is_simulated |
| M17 unverified-canonical block off | new | KILLED | test_reuse_plan_fails_closed |
| M18 DISTINCT-pair approval block off | new | KILLED | test_reuse_plan_checks_contract_and_blocks_distinct_pairs |
| M19 revert to the old sorted-extent partial screen | new | KILLED | test_partial_subset_sliver_reaches_human_review |
| M20 contract/version check off | new | KILLED | test_reuse_plan_checks_contract_and_blocks_distinct_pairs |
| M21 provenance defaults to verified | new | KILLED | test_reuse_plan_fails_closed |
| M22 adapter errors not mapped | new | KILLED | test_adapter_errors_map_to_registration_failed_closed |
| M23 mirror rule loosened (drop RMS and 4x conditions) | new | SURVIVED | none (implementer disclosed it as untested) |
| M24 triangle cap off | new | KILLED | test_triangle_bound_is_enforced |
| M25 preview model_revision_id check off | new | KILLED | test_design_preview_must_be_bound_to_the_revision |
| M26 provenance made an init field (replace would copy it) | new | KILLED | test_replace_drops_verified_provenance |
| M27 preview root check off | new | KILLED | test_design_preview_must_be_bound_to_the_revision |
| M28 preview scale_state check off | new | SURVIVED | none |
| M29 preview parent_binding check off | new | SURVIVED | none |
| M30 diameter screen always fires | new | KILLED | test_two_percent_taller_bottle_is_distinct |

Probes that I re-ran myself against the current module (scratchpad, not committed):
- V01 sliver (my original 6-vertex diagonal strip on the side face of a 100x100x300 column, 3
  seeded poses): it was DISTINCT in V01 and is now NEEDS_HUMAN_REVIEW with
  partial_coverage_cannot_confirm_duplicate on all 3 seeds. Fixed.
- Transitive chain (bottle heights 1.0 / 1.003 / 1.006, now with verified Scan Master entries):
  a-b and b-c are PROPOSED, a-c is NHR, and the 3-member group is NEEDS_HUMAN_REVIEW. An owner can
  still APPROVE that group, because a-c is NHR rather than DISTINCT; the plan records
  review_decision NEEDS_HUMAN_REVIEW. This is intended human authority, and it is acceptable.
- Residual on DesignPreview (the implementer note): I passed a box mesh inside a DesignPreview
  whose lineage fields match a nominal bottle Design Model revision. from_design_model accepted it
  and labelled it DESIGN_PREVIEW_BOUND_TO_REVISION / authority_verified True. Confirmed: the
  binding checks lineage consistency, not geometry provenance. See P3-A.
- An entry built directly can be relabelled by calling entry._verified(...) (or
  object.__setattr__), which sets authority_verified True. This is a private API, and Python
  cannot prevent it. See P3-B.

## V01 findings: disposition
- P2-1 (partial screen): RESOLVED. duplicate_geometry_review.py:527-537 now compares only the
  largest partial extent with the diameter bound sqrt(sum ext^2) of the complete mesh, plus
  tolerance. This is a sound necessary condition: any width of a subset is at most the subset
  diameter, which is at most the parent diameter, which is at most the norm of the parent extents
  measured along orthogonal axes. Doc :55-61 and :113-115 now describe it accurately. M19 and M30
  are both killed.
- P2-2 (authority asserted by the caller): RESOLVED for the scope of this task.
  - :109 makes geometry_provenance a field with init=False. Direct construction and
    dataclasses.replace always yield CALLER_ASSERTED_UNVERIFIED (M21 and M26 killed).
  - The factories at :194 and :232 set a verified provenance.
  - The summary (:240-241) and the plan (:930) expose the provenance.
  - build_reuse_plan refuses an unverified canonical entry (:917-918, M17 killed).
  - from_design_model now requires a DesignPreview with lineage consistent with the revision
    (:208-220). Residual limits are in P3-A and P3-B.
- P3-1 (test gaps): RESOLVED for M2, M5, M11 and M16. M15 is accepted as defence in depth.
- P3-2: RESOLVED (:775). InvalidGeometry and GeometryCapabilityUnavailable subclass
  GeometryAdapterError (geometry_adapter.py:32-40). M22 killed.
- P3-3: RESOLVED (:57, :134-135, M24 killed).
- P3-4: RESOLVED (:884-888, M20 killed). Content binding, not origin binding, remains inherent
  and is documented.
- P3-5: RESOLVED (:921-922, M18 killed). The test uses a forged report rather than a natural one;
  that is adequate because the check is purely structural.
- P3-6: PARTIALLY RESOLVED (:695-706); see P3-C.
- P3-7: RESOLVED (:312-325). Only the ICP parameters actually used are reported, with
  scaling_enabled False.
- P3-8: RESOLVED. Doc :32-35 on tessellation and :64-67 on group formation are now accurate.
- P3-9: RESOLVED by an explanatory comment (:40-41) and doc :46-47.
- P3-10: RESOLVED in the doc (:121-123); the limit is disclosed.

## Verified OK (re-checked)
- No reflection can be accepted. The candidate poses (:555-562) are all proper rotations. Every
  ICP start (:619), every result and the refined transform (:575) pass _validate_rigid_transform.
  The adapter uses with_scaling False. The mirror branch can only return DISTINCT (:703-706).
- Authority is unchanged and nothing is captured-labelled or upgraded. The report and the plan
  carry authority_changes NONE, no auto-merge, no deletion and PHYSICAL_EVIDENCE_PENDING.
  existing_scan_master_authority_preserved is True.
- Fail-closed ordering is unchanged. Bounds and scale/unit checks run before any geometry work.
- Group formation is unchanged and correct. No transitive merge happens, and partial pairs do not
  absorb a component.

## New / residual findings

### P1
None.

### P2
None.

### P3
- P3-A. DesignPreview provenance (the implementer residual). Because a DesignPreview can be built
  directly with any mesh, DESIGN_PREVIEW_BOUND_TO_REVISION proves lineage consistency, not that
  tessellate_design_preview produced the mesh from this revision (probe confirmed). I judge this
  ACCEPTABLE for the software half, for three reasons:
  - DesignModelRevision carries no tessellation digest that could be checked;
  - a Design Model is never captured authority, and nothing is upgraded;
  - a reuse plan still needs an explicit owner APPROVE record, which is the real gate.

  Recommended follow-ups:
  - state in doc :24-26 that the check is a lineage check and that the preview mesh is not
    regenerated;
  - optionally rename the label to something like DESIGN_PREVIEW_LINEAGE_CONSISTENT;
  - or, stronger, regenerate the preview inside from_design_model, or bind it to a digest from
    tessellate_design_preview.
- P3-B. LibraryGeometryEntry._verified (:156-158) is callable on any instance and mutates a frozen
  object in place. Python cannot fully prevent this, and the leading underscore marks it private.
  Consider a module-level helper, or a check that it is only used on freshly constructed entries.
  Not blocking.
- P3-C. Mirror rule at :695-706 (M23 survives, as the implementer disclosed). Safety holds either
  way, because a reflection is never PROPOSED. One trade-off is worth recording, though. A true
  mirror pair whose proper fit has RMS of at most 0.6 (a nearly achiral part) now falls to
  NEEDS_HUMAN_REVIEW with localized_deviation_exceeds_tolerance instead of DISTINCT.
  Consequences:
  - such an NHR pair group contains no DISTINCT pair, so the P3-5 block does not apply and an
    owner could APPROVE it;
  - mirror_registration is in the pair record, but it is not surfaced as a reason.

  Suggestions:
  - add a non-decisive reason such as reflected_fit_better when the mirror fit passes _fits, so
    the human sees it;
  - add a seeded test where the 4x/RMS condition decides the outcome.
- P3-D. M28 and M29 survive: the preview scale_state and parent_binding_revision_id lineage checks
  (:213, :218) are untested. Each needs a one-line parametrize addition in
  test_design_preview_must_be_bound_to_the_revision. Fitted (non-standalone) Design Model previews,
  with a scan_master_revision_id and geometry digest, also have no positive test.
- P3-E. The implementer reported 140 tests across related suites. I ran a different set (87
  passed) and the module count of 33 matches; I did not reproduce the 140 figure itself.

## Not verified
- GitHub Actions results (the files are untracked; there is no CI run).
- Determinism of the report digest on macOS or Linux.
- Any physical or factory accuracy. All fixtures are synthetic; PHYSICAL_EVIDENCE_PENDING stays.
