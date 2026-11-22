# CLAUDE_PEER_REVIEW - PL-0483 multi-scan alignment (PR #28) - V03 re-review

- Reviewer: independent Claude peer reviewer (not the author; not CHATGPT_AUDIT / CODEX_PEER_REVIEW).
- Range: 9db5f4c9 (V02) .. f2bc4a00, read-only worktree PackLab-wt-multiscan.
- Reviewer ran: `pytest tests/core/test_multiscan_alignment.py` with PYTHONPATH=worktree core/src -> 28 passed (46 s).
- Probes: reviewer scripts in scratchpad/rv3 (not committed); they use the PR generator (`scan(..., density=)`) and the
  owner's read-only scene_dense.ply. The scale is ASSUMED to be 300 mm per scene diagonal. Note: the scratchpad is shared with
  the implementer (my V02 real3.py was overwritten), so V03 results come only from the rv3/ scripts.

## Verdict: CHANGES_REQUIRED

V02 H5/H6 are fixed as stated: pairs align at 0.5-0.05 pts/mm^2, the side wall is frame-invariant, and a moved
copy of the real cloud aligns. All V01 wrong-accept probes are still refused at 0.5, 0.1 and 0.05: wrong role,
r+3, h-10, no-boss body, scale +2/+3/+5 %, connected spike. Floaters are removed. Two blocking issues remain.

## HIGH

H7. A wrong yaw on a non-symmetric part is accepted. In a body/closure density sweep over seeds (1,2), (3,4), (5,6):
- At <= 0.2 pts/mm^2, every accepted pair has `yaw_determined=False`, including pairs whose yaw is correct
  (0.0-0.6 deg). The flag therefore carries no information at realistic densities.
- Body at 0.05, seeds (3,4): ACCEPTED with a 128.2 deg yaw error (0.61 mm). The closure reaches 6.3 deg at 0.1.
- The boss is observable: the same gate refuses a no-boss body for "diameter mismatch". The part is
  measurably non-symmetric, yet a wrong yaw passes.

The test (test_multiscan_alignment.py:347-361) explicitly permits this. I agree with the coordinator that it must be
a refusal. "Yaw undetermined" is acceptable only when the part is shown to be rotationally symmetric, e.g. the
footprint/profile is circular within tolerance on both scans. Otherwise refuse, or require a yaw that is pinned
within the probe angle. Add a test that a boss body at 0.05 either aligns within 5 deg or is refused.

H8. The real cloud keeps a fragment, not the jar (`_largest_cluster`, multiscan_alignment.py:275-286 /
`_prepare`). Clusters above the refitted mat (spacing 0.60, eps 3.24 mm):

| Cluster | Points | xy extent | z range | Centre |
|---|---|---|---|---|
| A | 28,598 | 40x41 mm | 48.6-53.5 | (-13, 11) (likely the lid top) |
| B (kept) | 4,843 | 45x91 mm | 37.8-59.6 | (75, -59) |
| C | 975 | - | - | - |
| D | 436 | - | at z 13 | - |

The kept cluster B never comes within 37 mm of the mat, so it does not stand on it. The kept "part" has no
measurable mid diameter (`_width` is NaN). The real-cloud moved-copy (0.03 deg) and 85 % subsample (0.01 deg)
passes are therefore self-consistency of a floating fragment, not evidence about the jar. Fix: require the chosen
cluster to touch the mat (min z within a few mm of mat_margin) and to have a plausible footprint, and pick by
contact/footprint rather than voxel count. Refuse with a clear reason when no cluster qualifies, and test this.

## MEDIUM

M5 (carried). The tolerances (1.5 %, 0.9 coverage, 0.05 free space) are still synthetic-only. `_adapt` loosens the
distance, slice and rmse limits with sparsity; the dimension gates still refused scale errors of 3 % or more at
0.05 pts/mm^2 (checked).
M6 (carried). Part height still comes only from the mat contact.

## Not verified
CI. Real upright+flipped pair (none exists). True scale of the real cloud. Physical accuracy (METRIC_UNVERIFIED).
