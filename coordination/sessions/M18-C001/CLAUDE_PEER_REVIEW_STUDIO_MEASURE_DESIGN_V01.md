# CLAUDE_PEER_REVIEW — Studio Measure & Design (PR #14) V01

- Reviewer: independent Claude peer reviewer (did not author the change)
- Scope: PL-0445, PL-0446, PL-0447, PL-0458
- Base/head: `origin/main` ... `origin/feat/studio-measure-design` @ `904d3aa0` (15 files, +2345/-11)
- CI: `PackLab Windows Python Quality` run 44814901196, headSha 904d3aa0, conclusion success (checked with `gh run view`). No frozen-build/installer workflow run on this head: NOT_VERIFIED.
- Local rerun (temp detached worktree, `uv run --locked pytest`): test_measure_design, test_fitting_strategy, test_revolved_design_model, test_design_model -> 33 passed.
- Real-window evidence inspected: `Documents/PackLab-work/studio-e2e-measure/` (screenshots 01-11, e2e_log.json, dimension-report.json/.md, project/derived/scan_master manifest). Values match the report (121.6 mm/unit ±0.83 %, 50/51 views, print correction 0.98; H 38.2±1.2, body Ø 72.5±2.7, lid Ø 67.4±4.5 mm_unverified; METRIC_UNVERIFIED everywhere).

## Verdict: FAIL (CHANGES_REQUIRED) — two small MEDIUM fixes; core changes themselves are sound

## HIGH
None.

## MEDIUM
- **M1 Evidence class overclaim.** `apps/windows-studio/src/packlab_studio/measure_design.py:535` defaults `evidence_class="accepted_owner_physical"` and `measure_view.py:356-363` never overrides it. The real test-333 Scan Master manifest (`project/derived/scan_master/a0d311ab.../manifest.json`) and the synthetic UI test both carry `accepted_owner_physical` for a mat whose print is not caliper-verified (owner reprint pending). `core/.../scale_provenance.py:320-342` uses exactly this class to permit METRIC_VERIFIED promotion, so a later promotion step would find the reference evidence already "accepted". Scale state is still METRIC_UNVERIFIED today, but the label is wrong. Fix: default `synthetic_test_fixture` or add an unverified physical class in core; switch to `accepted_owner_physical` only after the caliper record exists.
- **M2 Dependency registered nowhere.** `pyproject.toml:14` pins `opencv-python-headless==5.1.0.95` (the lock has the sha256 hashes), but `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md:23,77` still says OpenCV is "Planned, not installed or selected" and says the pinned version must drive the compliance record. There is no `tools/packaging/windows_component_license_registry.json` entry and no `frozen_runtime.py` handling. The wheel is Apache-2.0 but bundles FFmpeg (LGPL) and other third-party natives. Before acceptance: add the register row and evidence (wheel SHA, bundled-native inventory, LGPL obligations) and a registry entry, or exclude cv2 from frozen builds. Frozen build: NOT_VERIFIED.
- **M3 Owner-review strategy thresholds are fitted to the data, not gates.** `measure_design.py:1251-1258` sets coverage to `min(observed) - 0.01` and section CV to `max(observed) + 0.01`. These pass by construction, have no floor and no ceiling (0.704 / 0.402 on test-333). The only real gate is `axis_radial_cv <= 0.05` (`:1142,:1247`) plus at least 3 sections. The override is explicit and recorded: it is opt-in, the policy is hashed into `recommendation_id` (`fitting_strategy.py:293`), and it appears in the notes and screenshot 08. Core defaults are not weakened. Still, add absolute bounds (for example coverage >= 0.5, section CV <= 0.5) and a negative test showing the override refuses when axis CV > 0.05. Neither exists today.

## LOW
- L1 `measure_view.py:207-211`: steps run on the UI thread (~10 s for marker scale). This is acknowledged in a `ponytail:` comment.
- L2 `measure_design.py:1019,1023`: in the Scan Master lineage the raw-capture digest is the built-model file hash. The limitation is recorded honestly, but the chain does not reach the PackScan.
- L3 `measure_view.py:544-563`: Design Model revisions go to `derived/design_model/*.json` (create-only), but they are not registered in project authority state and no revision is selected. PL-0447 authority stays partial.
- L4 `tests/core/test_revolved_design_model.py:262`: the negative test covers only a missing `actor_id`. Missing `reason` and `previous_revision_id` (`revolved_design_model.py:313-317`) are untested.
- L5 `tests/core/test_design_model.py:231`: the test checks the regex, not `DesignModelRevision(project_id=<uuid>)` end to end. That path is exercised only indirectly by the studio test.
- L6 Print correction lives in per-machine QSettings, not per project. It is captured in the reference digest and side length (`measure_design.py:497-512`), which is acceptable.
- L7 The fitted Design Model (H 34.31 / Ø 76.13) differs from the measured H 38.2 / Ø 72.5 by 3.6-3.9 mm, and the measured lid Ø 67.4 is smaller than the 77.6 bbox. The owner then edited the model to 39.3/72.1. This should be noted as a fit-fidelity limit.

## Accepted-core changes
- The `upright_axis` parameter (`fitting_strategy.py:197-278,456`) is type-checked, skips only the elongation check, and appends an uncertainty code that goes into the ID hash. Its test is meaningful (the squat ring needs review without it and revolves with it).
- The MANUAL_OVERRIDE acceptance (`revolved_design_model.py:308-319`) requires actor, reason and a previous revision, and keeps all lineage equality checks.
- The `_PROJECT_ID` regex is narrowly scoped, and other IDs keep `_ID`.

## Limits
PL-0446 physical accuracy stays open until the owner reprints the mat and records caliper values. The synthetic ground truth in the tests is not physical evidence. This review is not an `AUDITED_PASS`.
