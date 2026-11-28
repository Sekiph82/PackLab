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
