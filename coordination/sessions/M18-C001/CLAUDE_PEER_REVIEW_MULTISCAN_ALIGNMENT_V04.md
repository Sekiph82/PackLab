# CLAUDE_PEER_REVIEW - PL-0483 multi-scan alignment (PR #28) - V04 re-review

- Reviewer: independent Claude peer reviewer (not the author; not CHATGPT_AUDIT / CODEX_PEER_REVIEW).
- Range: f2bc4a00 (V03) .. 2dda9d1e, read-only worktree PackLab-wt-multiscan.
- Reviewer ran `pytest tests/core/test_multiscan_alignment.py` with PYTHONPATH=worktree core/src: 42 passed (69 s).
- Reviewer probes are in scratchpad/rv4 (not committed). They use the PR generator and the owner's read-only
  scene_dense.ply. Nothing was copied into Git.

## Verdict: PASS (alignment code, synthetic scope); real upright+flipped pair NOT_VERIFIED

I found no wrong acceptance anywhere. The remaining issues all fail safe, by refusing.

## Evidence (reviewer's own runs)

**H7 sweep:** 96 pairs, density 0.5 / 0.2 / 0.1 / 0.05 x {boss body, closure, round body} x 8 new seeds.
- An accepted pair counts as wrong if any of these holds:
  - yaw_determined is True and the yaw error is 5 deg or more;
  - yaw_determined is False on a part that is not round;
  - tilt is 1.5 deg or more;
  - shift is 1 mm or more.
- Result: **0 wrong accepts**.
- Acceptance counts for boss body / closure: 8/8 at 0.5, 8/7 at 0.2, 3/5 at 0.1 and 0/0 at 0.05, with the rest
  refused. The round body was 8/8 at every density, with yaw flagged.
- At 0.05 pts/mm^2 the code refuses rather than guessing, which is strict but safe as allowed.

**V01-V03 probes:** these were all refused:
- wrong role (body and closure);
- radius +3 / +1.5 mm;
- height -10 mm;
- boss body vs round body;
- scale +2 / +3 / +5 %;
- connected spike.

The density checks among them ran at 0.2, 0.1 and 0.05. Floaters are removed, and a tilted mat pose is re-levelled.

**H8, real cloud** (scale 8.87 mm/unit as stated by the implementer; I did not check this scale independently):
- The object now stands on the mat: z 1.5-35.1 mm, height 34.7 mm, 5.3k points, not round.
- Rigid copy with nine random motions: 6 ACCEPT with yaw determined (point error median 0.08-0.18 mm, p95
  0.14-0.31 mm), and 3 REFUSE ("object not found on the mat" / "too little side wall").
- 85 % subsample refused (yaw undetermined). 70 % subsample refused (dimension mismatch). 2 % / 5 % scale refused.

## MEDIUM

- **M7.** Preparing the object depends on the input frame (`_voxel_first` / DBSCAN representatives on the mat-frame grid, and
  the frame's x axis taken from a helper vector). 3 of 9 rigid copies of the same real cloud were refused, and the shell is only about 220
  points against a 30-point floor. This is safe but brittle. Expect refusals on real pairs until density improves
  (80-photo capture).
- **M8.** The wrong-role body is now refused only narrowly: coverage 0.891 against 0.9, plus the yaw gate. In V02 it was a
  diameter mismatch. The `_slices` "seen" filter (only points with three neighbours from the other scan within 3 x max_distance count) makes coverage
  partly self-selecting. The dimension, free-space and yaw gates carry the safety.
- **M9 (carried).** Thresholds are calibrated on synthetic data only. Height comes from mat contact only. I could not
  confirm that the real "mat" (110x102 mm plane extent at 8.87) is the A4 mat, so the true scale is unverified.
  `surface_coverage` is a heuristic: the "closed / hole-free" wording in PL-0483 is not proven and should be stated as a
  limit, or moved to PL-0484/PL-0486.

## Not verified
- CI.
- Any real upright+flipped pair (none exists; PL-0486).
- Physical accuracy (METRIC_UNVERIFIED).
- A visual check that the real object cluster is the jar.
