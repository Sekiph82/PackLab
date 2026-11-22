# CLAUDE_PEER_REVIEW - PL-0482 scan part roles (Studio/core side), PR #29

- Reviewer: independent Claude peer reviewer (did not author the change; no source edits).
- Scope: `origin/feat/scan-part-roles` head `eb19e976` vs merge-base `72578f30` (origin/main), read-only worktree `PackLab-wt-roles`. 15 files, +536/-14.
- Read: TASKS.md PL-0482..PL-0489, full diff, `project.py` undo/redo (`_record_selection`, `_plan`, `_step`, `commit_edit`, `_read_authority`), `container._validate_manifest`, `import_report`, `receiver_session`, iOS `SessionGalleryStore.packScanManifest` and its mirror test, `tools/ci/ios_e2e_receiver.py`.

## Tests run by this reviewer (QT_QPA_PLATFORM=offscreen, PackLab .venv; pytest pythonpath -> worktree sources)
- `tests/studio/test_scan_part_roles.py tests/packscan tests/transfer`: 190 passed.
- `tests/studio` (excluding `test_reconstruction_execution.py`, which fails at collection with `ModuleNotFoundError: test_reconstruction_orchestrator` when run as a subset - sibling-import of a test module, unrelated to this diff): 403 passed, 3 skipped.
- `ruff check` + `ruff format --check` on the 12 changed .py files: clean.
- GitHub checks on PR #29 at review time: Python quality, iOS Simulator XCTest/E2E, device archive PENDING; signing-material scan PASS. CI = NOT_VERIFIED.

## Security of untrusted phone input
- `part_role` is enum-validated by the canonical schema (`schemas/packscan/manifest.schema.json`) inside `_validate_manifest` before `build_import_report` reads it; `manifest_part_role` re-checks and raises. Import report reading (`receiver_session.py`) re-validates with `is_part_role`, falling back to `assembled`. Project overrides are filtered on read (`scan_part_roles`: 64-hex digest + enum) and rejected on write (`set_scan_part_role`).
- Role never reaches a filesystem path. Row text is a `QListWidgetItem` (plain); tooltip lines are `html.escape`d; both new `parts_label`s and `status_label` are `PlainText`. No rich-text sink found. PASS.

## Findings

### HIGH
None.

### MEDIUM
- M1 `apps/windows-studio/src/packlab_studio/capture_inbox.py` `parts_summary_text` / `build_model.py` `refresh_history` / `shell.py:691`: the "Parts: ... present/missing" summary counts every imported scan in the global receiver inbox, not the open project's scans. PL-0482 says "Studio shows which of the six are still missing" (per project). With two packages in the inbox, a jar body scan can mark a bottle project's Body as present; with no project open the summary still claims completeness. The project has no scan-membership record today (only overrides keyed by digest and `latest_builds` per project), so this is a known ceiling, but it is shown to the owner as fact. Required before PL-0482 is checked: either scope to scans associated with the project (e.g. scans with an override or a build in this project) or label the line explicitly as "all received scans" and track scoping under PL-0485. Also every pre-PL-0482 scan defaults to `assembled`, so legacy inboxes report "Assembled: upright present" from unrelated packages.
- M2 Cross-platform contract not yet aligned (not a defect of this PR, a merge/rollout condition): `apps/ios-capture/PackLabCaptureTests/PackLabCaptureTests.swift:1120` mirrors the manifest schema with `allowed = required ∪ {started_at, ended_at, calibration_profile_ref}`; it must gain `part_role` when the phone starts emitting it, or the XCTest fails. Studio builds older than this PR reject any manifest containing `part_role` (`additionalProperties: false`) with `schema_invalid`. A `schema_version` bump is NOT recommended: old Studio rejects any non-1.0.0 version anyway (`container.py:162`), so a bump gives no compatibility, only forces multi-version support in new Studio. Recommended mitigation instead: the phone omits `part_role` when the role is `assembled` (keeps legacy-Studio compatibility for the default case) and the release notes state the minimum Studio version. The macOS E2E receiver (`tools/ci/ios_e2e_receiver.py`) only validates/counts and is unaffected now.

### LOW
- L1 `capture_inbox.py` `_change_role`: `activated` fires even when the owner re-picks the manifest's own role; with no override present this writes a new project revision + history entry whose effective role is unchanged. Harmless but noisy; compare against `effective_role` before saving.
- L2 `project.py` `set_scan_part_role`: each event stores the whole map twice (`previous_revision_id`/`selected_revision_id`), so state.json grows O(scans x edits); field names say "revision_id" but hold dicts (consistent with the generic undo mechanism, so acceptable). Tampered non-conforming entries in the stored map are preserved on merge (filtered on read, so not exploitable).
- L3 Test gaps: no test that tampered `authority.json` (`scan_part_roles` with non-hex digest / unknown role / non-dict) is filtered by `scan_part_roles()`; no assertion that tooltip HTML is escaped for a hostile `device_model`; no test of the project-scoping semantics in M1. Existing tests are not tautological: they exercise real `write_packscan` -> `import_file` -> report -> `entries()`, schema enum parity, negative roles (`lid`, `Body`, `""`, `None`, `3`), revision no-op, undo/redo across reopen, GUI combo -> project -> both pages -> undo redraw, and Turkish output.
- L4 i18n: 15 Turkish keys added, no duplicate keys in `TURKISH`; generic keys (`present`, `missing`, `Body`) are not used elsewhere via `tr()`, so no collateral translation changes. Combo labels are fixed at construction (same as the rest of the app; language applies on restart).

## Migration / authority
- Existing projects: `scan_part_roles` absent -> `{}`; existing import reports without `part_role` -> `assembled`; existing manifests unaffected (field optional, not in `required`). No Scan Master / Design Model authority, metric or provenance paths touched. Undo of the first assignment restores `None`, which reads back as `{}` (verified by test and code).

## Verdict
CHANGES_REQUIRED (M1 before PL-0482 can be checked; M2 is a tracked condition for the iPhone side). Code quality, input validation and undo/redo of the Studio/core side are otherwise sound and could merge as an incremental step if M1 is labelled honestly. PL-0482 must remain `[ ]` regardless: the iPhone New Scan wizard part is not in this PR. CI: NOT_VERIFIED (pending at review time).
