---
coordinationSchema: packlab-coordination/v1
artifactType: claude-peer-review
cycleId: M18-C001
version: 01
actor: CLAUDE_INDEPENDENT_REVIEWER
reviewedCommit: 4e8a64f4
tasks: [PL-0396, PL-0397, PL-0398, PL-0399, PL-0400, PL-0402, PL-0413]
notClaimed: [PL-0401, PL-0403, PL-0404]
date: 2026-11-10
---

# Claude Peer Review V01 — M18 scan-station and SOP planning batch (commit 4e8a64f4)

Reviewer did not author this work. Read-only review; no source, doc or `TASKS.md` edits, no commits.

## Material inspected

- `git show 4e8a64f4 --stat` (42 files, +1454) and diffs of the PL-0397/PL-0396 docs.
- Full text: `docs/development/PL-0396_SCAN_STATION_STARTER_BOM.md`, `PL-0397_SCAN_STATION_LIGHTING_AND_CAMERA_LAYOUT.md`,
  `PL-0398_CROSS_POLARIZATION_EVALUATION.md`, `PL-0399_REMOVABLE_SCAN_TREATMENT_PROCEDURE.md`,
  `PL-0400_OPERATOR_CAPTURE_CHECKLIST.md`, `PL-0402_PACKAGING_ASSET_NAMING_AND_IDS.md`, `PL-0413_SAMPLE_TO_LIBRARY_SOP_DRAFT.md`.
- `core/src/packlab_core/scan_station_layout.py`, `tests/core/test_scan_station_layout.py`, `tests/ci/test_m18_station_sop_docs.py`.
- `coordination/sessions/M18-C001/CLAUDE_IMPLEMENTATION_LOG_M18_STATION_SOP_V01.md`, Codex logs/criteria for PL-0397, PL-0401, PL-0403, PL-0404.
- `TASKS.md` lines 790–813 (execution contracts).

## Commands run and output

```
$ .venv/Scripts/python.exe -m pytest tests/core/test_scan_station_layout.py tests/ci/test_m18_station_sop_docs.py -q -p no:cacheprovider
...........................                                              [100%]
27 passed in 0.26s

$ .venv/Scripts/python.exe -m ruff check core/src/packlab_core/scan_station_layout.py tests/core/test_scan_station_layout.py tests/ci/test_m18_station_sop_docs.py
All checks passed!

$ .venv/Scripts/python.exe -m mypy core/src/packlab_core/scan_station_layout.py
Success: no issues found in 1 source file
```

Independent geometry script (reviewer-written, does not import the module; scratchpad `geom_check.py`): own look-at basis,
pinhole projection with tan-plane frame test, 41×41 dense sampling of each emitting panel face, 5° envelope sampling.

```
FOV long/short deg: 67.3 53.06
v01 landscape panel-in-frame poses: 36 azimuths: [60..300] | feet gaps: (30/60/300/330, 208.842 mm) | max envelope image fill: 0.606
v01 portrait  panel-in-frame poses: 24 azimuths: [90..270] | feet gaps: (30/60/300/330, 208.842 mm) | max envelope image fill: 0.455
v02 landscape panel-in-frame poses: 0 | feet gaps <=300.5 mm: [(90, 300.0), (270, 300.0)] | fill 0.606
v02 portrait  panel-in-frame poses: 0 | feet gaps <=300.5 mm: [(90, 300.0), (270, 300.0)] | fill 0.455
v02-500mm panels: 0 in frame, same 300.0 mm feet gaps
v02 stand/boom hardware (non-emitting) in frame: landscape 10 poses, portrait 6 poses
```

Module cross-check:

```
portrait  v01 issues 36 (24 in-frame, 12 stand-foot);  v02 issues at min_stand_clearance_mm=301: 6
landscape v01 issues 48 (36 in-frame, 12 stand-foot);  v02 issues at min_stand_clearance_mm=301: 6
gap camera az=90 to right stand foot: 300.0
```

Boundary-regex probe: `"there is no doubt the physical station passed production acceptance in kenya."` satisfies
`test_doc_states_no_physical_or_kenya_acceptance` → `True`.

Code-contract claims in PL-0402/PL-0413 checked against source: `_IDENTIFIER` (`packaging_asset.py:16`) and `_ID`
(`packaging_library_audit.py:34`) are `^[A-Za-z][A-Za-z0-9_.:-]{0,127}$`; `packaging-asset:` prefix (`packaging_asset.py:21`);
`packlab.packaging-asset.v1` (`packaging_asset.py:15`, `packaging_library_audit.py:875`); `packaging-sku:`
(`packaging_sku_library.py:234`), `packaging-component:` (`packaging_components.py:96`), `assembly-graph:` (`assembly_graph.py:402`),
`component_version` (`trigger_pump_library.py:41`); `AssetStatus` UNKNOWN/DRAFT/ACTIVE/ARCHIVED/RETIRED (`packaging_asset.py:64-69`). All accurate.

## Geometry verification summary

- FOV math (`scan_station_layout.py:24-31`) is correct: 35 mm-equivalent by diagonal (43.27 mm), 4:3 split → 67.3° × 53.1°.
- Look-at frame (`:74-85`) is correct (right = forward × z, up = right × forward; checked by hand for az=0). Per-axis
  `atan2(component, depth)` is a valid rectangular-frustum test. Degenerate case (camera directly above target) would divide by
  zero but is unreachable with these heights.
- Rev 01 claims reproduce exactly: panel in frame for rear views (36 landscape / 24 portrait poses), stand feet 208.8 mm
  (= 2·800·sin 7.5°) from the 30/60/300/330° stations. The rev 01 model matches the Codex original (`PL-0397_CODEX_LOG_V01.md:24`).
- Rev 02: no emitting surface in frame in either orientation, confirmed by dense sampling (module samples only 5 points/panel,
  `:132-137`, but dense sampling agrees). Envelope fill is well below the limit.
- **But the rev 02 stand-foot clearance passes with exactly zero margin** (see P1-1).

## Findings

### P0
None.

### P1

**P1-1: rev 02 stand-foot clearance only passes at the exact threshold, using point footprints.**
`core/src/packlab_core/scan_station_layout.py:127,166`; `docs/development/PL-0397_SCAN_STATION_LIGHTING_AND_CAMERA_LAYOUT.md:21,30`;
`docs/development/PL-0396_SCAN_STATION_STARTER_BOM.md:18`.
The stand feet at 1100 mm radius, ±90° sit radially behind the 90° and 270° camera stations, so the gap is 1100 − 800 = 300.0 mm.
The check is `gap < 300`, so the result passes at exactly 0 mm margin. With `min_stand_clearance_mm=301` you get 6 violations.
The model treats both the tripod and the counterweighted boom stand as points. Real tripod legs and boom-stand bases spread
several hundred millimetres, so at those two stations the bases would very likely collide or block the operator.
The doc and log say rev 02 has "zero violations" and fixes the rev 01 stand-foot defect, which overstates the fix. The test
`test_revised_layout_frames_envelope_without_lights_in_view` also depends on floating-point equality at the boundary.
Required change:
- Move the stand azimuths between camera stations (e.g. ±75°/±105°) and/or increase the foot radius.
- Model footprints as discs (tripod and stand base radii as explicit, recorded parameters) and keep a stated margin.
- Update the PL-0397 table, the PL-0396 BOM row, the module and the tests together.

**P1-2: PL-0398 has no task-specific dry-run test.**
`tests/ci/test_m18_station_sop_docs.py:28-32` is the only test that touches PL-0398, and it is the generic boundary regex.
The probe above shows that regex accepts an overclaiming sentence. The contract (`TASKS.md:792`) requires "synthetic dry-run tests".
Required change: add at least one PL-0398-specific check. For example: cross-polarization is optional and not the default; all
three trial arms are present; each arm is processed separately; the predeclared comparison metrics are present; the Clini
combined-method caveat is present. A synthetic trial-plan record validated against those rules would be better.

**P1-3: PL-0402 has no negative cases, which its contract requires.**
`tests/ci/test_m18_station_sop_docs.py:35-54`; contract at `TASKS.md:799` ("negative cases and explicit simulation labels").
Only positive IDs are tested. Nothing checks that the documented rejection rules (whitespace, slashes, control characters,
paths, >40-char IDs, >16-char view codes, non-allowlisted extensions, >180-char basenames, sequence not exactly 4 digits) actually
reject anything. The synthetic `SYNTHETIC-TEST-CMP-0001` and `SYNTHETIC-TEST-ASM-0001` examples (`PL-0402...md:47-48`) are not tested.
Required change: add parametrized negative fixtures that fail the proposed bounds and/or `_IDENTIFIER`, and cover all synthetic examples.

### P2

- **P2-1: PL-0397 doc numbers are barely tied to the module.**
  `test_pl0397_layout_references_executable_dry_run` (`tests/ci/test_m18_station_sop_docs.py:75-80`) only checks two file paths and
  the string "1300 mm above the tabletop". The doc's 300 mm panel radius, ±90°, 1100 mm foot radius, 800 mm camera distance,
  120/200/320 heights and 30° step could all drift away from `pl0397_v02_layout()` and the test would still pass.
  Suggested fix: assert each documented value against the layout object.
- **P2-2: rev 02 is near-overhead lighting and the doc does not say so.**
  `PL-0397...md:21`. From the package, the panel centres sit at about 75° elevation (about 81° from a side wall). Vertical
  label/side faces therefore get roughly 0.16–0.27 of the direct irradiance that top faces get, which risks dark labels next to
  clipped tops. The geometry check cannot see this. Add this to the limits paragraph (`:31`) as an item for the PL-0401 trial,
  and mention fill or bounce options.
- **P2-3: a single fixed background board cannot sit behind the object for a full 360° camera orbit.**
  `PL-0396...md:15`, `PL-0397...md:22`. For rear viewpoints the background is the room, which includes the light stands
  (P3-2) and the operator. State the intended background treatment for a full orbit, or accept a non-uniform stationary background.
- **P2-4: the doc tests are mostly string and heading checks.**
  The boundary regex (`:31`) accepts overclaims and checks for no forbidden claim language such as "validated", "accepted" or
  "production-ready". The PL-0400 topic check (`:62-63`) would pass on unsafe instructions. The PL-0399 check (`:86`) counts bold
  numbered items, not the gate content. For prose deliverables, structural checks plus a full independent reading are an
  acceptable minimum. A materially wrong document could still pass all of them, though, so the rigour comes from the review.

### P3

- **P3-1:** The envelope "fill" is an angle ratio (`scan_station_layout.py:114`), not an image-plane (tan) ratio. It is slightly
  conservative and is not documented as such.
- **P3-2:** Light stands and booms (non-emitting hardware) are in frame behind the object for 10 landscape / 6 portrait rev 02 poses.
  They are stationary, so this is harmless for SfM, but the module does not check them. Note this in the doc.
- **P3-3:** The emitting faces are sampled sparsely (5 points per panel, `:132-137`). Dense sampling agreed for rev 02, but an
  edge-crossing panel could be missed in other layouts.

## Consistency check

- The PL-0396 envelope (250 mm diagonal / 400 mm / 5 kg) matches PL-0397:5, PL-0400:34 and the module (`envelope 250/400`).
- PL-0396:18 and PL-0397:21 agree on the rev 02 values (300 mm radius, 1300 mm height, 1100 mm feet). Both inherit P1-1.
- PL-0400 and PL-0413 refer to the PL-0397 positions only generically, as "unvalidated starting points", so they contain no
  conflicting numbers. The calibration-only-set rule (PL-0397:37-38, PL-0400:44,56, PL-0413:39) and the food-contact
  no-clean/no-treat rule (PL-0400:24, PL-0413:29, PL-0399:12) are consistent.
- The PL-0413 lifecycle covers the `TASKS.md:813` chain (receive→clean→calibrate→capture→reconstruct→fit→audit/review→library),
  plus backup.

## Overstatement and non-claimed tasks

- Every reviewed doc carries an explicit no-physical-station / no-Kenya / no-production-acceptance boundary.
- PL-0401, PL-0403 and PL-0404 remain `[ ]` in `TASKS.md`. Their Codex logs say `BLOCKED_EXTERNAL_*`, and the implementation log
  lists them as not claimed.
- The PL-0404 rubric is headed "Rubric proposal only" and ranks only an `UNRANKED_INPUT_REQUIRED` synthetic row. Not overstated.
- The only overstatement found is the rev 02 "zero violations / fixes stand clearance" claim (P1-1).

## Safety and privacy (PUBLIC repo)

- I scanned the commit additions for e-mails, local user paths, credentials, tokens, Kenyan locations and supplier names. Nothing sensitive was found.
- Vendors named (Proaim, Kaiser, AESUB) are public product or SDS references, explicitly marked as not recommendations.
- "POVU" appears only as a generic launch-matrix reference with no SKU, volume or date data.
- The Codex logs contain commit SHAs and the words "Desktop sync", but no absolute local paths or personal data.
- PL-0399's chemical-safety handling is conservative and correctly scoped (no product selected, SDS restrictions recorded as written).

## Per-task verdict

| Task | Verdict | Required change |
| --- | --- | --- |
| PL-0396 | **CHANGES_REQUIRED** | Correct the BOM stand geometry after the P1-1 fix (row 18). Address the 360° background (P2-3). |
| PL-0397 | **CHANGES_REQUIRED** | P1-1: real stand/tripod clearance margin with footprint radii, plus an updated module and tests. P2-1: tie doc values to the module. P2-2: disclose the top-light side-face illuminance. |
| PL-0398 | **CHANGES_REQUIRED** | P1-2: add a PL-0398-specific synthetic dry-run/contract test. The document content itself is sound. |
| PL-0399 | **CLAUDE_PEER_AUDITED_PASS** | None blocking. Strengthening the gate-content tests (P2-4) is optional. |
| PL-0400 | **CLAUDE_PEER_AUDITED_PASS** | None blocking. P2-4 is optional. |
| PL-0402 | **CHANGES_REQUIRED** | P1-3: add negative-case fixtures and cover the CMP/ASM synthetic examples. The doc is accurate against the code contracts. |
| PL-0413 | **CLAUDE_PEER_AUDITED_PASS** | None blocking. |

The PASS verdicts cover the planning documents and their dry-run checks only. Real factory execution, calibration and physical
acceptance remain pending, as the contract requires.
