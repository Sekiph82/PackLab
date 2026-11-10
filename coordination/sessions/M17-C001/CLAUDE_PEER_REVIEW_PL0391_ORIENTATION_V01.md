# CLAUDE peer review: PL-0391 follow-up, artwork orientation (commit d5848eda)

- Reviewer: independent Claude reviewer agent. I did not author the change.
- Date: 2026-11-11
- Source: `d5848eda1bcfb835cb5879e3785ca9c50b4b5d89` on `main`. The working tree was clean at review start.
- Scope: follow-up to finding P2-1 in `CLAUDE_PEER_REVIEW_PL0390_0392_V01.md`, where label artwork rendered rotated 180°. The commit adds `_viewer_orientation`, changes `_artwork_uv`, and wires both into `_create_overlay` in `core/src/packlab_core/blender_scene_package.py:765-868`. It also adds a test and updates the pin in one smoke test.
- **Verdict: PASS.** Eligible for `CLAUDE_PEER_AUDITED_PASS` as a PL-0391 follow-up within synthetic software scope. There are no P0, P1 or P2 findings. The P3 findings below are non-blocking.

## Evidence

| Check | Result |
|---|---|
| Real-Blender suites (9 files), `PACKLAB_REAL_BLENDER_SMOKE=1`, Blender 5.2.2, `--basetemp` in scratch | **60 passed, 0 skipped** (208 s) |
| `ruff check core apps tools tests` | All checks passed |
| `mypy core apps tools` | No issues in 288 source files |
| Hosted CI for d5848eda (`gh run list`) | Windows Python Quality 42902240899 **success**; Signing Material Guard 42902240606 **success**. Hosted CI skips real-Blender tests, so the render evidence here is local only. |
| Diff footprint | One source file changed: the embedded `BLENDER_SCENE_RUNNER` string only. Two test files changed. No change to the core lineage or authority builders, `label_artwork.py`, `blender_label_render_overlay.py`, `label_dieline_svg.py`, or `TASKS.md`. |

### Empirical placement of the artwork's top-left pixel

I appended a probe to the built runner and ran it in scratch. For each overlay it fits world position against UV from Blender's evaluated mesh. Image top-left is Blender UV (0,1), because the image uses `TOP_LEFT` pixel origin. Synthetic 2×2 artwork: TL red, TR green, BL blue, BR white. Box 100×60×40 mm with a boss of radius 5 mm, height 20 mm, centred at (50,30). Placement boundary u 0.1–0.8, v 0.15–0.85.

| Overlay (zone kind, normal) | Seen by preset | Image TL in world (m) | Image TR | Viewer-right direction | Reads upright, L→R? |
|---|---|---|---|---|---|
| y=0 face (`BACK` zone, −Y) | `FRONT` (camera y=−0.202) | (0.02, 0, 0.034) | (0.09, 0, 0.034) | +X | yes |
| y=60 face (`FRONT` zone, +Y) | `BACK` (camera y=+0.262) | (0.08, 0.06, 0.034) | (0.01, 0.06, 0.034) | −X | yes |
| Boss wrap (+Z axis, θ 36°–288°) | `FRONT` / `THREE_QUARTER` | θ=288°, z=0.057 | θ=36°, z=0.057 | decreasing θ (dθ/du_img = −4.398 rad) | yes |

On the boss, the TL pixel at θ=288° sits on the −X side, which is the viewer's left from the −Y side. Rows run down: z goes from 0.057 to 0.043.

I composited the renders onto a dark background and inspected them by eye (scratch `probe_out/dark_render_{front,back,tq}.png` and `zoom_boss_*.png`):

- **FRONT preset**: the panel and the boss wrap both read red TL, green TR, blue BL, white BR.
- **BACK preset**: the +Y panel reads the same way for its viewer. The boss shows its unlabelled seam gap, as expected, because the wrap leaves out θ=−72°…36°.
- **THREE_QUARTER preset**: consistent. The boss shows more of its right-hand (green/white) side.

### Mutation test

Run on `git archive` copies in scratch. Only `return mirror_u, mirror_v` was mutated. Targets were the new orientation test plus the scene smoke test.

| Mutant | New front test | Smoke test (`uv_first_loop`) |
|---|---|---|
| `return False, False` (pre-fix behaviour) | FAIL (TL ≈ white 211/216/220) | FAIL |
| `return mirror_u, False` | FAIL (TL ≈ blue-ish 136/150/218) | FAIL |
| `return False, mirror_v` | FAIL (TL ≈ green-ish 137/214/168) | FAIL |

All 3 mutants were killed by both tests. The smoke test's `uv_first_loop == [1,0]` pin covers all three overlays, including the cylinder, so the wrap orientation is also guarded at the UV level.

## Math review (general case)

I extracted the runner functions and executed them directly (scratch `mathcheck.py`).

- **Planar ±Y faces.** Both faces return (mirror_u, mirror_v) = (True, True), a net 180° rotation, which matches P2-1. The +X normal with u=+Y case gives (False, True), which is correct: viewer-right is +Y.
- **Upside-down v (v=−Z).** Returns (True, False), which is correct.
- **Cylinder with `+Y_TO_PLUS_X`.** mirror_u is always True for any θ, because `Z × n = −dP/dθ` identically. mirror_v is True for the +Z axis. Any other azimuth raises `scene_wrap_azimuth_direction_unsupported`.
- **Footprint invariance.** Mirroring is applied in image space (`column → 1 − column`, `row → 1 − row`). The set of zone (u,v) that maps into [0,1] is therefore unchanged under every mirror combination, with or without centring. I checked this with an uncentred translate and with a centred CONTAIN mapping, under both `CANONICAL_UV` and `REVERSED_U`. Scale is untouched, so STRETCH, CONTAIN and COVER keep their size and bounds.
- **REVERSED_U.** It is still applied first, as a reflection about the boundary centre, and it composes with the new mirror. REVERSED_U now means "mirror image relative to the upright canonical reading". That is consistent semantics, but no document states it (see P3-3).
- **Horizontal v_axis or vertical normal** (for example a top-face label). This case returns (False, False) silently: `viewer_right` is the zero vector, and `v_axis[2]` is 0. The docstring defines up as world +Z but does not cover this case. It is unreachable today, because `_planar_geometry` (`blender_label_render_overlay.py:313-319`) only emits ±Y normals with v=+Z (see P3-1).
- **Cylinder axis other than +Z.** `_viewer_orientation` would return mirror_v=False for a −Z or +X axis. However, `_create_overlay` (`blender_scene_package.py:843-848`) hard-codes the axis to world Z when it builds vertices, so those results would contradict the mesh. This is also unreachable, because `_cylindrical_geometry` (`blender_label_render_overlay.py:361-369`) rejects any axis other than +Z, but the runner does not re-check it (see P3-1).
- **`base_matrix`.** The probe confirms that overlay world coordinates equal the source mm × 0.001 with no rotation. Computing the orientation in the source frame is therefore valid for the current importer path.

## Renderer vs core placement (judgement)

The mirroring belongs in the renderer **for now**, for three reasons:

1. The core records (zone u/v, `LabelArtworkMappingRevision`, overlay binding) describe face-parameter space and stay unchanged. No authority, lineage or digest record moves, apart from the runner sha that is already bound into the scene package. That runner sha correctly versions the presentation change.
2. The renderer is the only consumer that maps artwork pixels onto 3D. A repo grep for `artwork_mapping` / `translate_u` finds no other 3D consumer, and the SVG dieline embeds no artwork.
3. Mirroring in image space preserves the footprint exactly, so the core placement intent is honoured.

The "artwork up = world +Z, read from outside" convention is design intent, not rendering detail. When a second consumer appears (a Qt/GLB preview with textures, or an artwork-bearing dieline/print PDF), the convention should move into core as an explicit field on the overlay binding (for example `artwork_up_axis` / `artwork_right_axis`, or recorded mirror flags). Both consumers then agree, and the dieline's print orientation is tied to the same rule. This is not blocking.

## Findings

- **P3-1** `blender_scene_package.py:771-789`: `_viewer_orientation` does not guard the degenerate and unsupported inputs listed above. Those are a horizontal v_axis or a near-zero `viewer_right` (vertical normal), and a cylinder `axis` other than +Z, which `_create_overlay:843-848` hard-codes. The function returns flags silently instead of raising (for example `scene_overlay_artwork_up_undefined` / `scene_wrap_axis_unsupported`). Core upstream makes these unreachable today. A fail-closed guard costs about two lines and matches the runner's existing `azimuth_direction` check.
- **P3-2** `tests/core/test_pl0391_label_mockup_demo.py:145-148`: the test name and comment say "front label". However, the `FRONT` render preset puts the camera at −Y (`blender_render_preset.py:120`), so the test actually asserts the `LabelZoneKind.BACK` zone (y=0, normal −Y). The `LabelZoneKind.FRONT` zone (+Y) is visible only from the `BACK` preset and is covered only by the shared-code argument plus my manual BACK render. The label zone "front" (+Y) and the render preset "FRONT" (view from −Y) are opposite conventions. The test comment should say which zone is checked. Optionally, parametrize over the `BACK` preset too, at the cost of one extra render.
- **P3-3** `blender_scene_package.py:765-771` docstring: say that up and right are undefined for horizontal faces and non-Z wrap axes, and that `REVERSED_U` now yields a mirror image of the upright reading.
- **P3-4** (provenance, optional): the scene result and render evidence do not report the applied `mirror_u`/`mirror_v`. The runner sha versions the behaviour, but per-overlay flags in `overlay_facts` (`blender_scene_package.py:967-990`) would make orientation auditable from the evidence JSON.

### Pre-existing observation, outside this commit (not blocking; follow-up candidate)

- **O-1 (P2-class, pre-existing):** `map_label_artwork_to_zone` (`label_artwork.py:380-398`) computes the CONTAIN/COVER aspect in normalized zone UV, not in metric zone size. In the fixture, the 2×2 square artwork is CONTAINed into the 70×28 mm (unverified) zone and fills it fully, so it renders stretched 2.5:1 (visible in every render). "CONTAIN" therefore does not preserve the artwork's metric aspect on non-square zones. The tracker should not describe the PL-0391 mockup as aspect-correct artwork placement until a metric-aspect fit is added.

## Limits

All inputs are synthetic fixtures. This review verifies orientation conventions only. It makes no claims about colour, print fit, physical accuracy or real-camera fidelity. Real-Blender evidence is local, from approved Blender 5.2.2. Hosted CI does not execute those tests. Scratch artefacts are in the session scratchpad and are not committed.
