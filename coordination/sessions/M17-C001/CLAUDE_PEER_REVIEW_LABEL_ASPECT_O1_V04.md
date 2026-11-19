# CLAUDE_PEER_REVIEW — Label aspect O-1, V04 (confirmation of V03 P2-1 and P3-3 fixes)

- Reviewer: Claude (independent, non-implementing). I made no source edits and no git writes. This file is the only file I wrote in the repo.
- Reviewed state: HEAD `4ee6bb09` plus working tree. `git diff -- core/` sha256 `2a81129d…`; `git diff -- tests/core/` sha256 `69ae6353…`.
- Scope: synthetic software math only. No print, physical or manufacturing claim.

## Verified
- **P2-1 fixed** (blender_label_render_overlay.py:185-197). The overlay now recomputes the mapping with `map_label_artwork_to_zone(artwork, placement, fit_mode, host_size)` and requires the result to equal the given mapping. If that call raises `LabelArtworkError`, the overlay raises `mapping_not_reproducible`. I re-ran forge.py: all three V03 forgeries are now **REJECTED** with `label_render_overlay_mapping_not_reproducible`. They were CONTAIN-metric with stretched numbers, CONTAIN-metric off-centre with REVERSED_U, and STRETCH-normalized with letterboxed numbers.
- **P3-3 fixed** (label_artwork.py:106-121). The type check now runs before the digest. Through the dataclass, `(True, True)`, a list, strings, `5.0`, `(inf, 1.0)`, `(nan, 1.0)` and a 3-tuple all raise `LabelArtworkError: label_artwork_mapping_invalid`. Earlier `digest TypeError/ValueError` lines in edge.py come from my probe computing the digest itself; they are not the library's behaviour.
- **No regressions:**
  - Focused suites (test_label_artwork, test_blender_label_render_overlay, test_blender_scene_package, test_label_metric_surface_binding, test_packaging_sku_library): **80 passed**.
  - ruff check, ruff format (CI line-ending=auto) and mypy are clean on the changed files.
  - The HEAD vs working id comparison is unchanged from V03: normalized-default mapping ids and normalized-STRETCH overlay ids and geometry are still identical to HEAD.
  - The runner-UV simulation still has worst error 6.2e-15 with 0 failures.
- **Mutations** (scratch copy only):
  - Removing the recompute equality is killed by `test_overlay_refuses_a_hand_built_mapping_with_a_self_computed_id`. That test recomputes the digest itself, so it is a real forgery and not a tautology.
  - Removing the tuple check, or the float/non-bool check, is killed by `test_metric_host_size_must_be_a_tuple_of_real_floats`.

## Remaining notes (P3, non-blocking)
- **N2 survives.** If `LabelArtworkError` passes through un-wrapped, no test fails. This branch is effectively unreachable for a mapping that passed `__post_init__`; it is defensive only.
- **M10 and M11 still survive.** The drawn-rect bounds check is now unreachable by construction: the recomputed canonical rect always lies inside the zone. The basis/host-size iff invariant is still not tested in isolation.
- **The new tuple test does not isolate the type check.** It uses `replace()` without recomputing the digest, so for some inputs the digest check could reject them first. The mutations are still killed, through the str and int cases.
- **Still open from V03:** P3-1 (no CI test covers how the runner handles `drawn_rect`, and there is no golden overlay id), P3-2 (claim wording on metric ids) and P3-4 (the TASKS.md PL-0391 evidence ids are stale).
- **Real-Blender evidence is not verified by this reviewer.** The 4 passed / PNG e3060dc8… / package 01c0c679… result is coordinator-reported. It predates these fixes, but the fixes do not change geometry or ids for canonical mappings, as my HEAD/working comparison shows.

## Verdict
**PASS_WITH_NOTES.** V03 P2-1 and P3-3 are resolved. The remaining notes are P3 test-coverage and tracker-wording items.
