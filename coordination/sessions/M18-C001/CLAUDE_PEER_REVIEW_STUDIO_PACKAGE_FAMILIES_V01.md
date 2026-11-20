# CLAUDE_PEER_REVIEW - Studio package families (PL-0459) - V01

- Reviewer: independent Claude Code peer reviewer (not the builder; no source edited)
- PR: #17, branch `feat/studio-package-families`, head `10ae7979c84695f0b05969966bb62c4f673620a5`, base `origin/main` `341fd5b6`
- Verdict: **CHANGES_REQUIRED** (no HIGH; two MEDIUM items are small and test/provenance-only)

## Evidence I produced myself
- `git archive` of head and of main into a scratch dir (git-initialised so manifest commit lookup works).
- Core focused, head: test_cad_boolean, test_cad_feature_map, test_jerrycan_handle_opening, test_cad_step_roundtrip, test_cad_step_export, test_cad_brep, test_cad_parametric_handle_and_loft -> 41 passed. Same set minus the new file on main -> 37 passed.
- Studio + core, head, `uv sync --locked --offline` scratch env, offscreen: test_package_families, test_project*, test_labels*, test_engineering_export*, test_measure*, test_navigation*, test_cad_parametric_handle_and_loft, test_cad_boolean -> 91 passed, 1 skipped.
- Volume probe on the accepted PL-0293 fixture (box x[0,1] y[0,4] z[0,8], x-axis opening 0.6 x 1.4): main removes 0.00084 mm^3 (a 1e-3 sliver at x~0); head removes 0.84 mm^3 (full through-cut). The bug is real and the fix is correct.
- CI run 44834902922: completed/success, headSha 10ae7979, job "Locked Python quality" (verified with gh).
- Artifacts re-read: checks.json, log line 470 (`labels: Not done: document_envelope_invalid`), closure-cap and jerrycan-body STEP (PRODUCT label correct, SI_UNIT(.MILLI.,.METRE.)), closure-cap manifest (source_unit mm_unverified, all authority claims false), screenshots 03 and 07b.

## Accepted-core changes
1. `core/src/packlab_core/cad_boolean.py:330-331`: `Bnd_Box.Get()` returns (xmin,ymin,zmin,xmax,ymax,zmax); the old code read it as interleaved. `_indent_tool` (line ~374) was already using the grouped order. The fix changes accepted PL-0293 captured-path geometry, and only that geometry. `operation_id` does not change because it hashes provenance values, not tool geometry. The BREP revision id does change because it includes the geometry digest. No pinned ids or golden fixtures rely on the old values.
2. Ruled loft (`cad_adapter.py:374-392`, `cad_brep.py:201-217`): identity is not conflated, because a different geometry digest gives a different BREP revision id. Replay provenance is a gap, though; see M2.
3. STEP PRODUCT regex (`cad_step_export.py:233-235`): correct. `\s*` takes OCC's wrap and the helper rewrites both names. The count==1 fail-closed check is unchanged.
4. Round trip using precise bounds (`cad_step_roundtrip.py:199-202`): this does not loosen the gate. The tolerance formula is unchanged, and the check now compares true geometric extents instead of tolerance-inflated boxes. The drift-negative test is re-pointed at the new helper and still fails closed. Side effect: report `source_bounds` values, and so report ids, differ from pre-PR exports of the same input (LOW, L3).
5. `engineering_export.refresh_source`: this PR has no diff to it (it was already merged via PR #15). Nothing to review.

## Findings
- MEDIUM M1 `tests/core/test_cad_boolean.py:46-69`: the accepted captured handle-opening test asserts nothing about the cut going through the body, so it passed on the buggy code. This PR's new regression test (`tests/core/test_cad_parametric_handle_and_loft.py`) covers only the standalone path. Add a through-cut assertion (classifier OUT inside the opening, or removed volume ~0.84) to the captured-path test. Record in PL-0293 evidence that the accepted cut was effectively a no-op until this fix.
- MEDIUM M2 `apps/windows-studio/src/packlab_studio/package_families.py:1612-1618` (with `:867`, `:1022`, `:1571`): the loft mode (`ruled=True`) is hard-coded and appears in no persisted record (operation, workflow or BREP fields). On reload, the "reproduces the persisted operations" check compares only operation_ids, and those are blind to both the ruled flag and the tool geometry. A smooth rebuild, or a kernel change, would pass silently. Persist `loft_mode: "ruled"` in the workflow parts and compare the stored `brep_revision_id` (or geometry_sha256) on reload. If the digest is platform-dependent, at least surface a mismatch as a warning.
- LOW L1 `apps/windows-studio/src/packlab_studio/labels_view.py:264-285` / `design_workbench.py:256-258`: Labels fails closed with the opaque `document_envelope_invalid` on family revisions. It refuses safely and corrupts nothing. Note that saving a closure on a captured jar (test-333) makes that project's current Design Model unusable in Labels until undo. Detect `package_family_workflow` and say "Labels supports Measure & Design revisions; open the container revision". Labels is not in PL-0459's acceptance criteria.
- LOW L2 `tests/studio/test_package_families.py:229-245`: the closure replacement assertion accepts either success or refusal. In real-window evidence it was refused (`section_insufficient_points`), so the success branch on a real scan is shown only by the synthetic undo/redo test (line 360). This is acceptable as an honest disclosure, but do not claim replacement works on real scans.
- LOW L3: round-trip report ids differ from pre-PR exports for identical inputs (follows from item 4). Mention it in the release notes.
- LOW L4 `core/src/packlab_core/cad_boolean.py:285`: `body_feature_id` is checked for existence but not for `FeatureKind.BODY`.
- LOW L5 `apps/windows-studio/src/packlab_studio/project.py:633-659`: the standalone root is self-certifying. It is strictly parsed, its content digest and project_id are checked, mold=false and no captured ancestry, but no root registry exists in project authority. This matches ADR-0005 v1. Track it if roots become shared.

## Authority, units and gates (confirmed)
- The captured closure goes through the unchanged Scan Master lineage check (record CAPTURED_SCAN_MASTER, scan master id matches).
- Assembly records `thread_compatibility_claimed`, `seal_compatibility_claimed` and `interference_checked` as false, and `internal_thread_geometry_modelled` as false.
- `cut_parametric_handle_opening` refuses captured models (tested).
- Pouch has no parts, so export is disabled (tested).
- mm_unverified, DEFERRED_OWNER_VALIDATION and `mold_use_authorized=false` are preserved in documents, records, manifests and the UI text.
- No physical, factory or iPhone claims.
