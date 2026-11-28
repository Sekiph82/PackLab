# PL-0483: root cause of the refused real Assembled pair (V01, revised for V03)

Author: implementation specialist (Claude). This is not an independent review.
Branch: `fix/combine-root-cause`. Start SHA: `2b453a98`.
Data: the owner's builds were read in place, read-only. Nothing from them was copied.
Builds are named by relative id:
- upF: `r-921e3aee` (Fast, upright)
- dnF: `r-6b23d373` (Fast, flipped)
- dnH: `r-0c2153f1` (High, flipped)
- upH: `r-5d48b0eb` (High, upright; it misses the top 20 mm)

The part is a flat-oval bottle, about 35 x 63 mm in section and 173 mm tall, with a 30 x 43 mm closure.

## 1. Mat frames, scale and levelling: not the cause

| scan | mat-plane rms | object-axis tilt in its own mat frame | marker scale u (rel.) |
|---|---|---|---|
| upF | 0.300 mm | 0.92 deg | 0.78 % |
| dnF | 0.314 mm | 2.59 deg | 0.70 % |
| dnH | 0.314 mm | 0.66 deg | 0.69 % |
| upH | 0.283 mm | 0.49 deg | 0.77 % |

dnF stands about 2.6 deg tilted on its closure. The pose refinement already takes this out: after alignment the angle between the two axes is 0.23 deg. When tilt was left free, or the axes were levelled to each other, the worst-slice coverage did not improve (dnF 0.61 -> 0.59; dnH 0.59 -> 0.62).

Moving the flipped scan's height by -4..+4 mm did not help either. The worst slice stayed at or below 0.68.

The flip is a proper rotation diag(1,-1,-1), so the scan is not mirrored. Units are mm throughout.

## 2. Like with like: the Measure & Design method agrees

Each scan was measured with `isolate_object`, the marker frame and `_slice_diameters`, the same path as Measure & Design. The diameter ratio to upF was:
- dnF: 1.0016
- dnH: 0.9934
- upH: 0.9998

The median per-height diameter differences were +0.1, -0.4 and 0.0 mm. Heights were 173.1 for upF and 173.4 for dnH; dnF is 165.3 because it lost its free end.

The data therefore describe the same object at the same scale.

## 3. Why the combine refuses, after fixing the code defects

### Code defects found and fixed (V03)

1. **`_shell` took the outermost point of each patch of the unrolled wall.** Sparse MVS strays outside the wall therefore replaced the real wall: glare fans beside the upright foot, spikes at the oval's tips, and curtain fragments.
   - Fix: `_dense` drops points that have fewer than 25 % of the wall's median neighbour count within 3 mm. It is skipped when there are too few neighbours to judge (median under 12, sparse scans).
   - Effect on the dnF shell at z155: caliper 88.4 -> 56.4 mm.
2. **Section bands ended at `min(heights)`.** A flipped scan that loses its free end lacks the reference's bottom, so its top band was never checked. Fix: bands now span both walls' real overlap.
3. **Free-space conflict counted each scan's own mat glare (own z below 6 mm).** That glare was 97 % of a false 0.054 conflict on dnF. Fix: points below `GLARE_HEIGHT_MM` are skipped.
4. **No local-feature check.** A one-scan lug filling under 10 % of every slice passed the worst-slice share.
   - Fix: `_miss_patch` measures the largest connected patch of wall without a counterpart within the fixed coverage distance, as true area (per-point area from local density).
   - A 10x20 mm lug reads 208-273 mm^2. It refuses above max(40 mm^2, 40 spacing^2).
5. **The merge kept mat glare blobs.** Fix: points outside the other scan's xy footprint are left out. One-scan surfaces inside the footprint (a neck-ring underside) stay.
6. **The yaw refusal was not actionable.** It now names the rival turns or the plateau, and asks for the label or an asymmetric feature in view in both scans.

Coverage tolerance (2 mm), the 0.9 gate, pose search and yaw logic are main's.

### Tried and withdrawn (reviews V01 and V02)

- **V01: blanket 20 % / 30 mm contact zones and a 0.85 gate.** These hid lugs, grooves and steps.
- **V02: tolerance widened by measured noise (5 x sigma), plus a quantile pose objective.** This hid lugs and 1.5 mm steps, a fuzz patch or double wall could raise the tolerance, and dense labelled ovals regressed.

### The real data disagree (evidence)

| region (ref z) | upF vs dnH | upF vs dnF | the same shape in a probe that must refuse |
|---|---|---|---|
| closure, 160-171 (flipped scans stand on it, own z 2-13) | section -1.4 mm radius (29.1 x 43.3 vs 31.8 x 44.4) | -1.5 mm | "top r-1.5 last 20" |
| shoulder, 146-157 (flipped: downward-facing, curtain) | coverage 0.59-0.63, a 380 mm^2 uncovered patch | 0.57, 385 mm^2 | one-scan lug / bump probes |
| shared walls, scale | +1.06 % (limit 1.04 %) | +0.4 % | scale-error probes |
| upright foot, 5-30 | coverage 0.82-0.89 | 0.81-0.87 | |

The other parts of the wall agree: slices 0.90-0.98, median radial offset under 0.6 mm.

The fixes the review proposed do not remove these differences:

| attempt | effect on the real pairs |
|---|---|
| Denoise by MLS / plane projection (3 and 5 mm) | worst slice 0.46-0.52, median 0.92-0.94; no gain over raw (0.51-0.57 / 0.93). The disagreement is regional (mm over cm), not point noise (local sigma 0.35 mm). OpenMVS's own meshes disagree at the shoulder as well (0.27-0.37). |
| Removing surfaces facing the mat (outward n_z < -0.26 or -0.5) | changed nothing. The curtain's points face sideways (median own n_z -0.08). |
| A strict "below the 10 deg camera ring" test (n_z < -0.98) | removes nothing on walls. Without camera poses, normal sign on horizontal faces is ambiguous, so this test is not shipped. |
| z shift, tilt, levelling | did not help (section 1) |

**Conclusion.** The flipped scans reconstruct the closure 1.4-1.5 mm smaller in radius and the shoulder with a curtain. Both sit at the flipped scan's mat contact or under its overhang, where only low cameras see them. These are real disagreements in the data, at the size the refusal guarantees must catch.

Any rule that accepts this pair would also accept the reviewer's "top r-1.5 mm" and small-lug probes. The combine therefore refuses, naming each reason, and does not merge.

The likely capture cause is that in the upside-down pose the closure stands on the mat under the shoulder overhang. Options:
- Rescan upside down with the part raised on a narrow stand (closure clear of the mat).
- Or use the Body + Closure scans with Place closure (PL-0484) instead of an Assembled pair.

These are recommendations, not verified.

## 3b. Pipeline or photos? Stage-by-stage trace (read-only)

### A. Closure smaller in the flipped scans

Caliper (min x max, mm, 2-98 % over 36 directions) at a distance d from the closure top, in each scan's own mat frame:

| stage | upF d4-d8 | dnH d4-d8 | dnF d4-d8 |
|---|---|---|---|
| OpenMVS fused `scene_dense.ply` (mat frame) | 30.3-31.5 x 42.0-43.6 | 28.6-29.2 x 40.0-40.8 | 24.5-25.1 x 38.7-39.6 |
| object cluster / minus glare halo | same | same | same |
| 1 mm voxel band / minus strays | 30.5-31.4 x 42.3-44.4 | 28.2-29.1 x 40.0-41.4 | 24.3-25.1 x 38.2-40.2 |
| shell | 30.6-31.5 x 42.1-44.7 | 28.5-29.1 x 40.2-40.6 | 20.6-24.4 x 37.0-38.3 |
| OpenMVS `scene_dense_mesh` | 29.8-30.6 x 41.8-42.2 | 28.5-28.6 x 37.1-38.8 | 22.8-24.4 x 37.2-38.3 |
| OpenMVS `scene_refined` | | 28.0-28.5 x 36.8-38.8 | |

What this shows:
- **Already in OpenMVS's output.** The shrink is in the raw fused cloud and in both OpenMVS meshes. No PackLab stage changes it by more than about 0.5 mm, and the meshes are smaller still, so using the mesh instead of the dense cloud does not help.
- **Uniform along the closure (d3-d14).** It is not a contact fillet or glare erosion near the mat.
- **Larger at the Fast densify resolution.** Shrink in min / max caliper: about 2 / 3 mm for dnH, about 6 / 4 mm for dnF. Note that upF is also Fast (750 px) and is not shrunk, so resolution alone does not explain it.
- **Depth-map resolution is a pipeline setting.** The dense depth maps are 1000x750 px (High: COLMAP undistort max 2000 px, `--resolution-level 1`) and 750x562 px (Fast: `--max-resolution 750`). The photos are 4032x3024 px.

The photo silhouette test was inconclusive. Projected closure widths against the dark silhouette width (mid-grey threshold) in each scan's own undistorted photos, 56-65 views each:

| photos | flipped recon / photo | upF recon / photo |
|---|---|---|
| dnH | 1.065 | 1.112 |
| dnF | 1.017 | 1.054 |
| upF | 1.254 (dnH recon) | 1.285 |

The threshold bias changes with the background (1.0-1.3), so the photos cannot tell which closure size is true. Two decisive checks remain, both owner actions:
- A caliper on the closure: about 30.5 x 43.5 mm (upright) vs 28.6 x 40.5 mm (dnH), a 2-3 mm difference.
- A High+ rebuild of a flipped scan at full depth-map resolution (`--resolution-level 0`, undistort max 4032). This writes new files to the owner workspace, so it was not run here.

### B. Shoulder curtain

The curtain is already in the raw fused cloud and in OpenMVS's meshes:

| source | width at d22 (mm) | upF at the same height (mm) |
|---|---|---|
| dnH raw | 63.5 | 39.5 |
| dnH mesh | 56.9 | |
| dnH refined mesh | 55.8 | |

The shoulder appears 4-6 mm closer to the closure than in upF. `_dense` trims only its sparse fringe (dnH d18 raw 51.5 -> 45.8).

Free-space test with the OpenMVS per-view depth maps, read in place (dnH 81 maps, dnF 78). A point counts as seen through when at least 2 views measured a surface more than 2 mm behind it along the same ray, and more views see through it than support it:

| points (own z 12-36) | dnH removed | dnF removed |
|---|---|---|
| more than 3 mm off the upright surface (the curtain) | 73 % | 81 % |
| within 1 mm of the upright surface (real) | 4 % | 9 % |

The real points lost are mostly at the neck, z 12-24: 7-30 % removed. So the curtain is MVS fill that the cameras saw through. A camera-pose free-space filter removes most of it, but it would need the Studio to pass each build's depth maps. It is not shipped: it does not touch the closure (A), which alone keeps the pair refused.

### C. Scale +1.06 % (upF vs dnH)

| | mm/unit | u (rel.) | marker views | height (mm) |
|---|---|---|---|---|
| upF | 128.371 | 0.78 % | 257 of 258 | 173.19 |
| dnH | 126.306 | 0.69 % | 262 of 264 | 173.25 |
| dnF | 126.045 | 0.70 % | 258 of 259 | |
| upH | 125.461 | 0.77 % | 255 of 256 | |

COLMAP intrinsics agree across builds: fx 3114.6-3115.6 px, 0.03 %.

The marker scales agree. Heights differ by only 0.03 %, while the "scale" reading is +1.06 %. That reading comes from wall offsets that change with height, not from scale.

Body-only band ratio (z 30-140): 1.004 for dnH, 0.992 for dnF. The radial offset (flipped minus upright) runs from about +0.5 mm near the upright's mat (z 10-50), through 0, to -0.5 mm near the flipped scan's mat (z 105-135). It then reaches -1.35 at the closure, after +2.6 at the shoulder curtain.

Both flipped builds show the same trend: each scan reconstructs walls near its own mat slightly smaller. That is consistent with the closure finding (A) and is present in the raw OpenMVS clouds.

### D. dnH densified at 2x resolution (private `.local-data`, inputs deleted afterwards)

Setup:
- DensifyPointCloud with the same OpenMVS v2.4.0 as Studio (OwnerDev engines), with no window.
- Input: dnH's `scene.mvs` and its undistorted 2000x1499 images, `--resolution-level 0`, 14 threads.
- Depth maps are now 2000x1499. The original was 1000x750 (`--resolution-level 1`, 8 threads).
- Time: 51 min 59 s here, against 54 min 13 s for the original High build.
- Output: 10.06 M points (original 2.44 M), spacing 0.61 mm (original 0.69).

Caliper (mm) by distance d from the closure top:

| | d4-d8 raw | d4-d8 shell | d22 raw (curtain) | d22 shell | d26 raw |
|---|---|---|---|---|---|
| dnH 1000 px | 28.6-29.2 x 40.0-40.8 | 28.5-29.1 x 40.2-40.6 | 30.2 x 63.5 | 30.4 x 62.5 | 31.3 x 66.4 |
| dnH 2000 px | 29.2-29.5 x 39.2-40.8 | 29.0-30.2 x 41.6-42.0 | 31.0 x 53.6 | 31.0 x 54.6 | 31.8 x 60.3 |
| upF (750 px) | 30.3-31.5 x 42.0-43.6 | 30.6-31.5 x 42.1-44.7 | 27.9 x 39.5 (neck) | | 30.5 x 45.5 |

Combining upF with each dnH:

| dnH | result | closure section | worst slice | patch | scale |
|---|---|---|---|---|---|
| 1000 px | REFUSED | -1.4 mm | 0.592 | 380 mm^2 | +1.06 % |
| 2000 px | REFUSED | -1.6 mm | 0.571 | 792 mm^2 | +1.06 % |

Doubling the depth-map resolution:
- narrows the curtain by about 10 mm (d22 63.5 -> 53.6);
- widens the closure by only 0.3-1.2 mm in places;
- leaves the pair disagreeing.

Level 0 is already the full resolution of the undistorted images. A 4032 px densify would need a new COLMAP undistortion, and was not run because 2000 px did not clearly help.

### E. Visibility confidence from the depth maps (read in place)

Per band, from 3000 sampled points:
- **Support views:** views whose depth agrees within 2 mm.
- **Incidence:** median angle between the surface normal and the ray of each supporting view.

Camera elevations above the mat: p10 22 deg, median 35-39 deg, p90 52-56 deg. No views are lower than about 20 deg.

| scan / band | support views p10/50/90 | median incidence | views < 60 deg (median) | share with >= 3 such views |
|---|---|---|---|---|
| upF closure | 13/24/31 | 41 deg | 20 | 1.00 |
| dnH closure | 12/27/36 | 51 deg | 18 | 0.99 |
| dnF closure | 11/52/70 | 49 deg | 39 | 0.99 |
| upF neck | 7/13/23 | 39 deg | 10 | 0.99 |
| dnH neck | 5/13/23 | 59 deg | 7 | 0.90 |
| dnF neck | 4/12/20 | 58 deg | 6 | 0.85 |
| upF shoulder | 14/25/32 | 40 deg | 20 | 1.00 |
| dnH shoulder | 14/29/35 | 56 deg | 17 | 0.99 |
| dnF shoulder | 13/26/32 | 55 deg | 16 | 0.98 |
| body (all three) | 16-18 / 28-30 / 33-35 | 49-52 deg | 20-21 | 0.99-1.00 |

The hypothesis is not supported for the closure. In both flipped scans it is seen by as many views as in the upright scan (median 27 and 52 against 24). Those views are somewhat more grazing (49-51 against 41 deg), but 99 % of points have 3 or more views under 60 deg.

Only the flipped neck is weaker: 6-7 good views, 85-90 % of points with 3 or more, incidence 58-59 deg.

The smaller flipped closure is therefore consistent across about 27 depth maps. It is not a few grazing views.

**Assessment.** A confidence-weighted comparison would have to exclude a well-observed surface to accept this pair. A threshold strict enough to drop the flipped closure, for example under 25 supporting views or incidence over 45 deg, would also drop ordinary body walls in other scans. That reopens the one-scan closure and step probes. So such a comparison does not accept the pair without reopening the reviewer's probes. Not recommended.

### Verdict

- **Not a PackLab stage.** No stage from the fused cloud to the shell creates the closure shrink, the curtain or the scale reading.
- **Reconstruction side, not proven from the photos.** All three are already in OpenMVS's dense output, from photos taken at 4032 px but densified at 750-1000 px.
- **The full-resolution rebuild (D) was run and did not remove A.** A 2x-resolution densify only narrowed the curtain.
- **Actionable:** caliper the closure. Which closure size is true is a physical question, owner gate.
- **Gates unchanged.** No gate was loosened and no code changed in this step.

## 3c. Owner-confirmed override (product decision, PR #47)

The automatic gate is unchanged. When `align_part_pair` refuses, it may offer an override.

**When the override is offered.** All three conditions must hold:
- Every failure is an agreement gate: coverage, uncovered patch, section, or scale. Scale must be within `OVERRIDE_MAX_SCALE` (2 %).
- The pose is determined:
  - RMSE is within its limit, and the wall profile pins the turn; or
  - the wall profile has rivals and the printed label picks one under `_colour_yaw`'s significance rules (6 sigma peak; margin max(0.1, 4 sigma)).
- With a label pick, or with the coverage plateau as the only yaw failure, the yaw plateau is re-measured on the mean slice coverage. Slices the scans disagree on at every yaw (curtain, shrunken closure) otherwise flatten the worst-slice plateau. The plateau must still be within `yaw_probe_deg`.

**When it is never offered:**
- yaw undetermined between turns;
- height mismatch / missing end;
- too little overlap;
- free-space conflict (wrong role);
- RMSE;
- scale over 2 %;
- unknown roles;
- no mat.

**What the caller gets.** `MultiScanAlignmentError.override_disagreements` holds the measured list: kind, heights in mm, offsets in mm, patch area in mm^2. `disagreement_text` puts each item in plain words.

**The merge (`align_part_pair(..., owner_confirmed=True)`):**
- Split band: the three 5 mm slices around the highest smoothed slice coverage, derived from the data.
- The upright scan supplies everything above the band and the upside-down scan everything below; both overlap inside the band.
- Points outside the other scan's footprint are dropped.
- Result fields: `verification = OWNER_CONFIRMED_UNVERIFIED`, `disagreements`, and a limitation naming the split. `metric_status` stays METRIC_UNVERIFIED.

**In Studio:**
- A refused record keeps `override`. The panel lists the disagreements and shows "Combine anyway - I confirm both scans are the same part". A confirmation dialog repeats the disagreements and explains the result.
- The stored record keeps `status: combined`, so existing staleness and geometry flows still work. It also stores `verification: OWNER_CONFIRMED_UNVERIFIED`, `disagreements`, `owner_confirmed_at` and `confirmation`.
- The tree shows "combined - owner-confirmed, UNVERIFIED".
- Measure & Design: the scale provenance uses evidence class `owner_confirmed_unverified_combine`, and the details are prefixed OWNER_CONFIRMED_UNVERIFIED. Isolate results show the badge.
- Scan Master promotion: the reconstruction manifest lists the OWNER_CONFIRMED_UNVERIFIED limitation.
- Placement: sources carry `verification`, and the placement panel names unverified parts.

### Real pair upF + dnH through the override path (read in place)

**Offered disagreements:**
- section at 166 mm: the upside-down wall lies 1.6 mm inside (29.1 x 43.2 vs 31.8 x 44.4 mm; tolerance 0.9);
- coverage under 2 mm at 6-36, 46-51 and 142-167 mm (worst 51 %);
- a 429 mm^2 uncovered patch at 110-167 mm.

**Pose:**
- The label picks the half turn at 7.1 sigma (needs 6), with margin 0.175 (needs 0.10).
- Yaw plateau on mean coverage: +-2.5 deg.
- RMSE 0.697 mm.

**Merge:**
- Upright above 71 mm, upside-down below 86 mm. The band agrees at 97 % within 2 mm.
- 40,321 points: 19,849 from upF and 20,472 from dnH.
- Heights 173.2 / 173.2 mm; top at z p99.9 174.1 mm.
- Surface coverage: side, top and bottom all 1.0.

Calipers of the merged part (mm):

| z | caliper |
|---|---|
| 10 | 34.0 x 52.5 |
| 40 | 34.6 x 57.5 |
| 80 | 33.6 x 64.2 |
| 120 | 34.8 x 63.6 |
| 145 | 32.4 x 62.0 |
| 150 | 28.4 x 42.2 |
| 155 (neck) | 27.9 x 39.1 (no curtain; was 55.6) |
| 160 | 29.7 x 42.7 |
| 165 (closure) | 31.8 x 42.9 |
| 169 | 30.7 x 44.3 |

The closure and shoulder come from upF.

upF + dnF is not offered: it has a height mismatch (missing end).

**Automatic behaviour is unchanged.** 902 probe verdicts were compared with V03 (old suites, V02 fresh probes, V01 gate/thin probes) and 0 changed. The role, placement and zone outputs are identical as well.

## 3d. Override V04: offered only for a plausibly-same part (review V03)

The bounds come from the gate's own distances and from physics, not from the probes.

**Never offered:**
- when any non-agreement gate fails: height / missing end, overlap, free-space conflict, RMSE, or yaw that neither the wall nor the label pins;
- when an end was completed: a missing end is never combined on confirmation.

**Offered only when all of these hold:**
- **Size:** scale within 2 %, and every measured section within `OVERRIDE_MAX_DEVIATION_MM` = 2 mm in radius (so at most 4 mm in diameter). This is a fixed physical bound: the real flipped closure reads 1.4-1.6 mm small. It is not the spacing-adapted coverage distance, which a sparse scan widens to 3 mm. That gap let a 3 mm panel through at d 0.2 before the fix.
- **Mid-body:** inside 30-70 % of the height, the mid-body is kept from both scans. No wall patch there may stand out from the other scan's wall by more than the coverage distance beyond the automatic patch limit (true area). A three-slice band with gate coverage must exist there.
- **Outside the band:** the scan kept there (upright above the band, upside-down below it) has no such standing-out patch. That would be a feature the merge keeps unconfirmed.

**Merge:**
- Blend band: the best-agreeing three slices inside 30-70 %.
- Beyond the band, a scan's points stay when only that scan saw them: no point of the other scan's same surface class within the coverage distance, and not outside its wall. Surface classes are near-horizontal and steep; near-horizontal points weigh height twice, so a thin ledge's two faces are not counterparts. An example is a ledge underside.
- In the review's ring probe, 5 of the 39 underside points are kept (V03: 0). The rest are within 2 mm of the upright ring faces or lose the voxel to an upright point.
- Its points with a counterpart there, or standing outside the other scan's wall (curtain), give way.
- The footprint rule is kept.

**Badge:**
- `ReconstructionOutputManifest.verification` is a structured field: GATE_PASSED or OWNER_CONFIRMED_UNVERIFIED. It goes into `as_dict` only when set, so existing digests are unchanged.
- The Scan Master promotion sets it and includes it in the configuration digest.
- The interior merge records the body's verification and shows the badge. Placement sources carry it (tested).
- The UI states why an override is not offered.

### V03 review probes (fresh, seeds 1 and 3, d 0.5/0.2, noise 0/0.35)

No wrong part is offered: 0 of 88 wrong-part probes, and 0 of 48 special probes (seeds 1 and 3). Each probe's reason:

| probe | reason |
|---|---|
| neck r30 vs r26 | yaw or section |
| neck r30 vs r33 | section 3.0 mm in radius |
| shoulder 65 vs 60 | yaw / coverage |
| neck to 80 vs 84 | height |
| 3 mm label panel | no agreeing mid-body band, or a 154 mm^2 mid-body patch |
| lug 10x12x3 | 105-157 mm^2 mid-body patch, or yaw |
| lug 20x20x5 | 630 mm^2 mid-body patch, or no band, or yaw |
| r41 / r42.5 whole | size +2.5 %, or yaw |
| flipped missing end 8 + lug | missing end |
| upright missing top | height |
| oval a29 b19 | RMSE |
| oval vs body | yaw |

Genuine pairs:
- "flipped top 1.5 mm in (real-like)" is offered at all four densities and noise levels.
- "Top 2.5 mm in" gets no offer (yaw), which review V03 accepts.
- The ring-underside pair gets no offer (yaw; main refuses its yaw too).

### Real upF + dnH under these bounds: NOT offered

Reason: "a 57 mm^2 wall patch in the mid-body stands out more than 2.0 mm between the scans". It lies at z 52-65 mm, just above the 30 % line (52 mm), next to the upright foot zone where the scans disagree.

The data put the real pair inside the range of the wrong-part probes:

| | mid-body patch standing out more than 2 mm |
|---|---|
| real upF + dnH | 57-63 mm^2 (label pose; 58 at the geometric pose; final code 63) |
| lug 10x12x3, noise 0.35, d 0.5 | 98 mm^2 |
| lug 10x12x3, noise 0.35, d 0.2 | 45 mm^2 |
| lug 10x12x3, clean | 144-157 mm^2 |

The ordering holds at excess thresholds of 2.0, 2.25, 2.5 and 3.0 mm (real 57/53/43/39). The mid-body slices themselves agree at 0.94-0.98.

So a size-based bound cannot both offer this pair and refuse a 10x12x3 mm lug. Offering it would need a bound fitted to this pair (for example mid-body 35-65 % or a patch limit of about 60 mm^2). That is an owner/product decision and is not taken here.

## 3e. Tiered offer (product decision: the owner is the authority on "same part")

The tool cannot separate the real pair from the 10x12x3 lug probes, so it grades the differences instead of fitting a bound to the pair.

**Hard blocks (no offer):**
- yaw undetermined;
- wrong or unknown roles;
- missing or completed end;
- height mismatch;
- overlap;
- free-space conflict;
- RMSE;
- scale over 2 %;
- a section radius difference over 4 mm (2 x `OVERRIDE_MAX_DEVIATION_MM`; a neck or closure family change);
- no blend band: three adjacent slices inside 30-70 % whose sections agree within 2 mm (patches do not block the band).

**Tier A, small differences:** every disagreement is within the V04 physics bounds. A normal confirmation is enough.

**Tier B, large local differences (possibly different parts):** any section offset of 2-4 mm, or any wall patch standing out more than 2 mm beyond the automatic patch limit, in the mid-body or in the scan the merge keeps outside the band. Each such patch is added as a `deep_patch` disagreement (height range in mm, mm^2, depth in mm).

**In Studio:**
- The tier B dialog shows a red warning and the "I have checked the physical part; these differences are scan errors" checkbox. The confirm button is enabled only once it is ticked.
- The record stores `verification` OWNER_CONFIRMED_UNVERIFIED, `verification_tier`, and the full disagreement list.
- The badge reads "combined - owner-confirmed (tier B), UNVERIFIED".
- The Scan Master limitation names the tier, and the tier is in the configuration digest.

### Real upF + dnH: tier B

The differences listed in the dialog:
- section at 166 mm: the upside-down wall lies 1.6 mm inside;
- walls differ by more than 2 mm at 6-36, 46-51 and 142-167 mm (worst 51 %);
- a 429 mm^2 uncovered patch at 110-167 mm;
- a 63 mm^2 area at 53-65 mm standing 3.6 mm proud (mid-body);
- a 150 mm^2 area at 6-24 mm standing 2.3 mm proud (kept by the merge from one scan).

**Merge after confirmation:**
- Upright above 71 mm, upside-down below 86 mm.
- 41,753 points (20,571 from upF, 21,182 from dnH).
- Heights 173.2 / 173.2 mm; top at z p99.9 174.1 mm.
- RMSE 0.697 mm; yaw +-2.5 deg (label half turn).

Calipers of the merged part (mm):

| z | caliper |
|---|---|
| 10 | 34.0 x 52.5 |
| 40 | 34.5 x 57.5 |
| 80 | 33.6 x 64.2 |
| 120 | 34.8 x 63.6 |
| 145 | 32.4 x 62.0 |
| 150 | 29.1 x 42.0 |
| 155 (neck) | 28.0 x 39.0 |
| 160 | 29.8 x 42.7 |
| 165 (closure) | 31.7 x 42.8 |
| 169 | 30.7 x 43.8 |

### V03 review probes under the tiers (seeds 1 and 3, d 0.5/0.2, noise 0/0.35)

| probe set | count | no offer | tier A | tier B | automatic accept (as main / V03) |
|---|---|---|---|---|---|
| wrong part | 88 | 55 | 0 | 18 | 15 |
| special | 48 | 32 | 0 | 0 | 16 |
| genuine | 48 | 31 | 9 | 0 | 8 |

- **Wrong-part tier B:**
  - 3 mm label panel: 6
  - lug 10x12x3: 5
  - lug 20x20x5: 5
  - neck r30 vs r33: 1 (section 3.0 mm)
  - shoulder 65 vs 60: 1
- **Wrong-part with no offer:**
  - neck r30 vs r26 (4 mm): yaw or section
  - neck to 84: height
  - r41 / r42.5: size or yaw
  - the rest: yaw
- **Special, all no offer:** missing end, height, RMSE, yaw.
- **Genuine tier A:** the real-like "top 1.5 mm in" pairs.

## 4. Results V03 (final code)

| pair | result | reasons (all printed in the refusal) |
|---|---|---|
| upF + dnH | REFUSED | closure section -1.4 mm; scale +1.06 %; coverage 0.592 (shoulder); 380 mm^2 patch; yaw: the 180 deg turn fits as well and the label did not decide |
| upF + dnF | REFUSED | missing end with a closure section -1.5 mm; coverage 0.566; 385 mm^2 patch; yaw plateau +-6 deg |
| upH + dnH | REFUSED | upright lost its top 20 mm (design); shoulder section +1.9 mm; scale +1.29 %; 173 mm^2 patch |
| upH + dnF | REFUSED | design (upright top lost); coverage 0.745; 423 mm^2 patch |

All values remain METRIC_UNVERIFIED (no caliper evidence).

## 5. Refusal guarantees

Each suite was run against this worktree with the imports asserted. Wrong accepts, main -> V03:

| probe set | main | V03 |
|---|---|---|
| V02 fresh, ctrl (genuine pairs) | 1 | 0 |
| V02 fresh, inflate n0 | 1 | 0 |
| V02 fresh, inflate n0.35 | 1/12 (from review V02) | 1 |
| V02 fresh, lug n0 | 8 | 2 |
| V02 fresh, lug n0.35 | 13 | 7 |
| V02 fresh, lug n0.35 d0.2 | 16 | 15 |
| V02 fresh, shape n0 | 0 | 0 |
| V02 fresh, shape n0.35 | 2 | 1 |
| V02 fresh, shape n0.35 d0.2 | 2 | 1 |
| V02 fresh, split | 1 | 1 |
| V01 zone | 0 (128/128 refused) | 0 (128/128 refused) |
| V01 gate | 3 | 0 |
| V01 thin | 24 | 12 |
| V01 place | 3 | 3 |

- No probe flips from main's refusal to a wrong accept.
- Old suites (cpr-me, rv-missingend, rv-combine adv2): identical to main on every file except blob. Blob has +3 accepts, all with correct poses, and no wrong accepts. The labelled ovals (cpr colour, rvc adv2) are back to main's results.
- Genuine-pair refusals are no worse than main: the sweep is identical to main, the V01 zone genuine pairs accept 20/20, and the thin genuine pairs refuse 4 (main 5).
- Tests: the three core files give 132 passed. They include tests for:
  - fuzz inflation (a fuzzy upright patch must not hide a 10x20x4 mm lug; main accepts it)
  - true area (a one-scan 10x20 lug reads 150-380 mm^2)
  - a bump on a mat-facing slope
  - lugs, grooves and steps near either end
  - a one-scan boss
  - the merge footprint (a one-scan underside is kept, glare is dropped)
  - the sparse-fan shell
  - a flipped short scan of a different top

## 6. Residual risks

- The 40 mm^2 / 40 spacing^2 patch limit comes from synthetic genuine pairs (<= 14 dense, <= 53 at d 0.2) and probe lugs. Small lugs (25-36 mm^2) and noisy sparse scans still pass, as on main.
- The real pair stays refused until the flipped capture is fixed or the owner accepts a merge whose ends come from one scan without verification. That would be an owner decision, not a code default.
- Physical accuracy is unverified until there is caliper evidence.
