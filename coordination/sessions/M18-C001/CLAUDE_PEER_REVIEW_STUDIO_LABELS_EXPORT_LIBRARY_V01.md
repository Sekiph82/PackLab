# CLAUDE_PEER_REVIEW - PR #15 Studio labels / export / library (V01)

Reviewer: Claude Code independent peer reviewer (did not author PR #15). Own findings only; builder/tester claims are not adopted without inspection.
Scope: PL-0448, PL-0449, PL-0460, PL-0461. Branch `origin/feat/studio-labels-export-library`, head `8449d627`, diff vs `origin/main` (12 files, +2062/-18).

## Evidence inspected by the reviewer
- Diff read in full for core (`label_metric_surface_binding.py`, `blender_label_render_overlay.py`, `blender_scene_package.py`), `engineering_export.py`, `navigation.py`, `shell.py`; `design_workbench.py`, `labels_view.py`, `library_actions.py` read in their relevant sections.
- Detached worktree at 8449d627: `uv run pytest tests/studio/test_labels_export_library.py tests/studio/test_engineering_export.py` passed (14 tests). Core regression: `tests/core/test_*label*.py test_blender_scene*.py test_cad_brep*.py` passed (153 passed, 2 skipped).
- CI: `gh run view 44816113090` is "PackLab Windows Python Quality", headSha 8449d627..., completed/success.
- Real-window artifacts in `C:\Users\sekip\Documents\PackLab-work\studio-e2e-labels\`: STEP header ISO-10303-21, SI_UNIT `.MILLI.,.METRE.`, 2 CYLINDRICAL_SURFACE + 2 PLANE; binary STL with 386 triangles; PDF with 1 page (qtpdf parsed, render smoke PASS, DEFERRED_OWNER_VALIDATION, mold_use_authorized false); dieline SVG `274.035...mm` x `34mm` with mm_unverified unit and 10 mm scale mark; audit events CREATE/LINK/SKU_CREATE; backup/restore; contact sheet. I looked at the Blender `front.png` and `three_quarter.png` renders myself: the label sits on the body, is not mirrored (red disc on the left as in the source art), is centered on the front view and has no visible z-fighting stripes or visible gap.

## Findings

### HIGH
None.

### MEDIUM
M1. The wrap label host is half the jar height because sampling splits the body into two bands. In `apps/windows-studio/src/packlab_studio/design_workbench.py:223-224`, `max(3, len(points))` for a 2-point straight profile gives 3 samples. That splits a 50 mm straight jar into two 25 mm cylinder faces. The test enshrines this ("two 25 mm bands", `tests/studio/test_labels_export_library.py:85`). The STEP shows 2 CYLINDRICAL_SURFACE. As a result the wrap host is 25 mm and the label is 20 mm = 0.8 x 25 mm (`test:95`, checks.json). The renders show the label confined to the lower band. This is a sampling artifact, not the real label area of the user's model. Fix: unify same-domain faces (e.g. OCC `ShapeUpgrade_UnifySameDomain`) or allow 2 samples in this path, then assert that the wrap host height equals the full straight body height.

M2. Compatibility with the PR #14 records is not verified. `_document_from_studio_revision` (`design_workbench.py:273-329`) is only tested with a synthetic record built from a standalone nominal model (`test:252-270`). Real Measure & Design records (`origin/feat/studio-measure-design` `measure_design.py:1123-1139`) carry a scan-fitted, captured (Scan Master-parented) model, and their `revolved_fit` operation references the fitted revision. Not tested:
- the DOCUMENT_CONTRACT re-validation of captured models;
- `create_revolve_operation` against the latest edited model;
- the ignored `design_model_revision_id`/`revision_history` cross-check against `model.revision_id`.

Also, a scan-fitted (non-uniform/non-linear) profile falls back to 257 samples (`:225`). So the wrap label probably has no single cylinder host on real project models (not verified). Detection uses the byte sniff `b'"revolved_fit"' in data` (`:242`). Re-test after PR #14 merges, using a real saved record.

### LOW
L1. The core relaxation is sound but has no negative test. `label_metric_surface_binding.py:634-635` accepts axis ±Z, and the seam check is removed at `:662-663`. `blender_label_render_overlay.py:410-419` accepts ±Z and forces `az = 1.0`. I judge this correct because:
- full 2*pi span is still enforced (`:643`);
- the overlay re-verifies the metric binding (`overlay:168-173`);
- the wrap frame (seam +Y, +Y->+X) is PackLab-canonical and independent of the kernel UV;
- z extents come from face bounds, so the axis sign does not matter.

But nothing in `tests/core` exercises a -Z cylinder or rejects an X-axis cylinder; the `label_metric_cylinder_seam_incompatible` code disappears without a replacement test.

L2. `blender_scene_package.py:846-848` circumscribes the overlay radius (`r/cos(dθ/2) + offset`, ≤ +0.12% r, about 0.05 mm at r = 42.5 mm). This is visually fine, but the manifest `renderer_only_offset_mm_unverified` no longer equals the actual radial offset. Record the extra term or document it.

L3. In `labels_view.py:342,354` the render thread is a daemon and its job is `cancellable=False`. Blender is bounded by `timeout_seconds=300.0` (`design_workbench.py:469`), but if the window closes mid-render the Blender child may be orphaned. The real run took 444 s with no cancel path.

L4. `test_labels_export_library.py:130-132` passes vacuously when provenance is refused (the early `return`). `job.run()` is never exercised in tests; the only render evidence is the manual real-window run.

L5. Screenshot 03 is not stale. `studio_e2e_labels.py:109-114` deliberately tries a FRONT zone (expected refusal) and then switches the kind back to Wrap before the shot. However, the UI keeps the last error after the kind changes, and screenshot 03 therefore does not show the artwork/dieline success text (the list row and dieline file do evidence them).

L6. The dimension-sheet SVG has unitless `width="335"` (core M13 behavior, not changed here). Print-scale users need mm units; it is acceptable as mm_unverified metadata.

Positive: the format-reset fix (`engineering_export.py:184-190`) is correct and exercised by a loop over 4 formats. The dimension sheet refuses to overwrite. Library dimensions are `PACKLAB_ESTIMATE` with method `design-model-brep-bounds-mm-unverified` (`library_actions.py:84-115`). The SKU artwork link uses variant `wrap`. The core default `profile_sample_count=257` is unchanged, and the Studio sample count is part of the BREP revision provenance (`cad_brep.py:241`), so accepted core hashes are unaffected.

## Verdict
- PL-0448: CHANGES_REQUIRED (M1). PR #14 compatibility (M2) is NOT_VERIFIED.
- PL-0449: PASS (STEP mm, STL, OBJ/GLB, dimension sheet SVG/DXF/PDF evidenced).
- PL-0460: PASS.
- PL-0461: PASS.
- PR overall: CHANGES_REQUIRED (M1 before merge; M2 re-check after PR #14).
