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
- **Defect 2 (contact zones).** The parts of each scan nearest its own mat are seen only by the lowest cameras, at grazing angles and next to mat glare. These are the upright foot, and the flipped scan's shoulder and closure. The two scans disagree there by 1-4 mm, measured as per-cell median radius p90 on both the dense clouds and the OpenMVS meshes. The other scan sees the same surfaces from above, as its free end.
- **Gate calibration.** The 0.9 worst-slice gate was set on synthetic walls with 0.15 mm noise. The best real control is two independent upright builds, with no flip. It scored worst 0.83 on main.
- **Defect 3 (pre-existing).** Section bands ended at `min(heights)`. A flipped scan that loses its free end lacks the reference's bottom, not its top. The top band was therefore never checked, and only coverage had been catching such cases. This was found by rerunning the reviewer probe "bottle vs plain body flipped cut8" with the new gate.
- **Defect 4.** Free-space conflict counted each scan's own mat glare (own z below 6 mm). That glare made up 97 % of a false 0.054 conflict on dnF.

## 4. Fix (`core/src/packlab_core/multiscan_alignment.py`)

- `_dense`: before the outer-wall selection, drop points that have fewer than 25 % of the wall's median neighbour count within max(2.5 mm, 3 spacings). This is in the shared `_shell`, so placement and interior merge get it too.
- `_contact_zone`: the lowest 20 % of each scan's own height, at most 30 mm. It is left out of the ICP, coverage, scale and yaw shell. Sections still check it (`_Part.wall`) at a 2.0 mm radial tolerance. In the merge, each scan's zone is replaced wherever another scan's compared wall covers that height.
- Section bands now span the real z-overlap of both walls.
- Free-space conflict skips points below `GLARE_HEIGHT_MM`.
- `min_slice_coverage` changed from 0.9 to 0.85. After the fix, five real same-object pairs give worst slices of 0.873-0.953.
- The method string is now `_v3`.

The 30 mm cap was chosen from where the real disagreement ends (own z 0-28). A cap of 0.2 h without the 30 mm limit gave 0.891 / 0.900. This choice is a ponytail heuristic: a per-point visibility test using the build's camera poses would replace it.

## 5. Results (unpatched worktree code, studio-equivalent inputs)

| pair | result | coverage | RMSE | heights | notes |
|---|---|---|---|---|---|
| upF + dnH | COMBINED | 0.895 | 0.615 mm | 173.2 / 173.2 | yaw determined (plateau 3 deg), free space 0.001 |
| upF + dnF | COMBINED | 0.899 | 0.618 mm | 173.2 / 165.3 | end completed from upF (8 mm), scale 0.997 |
| upF + upH (control) | worst 0.953 | | | | refused by design: an upright scan cannot have a missing end |
| upH + dnH | worst 0.912 | | | | refused by design: upH lost its top |

Merged part (upF + dnH): 50,664 points, top at z p99.9 173.9 mm. Section calipers (min x max, mm) by height:

| z | caliper (mm) |
|---|---|
| 10 | 34.1 x 52.6 |
| 40 | 34.6 x 61.0 |
| 80 | 33.6 x 63.2 |
| 120 | 34.7 x 67.0 |
| 145 | 32.6 x 61.8 (no 70 mm curtain) |
| 155 | 27.9 x 39.3 |
| 165 | 31.8 x 42.9 |

Surface coverage is 1.0 for side, top and bottom. All values remain METRIC_UNVERIFIED (no caliper evidence).

## 6. Refusal guarantees

- The reviewer suites (cpr-me v3, rv-missingend: 14 scripts, about 650 cases) were rerun against this worktree, with the imports asserted. They produced 0 new wrong accepts.
- The only WRONG flags are the 9 known false flags from `align_part_pair` overriding the role; those poses are correct (0.0-0.3 deg). Main shows the same set.
- An intermediate wrong accept was fixed by the band-overlap change and now has a regression test.
- Genuine-pair availability against main moved in both directions. There are 7 new refusals, all fail-safe and mostly "yaw undetermined", because the zoned shell is shorter: 4 sparse (d0.1) bodies, 1 labelled oval at the default 5 deg, and 2 blob/missing-end bottles at d0.2. There are 8 new accepts: 2 spout pairs, and 6 blob/sweep pairs. The sweep also flips some closures at d0.1 and d0.2 in both directions.
- Tests: `tests/core/test_multiscan_alignment.py`, `test_part_placement.py` and `test_interior_merge.py` all pass. Three new tests were added. Two of them fail on main: sparse-fan shell, and lumps in the flipped contact zone.

## 7. Residual risks

- A different part that differs only within a contact zone, by less than 2 mm in radius and with no section band landing there, is not refused.
- The 0.85 gate and the 30 mm / 20 % zone are calibrated on one physical bottle (5 pairs). They need more real parts.
- The real coverage margin is small: 0.895 and 0.899 against 0.85.
- Physical accuracy is unverified until there is caliper evidence.
