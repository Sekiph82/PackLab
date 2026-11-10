# CLAUDE peer review: O-1 follow-up, metric-aspect CONTAIN/COVER artwork fit (commit e97d4027)

- Reviewer: independent Claude reviewer agent. I did not write this change.
- Date: 2026-11-11
- Source: `e97d4027f11e1f09bb991b55d583f3b89d0c90d6` on `main`. Local HEAD has since moved to `f8a8a48b`. `label_artwork.py` and `tests/core/test_label_artwork.py` have not changed since e97d4027. The working tree was clean at the start and end of the review.
- Scope: finding O-1 in `CLAUDE_PEER_REVIEW_PL0391_ORIENTATION_V01.md`. The commit adds the optional `host_size_mm_unverified` argument to `map_label_artwork_to_zone` and adds `LabelArtworkMappingRevision.aspect_basis`.
- **Verdict: CHANGES_REQUIRED (minor; tests and claim wording only).** I found no defect in the production math. Independent checks show that the metric CONTAIN/COVER/STRETCH paths are correct. They also show that default-path mapping revision IDs are bit-identical to the pre-change module. Two P2 test-discrimination gaps block acceptance: the committed tests do not guard the commit's two headline claims. There are also four P3 findings.

## Evidence

| Check | Result |
|---|---|
| Old-vs-new equivalence: `git show e97d4027^:…/label_artwork.py` loaded side by side. 26 random placements × 40 random artwork sizes (0.1–10⁴ units, mixed precision) × 3 fit modes | **3,120/3,120** default mappings identical in `revision_id`, target rect, crop, `scale_u/v` and `translate_u/v` |
| Legacy record round-trip: `LabelArtworkMappingRevision(...)` built from old-module values with no `aspect_basis` argument | 3,120/3,120 validate and equal the new default mapping. Changing `aspect_basis` on a legacy record with `replace()` is rejected by the digest check. |
| Metric property checks: 9,360 random (artwork, zone, host 1–500 mm, fit) cases | All values finite. The affine maps crop corners exactly onto target corners for u and v. **CONTAIN**: the drawn rect stays inside the boundary and is centred in u and v. It touches one pair of edges and keeps the artwork aspect in mm (rel. err < 1e-9). The mm scale is isotropic (`scale_u·W == scale_v·H`). **COVER**: the target equals the boundary, and the crop stays inside the source and is centred. The crop aspect equals the zone's mm aspect, and the mm scale is isotropic. **STRETCH**: geometry is identical to the default path, and the revision ID differs (the basis is bound into it). Scaling the host size uniformly does not change the geometry. A square host reproduces the default geometry to within 1e-12. |
| Host-size input probe (21 inputs × 3 modes) | bool, NaN, ±inf, 0, negative, wrong length, list, str, None, complex and `np.int64` are rejected with `label_artwork_host_size_invalid`. int and `np.float64` are accepted. Extreme ratios fail closed (see P3-2). |
| Label/artwork/overlay/Blender/SKU/dieline/zone suites (16 files), `PACKLAB_REAL_BLENDER_SMOKE=1`, Blender 5.2.2 | **165 passed, 0 skipped** (219 s) |
| `ruff check core apps tools tests` | All checks passed |
| `mypy core apps tools` | No issues in 289 source files |
| Hosted CI (`gh run list --branch main --limit 4`) | The e97d4027 Windows Python Quality run 42905028701 was **cancelled** (superseded). Run 42905352476 at descendant `69b2e726` (identical label files) **success**. Signing Material Guard 42905029147 success. Hosted CI skips the real-Blender tests. |
| Consumers of `scale_u/scale_v/aspect_basis/LabelArtworkMappingRevision` | The Blender runner `_artwork_uv` (`blender_scene_package.py:798-813`) divides by `scale_u` and `scale_v` separately, so non-uniform scale is handled. The image uses `extension=CLIP`, which keeps the letterbox transparent. Earlier STRETCH smoke runs already exercised non-uniform scale in real Blender. The overlay (`blender_label_render_overlay.py:127-185`), SKU references (`packaging_sku_library.py:95-123`) and assignment (`label_artwork.py:234-302`) check only IDs and digests. Nothing reads `aspect_basis` except `as_dict`. |

### Mutation test (temp copy in scratch, with its own `git init`; repo untouched)

Targets: `test_label_artwork.py` alone, then together with 8 consumer suites (75 tests).

| Mutation | label_artwork only | + consumers |
|---|---|---|
| M1 CONTAIN `drawn_height` ignores host (wide-artwork branch) | SURVIVED | SURVIVED |
| M2 CONTAIN `drawn_width` ignores host | killed | killed |
| M3 `target_aspect` reverted to normalized | killed | killed |
| **M4 metric `scale_v = scale_u` (renderer samples distorted artwork; target rect still correct)** | **SURVIVED** | **SURVIVED** |
| M5 `aspect_basis` dropped from the ID (both sides) | SURVIVED | SURVIVED |
| M6/M7/M8 bool / positivity / finiteness check removed | killed | killed |
| M9 `as_dict` omits basis | killed | killed |
| M10 `_ASPECT_BASES` allow-list removed | SURVIVED | SURVIVED |
| M11 default `scale_v` from `drawn_height` (fp drift in default IDs) | SURVIVED | SURVIVED |
| **M12 basis always hashed (every default mapping ID changes)** | **SURVIVED** | **SURVIVED** |
| M13/M14/M15 COVER crop / CONTAIN u / CONTAIN v centring removed (existed before this commit) | SURVIVED | SURVIVED |

## Findings

- **P2-1 — the metric transform the renderer consumes is not tested.** See `tests/core/test_label_artwork.py:305-331`. The new test checks only `target_rect_normalized_uv` and the COVER `source_crop_rect`. The Blender runner draws the artwork from `scale_u/scale_v/translate_u/translate_v` (`blender_scene_package.py:803-804`). Mutation M4 (`scale_v = scale_u` in the metric branch, `label_artwork.py:432`) survives every suite, and with it the artwork would render stretched again even though the recorded rect looks correct. That is O-1 coming back silently. The test also exercises only the `source_aspect < target_aspect` CONTAIN branch, so M1 (`label_artwork.py:422`) survives. **Required:** assert that `crop·scale + translate == target` for u and v, and assert isotropic mm scale (`scale_u·W == scale_v·H`) for CONTAIN and COVER. Cover both CONTAIN branches, for example with tall artwork or a tall host.
- **P2-2 — the "historical revision IDs are bit-identical" claim is not tested.** The assertion `"aspect_basis" not in mapping.revision_id` (`tests/core/test_label_artwork.py:341`) cannot fail, because `revision_id` is a hex digest. M12 (every default mapping ID changes) and M11 (fp drift) both survive all suites. Nothing in the repo pins a mapping ID. The claim is true today; I confirmed it over 3,120 cases. **Required:** pin at least one golden default `label-artwork-mapping:` ID (CONTAIN, COVER and STRETCH) computed at e97d4027^. Also add one test showing that metric and default mappings with the same geometry have different IDs, which kills M5.
- **P3-1 — the scope of "default ids unchanged" is overstated.** `as_dict()` now always emits `aspect_basis` (`label_artwork.py:145`). That dict is embedded in the overlay identity (`blender_label_render_overlay.py:185`, digested at `:211-233`) and in the scene manifest (`blender_scene_package.py:515`). So for unchanged default mappings, `label-render-overlay:` IDs and scene-package manifest digests change. Empirically, front, back and wrap overlay IDs all differ from IDs computed with the old `as_dict`. The scene-package ID had already changed through the runner change in d5848eda, so the recorded `8f9b4b57…` was already stale. No persisted overlay or scene IDs exist in the repo, and runners still read old manifests. **Fix:** in TASKS/commit evidence, narrow the wording to "mapping revision IDs unchanged; derived overlay/scene IDs change". Alternatively, emit `aspect_basis` in `as_dict` only when it is not the default.
- **P3-2 — extreme host ratios raise an uncaught `ZeroDivisionError` in COVER** (`label_artwork.py:443` then `:451-452`). Example inputs: `(1e-300, 1e300)`, `(1e300, 1e-300)` and `(5e-324, 1.0)`. The function still fails closed, but callers that catch `LabelArtworkError` do not catch this error. CONTAIN raises `label_artwork_mapping_invalid` for the same inputs. **Suggested:** guard the crop extent or the aspect before dividing.
- **P3-3 — host size is not traceable or cross-checked.** The mapping records `aspect_basis` but not the host size, the metric-binding ID, or the zone size in mm (`label_artwork.py:457-472`). `create_label_render_overlay_binding` has the `LabelMetricSurfaceBinding` (`blender_label_render_overlay.py:124`). It never checks that a `METRIC_ZONE_MM_UNVERIFIED` mapping matches that binding's `host_width/height_mm_unverified`, so a mapping built from a wrong host size is accepted silently. **Suggested:** record the host size, or the binding revision ID, in the mapping identity. Then verify it in the overlay builder.
- **P3-4 — the fix is opt-in and not wired into any caller.** No code in `core`, `apps` or `tools` calls `map_label_artwork_to_zone` with `host_size_mm_unverified`. The PL-0391 mockup and smoke paths use STRETCH or the default basis. O-1 therefore still applies to the rendered PL-0391 mockup. The TASKS wording does not claim otherwise, and it should stay that way.
- **P3-5 (existed before this commit)**: centring of the CONTAIN rect and the COVER crop is not tested (M13–M15 survive).

## Limits

All inputs are synthetic fixtures. This review covers software math, identity and consumers only. It makes no claim about print fit, colour, physical accuracy or real-camera fidelity. Host sizes are `mm_unverified`. Real-Blender evidence is local, from Blender 5.2.2; hosted CI does not run those tests. Scratch scripts are `prop.py`, `inputs.py`, `downstream.py` and `mutate.py` under the session scratchpad `o1/` folder. They are not committed.
