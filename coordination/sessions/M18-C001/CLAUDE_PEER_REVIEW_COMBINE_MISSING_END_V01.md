# CLAUDE_PEER_REVIEW - PR #45 (aaea77a0)
Independent reviewer, not the implementer. Tests: 119 pass. PR #28/#43 probes: unchanged.

## HIGH
- H1 multiscan_alignment.py:614,936-950: the contact uses the raw max height. A 3 mm top blob plus an 8 mm missing end is accepted with a 2.3-2.5 mm z-shift (3/4 seeds). Base refused it.
- H2 :936-950: 2% scale passes when the shorter end is open (cut 16/16, base 0/16; open jar 16/16, base 8/16). Flipped shift is 1.0-1.6 mm.

## MEDIUM
- A taller open part (88/91 vs 80 mm) with the same walls is accepted 8/8.

## LOW
- project_parts.py:110,632: a deleted chosen build silently falls back to latest and the stale choice stays saved. No 2%-scale or blob tests.

## Real clouds
- Band offsets: -0.96..+1.21 mm (dnF), -1.45..+2.31 mm (dnH).
- A scale fit (-0.31% / +0.68%) leaves 1.3 / 2.2 mm residual.
- A 0.5-1.5 mm radial correction leaves the worst slice unchanged (0.63; 0.59-0.61).
- Within 2 mm: 0.86-0.89; within 3 mm: 0.95. Wall spread 1.1-1.9 mm.
- Cause: noise and scan ends, not an offset. A radial tolerance would hide 2% scale.

**CHANGES_REQUIRED.** Use a robust top and wall-check the contact. Add a scale bound. Tune distance to noise only after caliper evidence.
