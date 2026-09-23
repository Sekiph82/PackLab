# PL-0066 — Codex Log V02

Task: PL-0066 — Fail-closed calibration-profile compatibility remediation
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CHATGPT_AUDIT_CRITERIA_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CHATGPT_AUDIT_V01.md

## Synchronization

- Git root: `C:\Users\sekip\Desktop\PackLab`
- Branch: `main`
- Preflight fetch: `git fetch origin main --prune` succeeded.
- Preflight divergence: `git rev-list --left-right --count HEAD...origin/main` returned `0 0`.
- Preflight status: `git status --porcelain` returned clean before PL-0066 edits.
- Root `TASKS.md` authorized `M02-RESUME-REMEDIATION-BATCH-001` / `CODEX`.
- Starting commit: `cfc476d4d302ae9aa5228d6214bded7f83521ae5`
- Implementation commit: `0e1a5d445e89f37511df6a69482cb4ab5374682d`
- Remote implementation proof: `git ls-remote origin main` returned `0e1a5d445e89f37511df6a69482cb4ab5374682d refs/heads/main`.

No destructive Git operation was used.

## Files Changed

- `core/src/packlab_core/calibration/profile.py`
- `tests/calibration/test_profile_storage.py`
- `docs/calibration/profile-storage.md`
- `tests/calibration/test_synthetic_ground_truth.py`
- `coordination/sessions/M02-C001/PL-0066_CODEX_LOG_V02.md`

`tests/calibration/test_synthetic_ground_truth.py` is a minimal adjacent regression update required because a synthetic profile without owner/native/physical provenance is now correctly invalid for reuse under the PL-0066 V02 fail-closed contract.

## Defect Mapping

Blocking V01 audit findings:

1. Profile reuse did not validate full persisted structural contract before compatibility.
2. Profiles with unavailable owner/native/physical provenance could be reusable.
3. Timestamp checks only used a suffix test.
4. Runtime structural checks were weaker than `calibration-profile.schema.json`.
5. Tests did not cover the invalidation dimensions claimed by the contract/log.

Remediation:

- Added runtime construction of the persisted profile document shape and validation through `schemas/packscan/calibration-profile.schema.json` with Draft 2020-12 and format checking.
- Added explicit fail-closed structural/provenance checks for:
  - valid profile ID;
  - known schema version;
  - known resolution policy;
  - non-empty required key strings;
  - valid camera position, orientation and focus mode;
  - positive image dimensions;
  - positive finite zoom factor;
  - owner physical session source;
  - owner-device native capture evidence;
  - owner-completed physical measurement evidence;
  - accepted/warning quality status;
  - confidence score in `[0, 1]`;
  - non-negative reprojection RMSE;
  - accepted view count `>= 1`;
  - real RFC3339 UTC timestamps ending in `Z`;
  - required unit constants.
- Preserved exact-resolution compatibility and explicitly allowed same-aspect `uniform_scale_about_origin` compatibility only after structural/provenance validation succeeds.
- Added tests for unavailable provenance, malformed timestamps, invalid dimensions, empty key fields, bad confidence score, bad RMSE, invalid accepted-view count, unknown policy and unknown schema version.
- Updated synthetic-ground-truth profile reuse expectation so synthetic evidence remains accepted for mathematical confidence but invalid for reusable calibration profile storage.
- Updated profile-storage docs to state schema validation and required provenance/evidence states.

## Validation

Expected result: exit code `0`; listed pass counts. Failure condition: invalid structural/provenance profile returning compatible, schema/runtime drift, synthetic provenance being reusable, lint failure, `TASKS.md` diff, whitespace error, secret/signing match, or fabricated physical/native evidence.

| Command | Actual Result |
|---|---|
| `python -m ruff format core\src\packlab_core\calibration\profile.py tests\calibration\test_profile_storage.py tests\calibration\test_synthetic_ground_truth.py` | `3 files left unchanged`. |
| `$env:PYTHONPATH='core/src'; python -m pytest tests\calibration\test_profile_storage.py` | `11 passed in 0.16s`. |
| `$env:PYTHONPATH='core/src'; python -m pytest tests\calibration\test_profile_storage.py tests\calibration\test_synthetic_ground_truth.py` | `17 passed in 0.16s`. |
| `$env:PYTHONPATH='core/src'; python -m ruff check core\src\packlab_core\calibration\profile.py tests\calibration\test_profile_storage.py tests\calibration\test_synthetic_ground_truth.py` | Initial run requested `datetime.UTC`; fixed. Final run: `All checks passed!`. |
| `$env:PYTHONPATH='core/src;C:\Users\sekip\AppData\Local\Temp\packlab-cv'; python -m pytest tests\calibration` | `58 passed in 0.28s`. |
| `$env:PYTHONPATH='core/src;C:\Users\sekip\AppData\Local\Temp\packlab-cv'; python -m pytest tests\packscan tests\calibration` | `114 passed, 1 warning in 0.54s`; warning is the expected duplicate ZIP-entry warning in the negative PackScan duplicate-name test. |
| `python -m mypy core\src\packlab_core\calibration\profile.py tests\calibration\test_profile_storage.py tests\calibration\test_synthetic_ground_truth.py` | Unavailable on this Windows Python: `No module named mypy`. No type-pass claim is made. |
| `git diff --check` | Passed. Git printed only LF-to-CRLF working-copy normalization warnings for touched text files. |
| `git diff -- TASKS.md` | Empty. |
| `rg -n "BEGIN|PRIVATE KEY|API[_-]?KEY|TOKEN|PASSWORD|SECRET|DEVELOPMENT_TEAM|PROVISIONING_PROFILE|CODE_SIGN_IDENTITY" core\src\packlab_core\calibration\profile.py docs\calibration\profile-storage.md tests\calibration\test_profile_storage.py tests\calibration\test_synthetic_ground_truth.py` | No matches; command exited `1` for no matches. |

## Focused Evidence

Focused PL-0066 tests now prove every invalid structural/provenance case returns `invalid`, `reusable = False`, no compatibility reasons, and an explicit reason:

- unavailable/placeholder provenance;
- malformed created/verified timestamps;
- zero/negative dimensions;
- empty device model and lens identity;
- confidence score out of range;
- negative reprojection RMSE;
- zero accepted view count;
- unknown resolution policy;
- unknown schema version.

## Scope, Privacy, and Limitations

- `TASKS.md` was read only and not edited.
- No ChatGPT audit artifact was created or edited.
- No PL-0067, PL-0068, or M03 work was started.
- No secret, credential, signing material, private Kenya scan, confidential supplier file, cache, native/device, or physical evidence was added.
- No owner-native capture, printer, ruler, device, or physical measurement validation was performed or claimed.
- Synthetic profiles remain invalid for reuse unless owner/native/physical evidence states are present.

## Push Evidence

- Implementation commit pushed to `origin/main`: `0e1a5d445e89f37511df6a69482cb4ab5374682d`.
- Remote proof after push: `git ls-remote origin main` returned `0e1a5d445e89f37511df6a69482cb4ab5374682d refs/heads/main`.

READY_FOR_INDEPENDENT_AUDIT
