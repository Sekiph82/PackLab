# PL-0192 Codex Implementation Log V01

Task: **Build pre-reconstruction QA report**
Required actor: **CODEX**
Status: **READY_FOR_INDEPENDENT_AUDIT**

## Authorization and synchronization

- Live GitHub `TASKS.md` authorizes M08 / M08-C001 / remaining PL-0188 through PL-0201 / READY / CODEX; PL-0191 V01 log is remotely visible.
- Starting synchronized SHA: `21911034908764f3a80aa5dc83a2f8cc0f2f3093`.
- Final child implementation SHA: `a81f47c49b81f17f9905c8e1089aa04a45cd577e`.
- Branch: `main`; worktree clean; local/origin divergence: `0 0`; remote: `Sekiph82/PackLab`.
- M07 remains `AUDITED_PASS`; PL-0068 remains `OWNER_REQUIRED`; M09/later milestone remains unauthorized.
- Active master prompt/criteria, PL-0192 V01 prompt/criteria, repository instructions and governance protocol reread. No conflict found.

## Implementation

- Added backend-neutral `build_pre_reconstruction_qa` and immutable sample/failure contracts in `core/src/packlab_core/pre_reconstruction_qa.py`. It binds outputs to capture identity, the authoritative PackScan image source digests, and the `metadata/photos.json` digest; verifies source payload size, SHA-256, and checksum-index agreement before analysis; and never modifies PackScan inputs.
- Added a Windows Studio Qt adapter in `apps/windows-studio/src/packlab_studio/pre_reconstruction_qa.py`. It decodes only hash-verified image bytes through the existing PySide6/Qt dependency, disables auto-orientation, samples grayscale to a deterministic nearest-scale fit of at most 1024x1024, and reports unsupported/corrupt images through normalized failure codes. The core remains independent of Qt.
- Sharpness uses `laplacian_variance_8bit_grayscale_v1`: variance of the 4-neighbour 8-bit luma Laplacian over interior samples. The profile threshold is 20.0 inclusive; lower scores warn. Exposure uses 8-bit grayscale mean luma (acceptable inclusive range 40 through 215) and the combined fraction of samples below 16 or above 239 (maximum 0.05 inclusive). Every photo records the measured values, algorithm IDs, decoder ID/version, and the applied thresholds.
- Coverage uses only capture-mode evidence already in PackScan. Guided orbit compares photo count with the declared minimum view count and explicitly states per-photo sector angles are not recorded. Turntable reports its single manifest frame and warns when the declared frame set has more than one frame; freehand and missing targets are unavailable rather than inferred.
- Metadata consistency checks photo count and order against manifest image declarations; contiguous zero-based sequences; unique and valid photo IDs/paths; stored dimensions; filename/orientation fields; field-specific units, source/status, integer/range rules for focal length/exposure/ISO/white balance; and decoded-vs-declared image dimensions. Invalid data is surfaced through stable reason codes.
- The canonical, timestamp-free report is labeled `non_authoritative_capture_qa`; its overall outcome directs human review and explicitly disclaims geometry/physical-accuracy authority. No source pixels, filenames, device identifiers, prompt fields, model claims, derived geometry or image media are included.
- Bounds: maximum 512 manifest images, 1,000,000 decoded samples per image, 64,000,000 aggregate decoded samples, 100,000 source-pixel maximum per dimension, and a 256 MiB compressed payload cap in the Qt adapter. No dependency, model, hosted service or checkpoint was added.

## Changed files

- `core/src/packlab_core/pre_reconstruction_qa.py` (new)
- `apps/windows-studio/src/packlab_studio/pre_reconstruction_qa.py` (new)
- `tests/core/test_pre_reconstruction_qa.py` (new synthetic PackScan and Qt PNG coverage)
- `coordination/sessions/M08-C001/PL-0192_CODEX_LOG_V01.md` (this log)
- No `TASKS.md`, master log, audit/criteria artifact, accepted predecessor, dependency/lockfile, model/runtime/checkpoint, private capture, RAW_CAPTURE bytes, signing material or generated media changed.

## Validation

- Focused PL-0192 and predecessor regressions: `uv run --locked pytest -q tests/core/test_pre_reconstruction_qa.py tests/core/test_mask_review.py tests/core/test_mask_revisions.py tests/core/test_manual_mask_correction.py tests/core/test_mask_postprocessing.py tests/core/test_object_mask_lifting.py` — expected: deterministic report identity, source digests/immutability, sharpness and exposure threshold boundaries, clipping limits, metadata schema/path/order errors, missing/unsupported decode disposition, dimensions/digest rejection, Qt decode adapter and predecessor regressions pass; failure: any assertion or non-zero exit. Actual: **54 passed**, exit 0.
- Exact locked full suite: `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q` — expected: no failures; failure: any failed test/non-zero exit. Actual: **898 passed, 6 skipped, 1 deselected, 2 warnings**, exit 0. Warnings are existing duplicate ZIP entry fixture warnings in PackScan/transfer tests.
- Changed-file Ruff: `uv run --locked ruff check core/src/packlab_core/pre_reconstruction_qa.py apps/windows-studio/src/packlab_studio/pre_reconstruction_qa.py tests/core/test_pre_reconstruction_qa.py` — expected clean; actual passed, exit 0.
- Changed-file format: `uv run --locked ruff format --check core/src/packlab_core/pre_reconstruction_qa.py apps/windows-studio/src/packlab_studio/pre_reconstruction_qa.py tests/core/test_pre_reconstruction_qa.py` — expected already formatted; actual passed, exit 0.
- Whole-repository Ruff: `uv run --locked ruff check` — exit 1 for two existing findings in unchanged `preview/windows/packlab_preview.py` (import order and unused `tkinter.ttk`).
- Whole-repository format: `uv run --locked ruff format --check` — exit 1; **78 files would be reformatted, 1938 files already formatted**. All three changed implementation/test files pass changed-file format.
- Targeted mypy: `uv run --locked mypy --follow-imports=silent core/src/packlab_core/pre_reconstruction_qa.py apps/windows-studio/src/packlab_studio/pre_reconstruction_qa.py` — expected no errors in changed files; actual **Success, 2 source files**, exit 0. Silent dependency following avoids four known unrelated errors in unchanged `packlab_core/packscan/container.py`.
- Compile: `uv run --locked python -m compileall -q core/src apps/windows-studio/src tests` — expected no syntax errors; actual passed, exit 0.
- `git diff --check` — expected no whitespace errors; actual passed, exit 0.
- Protected-file/scope review: `git diff -- pyproject.toml uv.lock TASKS.md coordination/sessions/M08-C001/MASTER_REMAINING_CODEX_LOG_V02.md` was empty. Changes are limited to the authorized core report, Qt decoder adapter, synthetic tests, and this child log.
- Dependency/license review: `pyproject.toml` and `uv.lock` are unchanged; Qt is the existing PySide6 application dependency. The core analyzer uses the Python standard library. No model, hosted service, dependency, checkpoint or binary was introduced.
- Privacy/secrets/signing review: targeted token/private-key/password scan of the three changed Python files found no matches (expected ripgrep no-match exit 1). Only synthetic fixtures were used; no private scans or ambient user identity were read.
- Generated/binary review: changed files are Python source/test/log text. The adapter analyzes in-memory PackScan source bytes without writing or mutating them; no output image/media files are generated.
- Failures/fixes: initial adapter import used `qVersion` from QtGui; corrected it to QtCore. Static checking exposed narrowing issues around untrusted JSON fields, which were made explicit. A focused test initially used clipped black/white synthetic pixels while expecting no exposure warning; its fixture was corrected and boundary coverage now verifies inclusive means and combined clipped fraction. Final checks pass.
- Native Studio UI acceptance, real capture imagery, device decode-plugin coverage, and physical accuracy were unavailable and are not claimed. Unsupported image formats remain explicitly unscored.

## Publication

- Implementation/evidence commit: `a81f47c49b81f17f9905c8e1089aa04a45cd577e` (`Add pre-reconstruction capture QA report`).
- Starting synchronized SHA: `21911034908764f3a80aa5dc83a2f8cc0f2f3093`.
- Implementation push succeeded. Follow-up fetch, `git rev-parse a81f47c49b81f17f9905c8e1089aa04a45cd577e`, `git rev-parse origin/main`, and `git ls-remote origin refs/heads/main` all resolved to `a81f47c49b81f17f9905c8e1089aa04a45cd577e`; divergence at implementation boundary was `0 0`.
- This is the separate child-log-only commit following implementation; its remote visibility and final parity are verified after publication.
- PL-0193+ and M09 had not started at this PL-0192 child boundary. Continue to PL-0193 under the active master batch after this log is remotely verified.

READY_FOR_INDEPENDENT_AUDIT
