# CLAUDE_PEER_REVIEW - PR #19 repeatable fit / reproducible build (PL-0462, PL-0463) - V02

Reviewer: independent Claude peer reviewer (not the builder). Date 2026-11-21. Follows V01 (CHANGES_REQUIRED at 30c5bf97).
Scope: head 53b5fed7163e76d625720e48f55a42b24a78d875, diff 30c5bf97..53b5fed7 plus the full diff against origin/main.

## Verified myself
- Focused tests at 53b5fed7 (detached temp worktree, Desktop .venv): test_measure_design.py + test_build_model.py, 38 passed.
- CI run 44852998886 "PackLab Windows Python Quality": completed/success, headSha 53b5fed7, branch fix/repeatable-fit-build.
- I re-ran my V01 probes (probe.py, probe2.py) and the implementer's probe3.py on 53b5fed7. Scripts are in
  C:\Users\sekip\AppData\Local\Temp\claude\57fb7811153eaca1\6a444d85-9a45-42be-b7f5-fbce40ad634c\scratchpad\
  - The oval 40/31 at 40/50/60/67 % arcs now falls back to the measured axis and is refused (CV 0.087-0.090, the same as origin/main).
  - The 4 mm dent on a 2/3 arc is refused (0.051). The 6 mm dents are refused.
  - The oval 40/35 at 40-60 % arcs passes at CV 0.046-0.048. origin/main also passes these, so this is not a regression.
  - probe3 reports "weaker than origin/main: 0" over 24 fixtures, and I confirm it.
- Sparse byte-identity across the three seeded builds was verified in V01. The PR body now says "sparse .bin byte-identical; database.db bytes differ".

## V01 findings
- HIGH-1: RESOLVED. robust_axis_roundness bounds the axis: centre shift at most 0.10 of the measured side radius, radius change at
  most 0.10, inliers at least 0.60. Otherwise it uses the measured axis. The CV is untrimmed over all slice points (the same formula
  as origin/main). axis_source and the bounds are recorded in as_dict, which is hashed into the strategy reason. Method id is
  ..._v3. Parametrized tests cover oval 40/50/60/67 % and dents 4/6 mm, and each one asserts that origin/main refuses it too.
- MEDIUM-1: RESOLVED. measure() max_body_diameter is byte-for-byte back to the origin/main rule.
- MEDIUM-2: RESOLVED as disclosure. The PR body is corrected. The 24 mm vial test documents that the coverage rule depends on mesh
  density times object size: it is judged at 1.2-2.0 mm vertex spacing and cannot be judged at 3.8 mm.
- MEDIUM-3: still open for the coordinator, as recommended in V01 (annotate PL-0447 as EVIDENCE_SUPERSEDED, keep [x]).
- LOW: handled (seed comment, PR wording).

## New observations
- MEDIUM (scope, not safety): "robust side-wall outlier rejection", which PL-0462 asks for, is no longer delivered. The untrimmed CV
  counts stray points again: the robustness test was reduced from 40 outward / 60 inward strays to 10 / 10. Only the axis estimate is
  robust now. This is the safe trade-off, but it must be stated in TASKS.md, and it is one reason PL-0462 stays open.
- LOW: the new gate judges only the slices that meet coverage, while origin/main judged every slice with at least 8 points. A badly
  covered slice that is not round is now ignored if 4 others count. I found no fixture where this flips a verdict.
- LOW: inside the bounds, the fitted axis can lower the CV slightly (dent 4 mm on a full ring: 0.043 to 0.042). This is the intended,
  bounded bias correction.
- Real builds: all 8 test-333 builds are refused (7 "cannot judge", seeded run 3 "not round", CV 0.142). The verdict is the same
  refusal every time, but no real repeatable PASS exists.

## Verdict
PASS for merging the source change (CLAUDE_PEER_AUDITED_PASS for the PR code at 53b5fed7). There is no gate weakening compared with
origin/main, and determinism and provenance are verified.

Task lifecycle recommendation:
- PL-0462: keep open. There is no real capture with a repeatable pass, and outlier rejection was traded away. Record both limits.
- PL-0463: may be closed only with the limitation recorded: the COLMAP sparse stage is byte-identical; OpenMVS has no seed
  (177.5k-181.1k points); max body diameter spread is 64.2-71.8 mm across the seeded runs. Otherwise keep it open.
- PL-0447: add the EVIDENCE_SUPERSEDED annotation.
