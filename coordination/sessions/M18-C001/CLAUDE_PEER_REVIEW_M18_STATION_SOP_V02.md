---
coordinationSchema: packlab-coordination/v1
artifactType: claude-peer-review
cycleId: M18-C001
version: 02
actor: CLAUDE_INDEPENDENT_REVIEWER
reviewedCommit: e1a719c6
previousReview: CLAUDE_PEER_REVIEW_M18_STATION_SOP_V01.md (reviewedCommit 4e8a64f4)
tasks: [PL-0396, PL-0397, PL-0398, PL-0399, PL-0400, PL-0402, PL-0413]
notClaimed: [PL-0401, PL-0403, PL-0404]
date: 2026-11-10
---

# Claude Peer Review V02 — M18 remediation re-review (commit e1a719c6)

The reviewer did not author the remediation. This is a read-only review: no source, doc or `TASKS.md` edits, and no commits.

## Material inspected

- `git show e1a719c6`, covering all 7 files:
  - module: `core/src/packlab_core/scan_station_layout.py`
  - docs: PL-0396, PL-0397, PL-0402
  - tests: `tests/ci/test_m18_station_sop_docs.py` (full rewrite, read in full) and `tests/core/test_scan_station_layout.py`
- `coordination/sessions/M18-C001/CLAUDE_IMPLEMENTATION_LOG_M18_STATION_SOP_V02.md` (finding → change map).
- `git diff e1a719c6` on the reviewed paths showed nothing, so the working tree matches the commit.

## Commands run and output

```
$ .venv/Scripts/python.exe -m pytest tests/ci/test_m18_station_sop_docs.py tests/core/test_scan_station_layout.py -q -p no:cacheprovider
.........................................................                [100%]
57 passed in 0.29s

$ .venv/Scripts/python.exe -m ruff check core/src/packlab_core/scan_station_layout.py tests/core/test_scan_station_layout.py tests/ci/test_m18_station_sop_docs.py
All checks passed!

$ .venv/Scripts/python.exe -m mypy core/src/packlab_core/scan_station_layout.py
Success: no issues found in 1 source file
```

### Independent clearance and frame recheck

I reran the V01 script, which does not import the module. It uses its own look-at basis, a 41×41 dense panel sample and a 5° envelope sample. Feet are now at 1300 mm, ±105°.

```
v02 landscape panel-in-frame poses: 0 | smallest foot gaps: az 90/120/240/270 = 566.458 mm | max envelope image fill 0.606
v02 portrait  panel-in-frame poses: 0 | smallest foot gaps: az 90/120/240/270 = 566.458 mm | max envelope image fill 0.455
v02 with 500 mm panels: 0 in frame, same gaps
closed form: sqrt(800² + 1300² − 2·800·1300·cos 15°) = 566.5 mm
elevation, panel centre → package centre 74.7°; → side wall 81.7°; boom reach foot→panel 1013 mm
```

The module agrees with this:

```
module min_stand_clearance_mm(v02) = 566.5
v02 issues: 0 (portrait, landscape); at threshold 566: 0; at 567: 12 (boundary is the true 566.5 mm minimum)
v01 issues still 36 portrait / 48 landscape (regression case still detected at the 450 mm default)
```

## Verification of V01 findings

| V01 finding | Status | Evidence |
| --- | --- | --- |
| P1-1: stand clearance at exactly 300 mm, point model | **Resolved** | Feet are now off the camera radials at 1300 mm, ±105° (`scan_station_layout.py` `pl0397_v02_layout`). The real minimum is 566.5 mm, against a 450 mm default threshold whose docstring says it stands for an assumed footprint. That leaves 116 mm of margin, which I verified independently. `test_pl0397_and_pl0396_values_match_the_checked_layout` asserts the minimum is ≥550 mm, so a regression back toward the boundary fails. The PL-0397 table and dry-run text and the PL-0396 BOM row agree: 1300 mm / ±105°, about 1.0 m reach (computed 1013 mm). |
| P1-2: PL-0398 had no task-specific test | **Resolved** | `test_pl0398_trial_design_is_paired_preregistered_and_unclaimed` checks five things against the doc text: optional/non-default status, the three trial arms, the five metrics, thresholds chosen before data collection, and the light-loss/fixed-exposure, transparent-PET-separate and no-performance-claim statements. These are task-specific contract checks that fail if the trial design is removed or weakened. |
| P1-3: PL-0402 had no negative cases | **Resolved** | The doc gains a "Proposed grammar" section. Tests now cover 12 malformed IDs (lowercase, short, long, whitespace, slash, path, semantic token, non-digit, unknown type, bad synthetic, leading space, trailing newline) and 9 bad filenames (extension, sequence width, role order, SKU as asset, double extension, date as view, missing field, over-length basename, non-ASCII). Valid IDs are also checked against the runtime `_IDENTIFIER`. |
| P2-1: doc numbers not tied to the module | **Resolved** | The test checks camera distance, heights, the 30° step, panel radius and height, right-panel azimuth, foot radius and azimuth, and the matching strings in both PL-0397 and PL-0396. |
| P2-2: near-overhead lighting not disclosed | **Resolved** | PL-0397 now states about 75° elevation (I computed 74.7°), lower side-face light, a PL-0401 check, and bounce/fill options. |
| P2-3: full-orbit background | **Resolved** | The PL-0397 background row and limits now specify a stationary, uncluttered room for rear views. |
| P2-4: claim language unchecked, weak gate test | **Resolved, with a residual (P3-A)** | An unqualified-claim guard now runs per sentence on all 7 docs, with a self-test. The PL-0399 test now asserts all seven gate names in order. |
| P3-1/2/3 | **Resolved** | The angle-ratio metric is documented. Stands and booms in rear views are noted (my recheck finds stand/boom hardware in 8 rear poses per orientation; it is non-emitting and stationary). Panels are now sampled on a 5×5 grid including edges, and agree with my dense sample. |

## Remaining findings

### P0 / P1
None.

### P2

- **P2-A: the 450 mm footprint threshold is an unsourced assumption.** See the `layout_issues` docstring and `PL-0397...md` dry-run paragraph. The threshold is described as "tripod leg spread plus stand base radius" but gives no component values. A counterweighted boom-stand base can be large.
  - The docs do say to replace it with measured footprints, and the 566 mm point gap leaves room to orient the legs so they interleave. So this does not block a planning document.
  - Recommended: state the assumed tripod and stand radii separately. Record the measured values in PL-0401.

### P3

- **P3-A: the claim guard is broad.** The `NEGATION` vocabulary (`if`, `must`, `may`, `only`, `before`, `un\w+`) means a sentence such as "The station is validated under …" would pass. It is still a useful smoke guard, and the independent reading remains the real control.
- **P3-B: the PL-0402 grammar is copied into the test** (`CANONICAL`, `SYNTHETIC`, `VIEW`), not parsed from the doc. The doc grammar could drift without a test failure. The current text and the test match.
- **P3-C: one panel azimuth is not asserted.** The PL-0397 binding test checks the left panel's radius but asserts the azimuth (±90° panel, ±105° foot) only for the right panel. Both lights are built from the same tuple, so the risk is low.
- **P3-D: overhead head clearance is not recorded.** The boom height above the floor depends on tabletop height (the boom is about 2.0 m above the floor for a 750 mm table). The required setup record already captures tabletop height. Add an operator head-clearance check during PL-0401.

## Shared test-file rewrite: PL-0399, PL-0400, PL-0413

- **PL-0399:** the test is stronger than in V01. It checks the default-none rule, all seven gate names in order, and "every gate must pass". The doc is unchanged since V01.
- **PL-0400:** the A–F sections and topic checks are kept, plus STOP and "do not clean". The doc is unchanged.
- **PL-0413:** the stage-order test is unchanged. The doc is unchanged.
- All three docs also pass the new boundary and claim-guard tests, and the 57-test run is green. The V01 PASS stands.

## Overstatement and non-claimed tasks

- PL-0401, PL-0403 and PL-0404 are still not claimed (V02 log, "Still not claimed").
- The new text adds no physical, Kenya or production claim. The PL-0397 note correctly attributes the old 1100 mm / ±90° draft to the earlier revision.
- No new sensitive data is in the diff.

## Per-task verdict

| Task | Verdict | Notes |
| --- | --- | --- |
| PL-0396 | **CLAUDE_PEER_AUDITED_PASS** | BOM stand geometry is corrected and bound to the layout by test. P2-A is advisory. |
| PL-0397 | **CLAUDE_PEER_AUDITED_PASS** | Clearance is 566.5 mm off-radial (verified independently). Doc and module values are bound. Lighting and background limits are disclosed. |
| PL-0398 | **CLAUDE_PEER_AUDITED_PASS** | A task-specific trial-design dry-run was added. Doc content was sound in V01. |
| PL-0399 | **CLAUDE_PEER_AUDITED_PASS** (reconfirmed) | Gate-name test strengthened. |
| PL-0400 | **CLAUDE_PEER_AUDITED_PASS** (reconfirmed) | |
| PL-0402 | **CLAUDE_PEER_AUDITED_PASS** | Negative cases and grammar added. Code-contract claims were verified in V01. |
| PL-0413 | **CLAUDE_PEER_AUDITED_PASS** (reconfirmed) | |

These PASS verdicts cover the planning documents and their synthetic/geometric dry-run checks only. Real station assembly, calibration, PL-0401 physical repeatability, and factory or Kenya execution stay pending as the contracts require.
