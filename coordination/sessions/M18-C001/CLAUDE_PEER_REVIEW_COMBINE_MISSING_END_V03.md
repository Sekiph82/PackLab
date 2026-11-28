# CLAUDE_PEER_REVIEW V03 - PR #45 (16f4aade)
Worktree imports verified. 96 pass. PR #28/#43 suites unchanged (wrong-role accepts pose-correct, same as main).

## Fixed
- Coaxial necks: 5/5 heights correct, all accepted, matching base2.
- Blob 3/6/10 mm, taller open part, upright missing top: 0 wrong accepts.
- ±1.5/2% scale: refused (u <= 0.01).
- Straight-walled flipped missing base: 18/18 accepted.

## MEDIUM
- multiscan_alignment.py:451-481: an off-axis spout 8-10 mm tall reads 70.1 mm instead of 78/80 mm. Main accepts spout20x8; the PR refuses it.
- Fix: run the ring test about the level's own centre, not the part axis.

## LOW
- The scale bound is hypot(u1, u2) at 1 sigma. With u = 0.015 per scan, ±1.5-2% scale errors are accepted with a 1.2-1.6 mm shift. Real builds have u ≈ 0.007-0.008, so the bound is about 1.04%. Cap the bound.

Real pairs refused (read-only).

**CHANGES_REQUIRED** (spout height).
