---
coordinationSchema: packlab-coordination/v1
artifactType: codex-log
cycleId: M18-C001
version: 01
actor: CODEX
status: LOCAL_COMPLETE_AUTONOMOUS_QUEUE_ARMED
promptPath: coordination/sessions/M18-C001/PL-0397_CODEX_PROMPT_V01.md
criteriaPath: coordination/sessions/M18-C001/PL-0397_VALIDATION_CRITERIA_V01.md
startingCommit: f8745047063aca6c17378ecb33604e6e1e5b5f02
finalCommit: f8745047063aca6c17378ecb33604e6e1e5b5f02
---

# PL-0397 Codex Log V01 — Lighting and camera layout

## Inputs and synchronization

- Read PL-0397 prompt/criteria, the PL-0396 BOM, and current COLMAP, Agisoft and OpenCV capture/calibration guidance.
- Local HEAD remains `f8745047063aca6c17378ecb33604e6e1e5b5f02`; fetched `origin/main` remains `db772e35f386fcba88fa6dbdd01d186959fa7162`. Checkout is dirty and 95 commits behind. No reset/merge/stash/commit/push/Actions/Desktop refresh.
- `NO_LOCAL_WORKTREE_CREATED`.

## Work and evidence

- Added `docs/development/PL-0397_SCAN_STATION_LIGHTING_AND_CAMERA_LAYOUT.md` with a measurable coordinate system and explicitly unvalidated starting locations: 800 mm lens-to-axis, camera heights 120/200/320 mm, two diffused lights 800 mm horizontal floor radius at ±45° and 650 mm above the tabletop, plus a 12-view/30° camera orbit proposal.
- Reconciled with PL-0396: the 600 × 600 mm tabletop supports the turntable/object only; tripod and lights stand on the floor. Their floor coordinates are measured from the tabletop origin projected to floor; tabletop height above floor is recorded. Stand feet and cables are kept outside the operator orbit.
- Ordinary COLMAP sets keep the object stationary in one orientation and move the camera. Changed object orientations and turntable-aware modes are kept separate until validated.
- Added a capture setup record for station revision, sample envelope/orientation, camera/lens/settings, camera and light coordinates, background, calibration/scale references, review observations and mode identity.

## Independent review

- Source reviewer checked cited COLMAP/Agisoft guidance, the unvalidated numerical assumptions, and cross-document geometry with PL-0396. The initial 600 mm table/800 mm support mismatch was corrected by placing tripod/light stands on a stable floor with coordinates referenced to the tabletop origin. Final geometry review passed.
- Security reviewer confirmed no physical/Kenya evidence overclaim, no private data included, and appropriate provenance fields. Both reviews were advisory; no physical station was tested.

## Validation and limitations

- Expected: a future operator can reproduce a documented starting layout and actual deviations without treating suggested positions as proven optimum. Failure condition: incompatible station coordinates, hidden object motion within a normal COLMAP set, or a claim of physical repeatability/accuracy without PL-0401 evidence.
- This is a documentation task; no runtime test was applicable or run. The 800/120/200/320/650 mm and ±45° values are proposals, not measurements or standards.
- No hardware, physical sample, camera or Kenya factory site was available/used. No calibration, dimensional accuracy, scan quality or repeatability result is claimed.

## Privacy and publication

- No images, scans, operator data, credentials or supplier files added. Local changes remain unpublished due the dirty, behind checkout and no-CI rule.

**LOCAL_COMPLETE_AUTONOMOUS_QUEUE_ARMED** — layout proposal and peer review are complete locally; physical repeatability remains PL-0401 work.
