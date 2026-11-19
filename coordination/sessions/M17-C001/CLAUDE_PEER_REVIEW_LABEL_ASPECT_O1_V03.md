# CLAUDE_PEER_REVIEW — Label aspect O-1, V03 (metric CONTAIN/COVER wired into render overlays)

- Reviewer: Claude (independent, non-implementing). I made no source edits, commits, pushes or stash/reset/clean. This file is the only file I wrote in the repo.
- Reviewed state: HEAD `4ee6bb09` plus uncommitted working-tree changes. `git diff -- core/` sha256 `93e08956…`; `git diff -- tests/core/` sha256 `a82d24f9…`.
- In scope: the 4 changed core modules (label_artwork, label_metric_surface_binding, blender_label_render_overlay, blender_scene_package) and 4 tests (test_label_artwork, test_blender_label_render_overlay, test_blender_real_scene_smoke, test_pl0391_label_mockup_demo). The diffs under scripts/codex, tools/codex and tests/ci are a separate change and I did not review them.
- Scope of claims: synthetic software geometry and math only. Nothing here is a print, physical-fit or manufacturing claim.

## Evidence I produced myself
1. **Focused suites** (.venv, QT_QPA_PLATFORM=offscreen): label_artwork, blender_label_render_overlay, blender_scene_package, label_metric_surface_binding, packaging_sku_library: **78 passed, 0 skipped**. Non-Blender parts of blender_render, render_batch, glb_export, pl0391 demo and real_scene_smoke: **15 passed, 6 skipped** (all 6 skips are real-Blender gated).
2. ruff check passes. ruff format --check with the CI line-ending=auto config passes on all 8 files. mypy passes on the 4 core modules.
3. **HEAD vs working comparison.** I extracted HEAD with git archive into the scratchpad and computed ids in both trees for front/back/wrap × square, 3:1 and 1:4 artwork × both bases × CONTAIN/COVER/STRETCH:
   - **Normalized (default) mappings:** ids are identical for all fits.
   - **Normalized STRETCH overlays:** ids and geometry are identical.
   - **Metric mappings:** ids change for every fit, because the host size is now part of the identity. Metric COVER/STRETCH overlay geometry is identical, but their overlay ids change through the mapping id.
   - **Metric CONTAIN:** geometry changes as intended (drawn_rect added, quad/patch shrunk).
   - **Normalized CONTAIN/COVER:** HEAD accepted these overlays; they are now rejected with metric_aspect_mapping_required.
4. **Math and runner-UV simulation.** I extracted the runner _artwork_uv from BLENDER_SCENE_RUNNER with ast and ran 3 zone kinds × 3 boundaries × 4 artwork aspects (1:1, 3:1, 1:4, 16:9) × 3 fits × CANONICAL_UV/REVERSED_U × wrap seams {0, 0.1, 0.65}. Results:
   - The UVs at the drawn corners equal the expected crop corners, mirrored for REVERSED_U. Worst error was 6.2e-15.
   - CONTAIN: the drawn quad/arc has the artwork aspect in mm, fits inside the zone, and touches the zone on one axis.
   - COVER: the crop aspect equals the zone mm aspect.
   - Wrap: theta0 = 2*pi*(drawn_u0 - seam).
   - All of these hold to about 1e-8 relative. The residual comes from a pre-existing source: the wrap overlay takes its z extent from Bnd_Box, which includes the face tolerance, while the binding uses the parametric height. This change did not introduce it.
   - The mirror about the placement boundary is correct only because the canonical CONTAIN rect is centred (see P2-1).
5. **Mutation run.** I applied mutations to a scratch copy only, then ran the 5 focused suites. Killed: M1 (drop the normalized-fit reject), M2 (drop the host-size mismatch check), M3/M4 (planar/wrap geometry uses the boundary instead of the drawn rect), M6 (host size left out of the digest), M8 (swap host axes in CONTAIN), M9 (helper skips the placement check), M13 (COVER uses the normalized aspect), M14 (helper swaps the host axes). Survived: M5, M7, M10, M11, M12 (details in P3-1).

## Findings

### P2-1 — Forged but self-consistent mappings are not re-derived (blender_label_render_overlay.py:174-199)
The overlay checks only aspect_basis, host_size_mm_unverified and that the drawn rect lies inside the zone. A mapping revision id is a public digest, so anyone can build a self-consistent record. I built three such records and all three were **ACCEPTED**:
- (a) fit_mode=CONTAIN, metric basis, correct host size, but a full-zone target with non-uniform scale. This renders distorted, which is exactly what O-1 is meant to prevent.
- (b) Metric CONTAIN with an off-centre drawn rect, used with REVERSED_U. The runner mirrors about the placement boundary, so the drawn quad samples outside the artwork.
- (c) fit_mode=STRETCH, normalized basis, with letterboxed CONTAIN numbers.

This gap was already present at HEAD. This change widens its effect, because the mapping target rect now also drives the 3D quad/patch geometry. Recommended fix, one line in the spirit of the existing verified != metric_binding check: require mapping == map_label_artwork_to_zone(artwork, placement, fit_mode=mapping.fit_mode, host_size_mm_unverified=mapping.host_size_mm_unverified). This rejects all three forgeries and makes the bounds check and the centring assumption hold by construction. It is not a regression for honest callers, so it does not block.

### P3-1 — Gaps in test sensitivity (surviving mutations)
- **M5 / M12 (blender_scene_package.py:829, :844, :801):** no non-Blender test exercises the runner use of drawn_rect_normalized_uv, or the mirror boundary choice. Only the gated real-Blender smoke covers them. My extracted _artwork_uv simulation is an inexpensive pattern that a CI test could reuse.
- **M7 (blender_label_render_overlay.py:221):** nothing pins the claim that COVER/STRETCH overlay ids are unchanged. There is no golden overlay id. A golden id for a normalized STRETCH overlay would lock it; I confirmed equality against HEAD manually.
- **M10 (blender_label_render_overlay.py:186-199):** the drawn_rect_outside_zone reject has no test. It can only be reached with a forged mapping.
- **M11 (label_artwork.py:104-105):** the basis/host-size iff invariant can be removed without failing the 5 suites. The forged replace() cases in the new host-size test are rejected by the digest check anyway, before the invariant is reached. That test therefore does not isolate the invariant. Recomputing the digest in the forged record would make it discriminating.

### P3-2 — Claim precision: metric mapping and overlay ids changed
Claim 4 says COVER/STRETCH geometry and ids are unchanged. That holds for the normalized basis. For metric mappings (V01/V02, committed at HEAD), every mapping id changes, and so does every overlay id built on one. The geometry is unchanged. No production caller or persisted artefact used metric mappings, so the impact is nil. The wording should still be corrected.

### P3-3 — Weak type validation of host_size_mm_unverified in the dataclass (label_artwork.py:106-115)
(True, True) and a list are accepted. A string raises TypeError instead of LabelArtworkError. A non-iterable value raises TypeError in the digest. The factory validates properly, and the overlay compares with != against a tuple, so a list fails closed. Cosmetic.

### P3-4 — Persisted manifests and recorded evidence
- **Pre-change scene manifests are not rejected.** There is no Python loader. The runner falls back to placement_boundary_normalized_uv when drawn_rect_normalized_uv is absent, so old manifests render exactly as before, including their old distortion.
- **Rebuilding from in-memory inputs that use normalized CONTAIN/COVER now fails closed.** The only such callers were tests.
- **No production caller (core/apps/tools) builds overlays.** create_blender_scene_package / BlenderArtworkBinding are used only in tests.
- The runner does not bounds-check a manifest-supplied drawn_rect_normalized_uv. The manifest digest is self-certifying, so a hand-edited manifest could move the quad. This is presentation-only and consistent with how the runner treats the other geometry fields.
- The TASKS.md PL-0391 line still cites scene package 8f9b4b57… and PNG 95833b8a…, and says no caller passes the host size. Both are superseded by this change and should be updated when it is accepted.

### P3-5 — PL-0391 pixel-test adjustment (the coordinator asked me to judge this)
Real-Blender result as reported by the coordinator: 4 passed in 561 s, PNG e3060dc8…, scene package 01c0c679…. **I did not re-run it** (instructed not to), so for me it is NOT_VERIFIED and builder-reported evidence only. My judgement on whether the adjustment is legitimate, based on the geometry:
- **Saturation 0.02 -> 0.01: legitimate.** The front zone is 70x28 mm. The square artwork is now 28x28 mm, so it covers 40% of its former area. The back zone shrinks the same way, and the wrap shrinks from 18.85x12 to 12x12 mm. A smaller saturated fraction is the expected effect. The bound still fails on an all-white or unlabelled render, but it is now weak. Pinning the new observed ratio with a margin would be tighter.
- **Wide-row threshold 60 -> 40: legitimate.** The front label is about 28 mm wide against the 10 mm boss diameter, so roughly 90 px versus 30 px as stated. 40 still separates the two, but by a margin of only about 10 px over the boss. That margin is acceptable but tight if the camera or resolution changes.
- **Corner samples 0.08/0.92 -> 0.2/0.8: legitimate and arguably better.** On a 2x2 texture the texel centres are at 0.25/0.75. Samples at 0.08 are half a texel from the edge, where bilinear and edge filtering blend colours more as the label gets fewer pixels. The four-quadrant colour/orientation assertions are unchanged, so the test still detects mirror or flip regressions.
- **Timeouts 180 -> 600 s:** these stay within _MAX_RENDER_TIMEOUT_SECONDS = 600 and are not part of the request identity. Test-only, and acceptable.
Overall: none of the relaxations removes a regression signal that O-1 should keep. The contraction follows directly from the intended CONTAIN fit.

## Verdict
**PASS_WITH_NOTES** for the synthetic software scope:
- The CONTAIN/COVER metric math, the drawn-rect geometry, the REVERSED_U mirror and the wrap seam are correct for canonical mappings.
- Default and normalized-STRETCH ids are stable.
- Honest callers fail closed on normalized CONTAIN/COVER and on a host-size mismatch.

Recommended before or soon after acceptance: P2-1 (re-derive the mapping in the overlay), the P3-1 test gaps, and the P3-2/P3-4 tracker wording. The real-Blender evidence remains coordinator-reported and was not re-run by this reviewer.
