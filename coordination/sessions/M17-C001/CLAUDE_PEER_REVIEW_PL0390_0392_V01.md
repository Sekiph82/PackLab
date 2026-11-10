# Claude peer review: PL-0390, PL-0391, PL-0392 and the Blender pipeline fixes (V01)

Date: 2026-11-10. Reviewer: independent Claude peer reviewer. I did not write the work under review.
Reviewed HEAD: `5277c132`, which contains `68f9e93b` (Blender fixes and PL-0391) and `916d90be` (PL-0390 parser).
No source, test, doc or TASKS edits were made. All scratch outputs and mutations ran on copies in the session scratchpad.

## Verdicts

| Scope | Verdict |
| --- | --- |
| Blender pipeline fixes in `68f9e93b` (clear the default scene, axis rotation, light power scaling, foreign-mesh guard) | **PASS** |
| PL-0390: STEP round trip plus independent parse | **PASS** (CLAUDE_PEER_AUDITED_PASS eligible; software/numerical scope only) |
| PL-0391: dieline, artwork and rendered mockup | **PASS** against frozen criteria V01. The P2 orientation finding must be recorded as an open limitation or follow-up. |
| PL-0392: one geometry reused by several POVU SKUs | **PASS** against criteria V02 (synthetic fixture only) |

None of these verdicts claims physical, print-fit, colour, mould, manufacturing or Kenya-inventory validity.

## Evidence I produced

- **Real Blender 5.2.2 LTS** (`PACKLAB_REAL_BLENDER_SMOKE=1`, `-s`, `--basetemp` in scratch).
  - Suites: `test_pl0391_label_mockup_demo`, `test_blender_real_scene_smoke`, `test_blender_render`, `_render_batch`, `_render_preset`, `_glb_export`, `_scene_package`, `_render_provenance`, `_label_render_overlay`.
  - Result: **59 passed, 0 skipped**, 188.9 s.
  - `PL0391_MOCKUP_EVIDENCE`: scene package `blender-scene-package:8f9b4b57…9415378`, preset `blender-render-preset:6c35ca6f…85df`, PNG sha256 `95833b8a…8d43`, 512×512, 59,513 visible pixels, 3 overlays, SVG dieline sha256 `36976e83…`, `a2205081…`, `d7b197df…`.
- **Other tests and checks.**
  - PL-0390/0392 tests (`test_packaging_sku_library`, `test_pl0390_step_independent_parse`, `test_cad_step_roundtrip`, `test_cad_step_export`): 17 passed.
  - `test_cad_mesh_export` (viewer GLB path): 9 passed.
  - `ruff check core apps tools tests`: clean.
  - `mypy core apps tools`: no issues in 288 files.
- **Hosted CI** (read only).
  - `5277c132` Windows Python Quality run 42899548019: success, `2875 passed, 17 skipped, 1 deselected`. The skips are the real-Blender gates; the OCP lineage tests ran.
  - Signing Material Guard: success.

### Rendered images (composited on a dark background and viewed)

- **PL-0391 three-quarter mockup.** The package is clearly rendered: the 100×60×40 box and the 20 mm cylinder boss on top.
  - The front label sits flat on the front face. The wrap label sits on the boss.
  - The top face is bright but shaded: 11 % of pixels have all channels ≥250. Labels are not blown out (3.4 % saturated pixels).
  - No default cube and no foreign objects are visible.
- **Batch renders.**
  - FRONT: 0.2 % white. BACK: 0.7 % white. THREE_QUARTER: 10.6 % white.
  - The same correct package appears in all three. The front and back labels register on their faces, and the boss wrap is visible.
  - The transparent-render smoke shows the same scene.

### Axis fix verified empirically (Blender probe on a copy of the PL-0391 project)

- Before the runner, the scene holds the factory `Cube`, `Light` and `Camera`. After it, only the tagged body and the 3 presentation-only overlays remain.
- The GLB POSITION accessor holds source mm Z-up values: min `[0,0,0]`, max `[100,60,60]`, node scale 0.001.
- After the import plus the −90° X rotation, `matrix_world` is `diag(0.001)` and the body world bounds are `[0,0,0]–[100,60,60]` mm. This exactly matches the source, so the (x,y,z)→(x,−z,y) importer mapping is undone correctly.
- Overlay-to-body distance, measured with `closest_point_on_mesh`:
  - Planar front and back: max **0.001 mm**, which is the declared renderer-only offset.
  - Boss wrap: max 0.037 mm, which is the chord error of the tessellated boss.
  - Control with the rotation reverted: 34.0 mm and 60.0 mm misregistration. The fix is necessary and correct.
- **Viewer GLB path:** `cad_mesh_export.py` is untouched, and its 9 tests pass.
- **Blender GLB export** reuses `_build_scene`. Its output now holds only the expected 4 nodes (`PackLabComponent_package-body` plus 3 overlays) with `export_yup=True`, so it is a properly converted Y-up glTF. It has no app consumers.

### Foreign-mesh guard and default-scene clearing

- `_build_scene` removes every object before import (`blender_scene_package.py:878-879`) and tags only the imported body (`:886`). Overlays are tagged `packlab_presentation_only` (`:838`).
- The render runner (`blender_render.py:541-543`) rejects any non-presentation mesh that lacks `packlab_scene_object`. An untagged presentation object would therefore fail closed (`render_scene_foreign_mesh_present`), not render silently.
- No legitimate mesh is rejected. The runners create only the camera and lights; the batch, transparent, provenance and overlay real renders all pass.
- The runner script is digest-bound (`package.runner_script` must equal `BLENDER_SCENE_RUNNER`), and Blender runs with `--disable-autoexec`.

### Light scaling

- Lights sit at `center + preset_relative × scene_span`, with size scaled the same way. Energy `× (scene_span/3 m)²` therefore keeps irradiance independent of package size.
- This is correct for disk area lights at a fixed size-to-distance ratio. The 3 m constant is a calibration choice (see P3-3).

### PL-0390 mutations (on temp copies of the exported STEP)

| Mutation | Independent text parse | OCP `validate_step_export_round_trip` |
| --- | --- | --- |
| Baseline | pass (1029 points, radial 5.0, height 100.0) | PASS, units `millimetre`, 1 solid, max delta 2.6e-23 |
| `.MILLI.` removed (metre) | fails `unit` | `cad_step_roundtrip_unit_mismatch` |
| All coordinates ×1.01 | fails `radial`, `height` | `cad_step_roundtrip_bounds_drift_exceeded` |
| Duplicate orphan `MANIFOLD_SOLID_BREP` entity | fails `solidcount` | PASS (an unreferenced entity is not transferred) |
| Product renamed | fails `name` | `cad_step_roundtrip_part_name_mismatch` |

- Export and reopen genuinely execute in OCP; the STEP writer and reader logs are present, and there is no skip path.
- A missing kernel raises `cad_step_roundtrip_capability_unavailable`, so it fails rather than passes.
- The independent parser discriminates every mutation and is stricter than the kernel on orphan solids. It is meaningful.

### PL-0392 probe

- A same-ID asset with a different revision (2 L volume) gives two geometry revisions. The test's set-equality assertion would then fail.
- A stale asset registry is rejected with `packaging_sku_asset_target_stale_or_missing`.
- The test therefore discriminates geometry drift.

## Findings

### P0 / P1

None.

### P2

**P2-1: label artwork renders rotated 180° on the planar faces, and probably flipped vertically on the wrap.** This is pre-existing in the zone-UV → artwork mapping, not introduced by `68f9e93b`.

- Probe: overlay vertex → image UV.
  - Front face (y=0): image UV (0,1), the artwork's top-left pixel, lands at (x=90, z=6) mm. Viewed from the front, that is the bottom-right of the zone.
  - Back face: the same bottom-right result when viewed from behind.
- The render matches. The synthetic 2×2 art (TL red, TR green, BL blue, BR white) appears as TL white, TR blue, BL green, BR red.
- Cause: in `_create_overlay`/`_artwork_uv` (`blender_scene_package.py:766-774, 789-794, 812-813`), placement `v` increases with +z. `_artwork_uv` then maps `v` to TOP_LEFT pixel rows, which increase downward. Horizontal handedness follows the OCC face parameterization, and the pipeline has no "artwork-up" authority.
- The PL-0391 pixel test checks only saturation and white ratio, so it cannot detect orientation.
- The frozen PL-0391 criteria do not cover orientation, so this does not block. The tracker must not describe the mockup as visually correct artwork placement. Open a follow-up for an artwork-up / face-handedness rule plus an asymmetric-artwork orientation test.

### P3

- **P3-1: stale evidence in the implementation log.** The log records scene package `4d341511…` and PNG `f9f3545b…`. At HEAD the package revision is deterministic and is `8f9b4b57…` (identical across two fresh directories), and my PNG is `95833b8a…`. The logged evidence predates the committed source. Record the re-run values above in the tracker instead.
- **P3-2: render evidence `light_facts` records preset watts, not the effective scaled energy.** The implementer already disclosed this.
- **P3-3: the light-power reference `3.0` m is a hard-coded calibration constant** (`blender_render.py:567`). It is not tied to the preset's own geometry.
- **P3-4: `test_pl0391_label_mockup_demo.py:85` passes preset bounds** `(0,-0.06,0)–(0.1,0,0.06)` that do not equal the package bounds `(0–0.1, 0–0.06, 0–0.06)` m. This is harmless because the runner reframes on the actual bounds, but it is misleading.
- **P3-5: PL-0390 independent-test limits** (`test_pl0390_step_independent_parse.py:42-53`).
  - Expected extents come from `kernel_report.source_dimensions` (OCC bounds), not from the Design Model profile (r=5, L=100).
  - The z check is extent-only, so a translated solid would pass.
- **P3-6: PL-0392 assertions on `geometry_copied`/`source_mutated` are tautological.** Both are hard-coded `False` in `packaging_sku_library.py:249-250`.
  - Non-mutation is genuinely shown by the asset revision snapshot.
  - Non-copying is shown by the exact geometry-reference key set.
- **P3-7: orphan default datablocks remain after `objects.remove`.** The `Cube` mesh and the default `Material` stay as zero-user datablocks. They are harmless and are not rendered or exported.
- **P3-8: the CAD GLB stores Z-up coordinates in a nominally Y-up glTF.** This is pre-existing; the Blender path now compensates. The Blender-exported GLB and the CAD GLB now use different axis conventions; nothing compares them today.

## Criteria check

### PL-0391 V01

1. **Pass.** The SVG intent binds the model, BREP, zone and placement revisions, and these IDs appear in the SVG text.
2. **Pass.** Overlays share the model, BREP, metric binding, artwork, mapping, assignment and zone with the SVG chain.
3. **Pass.** The render goes through `build_blender_render_runner` on the scene package. Evidence: sha256 match, `visible_pixel_count`, scene package revision binding, `network_access` NONE. I independently viewed the image.
4. **Pass.** `mm_unverified`, `DEFERRED_OWNER_VALIDATION`, `print_fit_verified`/`print_ready`/`manufacturing_authorized` false, and overlay `physical_fit_verified` false are all visible.
5. **Pass.** With the flag set and Blender missing, the test calls `pytest.fail`. Hosted CI runs only the lineage test. Local real-render evidence (this review's run) supplies the rendered demonstration, and the limit must stay disclosed in the tracker.

### PL-0390 V01

1. **Pass.** OCP export plus reader reopen, and a separate regex text parser.
2. **Pass.** Millimetre unit in both. Dimensions (10, 10, 100) agree within 1e-5 (text) and 1e-6 (kernel).
3. **Pass.** The fixture is written under `tmp_path`, and the export refuses an existing destination.
4. **Pass.** The report has `numerical_fidelity_only`, `mold_use_authorized=False` and `DEFERRED_OWNER_VALIDATION`.
5. **Pass.** The capability probe fails closed.

### PL-0392 V02

1. **Pass.** Synthetic asset ID and name, no supplier, UNKNOWN status; `SYNTHETIC-TEST-POVU-*` DRAFT SKUs. All asserted.
2. **Pass.** Both SKUs pin the same asset ID and revision.
3. **Pass.** Artwork revision and content SHA differ; no `<svg`; `artwork_bytes_included` false; the asset revision is unchanged; the exact key set is checked.
4. **Pass.** The display name states "not Kenya inventory".
5. **Satisfied now.** This consolidated run executed the test, and it passes locally and in hosted CI.
