# CLAUDE_PEER_REVIEW - PR #22 Studio visual polish (PL-0464 + F7-F10, F12-F14, F16) - V01

Reviewer: independent Claude peer reviewer (did not author the change). Date 2026-11-22.
Scope: `origin/main...origin/feat/studio-visual-polish`, head `5bc8e64d3e3a05c03854ad43ae3ac93dbc3bf0c2`
(20 files, +1679/-139; all under `apps/windows-studio/src` and `tests/studio`). Implementer
screenshots in `Documents\PackLab-work\studio-visual-polish\` inspected (contact sheet plus individual
tr/en 1280x720 and 1389x868 pages). No source edited by the reviewer.

## Evidence checked
- Windows Python Quality run 45014947007: success, `uv run --locked pytest -q` = 3449 passed,
  15 skipped, 1 deselected; ruff clean.
- Capture macOS CI run 45014947013: "Unsigned iOS device archive" failed at step
  "Ensure iOS 18.0 platform is installed for the device archive" (runner setup); simulator
  build/XCTest succeeded; E2E job still in progress at review time. The diff touches no iOS,
  workflow or shared-core files (`git diff --name-only` outside windows-studio/tests: empty).
  The same workflow passed on this branch at 5cfd4fc8 (run 45013530182) and on main 2026-11-21
  (44853845060); no recent main failure at this step. Classified runner/infra, not PR-caused.

## Findings

### HIGH
None.

### MEDIUM
- M1 `i18n.py:translate_widget_tree` (lines ~42-62) rewrites the display text of every
  QComboBox item via the English-text dictionary, but `package_families_view.py:280,284,380`
  uses `self.preset.currentText()` as the logic key (and provenance `preset:<slug>`). Today no
  preset name is a TURKISH key (verified: none of the `pf.PRESETS` names match), and presets are
  repopulated on family change, so behaviour is currently unchanged. However, adding e.g.
  "5 L jerrycan" to TURKISH later would make `default_parameters` silently fall back to the first
  preset (`name = preset if preset in presets else next(iter(presets))`) -> wrong nominal
  dimensions and wrong provenance, with no error. Request: store preset name as item data and
  read `currentData()`, or add a regression test asserting no `pf.PRESETS` key is in TURKISH.
  Not blocking for this PR; track before the next i18n expansion.

### LOW
- L1 `build_model.py:latest_builds` - read-only, tolerant of OSError/ValueError, non-dict JSON
  and non-str digest (good), but `RecursionError` from pathological nested JSON is not caught;
  "Open selected model" is offered for `active`/`failed` workspaces whose dense PLY may be
  partial. No test covers malformed/non-dict/missing-digest manifests.
- L2 `shell.py:start_build` errors from "Build selected scan" are reported via `_inbox_note`
  (Capture Inbox status), not visible on the Build 3D Model page.
- L3 `viewport.py:_shade_mesh` - projection matches `_project` (unit/pz identity verified),
  painter's-sort and two-sided headlight are correct; but it is a Python per-triangle loop and
  Package Families meshes are not LOD-capped. No test exercises SHADED rendering at all.
- L4 `model_viewer.py:fit` - 2-98 percentile for pure clouds, full extent for meshes/mixed:
  correct and tested for the outlier case; NaN coordinates would propagate to the camera
  (pre-existing behaviour); mixed mesh+cloud not tested.
- L5 `preferences.py` v1->v2: drops only `dock_state`, keeps geometry/route; v0 path keeps
  `last_page` migration; unknown/future versions -> defaults (no crash). Downgrading to an older
  build resets preferences. Only v1 is tested; add v0 and future-version cases.
- L6 Tooltips: `inbox_row` HTML-escapes every audit line; phone-provided `device_model`/
  `device_name`/`scan_name` go only into plain-text list items or PlainText labels. No test with
  markup payloads.
- L7 Screenshots are offscreen-platform renders (non-Windows font), so they do not prove real
  Segoe UI metrics. At 1280x720 TR, Library create/backup actions sit below the fold (scroll
  needed); idle Jobs dock is an empty white strip. No truncation, overlap or horizontal overflow
  observed; Turkish text fits.
- L8 `app.py` removes `setApplicationDisplayName` (intended: avoids duplicated title; tested).
  `set_project_available` no longer hides docks (intended; tests updated, not weakened).

Audit identifiers (DEFERRED_OWNER_VALIDATION, mm_unverified, capture_id/sha256 in tooltips,
Scan Master/Design Model terms) stay verbatim; tested for the editor status. No hidden logic
change found in Scan Master, Design Model, export or reconstruction paths.

## Verdict
Source: PASS (CLAUDE_PEER_AUDITED_PASS for PL-0464 UI scope), with M1 recommended as follow-up.
macOS CI for 5bc8e64d: NOT_VERIFIED (infra failure, run in progress) - rerun before merge evidence.
