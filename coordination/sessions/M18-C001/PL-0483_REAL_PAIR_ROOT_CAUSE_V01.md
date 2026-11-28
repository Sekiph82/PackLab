# PL-0483: root cause of the refused real Assembled pair (V01)

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

## 3. Why coverage failed: artifacts plus contact zones, not a frame error

- **Local point noise is small.** The residual to a local plane has a robust sigma of 0.30-0.35 mm per scan (synthetic tests: 0.10-0.13 mm). Smoothing the points with an MLS projection did not raise coverage.
- **Defect 1 (`_shell`).** `_shell` keeps the outermost point of each patch of the unrolled wall. Sparse MVS strays outside the wall were therefore taken as the wall: glare fans beside the upright foot, spikes at the oval's tips, and a curtain under the flipped scan's downward-facing shoulder (70 mm wide at the shoulder against a 63 mm body). The real wall under them was dropped. Every check (ICP, coverage, sections, scale, yaw) then compared artifacts.
- **Defect 2 (gate statistic vs real MVS walls).** The fixed 2 mm / worst-slice-0.9 coverage was set on synthetic walls (local noise sigma 0.09-0.13 mm). The owner's real walls have sigma ~0.35 mm, and 0.8-1.0 mm at the oval tips and under the flipped shoulder. The two real builds disagree there by 2.4-3.3 mm. Misses sit where the surface is noisy: combined sigma at misses 0.83-1.0 mm, against 0.63 mm at hits. Two upright builds (no flip) scored worst slice 0.83 on main.
- **Defect 3 (pose search on the worst slice).** A few badly seen slices (flipped shoulder curtain, 0.5-0.6 at any yaw) flattened the yaw / contact optimum: yaw plateau 9 deg, "walls fit 3 mm off the contact". When this happened the label texture was never consulted, because the half-turn twin lost 0.06 coverage while still fitting the wall profile.
- **Defect 4 (pre-existing).** Section bands ended at `min(heights)`. A flipped scan that loses its free end lacks the reference's bottom, not its top, so the top band was never checked. A reviewer probe found this: bottle vs plain body, flipped, cut 8 mm.
- **Defect 5.** Free-space conflict counted each scan's own mat glare (own z below 6 mm). That glare made up 97 % of a false 0.054 conflict on dnF.

V01 tried blanket contact zones (lowest 20 % / 30 mm) and a 0.85 gate. Review V01 rejected this: zone features (lugs, grooves, steps, flared foot) went unchecked, and a one-scan 20x25x4 mm boss reached 0.88-0.90 coverage, the same as the real pairs. Both were removed in V02.

## 4. Fix V02 (`core/src/packlab_core/multiscan_alignment.py`)

- `_dense` (shared `_shell`): before the outer-wall selection, drop points that have fewer than 25 % of the wall's median neighbour count within max(2.5 mm, 3 spacings).
- `_surface_noise`: for each shell point, the rms residual to the local plane (radius max(3 mm, 2.5 spacings)), then the median over its 64 nearest points. Feature edges are thin lines and do not raise it; noisy patches do. Synthetic proxies: 0.09-0.13 mm. Real scans: 0.32-0.35 mm.
- Acceptance coverage (gate only): a point counts as covered within max(2 mm, 5 x (own + other's noise)).
  - Clean walls therefore keep exactly main's 2 mm and main's 0.9 gate.
  - The real pairs get 3.4-3.5 mm, and this is recorded in `limitations` as "smaller one-scan features are not detected".
  - Sections add 1 x the band's noise (synthetic +0.2-0.3 mm, real +0.7 mm).
- `_miss_patch` (new gate, the discriminator review V01 asked for):
  - A miss is a point whose other-scan neighbour is within 3x the distance but beyond the noise-aware tolerance. If the largest connected patch of misses exceeds max(30 mm^2, 8 spacing^2), the pair is refused.
  - Misses do not count where either surface faces the mat (outward normal z < -0.3) in the capture of the scan that supplied the point, because that scan saw the surface from below at grazing angles. This covers the real shoulder curtain. A lug's outer face is vertical, so it still counts.
  - Measured patch sizes:

| case | largest patch (mm^2) |
|---|---|
| synthetic genuine, d >= 0.2 | <= 11 |
| synthetic genuine, d 0.1 | <= 20 |
| owner real pairs | 15-27 (accepted pairs 18 / 20) |
| 4 mm base or top lug, d 0.5 | 90-117 |
| 4 mm base or top lug, d 0.2 | 31-70 |

- Pose search ranks poses by the 20th-percentile slice. The gate still uses the worst slice.
- Label twins also include the turns the wall profile cannot separate (`_yaw_rivals`, the same test as `_yaw_unique`).
- Section bands span the real overlap. Free-space conflict skips own glare under `GLARE_HEIGHT_MM`.
- Merge: every surface stays except points outside the other scan's xy footprint (3 mm cells, grown by one cell), which that scan saw as empty mat. One-scan surfaces such as a neck-ring underside are kept (72/96 and 78/124 flipped points).

## 5. Results V02 (worktree code, studio-equivalent inputs, gate 0.9)

| pair | result | coverage | RMSE | heights | yaw | patch | notes |
|---|---|---|---|---|---|---|---|
| upF + dnH | COMBINED | 0.934 | 0.697 mm | 173.2 / 173.2 | determined (+-4.5 deg) | 18 mm^2 | free space 0.001 |
| upF + dnF | COMBINED | 0.939 | 0.644 mm | 173.2 / 165.3 | determined (+-3 deg) | 20 mm^2 | end completed from upF (8 mm) |
| upH + dnH | REFUSED | | | | | | by design (PR #45): the upright scan lost its top 20 mm and no other scan can show the part is not taller. Also scale +1.29 % and shoulder section +1.9 mm |
| upH + dnF | REFUSED | | | | | 94 mm^2 | same design refusal, plus the 94 mm^2 patch |
| upF + upH (control) | REFUSED | worst 0.901 | | | | | design refusal only |

Merged upF + dnH: 57,691 points, top at z p99.9 173.8 mm. Calipers (min x max, mm) by height:

| z | caliper (mm) |
|---|---|
| 10 | 34.0 x 56.4 |
| 40 | 34.7 x 60.8 |
| 80 | 33.5 x 63.5 |
| 120 | 34.7 x 66.8 |
| 145 | 32.7 x 67.2 |
| 155 | 30.7 x 55.6 |
| 165 | 31.6 x 44.5 |

The shoulder curtain at z 155 now stays in the merge: it lies inside the upright scan's footprint. Measure & Design's robust wall percentiles carry it, as they do on main.

All values remain METRIC_UNVERIFIED (no caliper evidence).

## 6. Refusal guarantees

Each suite was run against this worktree with the imports asserted. WRONG counts (wrong accepts):

| probe set | main | V01 head | V02 |
|---|---|---|---|
| review probes, contact zones (128 wrong parts) | 0 wrong | 48 wrong | 0 wrong (128/128 refused) |
| review probes, extra boss (gate) | 3 | 6 | 0 |
| review probes, thin features | 24 | 25 | 16 |
| review probes, placement | 3 | 3 | 3 |

- Neck-ring underside in the merge (review probe): 72/96 and 78/124 flipped points kept. V01 kept 0.
- Old suites (cpr-me v4, rv-missingend, rv-combine adv2; about 650 cases): no new wrong accepts. The cpr v01 and missing suites still show only the known role-override false flags, with correct poses: 7 and 2, against 8 and 2 on main.
- Availability: 18 genuine pairs that main accepts are now refused, every one with "yaw undetermined" (fail-safe). They are mostly sparse or tall synthetic pairs whose yaw plateau widened under the quantile pose objective; 4 of them are the review's tall genuine pairs at d0.2. The other direction is +1.
- Tests: `test_multiscan_alignment.py`, `test_part_placement.py` and `test_interior_merge.py` give 130 passed. They include new tests for:
  - lugs near either end
  - a groove near the end
  - a 2 mm top step
  - a one-scan boss
  - a one-scan underside kept in the merge
  - a noisy wall patch still combining
  - the sparse-fan shell
  - a flipped short scan of a different top

## 7. Residual risks

- On the real scans, a one-scan feature under about 3.5 mm in relief and under about 30 mm^2 is not detected. This is stated in `limitations` for every such combine; the scans' measured noise allows no better.
- A difference confined to surfaces facing the mat in one scan's capture (a flipped shoulder) only counts through coverage and sections, not the patch gate.
- Real-data calibration comes from one physical bottle: 5 pairs, 2 accepted. Before tightening the 30 mm^2 patch / 5x noise rule, check them on more real parts.
- The merge keeps the flipped shoulder curtain.
- Physical accuracy is unverified until there is caliper evidence.
