# Claude independent peer review: M18 PL-0414..PL-0418 (V01)

Date: 2026-11-10. Reviewer: independent Claude Code peer-review agent. I did not implement this work. Only this report was written; no source, test, tool, doc or `TASKS.md` file was edited. Nothing was committed, pushed, stashed or reset. All mutation and probe work ran on temp copies in the session scratchpad.

## Scope

- Commit under review: `08ed55e244f229cf61a770ef5491f0fc5ed8237a` ("feat(pl-0414..pl-0418): rescan decision tree, change processes, scan backup policy"). HEAD was this commit when the review ran.
- I read every changed file in full: `core/src/packlab_core/rescan_decision.py`, `tools/dev/scan_copy_manifest.py`, the five `docs/development/PL-0414..0418_*.md`, the three new tests, the doc-guard diff in `tests/ci/test_m18_station_sop_docs.py`, the frozen criteria `PL-0414..0418_VALIDATION_CRITERIA_V01.md`, and the implementation log.
- I also read the dependencies: `pre_reconstruction_qa.py` (component/status producer), `recapture_sector_suggestions.py` (decision values), `packaging_asset.py`, `packaging_sku_library.py`, `packaging_library_store.py` (for any deletion API), `packaging_library_backup.py`, and the PackScan `turntable` manifest contract (`docs/packscan/manifest-contract.md`).
- The workspace had unrelated pre-existing changes that were not made by me and that I did not touch: a staged deletion of `.github/workflows/_coordinator_pl0005_close.yml` and a modified `.gitignore`.

## Commands and results

| Command | Result |
| --- | --- |
| `pytest -q tests/ci/test_m18_station_sop_docs.py tests/core/test_m18_change_processes.py tests/core/test_rescan_decision.py tests/ci/test_scan_copy_manifest.py tests/studio/test_packaging_library_backup.py tests/core/test_packaging_sku_library.py tests/core/test_packaging_asset.py` (`QT_QPA_PLATFORM=offscreen`) | 130 passed |
| `ruff check core apps tools tests` | All checks passed |
| `mypy core apps tools` | Success: no issues found in 288 source files |
| Adversarial probe of `decide_rescan`: scratch `probe_rescan.py`, about 30 payloads, including real-producer turntable and missing-metadata reports | Findings F1–F4 and F6 |
| Contract probe of PL-0415/16/17 claims: scratch `probe_change.py` | Findings F8–F10 |
| Probe of `scan_copy_manifest`: scratch `probe_copy.py`, with real NTFS junctions created via `mklink /J` in the scratchpad | Findings F5 and F7 |
| Mutation run on a temp copy of `packlab_core`, with the pytest `pythonpath` overridden so the mutant was the module imported | See below |

Mutation results for `test_rescan_decision.py` plus the doc guards:

- (a) Removed `or recapture_decision == "unavailable"`: **survived.**
- (b) Swapped the `surface_treatment_review`/`targeted_recapture` order: killed, but only by the doc-table guard.
- (c) Dropped `pixel_exposure` from the retake check: **survived.** The dark-photo test also trips sharpness.
- (d) Disabled the rule that maps QA `coverage == warning` to `full_rescan`: **survived.** No test covers this rule.

One doc-guard failure that appeared in the mutant runs was an artefact of my override: a repo-relative schema lookup failed from the temp path. I confirmed it does not occur on the baseline.

## Findings

### P1

**F1. PL-0414: missing, unknown or contradictory evidence yields `proceed_to_reconstruction_review`.** The doc and frozen criterion 3 say "Missing evidence never yields proceed".

- Location: `core/src/packlab_core/rescan_decision.py:80-136`, and the doc claim at `docs/development/PL-0414_RESCAN_RECAPTURE_DECISION_TREE.md:29`.
- The rules only fire on specific status strings. Anything absent or unrecognised falls through to `proceed` at line 134. The probe returned primary `proceed_to_reconstruction_review` for all of these:
  - `components == {}`;
  - the `metadata_consistency` component missing, or the `coverage` component missing;
  - a component that is not a dict (e.g. `"sharpness": "garbage"`);
  - an unhandled status (`coverage: "failed"`, `metadata_consistency: "warning"`);
  - a recapture `decision` that is missing or unknown (`"garbage"`);
  - the `sharpness` component at `warning` while `photos == []`;
  - `qa_report.overall.status == "review_required"`, which is never read.
- Required fix: require each of the five known components to be present with a recognised status. Also require the recapture `decision` to be one of `{no_recapture_indicated, targeted_recapture, full_rescan, unavailable}`. Anything else, including a QA `overall.status` other than `no_automated_concern` with nothing fired, should map to `manual_review_insufficient_evidence` (or be rejected). Add tests for these cases.

**F2. PL-0414: every valid multi-frame turntable PackScan is routed to `full_rescan`.**

- Location: `rescan_decision.py:82-83`, and the doc claim at `PL-0414_...md:25` ("fewer views than declared").
- The producer (`pre_reconstruction_qa.py:440-474`) marks turntable `coverage` as `warning` whenever `frame_count != 1`. Its reason code is `manifest_records_one_turntable_frame_only`. PackScan 1.0 turntable manifests carry exactly one `frame_index`/`frame_count` per file (`tests/fixtures/packscan/manifest-valid-turntable.json`: 3 of 36).
- A clean, sharp, well-exposed 36-frame turntable report from the real producer therefore gives primary `full_rescan` ("Repeat the complete capture per PL-0400"). The warning here is structural; it is not a coverage shortfall. This would mislead an operator on every turntable capture.
- Required fix: map coverage `warning` to `full_rescan` only for `guided_orbit` with `observed_view_count < minimum_view_count`. Route the turntable single-frame warning to manual review or sequence-level assessment, correct the doc wording, and add a test.

**F5. PL-0418: `verify` returns `SCAN_COPY_VERIFY_PASS` for a "copy" that is an NTFS junction back to the source.**

- Location: `tools/dev/scan_copy_manifest.py:23-27`, and the claims at `PL-0418_SCAN_BACKUP_POLICY.md:37` and in the module docstring ("Symlinks are refused so a copy cannot silently point back at the source").
- On Python 3.12 on Windows, `Path.is_symlink()` is `False` for junctions, and `rglob` recurses through them. The copy root itself is never link-checked either.
- Probe results on this machine:
  - copy root = junction to source: PASS;
  - a real folder whose `captures/` is a junction to the source captures: PASS;
  - verifying the source folder itself: PASS. That last case is procedural, but worth stating in the SOP.
- The policy releases a physical sample for disposal on this PASS (`PL-0418_...md:41`), so a false PASS can cause irreversible data loss.
- The repo already has the right pattern: `packaging_library_backup._is_link_or_junction` (`packaging_library_backup.py:651-653`).
- Required fix:
  - Refuse links and junctions (preferably any reparse point, via `os.lstat(...).st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT`) on the root and on every entry.
  - Optionally refuse a copy root whose `resolve()` equals the manifest's source.
  - Add a junction test. There is currently no link test at all.

### P2

**F3. PL-0414: missing photo metadata produces primary `full_rescan` instead of a source/re-import action.**

- With the real producer and `metadata/photos.json` absent, `metadata_consistency` is `unavailable` and `records = []`. Guided-orbit `coverage` then becomes `warning` (0 < minimum).
- Result: primary `full_rescan`, with manual review second (`rescan_decision.py:80-83`). The photos may all exist; the operator is told to recapture the whole object rather than to fix or re-import the source.
- Required fix: treat metadata `unavailable` as rule 1, or suppress coverage-derived `full_rescan` when metadata is not `pass`.

**F4. PL-0414: QA warnings below the texture threshold are silently dropped.**

- Location: `rescan_decision.py:89-99` and `110-119`.
- With `object_surface_texture` at `warning` and 1 of 4 views low-texture, nothing fires and the result is `proceed`. The QA report's own `overall` says `review_required`.
- Retake only considers sharpness/exposure. A minority of low-texture views is neither retaken nor routed to review.
- Required fix: route sub-threshold texture warnings to `retake_flagged_photos` (by path) or to manual review, and document the behaviour below 50 %. This is closely tied to F1 (ignoring `overall`).

**F7. PL-0418: an empty or inconsistent manifest verifies as PASS.**

- Location: `scan_copy_manifest.py:48-64`.
- `create` on an empty folder (for example the wrong folder, or one not yet synced) gives `files: []`, and `verify` against any empty folder returns PASS.
- A manifest with `files: []` but `file_count: 2` also passes, because `file_count` and `total_bytes` are never cross-checked.
- Under the "release sample only after PASS" rule, this is a plausible operator-error path to a false release.
- Required fix:
  - Refuse to create a manifest with zero files.
  - Have `verify` reject `file_count == 0`.
  - Have `verify` check `file_count` and `total_bytes` against `files`.

### P3

- **F6. PL-0414 robustness and traceability.**
  - Non-JSON-safe input raises an unexpected `ValueError`/`TypeError` from `_digest` instead of `RescanDecisionError` (`rescan_decision.py:36-38`, 145): a NaN value, `bytes`, or a `MappingProxyType` payload.
  - Bool or inconsistent texture counts are accepted (`True/True`, or `low > assessed` giving a fraction of 9.0), as are counts that contradict a `pass` status (line 93).
  - `targeted_recapture` can be emitted with `sector_ids: []`.
  - The two input reports are each digest-bound, but they are not cross-bound to the same capture. QA `capture_id` is never compared with the recapture source.
  - Test gaps: mutants (a), (c) and (d) survive.
- **F8. PL-0415.**
  - The doc calls `validate_targets` "the intended guard" against deleting an old asset revision (`PL-0415_...md:19`). Nothing refuses deletion, and there is no asset-revision store or deletion API. A retained SKU revision is flagged only if a caller re-runs `validate_targets` with the current registry; `shelf_lineup.py:82` is the only app caller.
  - `catalog.with_revision` accepts a migration whose `assets` registry omits the old revision.
  - The doc should state that retention is a procedural control, with detection on re-validation. This matches criterion 4's "or flagged", so it does not block.
  - `SUPPLIER_FACT` for supplier fields is procedural only: `USER_DECLARED` is accepted by `with_field_update`.
  - The test name `..._reusing_verified_geometry` contradicts the unverified-geometry semantics.
  - Not covered by the doc: re-adding an identical earlier SKU revision (a rollback) fails with `packaging_sku_revision_duplicate`.
- **F9. PL-0416.**
  - The contract does not bind an artwork reference's `label_zone_design_model_revision_id` to the SKU's asset `design_model_links`. The dry-run itself pins a zone from an unrelated design model (`design-model:04d33a…`) to an asset whose only model is `design-scan-1`, and it is accepted.
  - The doc text "Map it to the existing Label Zone placement already used by the SKU" (`PL-0416_...md:13`) is therefore reviewer-enforced only, and should say so.
  - `asset.revision_id == _baseline().revision_id` is a tautology, not evidence that the asset was untouched. Immutability comes from the frozen dataclass.
- **F10. PL-0417.** `with_source_links` accepts a mixed lineage: a new Scan Master `scan-2` with the old Design Model whose parent is `scan-1`. Steps 3 and 4 and the no-go "reusing old geometry" (`PL-0417_...md:13-14`) are procedural, not contract-enforced. The doc should say so; a later contract check would also be valuable.
- **F11. PL-0418.**
  - Malformed manifest entries crash with an uncaught `TypeError`/`KeyError` instead of `manifest_invalid` (`scan_copy_manifest.py:53`). This fails closed (exit code is not 0), so it is low risk.
  - Empty directories are not recorded.
  - Case-only renames and traversal entries in the manifest fail safely, because manifest paths are only compared and never opened.

## Verified true

- **PL-0418 / `PackagingLibraryBackupService`:**
  - `_MAX_ARCHIVE_BYTES == 512 MiB` and `_CONTRACT == "packlab.packaging-library-backup.v1"`.
  - The inventory allow-list is `records/attachments/thumbnails` plus the state and lock files, so raw captures are excluded.
  - `create_backup`, `validate_backup` and `restore` (empty destination only) exist as the doc describes.
  - Streaming SHA-256 (1 MiB chunks) and the refusal to overwrite an existing manifest both work.
  - Missing, extra and bit-flipped files fail.
- **PL-0415:** a supplier change gives a new `packaging-asset:<sha256>` with the same `asset_id` and identical Scan Master and Design Model links. The old revision's supplier facts stay readable. The certification, accuracy and manufacturing flags are hard-coded `False`. Old and migrated SKU revisions coexist in history, and current lookup moves to the migrated one.
- **PL-0416:** an artwork-only change keeps the identical `packaging_asset_revision_id`, with `geometry_copied: false`. A missing artwork target is rejected, and intra-set zone/mapping/assignment mismatch is rejected by `from_accepted_assignment`.
- **PL-0417:**
  - A SKU never moves implicitly, because it is pinned to an exact asset revision.
  - A move to a different `asset_id` is rejected (`packaging_sku_geometry_identity_change_forbidden`).
  - Link classes reject any scale other than `RELATIVE`/`METRIC_UNVERIFIED`, and reject `mold_use_authorized=True`.
- **PL-0414:**
  - The output is deterministic, and the QA digest equals the producer's `PreReconstructionQAReport.sha256`.
  - The doc table matches the `ACTIONS` order, and the 50 % threshold matches.
  - The eight dry-run scenarios in the doc match the tests.
  - The output carries an advisory authority and a claim limit, and the function never mutates its input.
- **Overclaims:** all five docs are labelled planning drafts and keep the Kenya, site, supplier, storage, physical, PL-0401 and PL-0412 gates pending. Retry count, cadence and tolerances are labelled as planning values. No secrets or private data were found. The CI overclaim guard covers the new docs.

## Per-task verdicts

| Task | Verdict | Basis |
| --- | --- | --- |
| PL-0414 | **CHANGES_REQUIRED** | F1 (P1) contradicts criterion 3 and the doc. F2 (P1) gives a misleading primary action for every turntable capture. F3 and F4 (P2). Test gaps (F6). |
| PL-0415 | **PASS** (CLAUDE_PEER_AUDITED_PASS-eligible) | Criteria 1–5 met on the real contracts. F8 is a doc-precision note (P3). |
| PL-0416 | **PASS** (CLAUDE_PEER_AUDITED_PASS-eligible) | Criteria 1–5 met. F9: state that zone-to-asset binding is a reviewer check (P3). |
| PL-0417 | **PASS** (CLAUDE_PEER_AUDITED_PASS-eligible) | Criteria 1–5 met. F10: state that lineage coherence is a reviewer check (P3). |
| PL-0418 | **CHANGES_REQUIRED** | F5 (P1): a junction false PASS can authorise sample disposal. F7 (P2): an empty or inconsistent manifest gives PASS. The policy text and backup-service claims are otherwise accurate. |

Regardless of these verdicts, real factory execution, Kenya site use, supplier, mould and storage evidence, threshold and cadence calibration, and PL-0412 real backup/restore all stay pending. Nothing in this commit, and no PASS above, is physical or factory validation.
