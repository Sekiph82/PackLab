# CLAUDE_PEER_REVIEW - PL-0483 multi-scan alignment (PR #28)

- Reviewer: independent Claude peer reviewer (did not author the code). Not a CHATGPT_AUDIT / CODEX_PEER_REVIEW.
- Base/head: origin/main 29027c21 .. feat/multiscan-alignment 35a72737 (read-only worktree PackLab-wt-multiscan).
- Diff: core/src/packlab_core/multiscan_alignment.py (+303), tests/core/test_multiscan_alignment.py (+182).
- Tests run by reviewer: `pytest tests/core/test_multiscan_alignment.py` with PYTHONPATH=worktree core/src -> 6 passed (7.6 s).
- Reviewer probes (scratchpad scripts, not committed) reuse the PR's synthetic generator plus one read-only real cloud.

## Verdict: CHANGES_REQUIRED

Code is clean, deterministic, proper-rotation only (no mirror solution possible), labelled METRIC_UNVERIFIED,
uses open3d==0.20.0 which is already pinned in pyproject.toml (no new dependency). The flip/height model is
algebraically correct for clean data. But the acceptance metrics accept wrong alignments and wrong objects,
which is the core requirement of PL-0483 ("refuse poor alignments with a clear reason").

## Reviewer probe results (synthetic proxies from the PR's own generator)

| Case | Result |
|---|---|
| body pair baseline | ACCEPT fit 0.79 rmse 0.22, pose error 0.0 deg / 0.0 mm |
| closure pair baseline | ACCEPT fit 0.31 (threshold 0.2) |
| flipped scan, mm_per_unit +2 % | ACCEPT rmse 0.78, 1.6 mm shift |
| flipped scan, mm_per_unit +5 % | ACCEPT fit 0.38 rmse 0.79, **180 deg yaw error, 4.7 mm** |
| flipped scan, +10 % | REFUSE (fitness) |
| flipped scan passed with role flipped=False | **ACCEPT fit 0.98** (higher than the correct pose's 0.79) |
| cylinder r40 vs r43 (different object) | **ACCEPT** fit 0.31 rmse 0.78 |
| cylinder h80 vs h70 (different object) | **ACCEPT** fit 0.78 rmse 0.27 (merged part has a bottom floating at z=10) |
| body-with-boss vs plain cylinder | **ACCEPT** fit 0.79 |
| reference + 200 floaters above top | **ACCEPT** fit 0.25, **88 deg / 58 mm error** |

Real-data sanity (owner's scene_dense.ply, 48,628 pts, read-only, nothing copied; scale ASSUMED 300 mm diag):
self vs rigidly moved copy ACCEPT (0.01 deg); self vs random 95 % / 70 % subsample ACCEPT; self vs random 85 %
subsample REFUSE (fitness 0.194) because the RANSAC mat normal moved 1.5 deg and tilt is never refined;
self vs 70 % spatial crop REFUSE (fitness 0.03). The same physical surface is refused from sampling noise alone.

## HIGH

H1. multiscan_alignment.py:224 / :220 - fitness is both the flip/yaw hypothesis selector and the acceptance
metric, and it is structurally biased against correct upright+flipped merges: the correct pose adds the new
bottom surface (non-overlapping by design), a wrong pose stacks surfaces. Proven: wrong role gives 0.98 vs
correct 0.79, so `flipped=None` (both poses tried, :254) will choose the wrong flip on typical jars. Selection
should not rely on raw inlier share; role must be mandatory for pairs, or use a criterion that penalises
interpenetration / free-space violation.

H2. :258-266 thresholds (min_fitness 0.2, min_overlap 0.2, rmse 1.5 mm) do not discriminate different objects
or scale errors: 3 mm radius / 10 mm height differences and a 5 % scale error (with a 180 deg yaw flip) are
accepted. Thresholds appear set just below the closure case (0.31) rather than derived from a failure model.
Need checks such as bounding-dimension agreement (diameter/height of the shared side wall), scale consistency
between scans, and a degeneracy (yaw observability) report.

H3. :187-194 height is fixed from `top()` = median within 1 mm of the 99.9th percentile of the reference;
height is not an ICP DOF. 200 floaters (typical MVS noise) -> 88 deg / 58 mm wrong alignment accepted. Use a
robust top (e.g. largest horizontal planar cluster / percentile after outlier removal) and/or refine z.

H4. :176-178 tilt only from the mat-plane fit; real cloud test shows a 1.5 deg normal drift from subsampling
causes refusal of identical geometry. On real data this produces either false refusals or, combined with H1-H3,
wrong accepts. Add tilt DOFs (full 6-DOF point-to-plane after the constrained init) before relying on it.

## MEDIUM

M1. Rotationally symmetric parts (most jars/lids): yaw is unobservable; result still reports a yaw and merged
colours/labels can be seamed arbitrarily. No warning or degeneracy flag (e.g. Hessian eigenvalue of the yaw
column) - needed for PL-0487 label alignment.
M2. Tests (test_multiscan_alignment.py) never exercise: scale mismatch, wrong role, floaters/outliers, tilted
mat pose, symmetric parts, `to_mat_mm` path, different-but-similar objects. The different-object test passes
only because body vs closure differ grossly (overlap 0.13). Tests would catch a 180 deg yaw error only on the
boss-bearing synthetic body; a mirrored solution is impossible by construction (good); scale errors are not tested.
M3. Closed-surface claim ("hole-free outside", TASKS PL-0483) is not verified: no coverage/hole check of the
merged cloud; the test only counts points near top and bottom.
M4. `_mat_frame` (:86-95) is O(1000*N) Python loop; fine at 50k points, slow on multi-million dense clouds -
downsample before RANSAC.

## LOW

L1. `to_mat_mm` (:127-128) not validated (finite, rigid-with-scale, 4x4). L2. `colors` shape not validated
(:284 IndexError instead of MultiScanAlignmentError). L3. Traceability: `source_index` maps to scan, but the
original per-scan point index is dropped; keep it for audit. L4. `ScanAlignment.flipped` is relative to the
reference, not the scan role - document. L5. Module docstring says tilt/height from mat; fine, but the
limitation should also be in the result (e.g. `dof="yaw_xy"`).

## Not verified
No real upright+flipped scan pair exists; real-data check used an assumed scale and self-copies only.
CI not run by reviewer. Physical accuracy remains METRIC_UNVERIFIED.
