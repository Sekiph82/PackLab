# CLAUDE_PEER_REVIEW - PL-0401 software half (V03 confirmation)

Reviewer: independent Claude source reviewer (non-implementing). I made no edits to the files under review and no git writes. This file is the only one I created.

`main` HEAD is now `5faa81ed`, an unrelated PL-0358 commit since V02. The PL-0401 files are still untracked working-tree files. This review supersedes V02.

| File | SHA-256 |
| --- | --- |
| core/src/packlab_core/station_session_repeatability.py | eb4114a59dabf65166a50201171f213a7251982f679dca241c6e409f01a68500 |
| tests/core/test_station_session_repeatability.py | 63d9fecd33bafe5932513c2e8f254ffe0056ff81e3c4662167da159f7cdb29c9 |
| docs/development/PL-0401_STATION_REPEATABILITY_PROCEDURE.md | 74b3c3b14a76f71154d9bdd4f1e16edfc53f024e65893e4ccc8ee89f4e533b87 |

**Verdict: SOFTWARE_PASS.** V02 notes N-1 to N-4 are closed, and I verified each one against the source. No P1 or P2 findings remain. Physical validation stays PHYSICAL_EVIDENCE_PENDING, and PL-0401 stays unchecked until real multi-session station evidence exists.

## Commands run by the reviewer (Windows, Python 3.12.10, .venv)
- pytest of the new test file plus tests/core/test_repeat_scan_reproducibility.py: 53 passed. This matches the implementer claim.
- ruff check core apps tools tests: all checks passed.
- ruff format --check with line-ending auto: both files already formatted.
- mypy on the module: no issues.
- Mutation testing, each mutant on a temp copy injected through a pytest plugin, with the repo untouched:
  - All 34 V02 mutants were re-run, including the former survivors `floor_off` and `no_revset_bind` (anchor for `ignore_initial` updated). All 34 are now killed.
  - 7 new mutants: drop the finite check on transforms, drop the initial_transforms key check, allow a first-session key, compute the wrong rotation_beyond_initial, use a wrong initial_transform_supplied, drop the wrapper around digest hashing, and revert the reproduction comparison so NaN passes. 6 are killed.
  - The survivor is the NaN-safe comparison (`not abs(a - b) <= tol`, :454-457). It is equivalent at present, because the finite check on transform values (:439-448) blocks NaN first and was itself killed. I keep it as defence in depth, with no action needed.

## N-1 to N-4 closure
- **N-1 (floor-only path):** closed. The `floor_off` mutant is now killed.
- **N-2 (superset of revision IDs):** closed. The `no_revset_bind` mutant is now killed.
- **N-3 (malformed transforms):** closed.
  - Probe: a string transform raises `pl0222_scan_transform_invalid` before any arithmetic (:439-448).
  - Probe: a NaN transform in a report raises `pl0222_report_digest_invalid`, because hashing errors are now wrapped (:484-489).
  - Both now raise StationRepeatabilityError.
- **N-4 (alignment provenance and disclosure):** closed.
  - Unknown, misspelled or first-session `initial_transforms` keys raise `initial_transform_key_unknown_or_unused` (:206-210, probed).
  - The alignment record now has `initial_transform_supplied`, the `initial_transform` used, `rotation_to_canonical_deg` and `rotation_beyond_initial_deg` (:249-261).
    - `_rotation_deg` uses `acos((trace(B^T R) - 1) / 2)`, which is correct for the relative rotation.
    - Probe: a 90 deg re-placement seeded at -89.5 deg reports 90.0 deg total and 0.5 deg beyond the seed, with the flag true. A 3 deg yaw without a seed reports 3.0 and 3.0, with the flag false.
  - `registration_adapter` is recorded (:212, :338).
  - Doc :67-72 states that registration error on real data is unmeasured, that the synthetic clouds share sample positions, that the ICP gate does not bound residual rotation, and that s_L and the drift flags mix station drift with alignment error.

## Residual note (P3, wording only, no action required)
- Doc :71 calls s_L an "upper bound" on true station drift. That holds in expectation: alignment variance only adds to the between-session component. It is not a strict bound for each estimate, because the ANOVA estimate has its own sampling error and is truncated at zero. Suggested wording: "biased upward (in expectation) by alignment error". This does not affect correctness or safety.

## Disposition
SOFTWARE_PASS for the software half of PL-0401 (CLAUDE_PEER_REVIEW: V01 FAIL, then V02 PASS_WITH_NOTES, then V03 PASS). The physical half remains PHYSICAL_EVIDENCE_PENDING. The task checkbox stays open until real multi-session station evidence and PL-0221 thresholds exist.
