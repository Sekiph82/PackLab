---
coordinationSchema: packlab-coordination/v1
artifactType: claude-peer-review
cycleId: M17-C001
version: 02
actor: CLAUDE_INDEPENDENT_REVIEWER
reviewedCommit: c62220f2bdb730a13d879218a607e6300890df59
supersedes: CLAUDE_PEER_REVIEW_PL0375_0384_V01.md (PL-0380 and P2-6 only; other V01 verdicts unchanged)
tasks: [PL-0380, PL-0375, PL-0376]
---

# Independent peer re-review V02: PL-0380 P1 fix and pre_reconstruction_qa P2-6

This review covers commit `c62220f2`. The local tree equals `origin/main` (`c62220f2`). I made no edits to source, tests or the tracker.

## Commands and evidence

```
QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest tests/core/test_reconstruction_orchestrator.py \
  tests/core/test_pre_reconstruction_qa.py -q -p no:cacheprovider     -> 28 passed in 0.68s
ruff check core apps tools tests                                      -> All checks passed!
ruff format --check --config "format.line-ending = 'auto'" (4 changed files) -> 4 files already formatted
mypy core apps tools                                                  -> Success: no issues found in 285 source files
```

I rewrote my own V01 reproduction for the new API (`%TEMP%\m17probe\probe_0380_v2.py`). It uses real files and the test module's `_hasher`, and its first run is interrupted at stage 3:

| Case | HEAD result |
|---|---|
| same request | SUCCEEDED, output present |
| cross-workspace r1 → r2 (V01: accepted) | REJECTED: different job, workspace or input |
| cross-job (V01: accepted) | REJECTED: binding |
| cross-project, project-2, revision 99, workspace r9 (V01: accepted) | REJECTED: binding |
| forged `request_binding` recomputed for r2, r1 asset paths kept | REJECTED: outputs outside the workspace |
| prefix collision: workspace `working/reconstruction/r`, assets in `.../r1/` | REJECTED: outside the workspace (`+ "/"` separator holds) |
| artifact bytes tampered after checkpoint | REJECTED: missing or changed since the stage finished |
| artifact deleted | REJECTED: cannot be hashed (FileNotFoundError) |
| digest function returns non-hex | REJECTED: must be a lowercase SHA-256 digest |
| recorded `output_sha256` swapped | REJECTED: changed since the stage finished |
| `artifact_digest=None` with `resume_from` | REJECTED: checkpoints require an artifact_digest function |
| pre-cancelled token + valid resume | CANCELLED, no output |

P2-6 re-probe (`probe_qa.py`): a 5,000-digit integer in `photos.json` and one nested 200k levels deep now give `review_required` instead of an uncaught ValueError/RecursionError. The new parametrized test asserts the component status is `failed` with reason `photo_metadata_malformed_json`.

## Source review (c62220f2)

- `checkpoint_binding(request)` (`reconstruction_orchestrator.py`) hashes workspace, job_id, project_id, project_revision, configuration_digest and source_digest under the contract tag.
  - Resume requires an exact binding match.
  - Every output asset must be under `request.workspace + "/"`.
  - Recomputed per-output SHA-256 values must equal the digests the orchestrator recorded right after the stage returned. These are computed by the orchestrator, not supplied by the caller.
- During a fresh run, a stage whose outputs cannot be hashed becomes FAILED with no output. That avoids emitting an unverifiable checkpoint.
- The always-True `verify_checkpoint` stubs were removed. All six identity variants are parametrized, and changed, missing and out-of-workspace outputs are tested with real files.
- **Residual (P3).** The checkpoint object is still caller-held and unauthenticated. A forger can recompute the public binding, but cannot pass outputs from outside the workspace or with changed content, so the risk is limited to same-workspace files with matching hashes. The `execution.payload` of reused stages is trusted as recorded. Resume across a real process crash still needs checkpoint serialization and Studio persistence, a limit the implementation log already discloses.
- **Residual (P3, down from V01 P2-1).** No test covers pre-cancelled resume. I verified the behavior twice (V01 and V02 probes), so this is a coverage gap only.
- `pre_reconstruction_qa.py:150`: `except (UnicodeDecodeError, ValueError, RecursionError)`. `JSONDecodeError` is a `ValueError` subclass, so nothing that was caught before is lost.

## Noted, out of scope

`f0d04897` changes two pre-existing assertions so they match current behavior. In `test_blender_label_render_overlay.py`, the exported `source_dieline_revision_id` is now expected to equal the print-intent revision, with the dieline linked through `print_intent`. In `test_packaging_sku_library.py`, the keys are now nested under `geometry_reference`. These are semantic expectation changes in other tasks' tests. They need their own reviewer before those tasks are accepted, and they do not affect this verdict.

## Hosted CI

Run 42857124635 (head `c62220f2`): **completed / success**. Its log shows "All checks passed!" and "2605 passed, 16 skipped, 1 deselected, 2 warnings in 178.88s". This is the first green Windows Python Quality run covering the M17 modules.

## Verdicts (V02)

| Task | V01 | V02 |
|---|---|---|
| PL-0380 | CHANGES_REQUIRED (P1-1) | **CLAUDE_PEER_AUDITED_PASS**: P1-1 resolved and independently reproduced as rejected; P3 only |
| PL-0375 | CHANGES_REQUIRED | **CHANGES_REQUIRED**: P2-6 resolved; P2-2 fixture/provenance/noise gap still open |
| PL-0376 | CHANGES_REQUIRED | **CHANGES_REQUIRED**: P2-6 resolved; P2-3 still open |
| PL-0378 | CHANGES_REQUIRED | **CHANGES_REQUIRED**: unchanged (P2-5) |
| PL-0377 | CHANGES_REQUIRED | unchanged |
| PL-0379, 0381, 0382, 0383, 0384 | CLAUDE_PEER_AUDITED_PASS | unchanged (0dec41b6 is now pushed) |
