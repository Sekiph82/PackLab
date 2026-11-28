# CLAUDE_PEER_REVIEW: PR #47 combine root cause (V03)

Head `cca91489` vs main; fresh probes, real clouds read-only.

## HIGH
1. `multiscan_alignment.py:1800-1820`: the offer has no limit on disagreement size. Only RMSE, scale <= 2 % and yaw are checked. Wrong parts get the button: neck r30 vs r33 (6 mm diameter), a 20x20x5 lug (630 mm2), a 3 mm label panel (790 mm2), a 10x12x3 lug. (7 of 20 offered.) A genuine 2.5 mm shrunk closure gets no offer: the offer does not mean "same part".
2. A missing end is offered. Flipped cut 8 mm plus a lug is offered on patch alone; the merge (`:1848`) drops the upright base (z from 7.6 mm, bottom 0.57).

## MEDIUM
1. Override merge drops one-scan surfaces outside its band (flipped-only ring underside 36 -> 0 points). Band position unconstrained (12-28 to 58-75 mm).
2. The badge is free text only. The Scan Master limitation is not in `configuration_digest`. The interior merge shows no badge. The placement graph inherits `verification` but is untested.

## LOW
- Automatic: fresh 4 wrong vs main 6; V02 probes 26 vs 42; none new.
- Real upF+dnH override: RMSE 0.697, closure 31.8x43.4, neck 28.0x39.9, curtain gone. upF+dnF and the upH pairs refuse without an offer.
- CI: only `test_builds_run_up_to...` fails.

**Verdict: CHANGES_REQUIRED**
