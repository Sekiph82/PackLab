# PL-0193 Codex Implementation Log V01

Task: **Detect duplicate and near-duplicate photos on Windows**
Required actor: **CODEX**
Status: **READY_FOR_INDEPENDENT_AUDIT**

## Authorization and synchronization

- Live GitHub `TASKS.md` authorizes M08 / M08-C001 / remaining PL-0188 through PL-0201 / READY / CODEX; PL-0192 V01 log is remotely visible.
- Starting synchronized SHA: `aabf3eaf8fea86a47dd1616fe94a9ee2ca7ddeaa`.
- Final child implementation SHA: `d1991190612eb2b06d3c7c215e37459c2ece3d29`.
- Branch: `main`; worktree clean; local/origin divergence: `0 0`; remote: `Sekiph82/PackLab`.
- M07 remains `AUDITED_PASS`; PL-0068 remains `OWNER_REQUIRED`; M09/later milestone remains unauthorized.
- Active master prompt/criteria, PL-0193 V01 prompt/criteria, repository instructions and governance protocol reread. No conflict found.

## Implementation

- Added backend-neutral `build_photo_duplicate_report` in `core/src/packlab_core/photo_duplicates.py` and a Qt image-decoding adapter in `apps/windows-studio/src/packlab_studio/photo_duplicates.py`. Exact duplicate groups use SHA-256 over verified source image bytes. Near-duplicate candidates use the deterministic 64-bit `difference_hash_9x8_luma_v1` over bounded grayscale samples; the default inclusive threshold is Hamming distance 4, with caller values restricted to 0..16.
- The output binds each source path to its SHA-256 and byte size; each usable perceptual signature also records source dimensions, sampled dimensions, decoder ID/version, algorithm ID, hash bits and threshold. Near-candidate pairs include both source digests and measured Hamming distance. The result is canonical/timestamp-free and states candidates require review; it never deletes, rewrites or suppresses photos.
- Image ordering follows a valid contiguous zero-based `metadata/photos.json` sequence that matches manifest image order. When metadata is missing, malformed or mismatched, the detector uses lexical path order and records the fallback reason. Source bytes and metadata are checked against manifest size/SHA-256 and PackScan checksum-index values before analysis. Case-insensitive duplicate paths are rejected.
- Exact SHA duplicate detection remains available for images whose perceptual decoder is missing or unsupported. Near-duplicate hashing is unavailable for absent/failed samples, sample/source digest mismatch, source-dimension mismatch, fewer than 9x8 luma samples, or luma range below 8; these outcomes are recorded with stable reason codes. A uniform/low-contrast pair is not presented as a near match.
- Bounds: at most 512 images, each image payload at most 256 MiB, total source image payloads at most 2 GiB, at most 1,000,000 luma samples per image and 64,000,000 total. The Qt adapter scales to at most 512x512 per image using the existing PySide6 dependency. Pair generation is bounded by 512 images. No capture bytes are written or changed.

## Changed files

- `core/src/packlab_core/photo_duplicates.py` (new)
- `apps/windows-studio/src/packlab_studio/photo_duplicates.py` (new)
- `tests/core/test_photo_duplicates.py` (new synthetic core and Qt adapter coverage)
- `coordination/sessions/M08-C001/PL-0193_CODEX_LOG_V01.md` (this log)
- No `TASKS.md`, master log, audit/criteria artifact, accepted predecessor, dependency/lockfile, model/runtime/checkpoint, private capture, RAW_CAPTURE bytes, signing material or generated media changed.

## Validation

- Focused PL-0193 and predecessor regressions: `uv run --locked pytest -q tests/core/test_photo_duplicates.py tests/core/test_pre_reconstruction_qa.py tests/core/test_mask_review.py tests/core/test_mask_revisions.py tests/core/test_manual_mask_correction.py tests/core/test_mask_postprocessing.py tests/core/test_object_mask_lifting.py` — expected: exact duplicates, inclusive/exclusive near-hash boundaries, distinct images, deterministic metadata/path ordering, malformed/missing decoder and low-contrast disposition, payload/sample digest binding, dimensions, threshold input errors, 512-image bound, Qt decode adapter, source preservation and predecessor regression assertions pass; failure: any failed assertion/non-zero exit. Actual: **67 passed**, exit 0.
- Exact locked full suite: `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q` — expected: no failures; failure: any failed test/non-zero exit. Actual: **911 passed, 6 skipped, 1 deselected, 2 warnings**, exit 0. Warnings are existing duplicate ZIP entry fixture warnings in PackScan/transfer tests.
- Changed-file Ruff: `uv run --locked ruff check core/src/packlab_core/photo_duplicates.py apps/windows-studio/src/packlab_studio/photo_duplicates.py tests/core/test_photo_duplicates.py` — expected clean; actual passed, exit 0.
- Changed-file format: `uv run --locked ruff format --check core/src/packlab_core/photo_duplicates.py apps/windows-studio/src/packlab_studio/photo_duplicates.py tests/core/test_photo_duplicates.py` — expected already formatted; actual passed, exit 0.
- Whole-repository Ruff: `uv run --locked ruff check` — exit 1 for two existing findings in unchanged `preview/windows/packlab_preview.py` (import order and unused `tkinter.ttk`).
- Whole-repository format: `uv run --locked ruff format --check` — exit 1; **78 files would be reformatted, 1942 files already formatted**. All three changed implementation/test files pass changed-file format.
- Targeted mypy: `uv run --locked mypy --follow-imports=silent core/src/packlab_core/photo_duplicates.py apps/windows-studio/src/packlab_studio/photo_duplicates.py` — expected no errors in changed files; actual **Success, 2 source files**, exit 0.
- Compile: `uv run --locked python -m compileall -q core/src apps/windows-studio/src tests` — expected no syntax errors; actual passed, exit 0.
- `git diff --check` — expected no whitespace errors; actual passed, exit 0.
- Protected-file/scope review: `git diff -- pyproject.toml uv.lock TASKS.md coordination/sessions/M08-C001/MASTER_REMAINING_CODEX_LOG_V02.md` was empty. Changes are limited to the authorized duplicate service, Qt decoder adapter, synthetic tests and this child log.
- Dependency/license review: `pyproject.toml` and `uv.lock` are unchanged; Qt is the existing PySide6 app dependency and the core detector uses the Python standard library. No new model, hosted service, dependency, checkpoint or binary was introduced.
- Privacy/secrets/signing review: targeted token/private-key/password scan of changed source/test files found no matches (expected ripgrep no-match exit 1). Only synthetic photos and metadata were used; no private imagery or ambient user identity was read.
- Generated/binary review: changed files are Python source/test/log text. The Qt test image exists only in memory; production adapter only reads and decodes existing PackScan payload bytes and writes no images or media.
- Failures/fixes: corrected an initial strict-zip implementation issue in dHash row comparisons, a test-call argument typo, import ordering and mypy narrowing for manifest-provided values. All final focused/static/full checks pass.
- Native Windows Studio window acceptance, real capture-image review and physical/image-set owner review were unavailable and are not claimed. Threshold 4 and minimum luma range 8 are versioned review heuristics, not an accepted automatic deletion or rescan policy.

## Publication

- Implementation/evidence commit: `d1991190612eb2b06d3c7c215e37459c2ece3d29` (`Add deterministic photo duplicate review`).
- Starting synchronized SHA: `aabf3eaf8fea86a47dd1616fe94a9ee2ca7ddeaa`.
- Implementation push succeeded. Follow-up fetch, `git rev-parse d1991190612eb2b06d3c7c215e37459c2ece3d29`, `git rev-parse origin/main`, and `git ls-remote origin refs/heads/main` all resolved to `d1991190612eb2b06d3c7c215e37459c2ece3d29`; divergence at implementation boundary was `0 0`.
- This is the separate child-log-only commit following implementation; its remote visibility and final parity are verified after publication.
- PL-0194+ and M09 had not started at this PL-0193 child boundary. Continue to PL-0194 under the active master batch after this log is remotely verified.

READY_FOR_INDEPENDENT_AUDIT
