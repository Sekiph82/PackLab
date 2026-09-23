# PL-0062 — Codex Log V02

Task: PL-0062 — Marker policy source-of-truth integration remediation
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CHATGPT_AUDIT_CRITERIA_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CHATGPT_AUDIT_V01.md

## Synchronization

- Git root: `C:\Users\sekip\Desktop\PackLab`
- Branch: `main`
- Preflight fetch: `git fetch origin main --prune` succeeded.
- Preflight divergence: `git rev-list --left-right --count HEAD...origin/main` returned `0 0`.
- Preflight status: `git status --porcelain` returned clean before PL-0062 edits.
- Root `TASKS.md` authorized `M02-RESUME-REMEDIATION-BATCH-001` / `CODEX`.
- Starting commit: `96306a58b43ce12e208703bd07ae8aa48c2b706d`
- Implementation commit: `a95e5f96ae9c0b1e6f099e64710b91eb2d383dc8`
- Remote implementation proof: `git ls-remote origin main` returned `a95e5f96ae9c0b1e6f099e64710b91eb2d383dc8 refs/heads/main`.

No destructive Git operation was used.

## Files Changed

- `core/src/packlab_core/calibration/marker_detection.py`
- `docs/calibration/marker-detection.md`
- `tests/calibration/test_marker_detection.py`
- `coordination/sessions/M02-C001/PL-0062_CODEX_LOG_V02.md`

All implementation files are within the authorized PL-0062 V02 scope.

## Defect Mapping

Blocking V01 audit findings:

1. Detector code independently hard-coded `DICT_APRILTAG_36h11` instead of consuming `schemas/packscan/calibration-marker-policy.json`.
2. Tests did not prove detector resolution followed the machine-readable policy or failed on policy drift.
3. Duplicate-ID testing accepted multiple unrelated outcomes and did not require a bounded `duplicate_marker_id` invalid result under controlled duplicate detector output.

Remediation:

- Added `load_marker_policy()` to load the PackLab marker policy JSON.
- Derived exported `DICTIONARY_NAME` and `DICTIONARY_POLICY_VERSION` from the loaded policy rather than standalone string literals.
- Added `resolve_policy_dictionary(cv2_module, policy)` to map the policy `opencv_dictionary` value to the local `cv2.aruco` predefined dictionary.
- `detect_markers()` now loads the policy and resolves the OpenCV dictionary through that policy before detection.
- Unsupported/missing policy dictionaries return a bounded `unavailable` detection result with an explicit `unsupported_marker_dictionary:<name>` error instead of substituting another family.
- Added fake-OpenCV policy resolution tests proving:
  - the default detector dictionary name is loaded from the policy file;
  - a substituted policy dictionary is followed;
  - an unsupported policy dictionary raises `MarkerPolicyError`.
- Added `_duplicate_marker_result()` and a deterministic helper-level test proving duplicate raw detector IDs produce `DetectionBatch(status="invalid", errors=("duplicate_marker_id",))`.
- Preserved the synthetic OpenCV duplicate-scene test as a bounded integration check while the helper test now pins the duplicate rejection behavior.
- Updated marker-detection docs to state the policy-driven source of truth and unsupported-policy failure behavior.

## Validation

Expected result: exit code `0`; listed pass counts. Failure condition: dictionary resolution independent of policy, unsupported policy silently falling back, duplicate injected IDs not producing `duplicate_marker_id`, lint failure, `TASKS.md` diff, whitespace error, secret/signing match, or physical-scale inference.

| Command | Actual Result |
|---|---|
| `python -m ruff format core\src\packlab_core\calibration\marker_detection.py tests\calibration\test_marker_detection.py` | `1 file reformatted, 1 file left unchanged`. |
| `$env:PYTHONPATH='core/src'; python -m pytest tests\calibration\test_marker_detection.py` | `5 passed, 2 skipped in 0.08s`; skips are OpenCV-dependent scene tests without the OpenCV temp path. |
| `$env:PYTHONPATH='core/src'; python -m ruff check core\src\packlab_core\calibration\marker_detection.py tests\calibration\test_marker_detection.py` | `All checks passed!`. |
| `$env:PYTHONPATH='core/src;C:\Users\sekip\AppData\Local\Temp\packlab-cv'; python -m pytest tests\calibration\test_marker_detection.py tests\calibration\test_marker_policy.py` | `9 passed in 0.14s`. |
| `$env:PYTHONPATH='core/src;C:\Users\sekip\AppData\Local\Temp\packlab-cv'; python -m pytest tests\calibration` | `44 passed in 0.22s`. |
| `$env:PYTHONPATH='core/src;C:\Users\sekip\AppData\Local\Temp\packlab-cv'; python -m pytest tests\packscan tests\calibration` | `100 passed, 1 warning in 0.49s`; warning is the expected duplicate ZIP-entry warning in the negative PackScan duplicate-name test. |
| `python -m mypy core\src\packlab_core\calibration\marker_detection.py tests\calibration\test_marker_detection.py` | Unavailable on this Windows Python: `No module named mypy`. No type-pass claim is made. |
| `git diff --check` | Passed. Git printed only LF-to-CRLF working-copy normalization warnings for touched text files. |
| `git diff -- TASKS.md` | Empty. |
| `rg -n "BEGIN|PRIVATE KEY|API[_-]?KEY|TOKEN|PASSWORD|SECRET|DEVELOPMENT_TEAM|PROVISIONING_PROFILE|CODE_SIGN_IDENTITY" core\src\packlab_core\calibration\marker_detection.py docs\calibration\marker-detection.md tests\calibration\test_marker_detection.py` | No matches; command exited `1` for no matches. |

## Focused Evidence

The policy-resolution regression uses a fake `cv2.aruco` module with two dictionary constants. The detector resolver first selects the policy file's `DICT_APRILTAG_36h11`; after substituting policy data to `DICT_4X4_50`, it selects that fake constant instead. When the policy is changed to `DICT_DOES_NOT_EXIST`, resolution fails with `MarkerPolicyError("unsupported_marker_dictionary:DICT_DOES_NOT_EXIST")`.

The duplicate-ID regression injects raw detector IDs `[[7], [7]]` directly into the helper and proves the bounded invalid result is exactly `duplicate_marker_id`.

## Scope, Privacy, and Limitations

- `TASKS.md` was read only and not edited.
- No ChatGPT audit artifact was created or edited.
- No PL-0067, PL-0068, or M03 work was started.
- No secret, credential, signing material, private Kenya scan, confidential supplier file, cache, native/device, or physical evidence was added.
- Marker detection remains image-pixel only and does not infer physical scale, distance, printer accuracy, camera pose, or measurement accuracy.
- OpenCV-dependent positive marker scene tests use synthetic generated images only.

## Push Evidence

- Implementation commit pushed to `origin/main`: `a95e5f96ae9c0b1e6f099e64710b91eb2d383dc8`.
- Remote proof after push: `git ls-remote origin main` returned `a95e5f96ae9c0b1e6f099e64710b91eb2d383dc8 refs/heads/main`.

READY_FOR_INDEPENDENT_AUDIT
