# CLAUDE_PEER_REVIEW - PL-0483 multi-scan alignment (PR #28) - V02 re-review

- Reviewer: independent Claude peer reviewer (not the author; not CHATGPT_AUDIT / CODEX_PEER_REVIEW).
- Range: 35a72737 (V01) .. 9db5f4c9 (feat/multiscan-alignment), read-only worktree PackLab-wt-multiscan.
- Diff: multiscan_alignment.py (+~530 net), test_multiscan_alignment.py (+~90 net).
- Reviewer ran: `pytest tests/core/test_multiscan_alignment.py` with PYTHONPATH=worktree core/src -> 19 passed (37.5 s).
  Reviewer probes (scratchpad only, nothing committed) use the PR's own synthetic generator plus one read-only real cloud.

## Verdict: CHANGES_REQUIRED

All V01 wrong-accept findings are fixed on synthetic data (fails safe). New HIGH: the pipeline refuses correct
pairs as soon as point density drops, and it refuses a rigidly moved identical copy of the owner's real cloud.
As it stands it cannot align a real scan.

## V01 adversarial probes, re-run on 9db5f4c9

| Case | V01 | V02 |
|---|---|---|
| body pair / closure pair | ACCEPT (closure fit 0.31) | ACCEPT cov 0.99, err 0.1-0.2 deg / 0.02 mm |
| wrong role, body | ACCEPT 0.98 | REFUSE (diameter profile) |
| wrong role, closure | - | REFUSE (free-space conflict 0.435) |
| role unknown, body / closure | - | ACCEPT, correct flip, 0.1-0.2 deg |
| scale +2 % / +5 % | ACCEPT (5 %: 180 deg yaw error) | REFUSE (height + diameter mismatch) |
| cyl r40 vs r43 / r41.5 | ACCEPT | REFUSE (diameter) |
| cyl h80 vs h70 | ACCEPT | REFUSE (height, free space) |
| body vs plain cylinder | ACCEPT | REFUSE (diameter, coverage) |
| ref + 200 floaters | ACCEPT 88 deg / 58 mm | ACCEPT, 0.1 deg / 0.01 mm (DBSCAN removes them) |
| ref + connected 15 mm spike | - | REFUSE (height 94.4 vs 80); fails safe |
| plain cylinder (symmetric) | - | ACCEPT, yaw_determined=False (yaw arbitrary, flagged) |
| to_mat_mm tilted 1.5 / 3 deg | (refused in V01 real test) | ACCEPT 0.1 deg; `_refine_mat` re-levels from the mat points |

H1 (fitness bias / role), H2 (different objects / scale), H3 (floaters) and V01 M1/M2/L1-L5 are resolved on
synthetic data. For H4, the mat refit now absorbs a tilted to_mat_mm. The bounded 5-DoF ICP tilt is not separately
exercised: my probe was re-levelled before ICP ran.

## HIGH

H5. multiscan_alignment.py:268-278 and :287-308: DBSCAN (eps 3 mm on 1 mm voxels, min_points 5) and the
72-sector x 5 mm shell percentile cells assume the test's density of 0.5 pts/mm^2. With the PR's own generator
and test DENSITY set to 0.2, correct body and closure pairs are REFUSED: the body shows a "diameter mismatch" of
35.8 vs 76.6 mm because the object fragments, and the closure has coverage 0.40. At 0.1 and 0.05 the result is
"too little side wall". Real MVS clouds are sparse and uneven.

H6. Real cloud (owner scene_dense.ply, 48,628 pts, read-only, scale ASSUMED 300 mm/diag): every case REFUSED,
including a rigidly moved identical copy and 95 / 85 / 70 % subsamples. Example: "diameter mismatch at z=46 mm: 51.1 vs
54.0; too little overlapping side wall (1 of 6 bands); coverage 0.514". `_prepare` gives the same mat normal
and the same 4,843-point cluster for both copies, but the shell has 437 vs 251 points. The shell is not invariant
to the input frame: the x-axis helper changes the sector/voxel grid. Out of 36,372 points above the mat, only
4,843 are kept, which suggests the object is fragmented.
Fix: density-adaptive eps and cells (from median NN spacing), a frame-invariant shell, and tests at about 0.05-0.2
pts/mm^2 plus a rigid-copy self-alignment test.

## MEDIUM

M5. Thresholds (1.5 % / 1 mm dimension, 0.9 coverage, 0.05 free space) are calibrated only on synthetic
0.15 mm noise. The free-space check assumes downward cameras, as the implementer disclosed.
M6. The height of the flipped part still comes only from the reference `_top` plus mat contact. A connected
spike fails safe through the height gate, but a genuine 1-2 mm mat-contact offset (e.g. a domed bottom) is not observable.

## LOW

L6. `surface_coverage` is heuristic, and the docstring correctly says "not hole-checked". The "closed part"
completion claim of PL-0483 still needs PL-0484 mesh hole checks.

## Not verified
CI not run by reviewer. No real upright+flipped pair exists. Real-data result uses an assumed scale.
Physical accuracy stays METRIC_UNVERIFIED.
