# CLAUDE_PEER_REVIEW - PR #43 combine real data (fix/combine-real-data c5dfaa0f) - V01

Independent reviewer (not author; not CHATGPT_AUDIT/CODEX_PEER_REVIEW). Ran: 4 test files, 89 passed; reviewer probes in scratchpad rv-combine/.

## HIGH
H1. multiscan_alignment.py:620-663 `_colour_yaw`: Pearson correlation is contrast-invariant, so 10 % one-sided lighting on a PLAIN oval (lit front in one scan, back in the other) is ACCEPTED 180 deg wrong, yaw_determined=True (12/12 runs, k 0.1-0.7). Labelled oval + 60 % shading: also 180 deg wrong. Base refused these. The plain-oval test only covers exactly flat colour (NaN path).

## MEDIUM
M1. `align_scans` wrong role, labelled oval: accepted 180 deg / 100 mm off.
M2. `_mat_halo` :352: white flared foot (r45 under r40): base ACCEPT, PR REFUSE (section z=6). Fail-safe.

## LOW
L1. The 8 deg limit exists only in tests. Default stays 5, and labelled ovals are refused in 4/6 runs.

## Re-run suite
Radius, height, scale 2-5 %, boss vs plain, floaters, tilt, wrong role (body/closure), and a 96-pair sweep at 0.5-0.05: 0 wrong accepts. White body/closure with halo: kept. Real pair: refused as claimed (height 173.4/153.3, cov 0.796, free space 0.064).

## Verdict: CHANGES_REQUIRED (H1). No real good pair, so the thresholds are NOT_VERIFIED.
