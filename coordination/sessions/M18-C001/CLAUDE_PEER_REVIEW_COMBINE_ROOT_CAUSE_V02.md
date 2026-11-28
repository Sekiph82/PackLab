# CLAUDE_PEER_REVIEW: PR #47 combine root cause (V02)

Head `12572711` vs main. Fresh probes, noise 0.35.

## HIGH
1. `multiscan_alignment.py:722,808`: the noise tolerance has no cap and is local. One-scan lugs of 25-64 mm2, 2.5-3.5 mm proud: wrongly accepted 40/40 (main 13/20). Ring of bumps and 1-2 mm rims at 2.5-3.5 mm: 9/16 (main 1/16). A 1.5 mm radial step over 20 mm at the foot or lid: 4/4 (main 0/4).
2. Noise inflation (b): clean scans with a fuzz patch (0.6-0.9) or a 1 mm double wall hide a 10x20x4 lug (the control is refused at 112 mm2): 7/12 wrong (main 1/12). No limitation is raised.
3. `:823`: area = count x step^2 under-reads about 2x (a 200 mm2 face reads as 107-112). Clean lugs: 15/20 wrong (main 8/20).
4. `:816` mat-facing exclusion (c): a 3-4.5 mm bump on a downward-facing slope, clean scans: 4/4 wrong (main 0/4).

## MEDIUM
1. (d): 23 genuine pairs main accepts are refused. They include 6 dense labelled ovals told "need more side detail" (not actionable).
2. Merge keeps the shoulder curtain (z155: 55.6 vs ~41 mm).

## LOW
Reproduced 0.934/0.697 and 0.939/0.644; the upH pairs refuse. The V01 zone/boss probes give 0 wrong and the underside is kept. The old suites show no new wrong accepts (9 vs 10).

**Verdict: CHANGES_REQUIRED**
