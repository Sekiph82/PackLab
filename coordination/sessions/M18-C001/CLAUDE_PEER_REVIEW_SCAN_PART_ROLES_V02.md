# CLAUDE_PEER_REVIEW V02 - PL-0482 scan part roles (Studio/core side), PR #29

- Reviewer: independent Claude peer reviewer (not the author; no source edits). This is a re-review against my own V01 (`CLAUDE_PEER_REVIEW_SCAN_PART_ROLES_V01.md`). It is not a builder or tester report.
- Delta reviewed: `eb19e976..3d84dd1e` (PR head confirmed `3d84dd1efc5438c142b1f596e66703971f1a8362` via `gh pr view`). 7 files, +175/-44.

## Tests run by this reviewer (offscreen, PackLab .venv, worktree sources)
- `tests/studio/test_scan_part_roles.py tests/packscan tests/transfer`: 192 passed.
- `tests/studio` (excluding `test_reconstruction_execution.py`, the same pre-existing subset import issue as in V01): 405 passed, 3 skipped.
- `ruff check` / `ruff format --check` on all 12 changed .py files: clean.
- `gh pr checks 29` at review time: Locked Python quality, iOS Simulator XCTest, Simulator E2E and device archive all PENDING; signing-material scan PASS. CI = NOT_VERIFIED.

## Disposition of V01 findings
- M1 (summary counted the whole shared inbox): RESOLVED. `capture_inbox.counted_role` now counts a scan only in two cases: the owner assigned or confirmed its role in this project (override), or it was built in this project (`latest_builds(layout.root)`) and its manifest declared a role (`role_declared`). Legacy role-less scans never count until the owner assigns them. With no project open, nothing counts. The header now reads "Parts in this project:" (TR: "Bu projedeki parçalar:"). Both the Capture Inbox and Build pages use the same scoping (`build_model.py:1032`). The tests cover foreign scans, built-but-undeclared scans, assignments, Turkish output, and the no-project and new-project GUI states.
- M2 (cross-platform contract): UNCHANGED, and still a rollout condition, not a defect of this PR. When the phone starts emitting `part_role`, the iOS mirror test `allowed` set (`PackLabCaptureTests.swift:1120`) must include it. The phone should omit the key for the default `assembled` role. Import reports now write `part_role: null` when the role is absent, which keeps "declared" distinct from "defaulted". Good.
- L1 (same-role re-pick added a new revision): RESOLVED, in both the UI (`_change_role` early return) and the manager (`set_scan_part_role` no-op when the role is unchanged and the stored map is clean). Re-picking the manifest's role on an unconfirmed scan still writes a revision, which is intended because it is now the "confirm for this project" action.
- L2 (unbounded event growth): RESOLVED for owner events. They are now compact (`package_sha256`, `previous_role`, `role`) and capped at 200 (test uses a monkeypatched cap of 3).
- L3 (tampered state): RESOLVED. `_valid_part_roles` drops malformed entries and counts them (`scan_part_roles_ignored`). The UI shows a plain-text status, and the next save drops the bad entries. There is a test for a bad digest, an unknown role and a non-dict value.

## New findings (delta)
### HIGH
None.
### MEDIUM
None.
### LOW
- N1 `project.py` `_step` (undo/redo, unchanged generic code) still appends `scan_part_role_events` entries in the old shape (`previous_revision_id`/`selected_revision_id` holding full maps), and outside the 200 cap. The event list therefore mixes two schemas, and undo/redo cycles grow it without bound. Audit-only data, never read back for behaviour. Recommend the compact shape and the cap for undo/redo too (follow-up acceptable).
- N2 `capture_inbox.inbox_row` tooltip shows `(manifest: assembled)` for legacy scans whose manifest declared nothing. Suggest `(manifest: not declared)` using `role_declared`. Cosmetic.
- N3 `_overrides()` is called on each refresh and in `_change_role`, so the "invalid scan role entries" status can overwrite a more recent status message. Cosmetic.

## Security re-check
No change to the trust boundary. The role is still enum-validated at the schema, report and project layers. It never reaches a path, and every new label or status uses `PlainText`. PASS.

## Verdict
PASS (source/diff/tests). The Studio/core side of PL-0482 is acceptable to merge once the pending CI is green. CI: NOT_VERIFIED (pending at review time); the coordinator must confirm the checks pass on `3d84dd1e` before merge. PL-0482 itself stays `[ ]` until the iPhone New Scan wizard side lands (plus the M2 mirror-test update).
