# CLAUDE_PEER_REVIEW V02 - PR #45 (c54dbc1b)
Correction to V01: its pytest and real-cloud runs imported main's code because of a path error. V01 probes valid. Now: 86 pass. PR #28/#43 suites: unchanged. V01 H1, H2 and MEDIUM are fixed: 0 wrong accepts (blob 3/6/10 mm, ±1.5-2% scale, taller part 88/91 mm).

## HIGH
- multiscan_alignment.py:444-463 `_part_top` cuts off short narrow necks. Upright heights read 70.0 instead of 74-78 mm. Genuine full pairs that main accepts 5/5 are now refused 4/5.

## MEDIUM
- The real dnH scale ratio is 1.0086, against a 1.0 % limit.
- The end-shape check refuses straight-walled ends, including the real dnF case (missing base).

## LOW
- Genuine flipped bottle cut 11 mm: refused 4/4 (free-space 0.053-0.068).
- Fixed: a stale chosen build is now cleared with a notice. Tested: the newest successful build is used when a newer build failed.

**CHANGES_REQUIRED**.
