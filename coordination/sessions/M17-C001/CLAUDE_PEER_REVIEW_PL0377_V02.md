# CLAUDE_PEER_REVIEW — PL-0377 transparent PET (V02) + macOS XCTest count guard

Reviewer: independent Claude Code reviewer subagent (did not author the change). Date: 2026-11-11.
Scope: commit `77ee6730` (tests/core/test_pl0377_transparent_pet.py, implementation log V02, `.github/workflows/packlab-capture-macos.yml`), plus the Swift PackScanWriter limits and the XCTest added in `4862ec95`.
These are the reviewer's own findings. They are separate from the builder log `CLAUDE_IMPLEMENTATION_LOG_PL0377_V02.md`.

## Evidence I gathered
- `pytest tests/core/test_pl0377_transparent_pet.py test_object_surface_texture_qa.py test_rescan_decision.py test_reconstruction_anomaly.py`: 66 passed (the new file has 6 tests).
- `ruff check core apps tools tests`: clean. `ruff format --check` on the new file: clean. `mypy core apps tools`: no issues in 290 files.
- Mutation testing on a `git archive HEAD` copy in a temp dir. pytest `pythonpath=core/src` would shadow a PYTHONPATH override, so the full-tree copy was needed. All 7 mutants were killed:
  - M1: low-texture warning disabled. 2 failures.
  - M2: anomaly detector ignores boundary edges. 2 failures.
  - M3: no `surface_treatment_review` routing. 2 failures.
  - M4: the decision always proceeds. 2 failures.
  - M5: physical status changed to VALIDATED. 2 failures.
  - M6: test-side dropout made a no-op. 2 failures.
  - M7: test-side dropout removes all faces. 2 failures.
- Probe results:
  - Clear-PET textured-cell fraction: jar 0.00051, sachet 0.00034. Both route to `surface_treatment_review` as the primary action.
  - Intact meshes have 0 boundary edges. After dropout, the jar has 98 and the sachet has 22, which matches the builder log.
  - Jar intact mesh: `NO_RULE_TRIGGERED_DIAGNOSTIC_ONLY`. Jar after dropout: `REVIEW_REQUIRED [mesh_boundary_edges_present]`.
- Swift: `git grep "func test"` gives 205 XCTests at `4862ec95~1`, 206 at `4862ec95` and 206 at HEAD.
  - macOS run 42908906107 failed with: `result=Passed, total=206, expected=205, failed=0`.
  - That run passed both PL-0113 transparent XCTests.

## Criteria
1. **Deterministic warning: MET.** Test lines 97-110 check the low-texture warning, `review_required`, and `surface_treatment_review` routing. The test also checks determinism by running the QA twice. Mutants M1, M3 and M4 kill it.
2. **Incomplete reconstruction not represented as complete: MET.**
   - Line 122 is a closed-mesh control.
   - Line 132 checks the boundary-edge code. Line 134 checks `DEFERRED_OWNER_VALIDATION`. Line 135 checks mould use is not authorized. Line 137 checks scale stays RELATIVE.
   - Mutants M2, M5 and M6 kill it.
3. **Simulated authority: MET.** Lines 86-93 check the manifest's `pet_clear` finish, transmission > 0, the "not measured" warning, `synthetic`, and "no physical" authority. The module docstring labels the dropout as a SIMULATION.
4. **Deferred execution: N/A.** Tests do run.

## Findings
### P0 / P1 / P2
None.

### P3
- `tests/core/test_pl0377_transparent_pet.py:109`: `primary_action != "proceed_to_reconstruction_review"` is always true in this test.
  - `decide_rescan` is called without a recapture report, so it always adds `manual_review_insufficient_evidence/recapture_evidence_missing_or_unknown`.
  - Proceed is only added when nothing else triggered (`core/src/packlab_core/rescan_decision.py:209-211`).
  - The surface-treatment assertion on line 110 is what actually discriminates.
- `tests/core/test_pl0377_transparent_pet.py:131`: for `syn_sachet_pet_clear_v01`, the intact mesh is already `REVIEW_REQUIRED` because of `mesh_disconnected_components`, so the status assertion does not discriminate for the sachet.
  - The boundary-edge code check (line 132) together with the closed-mesh control (line 122) does make the test meaningful.
  - Optional hardening: run the detector on the intact mesh and assert `mesh_boundary_edges_present` is absent.
- `coordination/sessions/M17-C001/CLAUDE_IMPLEMENTATION_LOG_PL0377_V02.md:13`: "seeded" is inaccurate. The dropout is a deterministic geometric window (`test_pl0377_transparent_pet.py:55-70`) with no RNG. This is a wording issue only.
- Criterion 1 is met through the generic low-texture path, which matte HDPE also triggers (PL-0375). There is no transparency-specific detector in core.
  - The idealized shader shows about 0 specular cells, so the clear PET reads as featureless rather than as refractive.
  - The docstring is honest about this. Transparency-specific UX is covered by the iOS PL-0113 XCTests.
- Swift `PackLabCaptureTests.swift` `testPackScanWriterRejectsPythonIncompatiblePaths`:
  - It asserts only that something is thrown, not which error.
  - The new `resourceLimit` branches (entry count, entry bytes, control bytes, expanded total, package size) have no XCTest.
  - `PackScanWriter.swift` `validateManifest` reports a declared `size_bytes` over the limit as `schemaInvalid`, not `resourceLimit`. It still fails closed.

## macOS count guard (`.github/workflows/packlab-capture-macos.yml:25,575`)
**Verdict: PASS (correct fix).**
- The 205→206 change matches the source test count and the failed-run summary.
- Only the `all` group changed, which is correct because the new test belongs to no focused family.
- The remaining "205" mentions are dated historical docs.

### Swift PackScanWriter limits from `4862ec95`
Codex stash work, applied via a merge commit.
- The limits match `core/src/packlab_core/packscan/container.py:44-49,88,97`:
  - 512 MiB package and expanded total; 1024 entries; 64 MiB per entry.
  - 4 MiB for manifest, checksums and photos.json.
  - 1024 code points per path (Python `len` matches Swift `unicodeScalars.count`); 4096 UTF-8 bytes; control characters below 0x20 rejected.
- Swift additionally rejects `:` anywhere. A writer being stricter than the reader is safe.
- The overflow-checked additions are correct.
- No caller switches exhaustively on `PackScanWriterError`, and the app has no ProRAW/DNG capture path that 64 MiB per entry would block.
- Risk: low. The changes only fail packages early that the Python importer would reject anyway.

## Hosted CI for 77ee6730 (read-only)
At review time:
- Signing Material Guard 43040239977: success.
- PackLab Capture macOS CI 43040241013: in_progress.
- Windows Python Quality 43040240021: in_progress.

## Verdicts
- **PL-0377: PASS** for source and tests within synthetic scope, so it is CLAUDE_PEER_AUDITED_PASS-eligible. Acceptance is conditional on both in-progress hosted runs finishing with success. The macOS run supersedes `EXTERNAL_PENDING_MACOS_XCTEST` only if it reports 206/206 passed.
- Physical optics, real clear-PET photos and factory validation remain pending. This review claims none of them.
- **CI count fix: PASS.**
