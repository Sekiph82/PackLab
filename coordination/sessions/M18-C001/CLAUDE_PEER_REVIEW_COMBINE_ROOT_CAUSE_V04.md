# CLAUDE_PEER_REVIEW: PR #47 combine root cause (V04)

Head `38d71850`; fresh probes; real clouds read-only.

## HIGH
1. Wrong parts reach tier A (design breach):
   - 15x12x4 base lug, upright only: 4/4. The merge drops that region; `:1962` checks only the kept scan.
   - 3 mm recesses in the kept scan (z54-64 upright, z4-16 flipped): 8/8. `:770` sees only walls standing out.
   - h170 at +1.2 % scale: 8/8 (scale up to 2 % counts as physics).
   - Neck 1.8 mm larger: 5/8 (follows from the 2 mm bound).
   - Hard blocks held: end, height, yaw, conflict, over 4 mm.

## MEDIUM
1. Merge keeps one-scan surfaces with no gaps, but also keeps shrunk-closure points 2+ mm inside the neck: a duplicate inner layer (5-60 per pair).
2. The tier is missing from the Measure badge and the placement sources. Nothing turns verified.

## LOW
- The merge with main matches the branch delta, line for line.
- Worktree imports verified; 210/211 tests pass. `test_invalid_autosave...` flaked under load and passes alone and in order on head and main.
- Automatic path matches main (6 vs 6).
- Real data: tier B (63 mm2 at 3.6 mm, 150 mm2 at 2.3 mm). Neck 28.1x39.8, closure 31.8x43.0. upF+dnF and the upH pairs are blocked by height.

**Verdict: CHANGES_REQUIRED**
