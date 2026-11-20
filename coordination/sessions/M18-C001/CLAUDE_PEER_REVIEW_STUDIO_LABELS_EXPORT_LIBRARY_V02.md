# CLAUDE_PEER_REVIEW - PR #15 Studio labels / export / library (V02)

Reviewer: Claude Code independent peer reviewer (not the author). These are my own findings; builder and tester claims were re-checked, not adopted.
Head reviewed: `72bd7ac4` (origin/feat/studio-labels-export-library; origin/main is an ancestor). Follows V01 (head 8449d627).

## Evidence produced by the reviewer
- CI: `gh run view 44824757773` is "PackLab Windows Python Quality", headSha 72bd7ac4..., completed/success.
- Detached worktree at 72bd7ac4. I ran core label-wrap-axis, cad_brep, cad_*, revolved_design_model, label metric binding, overlay, scene package and technical_drawing tests, plus studio labels/export tests: 209 passed, 1 skipped.
- Hash parity check (my own script, outside Git). The same nominal 50x85 jar document was revolved with default arguments on an `origin/main` worktree and on 72bd7ac4. Both gave an identical `cad-brep:3b06ce3f...f8f6` revision id and an identical geometry_sha256 `78ace2e1...8be`. With `straight_run_tolerance` 1e-6 and 0.5, the precise bounds stayed `[-42.5,-42.5,0,42.5,42.5,50]`, the same as without it. The revision ids differ, as intended.
- Artifacts I inspected:
  - `checks.json`: straight jar dieline host height 50.0 mm, `band_approximated_by_cylinder: false`, tolerance 1e-6.
  - Real test-333 record: host 207.98 x 27.57 mm, tolerance 0.5 recorded in `...-wrap-dieline.json` `label_host`.
  - STEP in `.MILLI.,.METRE.`; PDF 1 page.
  - Real-model Blender `three_quarter.png` and screenshot 12 viewed: label seated on the body band, not mirrored, no z-fighting.

## V01 findings re-check
- M1 (half-height wrap host): RESOLVED. `cad_adapter.py:1413-1434` `_snap_straight_runs` is applied only when a tolerance is given (`:1448-1449`). `cad_brep.py:317-318` adds the key to the id payload only when it is not None, and `as_dict` behaves the same way. I confirmed by test that the default path is byte-identical. With a 1e-6 tolerance, only runs whose radius spread is at most 2e-6 mm are merged, so export/STEP/measurement parity holds to within 1e-6 mm.
- M2 (PR #14 compatibility): RESOLVED. A real record exercised in the window (test-333). `design_workbench.py:351-355` now cross-checks `design_model_revision_id` and `revision_history[-1]`. `labels_view.py:243-263` prefers `ProjectManager.selected_design_model()`. It falls back to the newest file only when `has_design_model_authority()` (`project.py:608-614`) is false, and returns None (no stale file) when authority exists but nothing is selected. Authority read errors are shown in the UI, not hidden (`labels_view.py:267-270`). This is correct.
- L1: resolved (`tests/core/test_label_wrap_axis.py`). L2: resolved (actual offset recorded, `blender_scene_package.py:850,884,1001-1006`). L3: resolved (`MockupJob.cancel` kills the Popen; job cancellable with a hook; cancelled state handled). L4/L5: resolved.

## New findings
### HIGH
None.
### MEDIUM
None.
### LOW
- N1. The label/mockup chain uses a different BREP from the export chain. Labels and the Blender mockup use the 0.5 mm-snapped `label_representation` (`design_workbench.py:281-290, 786-788`), while exports use the 1e-6 BREP. A ±0.5 mm radius snap allows up to about ±3.1 mm circumference error on the dieline. It is disclosed: in the model summary, in the `label_host` JSON (tolerance, BREP id) and as mm_unverified/DEFERRED. Recommendation: also record the actual band radius min/max (the spread), not only the tolerance.
- N2. There is no direct core unit test for `_snap_straight_runs` edge cases: a run touching profile ends, a tapered band within tolerance, a mid-band spread just above 2*tol. There is also no pinned "absent keeps id" assertion. My parity script covered the latter manually.
- N3. Snapping is greedy by radius spread only, so a taper of ≤1 mm over a band is treated as a cylinder for labels. This is acceptable within the declared tolerance but is not stated in the UI text.

## Verdict
- PL-0448: CLAUDE_PEER_AUDITED_PASS (real-window evidence plus real test-333 record; physical/print validation stays DEFERRED_OWNER_VALIDATION).
- PL-0449: CLAUDE_PEER_AUDITED_PASS.
- PL-0460: CLAUDE_PEER_AUDITED_PASS.
- PL-0461: CLAUDE_PEER_AUDITED_PASS.
- PR #15 overall: PASS (LOW items non-blocking).
