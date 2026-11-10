# Claude implementation log — PL-0375 / PL-0376 / PL-0378 rework (V02)

Date: 2026-11-10. Implementer: Claude Code (main session). This is not a review.

## Addresses

- **P2-2 (PL-0375):** realistic noise defeated the low-texture signal; the fixture was a noise-free constant array.
- **P2-3 (PL-0376):** the glossy PET fixture was a hand-made pixel array without provenance.
- **P2-5 (PL-0378):** suggestions were never checked against a designed known-missing sector, and no test
  showed that captured sectors are excluded.

## Changes

- `core/src/packlab_core/pre_reconstruction_qa.py`
  - New `ObjectMaskSamples`.
  - New optional `object_masks` parameter on `build_pre_reconstruction_qa`.
  - New per-photo and aggregate `object_surface_texture` component: masked 4×4 block-mean Laplacian textured
    fraction, warning below 0.12.
  - New thresholds recorded in the report.
  - With no masks the component reports `not_requested`, so existing behaviour is unchanged.
- `apps/windows-studio/src/packlab_studio/pre_reconstruction_qa.py`: adds an `object_masks` passthrough.
- `tools/datasets/calibrate_object_texture.py`: reproducible calibration table, plus the shared seeded noise
  and printed-label simulators.
- `tests/core/test_object_surface_texture_qa.py` (9 tests):
  - HDPE matte renders warn at σ 0 and 10 DN.
  - The reviewer's ±5 DN probe now warns.
  - The printed-label negative case passes at σ 0 and 10.
  - PET gloss renders give review_required, never a pass.
  - The Studio adapter real-decode path is covered.
  - Fail-closed cases: missing, misaligned and tiny masks.
- `tests/core/test_recapture_sector_suggestions.py`: 3 new PL-0378 tests on a synthetic orbit with designed gaps.
  - A single missing sector 5 is the only suggestion, with az bounds 225–270 and gap 45°.
  - A contiguous gap 3–5 ranks centre sector 4 first (90°) and never suggests a captured sector.
  - A full orbit with a QA gap gives full_rescan and no invented sector.
- `coordination/sessions/M17-C001/PL-0375_OBJECT_TEXTURE_CALIBRATION_V01.md`: method, data, table and limits.

## Local evidence

- `pytest -q tests/core/test_object_surface_texture_qa.py tests/core/test_pre_reconstruction_qa.py tests/core/test_recapture_sector_suggestions.py`
  → 28 passed.
- `tests/core/test_photo_duplicates.py` (an existing QA consumer) still passes.
- `ruff check core apps tools tests`: clean. `mypy core apps tools`: clean (286 files).
- Calibration: 64 views. Plain renders max 0.0680; labelled renders min 0.1906; all dispositions as expected.

## Not done / limits

- No real images were used, and there is no physical or factory claim.
- Specular-clipping detection for real PET is uncalibrated (see the calibration doc).
- Studio does not yet supply capture-time masks.
- PL-0377 is untouched (macOS XCTest).
