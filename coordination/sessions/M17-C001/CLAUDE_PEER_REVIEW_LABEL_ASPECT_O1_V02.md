# CLAUDE peer review V02: O-1 metric-aspect follow-up fixes (commit 1bbfe32f)

- Reviewer: independent Claude reviewer agent. I did not write this change.
- Date: 2026-11-11
- Source: `1bbfe32f673e999b5491deb93de606036afa2a4c` on `main` (local HEAD). The commit responds to `CLAUDE_PEER_REVIEW_LABEL_ASPECT_O1_V01.md` (CHANGES_REQUIRED, minor). It touches `core/src/packlab_core/label_artwork.py`, `tests/core/test_label_artwork.py` and `TASKS.md`, and it adds the V01 review file.
- The working tree was clean at the start of the review. The only file I created in the repo is this one, and it is uncommitted. I ran every mutation on a scratch copy.
- **Verdict: PASS.** This is a `CLAUDE_PEER_AUDITED_PASS`-eligible follow-up with limited scope: the option is opt-in and no caller passes it yet. Both V01 P2 blockers are closed and mutation-verified. P3-1, P3-2 and P3-4 are closed in code and wording. Three new P3 test-quality findings remain (below). None of them blocks acceptance.

## Closure of V01 findings

| V01 finding | Status | Evidence |
|---|---|---|
| P2-1: the drawn metric transform is untested | **CLOSED** | `test_metric_mapping_draws_with_equal_millimetre_scale_and_exact_transform` (`tests/core/test_label_artwork.py:400-436`) asserts `crop·scale+translate == target` on u and v. It also asserts isotropic mm scale, containment and centring, and it covers both CONTAIN branches and both COVER branches. M1, M2, M4 and M4b (`scale_v = scale_u`, or `scale_u·1.01`, in the metric branch), M16/M17 (CONTAIN/COVER branch swaps) and M21 (`translate_v` uses `scale_u`) are all **killed**. |
| P2-2: no pinned golden default ids | **CLOSED** | There are 6 pinned ids (`:334-361`): svg and png, each in CONTAIN, COVER and STRETCH. I recomputed all 6 with `label_artwork_old.py`. That file is byte-identical to `git show e97d4027^:core/src/packlab_core/label_artwork.py`, verified with `diff -q`. **6/6 old == pinned.** M12 (basis always hashed) and M5 (basis dropped from the id) are **killed**. The test then asserts that metric and default ids differ (`:385`). |
| P3-1: overlay and scene ids change for default mappings | **CLOSED** | `as_dict()` emits `aspect_basis` only when it is not the default (`label_artwork.py:145-149`). For the 6 golden cases, HEAD `as_dict()` is identical to the old module's `as_dict()`. I compared a `git archive e97d4027^` tree with HEAD. The only core or tests changes between them are label_artwork and turntable_sync. The comparison covered `create_label_render_overlay_binding` ids for FRONT, BACK and WRAP × CONTAIN, COVER and STRETCH (9 ids), and `create_blender_scene_package` revision ids plus manifest sha256 with an artwork binding × 3 fits, plus the base package. **13/13 lines are identical.** M9b (as_dict always emits the basis) is **killed** by `:371`. |
| P3-2: uncaught `ZeroDivisionError` in COVER | **CLOSED in code; see N-1 for the test** | The `target_aspect` finite/positive guard is at `label_artwork.py:419-420`, and the crop-extent guard is at `:457-458`. I probed 21 host inputs × 3 fits: all invalid inputs raise `LabelArtworkError`. `(1e-300,1e300)` and `(1e300,1e-300)` give `host_size_invalid`. `(5e-324,1)` gives `mapping_invalid` under CONTAIN and `host_size_invalid` under COVER. No probe raised an uncaught exception. |
| P3-3: host size is not traceable or cross-checked against the metric binding | Open, deferred | Unchanged. The commit does not claim to address it. It is acceptable while there is no caller. |
| P3-4: opt-in, no caller | **CLOSED (wording)** | The TASKS PL-0391 line now says "opt-in; no caller passes it yet, so the PL-0391 fixture mockup is not aspect-correct; default mapping, overlay and scene ids unchanged". That matches the evidence. |
| P3-5: centring untested (existed before) | **CLOSED** | M13, M13b (COVER crop centring, v and u), M14 and M15 (CONTAIN centring) are all **killed**. |

## Mutation results

The mutations ran on a scratch copy of the repository. I confirmed that pytest in that copy imports the scratch module, through `pythonpath` in `pyproject`. Target: `tests/core/test_label_artwork.py`.

| Mutant | Result |
|---|---|
| M1/M2 CONTAIN drawn size ignores host (wide branch / tall branch) | killed / killed |
| M3 `target_aspect` normalized | killed |
| M4 metric `scale_v = scale_u`; M4b `scale_v = scale_u*1.01` | killed / killed |
| M5 basis dropped from id; M12 basis always hashed | killed / killed |
| M9 as_dict never emits basis; M9b always emits basis | killed / killed |
| M13/M13b/M14/M15 centring removed | killed ×4 |
| M16/M17 CONTAIN/COVER branch condition swapped | killed / killed |
| M21 `translate_v` uses `scale_u` | killed |
| **M11 default `scale_v = drawn_height/height` (fp drift on default ids)** | **SURVIVED** (N-2) |
| **M18/M19/M20 P3-2 guards removed (singly / both)** | **SURVIVED** (N-1) |

## New findings

- **N-1 (P3): the P3-2 regression test never exercises COVER, so the new guards are unguarded.** See `tests/core/test_label_artwork.py:387-397`. The `with pytest.raises(...)` wraps the whole `for fit in ("CONTAIN", "COVER")` loop. The first CONTAIN call raises and leaves the block, so COVER never runs. The comment says the test proves "never an uncaught ZeroDivisionError (review P3-2)". With both guards removed (M20), the suite stays green. I confirmed directly that COVER then raises `builtins.ZeroDivisionError` for `(5e-324,1)`, `(1e-300,1e300)` and `(1e300,1e-300)`. The production fix is correct, but the test claims more than it checks. **Suggested:** put `pytest.raises` inside the loop, or parametrize over fit, and add `(1e-300, 1e300)` and `(1e300, 1e-300)`.
- **N-2 (P3): the golden ids do not detect floating-point drift on the default CONTAIN path.** The fixtures have power-of-two aspect ratios: 200×100 for svg and 2×1 for png. As a result, `drawn_height/height == drawn_width/width` holds exactly, and M11 survives. Over 20,000 random default CONTAIN sizes, that equality fails in **6,907** cases. So the bit-stability that the comment at `label_artwork.py:437` relies on is guarded only by that comment. Current code is correct: my 3,120-case old-vs-new equivalence run is still 3,120/3,120. **Suggested:** add one golden id with a non-dyadic aspect, for example 7×3 artwork CONTAIN.
- **N-3 (P3, nit):** `ratio` at `tests/core/test_label_artwork.py:381` and `assert ratio > 0` at `:386` are dead code. The comment says the host makes the metric geometry coincide with the default, but the test does not assert that. This is harmless.

## Other verification

| Check | Result |
|---|---|
| Old-vs-new equivalence (`prop.py`, against the e97d4027^ module) | `id_eq` 3,120/3,120. Metric property checks 9,360/9,360. Legacy record round-trip 3,120/3,120. |
| Label/artwork/overlay/Blender/SKU/dieline/zone/CAD-label suites (17 files), `PACKLAB_REAL_BLENDER_SMOKE=1`, Blender 5.2.2 | **187 passed, 0 skipped** (67 s) |
| `ruff check core apps tools tests` | All checks passed |
| `mypy core apps tools` | No issues in 289 source files |
| Hosted CI (`gh run list --branch main --limit 4`, read-only) | For 1bbfe32f, Windows Python Quality run **42907481785 succeeded** and Signing Material Guard run 42907481775 succeeded. Windows Python Quality run 42906974101 at f8a8a48b was cancelled (superseded). The macOS Capture CI run 42906973924 at f8a8a48b, which covers the turntable work and is outside this review's scope, was still in progress. Hosted CI skips the real-Blender tests. |

## Limits

All inputs are synthetic fixtures. This review covers software math, identity and test discrimination only. It makes no claim about print fit, colour, physical accuracy or real-camera fidelity. Host sizes are `mm_unverified`. The metric option is still opt-in with no caller, so the PL-0391 mockup itself is not aspect-correct. Real-Blender evidence is local, from Blender 5.2.2; hosted CI skips those tests. Scratch scripts are `prop.py`, `inputs.py`, `golden_v02.py`, `ids_v02.py`, `mutate_v02.py` and `m20_probe.py` in the session scratchpad `o1/` folder. They are not committed.
