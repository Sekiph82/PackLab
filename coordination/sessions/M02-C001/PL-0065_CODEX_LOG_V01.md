# PL-0065 — Codex Log V01

Task: PL-0065 — iPhone main-camera calibration procedure
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0065_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0065_CHATGPT_AUDIT_CRITERIA_V01.md

## Synchronization

- Git root: `C:\Users\sekip\Desktop\PackLab`
- Branch: `main`
- Preflight fetch: `git fetch origin main --prune` succeeded.
- Preflight divergence: `git rev-list --left-right --count HEAD...origin/main` returned `0 0`.
- Preflight status: `git status --short` returned clean.
- Root `TASKS.md` authorized `M02-BATCH-001` / `CODEX` before material work.
- Starting commit: `3423db5fd3f15d86ae1fc70ab3b6f78df2096cb7`
- Implementation commit: `b7a691dac59b2c076b0c98e5d7c1a5c95a4ba3f6`
- Remote implementation proof: `git ls-remote origin main` returned `b7a691dac59b2c076b0c98e5d7c1a5c95a4ba3f6 refs/heads/main`.

No destructive Git operation was used.

## Files Read

- `TASKS.md`
- `AGENTS.md`
- `coordination/MILESTONE_BATCH_PROTOCOL.md`
- `coordination/sessions/M02-C001/PL-0065_CODEX_PROMPT_V01.md`
- `coordination/sessions/M02-C001/PL-0065_CHATGPT_AUDIT_CRITERIA_V01.md`
- `docs/calibration/marker-detection.md`
- `docs/calibration/scale-estimation.md`
- `docs/calibration/pre-use-verification.md`
- `schemas/packscan/manifest.schema.json`
- `schemas/packscan/camera-intrinsics.schema.json`
- `tests/packscan/test_intrinsics_contract.py`
- `tests/packscan/test_manifest_contract.py`

## Files Changed

- `docs/calibration/iphone-main-camera-calibration.md`
- `schemas/packscan/iphone-main-camera-calibration.schema.json`
- `tests/calibration/test_iphone_main_camera_calibration.py`
- `coordination/sessions/M02-C001/PL-0065_CODEX_LOG_V01.md`

All implementation files are inside the authorized `docs/calibration/**`, `schemas/packscan/**`, and `tests/calibration/**` scope. This log is the required child evidence artifact.

## Implementation

- Added a repeatable iPhone 16 Standard main-camera calibration procedure.
- Defined when recorded EXIF/device API intrinsics may be used as metadata only and when dedicated calibration is required.
- Kept the baseline explicitly to iPhone 16 Standard, back main wide camera, `1.0x`; the procedure excludes LiDAR, depth/portrait assumptions, and Pro-only features.
- Required a seven-view dedicated capture procedure: fronto-parallel near/far, yaw left/right, pitch up/down, and corner coverage.
- Defined validation outputs: `reprojection_rmse_px`, accepted view count, confidence status, intrinsics payload link, printed-mat verification record, owner physical measurement status, and exact profile binding.
- Added a versioned JSON schema for iPhone main-camera calibration records, including `unavailable`, `candidate`, and `measured` states.
- Bound calibration records to device model, lens identity, image dimensions, orientation, zoom factor, focus mode, capture app version, and calibration profile version.
- Required owner-device capture evidence and owner-completed physical measurement records for `candidate` and `measured` records.
- Explicitly documented that no owner-produced iPhone calibration profile exists in this repository.

## Validation

Expected result for test commands: exit code `0`; required pass counts as listed. Failure condition: non-zero exit, failed assertion, changed `TASKS.md`, whitespace error, or scope/privacy violation.

| Command | Actual Result |
|---|---|
| `$env:PYTHONPATH='core/src'; python -m pytest tests\calibration\test_iphone_main_camera_calibration.py` | First run found a Markdown line-wrap-only assertion mismatch; fixed test to normalize whitespace. Final run: `3 passed in 0.05s`. |
| `$env:PYTHONPATH='core/src;C:\Users\sekip\AppData\Local\Temp\packlab-cv'; python -m pytest tests\calibration tests\packscan` | `65 passed, 1 warning in 0.48s`; warning is the expected duplicate ZIP-entry warning in the negative PackScan duplicate-name test. |
| `$env:PYTHONPATH='core/src'; python -m ruff check tests\calibration` | `All checks passed!` |
| `python -m ruff format tests\calibration\test_iphone_main_camera_calibration.py` | Final run: `1 file left unchanged`. |
| `$env:PYTHONPATH='core/src'; python -m mypy tests\calibration\test_iphone_main_camera_calibration.py` | Unavailable on this Windows Python: `No module named mypy`. No type-pass claim is made. |
| `git diff --check` | Passed. |
| `git diff -- TASKS.md` | Empty. |
| `git diff --stat` after `git add -N` | Listed only the three PL-0065 implementation/doc/test files. |

## Coverage

- Positive: schema contract freezes iPhone 16 Standard, main-wide `1.0x`, no-LiDAR/no-Pro-only baseline, profile-binding fields, source-policy fields, view-set requirement, validation outputs, and owner evidence requirements.
- Negative: mutation removing `image_height_px` from the profile binding is detected.
- Boundary: documentation test locks the distinction between metadata-only EXIF/device intrinsics and dedicated calibration, plus the no fabricated profile boundary.
- Regression: existing calibration and PackScan tests remain green.

## Failures and Fixes

- Initial focused doc test failed because a required sentence wrapped across Markdown lines. Fixed the test to normalize whitespace before searching required fragments.
- A schema-inspection command initially referenced a non-existent `intrinsics.schema.json`; corrected to the actual `camera-intrinsics.schema.json` and proceeded. No repository files were changed by that failed read.

## Scope, Privacy, and Physical Evidence Review

- `TASKS.md` was read only and not edited.
- No ChatGPT audit artifact was created or edited.
- No M03 work was started.
- No secret, credential, Apple signing material, private Kenya scan, confidential supplier file, local cache, or generated reconstruction intermediate was added.
- No owner-device measurement, native capture, iPhone execution, or physical calibration profile is claimed.
- The procedure and schema explicitly require owner-device/physical evidence before any `candidate` or `measured` profile may exist.

## Push Evidence

- Implementation commit pushed to `origin/main`: `b7a691dac59b2c076b0c98e5d7c1a5c95a4ba3f6`.
- Remote proof after push: `git ls-remote origin main` returned `b7a691dac59b2c076b0c98e5d7c1a5c95a4ba3f6 refs/heads/main`.

READY_FOR_INDEPENDENT_AUDIT
