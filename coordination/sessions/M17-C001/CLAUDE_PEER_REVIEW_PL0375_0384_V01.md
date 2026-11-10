---
coordinationSchema: packlab-coordination/v1
artifactType: claude-peer-review
cycleId: M17-C001
version: 01
actor: CLAUDE_INDEPENDENT_REVIEWER
reviewedCommit: 0dec41b63d0dc18d16f33f7de44857dda9da0603
tasks: [PL-0375, PL-0376, PL-0377, PL-0378, PL-0379, PL-0380, PL-0381, PL-0382, PL-0383, PL-0384]
---

# Independent peer review: M17 failure-behavior sprint PL-0375..PL-0384

I did not implement any of this work. I reviewed the local tree at `0dec41b6`. That commit is one ahead of `origin/main` (`29dd985a`) and has not been pushed. I edited no source, tests or tracker. Earlier `CLAUDE_*PL0375-0384_BATCH*` and `CLAUDE_PEER_REVIEW_PL0369/PL0370-0374_BATCH` verdicts were ignored. Frozen criteria used: PL-0375..0378 V01, PL-0379 V02, PL-0380 V01, PL-0381 V03, PL-0382 V01, PL-0383 V02, PL-0384 V01.

## Commands and evidence

```
QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest tests/core/test_pre_reconstruction_qa.py \
  tests/core/test_recapture_sector_suggestions.py tests/packscan tests/transfer tests/studio/test_recovery.py \
  tests/studio/test_project.py tests/studio/test_project_revision.py tests/studio/test_project_migration.py \
  tests/core/test_engine_probe.py tests/core/test_reconstruction_orchestrator.py -q -p no:cacheprovider
-> 199 passed, 2 warnings in 9.47s   (Python 3.12.10)

.venv/Scripts/python.exe -m ruff check core apps tools tests        -> All checks passed!
  (`ruff check .` reports 2 errors in preview/windows/packlab_preview.py, which is outside the CI scope and unrelated)
ruff format --check --config "format.line-ending = 'auto'" <5 changed files>  -> 5 files already formatted
.venv/Scripts/python.exe -m mypy core apps tools                     -> Success: no issues found in 285 source files

gh run list --workflow windows-python-quality.yml --limit 3
  42854695278  29dd985a  failure  -> "2 failed, 2588 passed, 16 skipped"; the failures are
     tests/core/test_blender_label_render_overlay.py::test_dieline_artwork_and_product_mockup_binding_share_authority
     tests/core/test_packaging_sku_library.py::test_povu_sku_variants_reuse_one_immutable_package_geometry_revision
     Neither belongs to PL-0375..0384. All in-scope modules passed in hosted CI at 29dd985a.
  42854449622 / 42854034592  cancelled (superseded).
  0dec41b6 (PL-0384) has no hosted run because it is local-only.
```

Independent probes (scratch scripts under `%TEMP%\m17probe`, nothing written to the repo):

- **PL-0379 mutation test.** I set `MAX_JSON_NESTING_DEPTH = 10**9`. The `deep` case then returns `schema_invalid` and `deep_object` returns `unsupported_version`, so the test fails without the limit. With the limit both return `corrupt_manifest`, and a 64-deep object passes the depth gate. A manifest about 4 MB deep (`[`*2e6) returns `corrupt_manifest` through RecursionError, with no crash. The test passes for the right reason.
- **c7ffa5db revert.** The current test again has the balanced 1,100-deep list, the 5,000-digit int, and both the dotted and undotted 5,000-digit versions. The weakening is gone.
- **PL-0384 provenance.** I extracted all 25 `packlab_studio/*.py` files from `109138a9^` into a scratch package and ran `new_project` + `commit_edit` with `python -I`. After normalizing UUIDs and timestamps, the output `.packlab-layout.json`, `working/project.json` and `working/state.json` are byte-identical to the fixture (`od -c` diff empty). Both have revision 1, no `authority.json`, and the same 8 directories. `git log -S authority.json` shows `109138a9` is the commit that introduced the authority file. The predecessor format is genuinely historical.
- **PL-0380 probes.** See P1-1 below.

## Findings

### P0
None.

### P1
- **P1-1 (PL-0380): resume is not bound to job, workspace or project identity.** See `core/src/packlab_core/reconstruction_orchestrator.py:126` (`StageCheckpoint`) and `:447-490` (`_validated_resume_prefix`). A checkpoint is bound only to `configuration_digest` and `source_digest`. Neither digest includes `workspace`, `job_id`, `project_id` or `project_revision` (`configuration_digest` covers job/orchestration/stage configuration and backend provenance only). What I reproduced:
  - Checkpoints saved from `working/reconstruction/r1` resume a request for `working/reconstruction/r2`. The run returns SUCCEEDED, and its manifest says `reconstruction_revision='r2'` while `asset_paths['feature-extraction:primary']` is `working/reconstruction/r1/feature-extraction/output` (`:418-425`).
  - A request with a different `job_id` is accepted.
  - A request for a different project (`project-2`, revision 99, workspace r9) is accepted, and the published manifest for project-2 points at project-1's r1 artifacts.

  The checkpoint also carries no artifact content digest. "Stale artifact / wrong digest" detection therefore rests entirely on the caller's `verify_checkpoint`, which receives only the checkpoint and has nothing stored to compare against. Every test verifier is a stub that always returns True. Taken together, this breaks traceability (one revision's manifest references another revision's or project's artifacts) and does not show that "completed immutable artifacts" are preserved (criterion 2).

  Required:
  - Bind checkpoints to `job_id`/`project_id`/`project_revision`/`workspace`.
  - Reject output asset IDs that are not under `request.workspace`.
  - Store per-output content digests in the checkpoint.
  - Add negative tests: cross-workspace, cross-job and cross-project checkpoints, and a verifier that rejects a modified artifact on disk.

### P2
- **P2-1 (PL-0380).** Cancellation combined with resume is not tested. My probe shows correct behavior: the result is CANCELLED with no output, the reused prefix appears in `stage_results`, and the next stage is CANCELLED. Add a regression test for it. Checkpoints are in-memory objects with no serialization and no Studio persistence (the implementation log admits this), so resume after a real process crash is not yet possible. Keep that limit explicit.
- **P2-2 (PL-0375).** `tests/core/test_pre_reconstruction_qa.py:190-203` uses an 8x8 constant-248 array.
  - Because 248 > 239, the "low texture" case is also a clipping case.
  - In my probe, a white surface with ±5 sensor noise (values 215–225, seeded) gives `sharpness = pass` (value 325.45). The overall `review_required` then comes only from the exposure warning. Realistic noise defeats the low-texture signal, and the noise-free fixture hides this.
  - There is no physically plausible fixture, no metric ground truth, no camera/lighting/surface provenance and no simulation label, all of which the contract requires. There is no negative (textured, should-pass) case, and the M17 synthetic dataset (`docs/datasets/M17_DATASET_CATALOG.md`) is not used.
- **P2-3 (PL-0376).** `tests/core/test_pre_reconstruction_qa.py:205-217` is the same kind of fixture: 100 hand-chosen luminance bytes. Criteria 1–2 are met only at the threshold level. The contract's requirements for provenance, labeled synthetic benchmark data and negative cases are not met.
- **P2-4 (PL-0377).**
  - The only evidence is the pre-existing PL-0113 XCTests (`apps/ios-capture/PackLabCaptureTests/PackLabCaptureTests.swift:2926-2955`), which evaluate the transparent preset and treatment acknowledgement.
  - There is no clear-PET fixture, and nothing tests criterion 2 ("incomplete/ambiguous reconstruction not represented as complete geometry"). No PL-0377-specific assertion was added.
  - The tests cannot be run on Windows.
- **P2-5 (PL-0378).** `tests/core/test_recapture_sector_suggestions.py:104-136` has two gaps:
  - **Criterion 2 is not shown.** The fixture occupies 1 of 24 sectors. The 6 suggestions are just the first six azimuth indices at elevation band 2, all tied at a 150° gap, so "points into the absent sector" holds trivially. No synthetic pose layout with a designed known-missing sector is checked against the suggested `sector_id`s.
  - **Criterion 3 is not asserted.** No test checks that the occupied sector is excluded from the suggestions.
- **P2-6 (consumer of validated PackScan payloads, relevant to PL-0375/0376).** `core/src/packlab_core/pre_reconstruction_qa.py:148-151` catches only `UnicodeDecodeError`/`JSONDecodeError` around `json.loads(metadata/photos.json)`. A `photos.json` holding a 5,000-digit integer raises an uncaught `ValueError`, and one 200k levels deep raises an uncaught `RecursionError` (reproduced). PL-0379's depth limit protects only manifest and checksums. Recommended fix: route `photos.json` through the same bounded reader, or catch `ValueError`/`RecursionError`. This is not a PL-0379 blocker because `photos.json` is not parsed on the import path.

### P3
- PL-0379: no test forges a central-directory `file_size` smaller than the actual stream, which is what exercises the "actual bytes while streaming" branch (`container.py` "ZIP entry length differs"). `zipfile` already caps reads at `file_size`, so this is defense-in-depth.
- PL-0379: `quarantine.py:63` parses the manifest for `capture_id` without the depth limit. RecursionError is a RuntimeError and is caught, and the result only extracts a ≤128-char string, so the risk is acceptable.
- PL-0379 security review of the ZIP64 reorder: it changes only which error code is reported. ZIP64 sentinels and multi-disk layouts both still fail closed before `ZipFile`. A ZIP64 locator cannot be smuggled into the central-directory tail: the CD must end exactly at the EOCD, extra fields must be 0, and names reject control bytes, so the `PK\x06\x07` signature cannot appear. The post-`ZipFile` `len(infos)` cross-check remains. The depth walk is iterative and O(n) over at most 4 MiB. No bypass or DoS found.
- PL-0381: the temp-file assertions (`tests/studio/test_project_revision.py:54,73,115`) glob only `.authority.json-*.tmp`. Glob `.*.tmp` to cover the state/project mirror temps as well.
- PL-0382: no test covers a truncated `authority.json` or a leftover `.authority.json-*.tmp` after a crash. My probe shows the truncated authority is rejected (`project cannot be opened`) with its bytes preserved. The leftover temp is ignored but never cleaned. A regression test is worth adding.
- PL-0383: `tests/core/test_engine_probe.py:50-59` (`test_wrong_colmap_argv_fails_the_fixture`) exercises only the test's own lambda, not production code. It is vacuous but harmless.
- PL-0384: the fail-closed tests do not match on the error message, so a failure for the wrong reason would still pass. My probe confirms the reasons are correct today: future schema gives "metadata malformed or unsupported", future authority 99 gives "authority malformed or unsupported", which differs from the message for authority v1 with empty metadata. 0dec41b6 is local-only, so hosted CI evidence is pending a push.

## Per-task verdicts

| Task | Verdict | Basis |
|---|---|---|
| PL-0375 | **CHANGES_REQUIRED** | P2-2, P2-6 |
| PL-0376 | **CHANGES_REQUIRED** | P2-3, P2-6 |
| PL-0377 | **CHANGES_REQUIRED** (after the fix, still EXTERNAL_PENDING_MACOS_XCTEST) | P2-4 |
| PL-0378 | **CHANGES_REQUIRED** | P2-5 |
| PL-0379 | **CLAUDE_PEER_AUDITED_PASS** | V02 criteria 1–8 covered by tests in `tests/packscan/test_container.py` and `tests/transfer/test_ingest_controller.py`; depth limit mutation-verified; hosted CI green for these modules at 29dd985a; P3 only |
| PL-0380 | **CHANGES_REQUIRED** | P1-1, P2-1 |
| PL-0381 | **CLAUDE_PEER_AUDITED_PASS** | V03 1–5: OSError/RuntimeError and bool/-1/1.5/None providers fail closed before publish, with authority/state/revision/raw bytes preserved; zero-space, ENOSPC and mirror-repair tests present; P3 only |
| PL-0382 | **CLAUDE_PEER_AUDITED_PASS** | Interrupted-commit mirror repair, corrupt/future metadata rejection without rewrite, checkpoint digest mismatch reported INVALID; tmp_path only; P3 only |
| PL-0383 | **CLAUDE_PEER_AUDITED_PASS** | POSIX chmod gate, Windows-neutral setup, and missing/invalid/unsupported/valid/nonzero/unexecutable diagnostics covered with injected runners; no engine executed; P3 only |
| PL-0384 | **CLAUDE_PEER_AUDITED_PASS** | Historical predecessor verified by regeneration; read-only open, deterministic migration (pinned clock, byte-identical), future/malformed inputs fail closed without overwrite; 6 tests pass locally; P3 note that hosted CI is pending a push |

None of these verdicts claims physical, factory, iPhone or real-engine validation.
