# PL-0190 Codex Implementation Log V01

Task: **Lift object masks into OBJECT_CAPTURE_GEOMETRY with multiview consensus**
Required actor: **CODEX**
Status: **READY_FOR_INDEPENDENT_AUDIT**

## Authorization and synchronization

- Live GitHub `TASKS.md`: M08 / M08-C001 / ordered remaining batch PL-0188 through PL-0201 / READY / CODEX. PL-0189 V01 log was remotely visible before this child began.
- Starting synchronized SHA: `233a97e471c23992a69522a570c906f2de44e5bd`.
- Branch: `main`; worktree clean at child start; `origin` is `https://github.com/Sekiph82/PackLab.git`; local/origin divergence: `0 0`.
- M07 remains `AUDITED_PASS`; PL-0068 remains `OWNER_REQUIRED`; M09/later milestone remains unauthorized.
- Active master prompt/criteria and PL-0190 V01 prompt/criteria read. `AGENTS.md`, coordination README, audit policy/index, and milestone batch protocol read. Mandatory pre-reads read in full: `docs/implementation/PL-0190_OBJECT_MASK_LIFT_MULTIVIEW_FUSION.md`, `docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md`, and `docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md`. No conflict was found.

## Implementation

- Added the backend-neutral `ObjectMaskLiftingService.lift(ObjectMaskLiftRequest)` core service in `core/src/packlab_core/object_mask_lifting.py`. It consumes an immutable mask-set revision, bounded synthetic-or-reconstruction world points, and explicit per-view camera/mask bindings; it has no model or UI dependency.
- Camera inputs name both a row-major rigid pose convention (`world_to_camera_row_major_4x4_column_vectors_v1` or `camera_to_world_row_major_4x4_column_vectors_v1`) and camera axes (`packlab-camera-x-right-y-down-z-forward-v1` or the accepted PackScan right/up/back convention). Unsupported or omitted conventions fail closed. A synthetic off-center known-point projection gate runs for each convention pair, then camera-to-world and PackScan axes normalize to PackLab right/down/forward camera coordinates. Matrices must be finite, affine, orthonormal and right-handed.
- Candidate projection is deterministic and sorted by point/camera ID. It rejects behind-camera and out-of-frame candidates. A per-view z-buffer built from all bounded reconstruction candidates applies the declared depth tolerance and raster scale before any mask pixel is sampled; occluded points produce not-observed counts, not mask rejects. Mask source asset, digest, dimensions, raster bytes/digest and recorded source-to-model transform are checked before voting. Projection samples use the nearest pixel center (`floor(coord + 0.5)`).
- The default versioned vote profile requires at least 2 visible observations, at least 2 support views, and support ratio `>= 0.70`; profile values are explicit and validated. Each bounded candidate receives observed/support/reject/not-observed, behind-camera, out-of-frame and occluded aggregates. The result retains deterministic vote records and the threshold-selected unfiltered point subset. No outlier pass is applied (`outlier_policy=none`).
- The result includes a deterministic identity over source/reconstruction/camera/mask revisions, normalized cameras and conventions, per-view intrinsics/source/mask identities, candidate data, threshold/visibility policy and selected-output digest. `created_at` is metadata excluded from identity. The manifest records `generated=false`, `authority_class=OBJECT_CAPTURE_GEOMETRY`, inherited relative/unverified scale, counts, parents, mask and image identities, camera evidence, threshold and visibility policies, and a PCA preliminary QA OBB marked as non-metric.
- `require_current_dependencies` fails stale when reconstruction, camera solution/evidence, source revision/digest/images, mask-set revision, camera/projection convention/version, voting profile, or visibility policy changes. `METRIC_VERIFIED` input/output is rejected because M09 is unauthorized.

## Changed files

- `core/src/packlab_core/object_mask_lifting.py`
- `tests/core/test_object_mask_lifting.py`
- `coordination/sessions/M08-C001/PL-0190_CODEX_LOG_V01.md` (separate log-only commit)

No `TASKS.md`, master log, audit/criteria artifact, owner ADR, accepted predecessor evidence, dependency/lockfile, model/runtime/checkpoint, private capture, RAW_CAPTURE bytes, signing material, generated reconstruction media, or PL-0191+/M09 implementation changed.

## Validation

- Focused PL-0190 and PL-0188/0186/0187 regression set: `uv run --locked pytest -q tests/core/test_object_mask_lifting.py tests/core/test_mask_revisions.py tests/core/test_manual_mask_correction.py tests/core/test_segmentation.py tests/core/test_mask_postprocessing.py tests/core/test_sam21_backend.py` — expected: camera convention, visibility/vote, boundary, invalidation, source integrity and predecessor checks pass; failure: any failed assertion/non-zero exit. Actual: **61 passed**, exit 0.
- Exact locked full suite: `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q` — expected: no failures; failure: any failed test/non-zero exit. Actual: **884 passed, 6 skipped, 1 deselected, 2 warnings**, exit 0. Existing warnings are duplicate ZIP entry fixture warnings from PackScan/transfer tests.
- Changed-file Ruff: `uv run --locked ruff check core/src/packlab_core/object_mask_lifting.py tests/core/test_object_mask_lifting.py` — expected clean; actual passed, exit 0.
- Changed-file format: `uv run --locked ruff format --check core/src/packlab_core/object_mask_lifting.py tests/core/test_object_mask_lifting.py` — expected already formatted; actual passed, exit 0.
- Whole-repository Ruff: `uv run --locked ruff check` — exit 1 for two existing findings in unchanged `preview/windows/packlab_preview.py` (import order and unused `tkinter.ttk`).
- Whole-repository format: `uv run --locked ruff format --check` — exit 1; **78 files would be reformatted, 1931 files already formatted**. Both changed PL-0190 files pass changed-file format.
- Targeted mypy: `uv run --locked mypy core/src/packlab_core/object_mask_lifting.py` — expected no errors; actual **Success, 1 source file**, exit 0.
- Compile: `uv run --locked python -m compileall -q core/src apps/windows-studio/src tests` — expected no syntax errors; actual passed, exit 0.
- `git diff --check` — expected no whitespace errors; actual passed, exit 0.
- Protected-file/scope review: `git diff -- TASKS.md coordination/sessions/M08-C001/MASTER_REMAINING_CODEX_LOG_V02.md` was empty; changes are limited to the allowed core service, dedicated synthetic test and this log.
- Dependency/license review: `pyproject.toml` and `uv.lock` are unchanged; no dependency, hosted service, model or binary was introduced.
- Privacy/secrets/signing review: targeted token/private-key/password pattern scan found no matches. Only public/synthetic points, masks and source identities were used; no private scan data or ambient user identity was read.
- Generated/binary review: additions are Python source/tests/log only; no geometry file or generated media was produced.
- Failure/fix: mypy initially identified a tuple-shape inference issue in PCA axis construction; the implementation now constructs explicit 3D tuples and targeted mypy passes. Ruff formatting was applied to the changed module; final changed-file checks pass.
- Native viewport/real-capture/physical acceptance was unavailable and is not claimed. Visibility currently uses the bounded supplied candidate cloud as its z-buffer; no separate depth-map adapter is included.

## Publication

- Implementation commit: `bf61ca1df3ea5cf158ad499ce0594f2193b64bec` (`Implement multiview object mask lifting`).
- Starting synchronized SHA: `233a97e471c23992a69522a570c906f2de44e5bd`.
- Implementation push succeeded. Follow-up fetch, `git rev-parse HEAD`, `git rev-parse origin/main`, and `git ls-remote origin refs/heads/main` all resolved to `bf61ca1df3ea5cf158ad499ce0594f2193b64bec`; divergence was `0 0`. The separate log-only commit follows.
- PL-0191+ and M09 had not started at this PL-0190 child boundary. After the PL-0190 log is published and verified, continue to PL-0191 under the active master batch.

READY_FOR_INDEPENDENT_AUDIT
