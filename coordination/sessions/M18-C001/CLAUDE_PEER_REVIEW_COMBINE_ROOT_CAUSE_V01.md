# CLAUDE_PEER_REVIEW: PR #47 combine root cause (V01)

Independent reviewer, not the author. Head `2fba1372` vs base `2b453a98`.

## HIGH
1. `multiscan_alignment.py:591-597, 1083-1102`: the contact zones leave the coverage and yaw checks. Only 6 section bands still look there, each an azimuth median at 2 mm. New zone probes: head wrongly accepts 48 of 128 (main 0). Cases: 3-4 mm groove at z8-14, 4 mm base/top lugs, 1.5 mm steps. A white 5 mm flared foot vs a plain body is accepted 3 of 9 at d0.2 (main 0). Far beyond the stated "<2 mm" residual.
2. `:80` gate 0.85: an extra 20x25x3-4 mm boss in one scan only is accepted 4 of 24 (cov 0.880-0.897, main 0). The genuine real pairs (0.895/0.899) fall in the same range: coverage no longer separates them.

## MEDIUM
1. `:1477-1488`: the merge drops zone surfaces that only that scan saw. Of 99-116 flipped neck-ring underside points, 0 are kept.
2. Reproduced 0.895/0.615, 0.899/0.618, strays (dnF z155 caliper 88.4->56.4). The upright base zone agrees, though: +0.3-0.6 mm, cov 0.82-0.95 at z10-25. The disagreement is only at z150-155 (+2.4 mm, cov 0.51). A 30 mm exclusion at both ends is unsupported.

## LOW
Earlier suites (642 cases): no new wrong accepts. 2 of 3 new tests fail on main. CI is green.

**Verdict: CHANGES_REQUIRED**
