# PL-0197 Codex Implementation Log V01

Task: **Calculate dense/object-cloud density and surface coverage indicators**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0197_CODEX_PROMPT_V01.md

Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0197_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live `TASKS.md` authorizes M08 / M08-C001 / the ordered PL-0188 through PL-0201 remaining batch / READY / CODEX. PL-0196 V01 predecessor log was remotely visible and ended `READY_FOR_INDEPENDENT_AUDIT`.
- Starting synchronized SHA: `6695200a5da67267f2ee995e5fe66c13dc0ad963`; branch `main`; origin `https://github.com/Sekiph82/PackLab.git`; worktree clean; local/origin/GitHub-main divergence `0 0`.
- M07 remains `AUDITED_PASS`; PL-0068 remains `OWNER_REQUIRED`; M09/later work remains unauthorized.
- Re-read the live tracker, PL-0197 V01 prompt/criteria, master remaining-batch V02 prompt, coordination README, audit policy, batch protocol, and user-provided repository instructions. No task-state or architecture conflict was found.
- This consumer accepts the PL-0190 `ObjectCaptureGeometry` output. It does not parse or re-derive mask rasters, execute a reconstruction backend, promote geometry authority, or claim physical/metric quality.

## Implementation

- Added `core/src/packlab_core/object_geometry_coverage.py` with an immutable, explicitly supplied `ObjectGeometryCoveragePolicy` and deterministic report builder.
- The service validates `OBJECT_CAPTURE_GEOMETRY` authority/scale invariants, parent revision and SHA-256 fields, camera/source/mask relationships, camera convention consistency, candidate/vote cardinality, vote count/rate/selection consistency, finite selected coordinates, and geometry point-count consistency. Malformed evidence fails closed with a bounded invalid report.
- Density is reported as normalized axis-aligned bounding-box voxel occupancy and points per occupied voxel. Coverage is reported as XY/XZ/YZ orthographic grid occupancy. Both are unitless proxies; output explicitly disclaims physical units and surface-area claims.
- Multiview support reports selected-point support/observed vote totals, average support ratio, minimum selected-point support ratio, and support votes per candidate point. It derives only from the parent geometry's retained point aggregates; it does not invent per-camera or omitted candidate evidence.
- Reports bind the geometry ID, parent revision IDs/digests, canonical camera evidence digest, canonical vote digest, normalized parent geometry digest, parent lift threshold-profile digest, and visibility-policy digest. Tuple ordering is normalized for deterministic report bytes. Inputs/source buffers are not mutated.
- Coverage thresholds are versioned, bounded, inclusive, and separate from the parent lift-selection profile. Empty selected geometry is reported as empty with thresholds not evaluated. Acceptance remains `not_evaluated`; no Scan Master, metric, or geometry-promotion state is emitted.
- Added `tests/core/test_object_geometry_coverage.py` covering empty/sparse/dense clouds, occupancy output, inclusive and just-below boundaries, multiview support aggregation, invalid parent and vote provenance, tuple reordering, source-buffer preservation, and invalid policy bounds.
- No Windows Studio seam was needed. No dependency, lockfile, schema, tracker, accepted predecessor, reconstruction artifact, generated raster, or binary changed.

## Changed files

- `core/src/packlab_core/object_geometry_coverage.py`
- `tests/core/test_object_geometry_coverage.py`
- `coordination/sessions/M08-C001/PL-0197_CODEX_LOG_V01.md` (separate evidence commit)

## Validation

Each command was expected to pass; any focused/regression/full test, changed-file lint/format/type/compile, integrity, privacy, or protected-scope failure would stop the batch.

| Command | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_object_geometry_coverage.py` | All PL-0197 cases pass | **5 passed**, exit 0 |
| `uv run --locked pytest -q tests/core/test_object_geometry_coverage.py tests/core/test_object_mask_lifting.py tests/core/test_mask_revisions.py tests/core/test_manual_mask_correction.py tests/core/test_sparse_connectivity.py tests/core/test_registered_photo_ratio.py tests/core/test_sparse_mapping.py tests/core/test_sparse_diagnostics.py tests/core/test_focal_lens_consistency.py tests/core/test_photo_duplicates.py tests/core/test_pre_reconstruction_qa.py tests/core/test_mask_postprocessing.py` | New coverage and neighboring M08/predecessor regressions pass; any failure blocks the batch | **173 passed**, exit 0 |
| `uv run --locked pytest -q` | Locked full suite green; any test failure blocks the batch | **959 passed, 6 skipped, 1 deselected**, exit 0; 2 existing duplicate-ZIP fixture warnings from `tests/packscan/test_container.py` and `tests/transfer/test_validation_gate.py` |
| `uv run --locked ruff check core/src/packlab_core/object_geometry_coverage.py tests/core/test_object_geometry_coverage.py` | No changed-file lint findings | **PASS**, exit 0 |
| `uv run --locked ruff format --check core/src/packlab_core/object_geometry_coverage.py tests/core/test_object_geometry_coverage.py` | Both changed Python files formatted | **PASS**, 2 files already formatted |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/object_geometry_coverage.py` | No type errors | **Success: no issues found in 1 source file**, exit 0 |
| `uv run --locked python -m compileall -q core/src/packlab_core/object_geometry_coverage.py tests/core/test_object_geometry_coverage.py` | Both changed files compile | **PASS**, exit 0 |
| `git diff --check` | No whitespace errors | **PASS**, exit 0; repeated against staged implementation before commit |
| `git diff --exit-code -- TASKS.md coordination/AUDIT_POLICY.md coordination/AUDIT_INDEX.md coordination/sessions/M08-C001/PL-0197_CODEX_PROMPT_V01.md coordination/sessions/M08-C001/PL-0197_CHATGPT_AUDIT_CRITERIA_V01.md pyproject.toml uv.lock` | Protected governance/prompt/criteria and dependency files unchanged | **PASS**, exit 0 |
| `uv run --locked ruff check` | Repository-wide lint clean; findings checked against changed scope | **2 pre-existing findings** in unchanged `preview/windows/packlab_preview.py` (I001 import order, F401 unused `tkinter.ttk`) |
| `uv run --locked ruff format --check` | Repository-wide formatting clean; candidates checked against changed scope | **78 unchanged files would be reformatted; 1953 files already formatted**. Both changed Python files pass the separate format check above. |
| Credential-pattern `rg` scan over changed implementation/test | No token or private-key match | **No matches**; `rg` exit 1 is its expected no-match result |
| Personal-path/email/RAW_CAPTURE/private `.packscan` `rg` scan over changed implementation/test | No private source-data match | **No matches**; `rg` exit 1 is its expected no-match result |
| `git diff --exit-code -- pyproject.toml uv.lock` and changed-path review | No unreviewed dependency/license change, generated media, binary, or out-of-scope file | **PASS**; no dependency change; only the listed two Python files and this log are in scope |

One test-fixture construction initially retained a selected vote in an empty-cloud case; the fixture was corrected to use a parent threshold profile under which all its votes are rejected. Initial import ordering, formatting, and type diagnostics were corrected. No unresolved changed-file finding remains.

No native reconstruction backend, physical capture, printer, or Windows Studio UI verification was run. Tests use the public synthetic object-lifting fixture. The proxy occupancy metrics depend on the selected cloud's normalized bounding box and grid resolution; they are not geometric surface area, volumetric density, or an acceptance gate. Parent geometry digests fingerprint the supplied object and linked provenance; this consumer does not independently recreate the producer's full PL-0190 identity, which includes unselected point coordinates not retained by `ObjectCaptureGeometry`.

## Scope, privacy, and dependency review

- Implementation and test changes are limited to the two listed Python files. `TASKS.md`, audit/prompt/criteria files, accepted predecessor code, and M09 paths were not edited.
- The service serializes only parent IDs/digests and diagnostic summaries; raw source images, source bytes, point IDs, unselected point coordinates, raster bytes, and mask pixels are not added to report output.
- No runtime/test dependency, model, checkpoint, hosted API, private capture, signing material, generated raster, binary, mesh cleanup, or geometry-promotion artifact was added.

## Publication

- Implementation commit: `6efb7761fc37bee62e3edd0d106cc3eb508368d9` (`PL-0197: add object geometry coverage diagnostics`); contains only the core report and dedicated tests.
- Child-log-only commit: created separately after the implementation commit; contains only `coordination/sessions/M08-C001/PL-0197_CODEX_LOG_V01.md`.
- Push target: `origin main` only.
- After push, local `HEAD`, `origin/main`, and GitHub `main` must match with `0 0` divergence and the remote log must end exactly `READY_FOR_INDEPENDENT_AUDIT`.

READY_FOR_INDEPENDENT_AUDIT
