# PL-0174 - Codex Work Order V02

Task: **Remediate COLMAP artifact record validation in the OpenMVS conversion boundary**

Repository:
https://github.com/Sekiph82/PackLab

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CHATGPT_AUDIT_V01.md

Prior prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CODEX_PROMPT_V01.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CODEX_LOG_V02.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`CHANGES_REQUIRED` / `CODEX` for PL-0174 and point to this prompt and criteria.
Preserve PL-0173 as `AUDITED_PASS`, PL-0068 as `OWNER_REQUIRED`, and PL-0175
and later as unauthorized. If the live tracker does not match, stop with
`TASK_STATE_MISMATCH`.

Read the V01 audit, V01 prompt/criteria/log, accepted sparse-export source and
tests, the PL-0163 reconstruction contract, the M07 engine baseline, and the
OpenReality architecture before editing. Preserve the accepted PL-0166
through PL-0173 contracts.

## Frozen remediation scope

Correct only the PL-0174 public conversion-boundary integrity gap identified
in `PL-0174_CHATGPT_AUDIT_V01.md`:

1. Validate the actual four COLMAP text artifacts, not only their names,
   UTF-8 encoding, counts, and cross-file IDs. Align the parser with the
   accepted sparse-export contract, including the supported camera-model
   allowlist and parameter cardinality, positive integer camera dimensions,
   non-zero image quaternions, safe unique image names, valid finite image
   poses/observations, bounded point values, RGB integer/range validation,
   and non-empty point tracks. Preserve the existing exact count and track
   consistency checks.
2. Add public-boundary regression tests proving the malformed camera, image,
   and point records from the V01 finding fail closed, plus any directly
   related boundary needed to show the parser is sensitive to the accepted
   producer contract. Tests must not weaken or rewrite accepted predecessor
   behavior.
3. Keep the immutable plan, canonical serialization/digest, OpenMVS `2.4.0`
   pin, authority limitations, no-execution boundary, and all V01 behavior
   unchanged except for the bounded validation correction.

Do not implement OpenMVS execution/discovery, `.mvs` writing, dense/mesh/
texture stages, orchestration, feature/matcher/image/camera processing beyond
the artifact parser correction, UI, neural/generative models, metric
calibration, filesystem materialization, schema/dependency/lock changes,
physical/native-device acceptance, or PL-0175+ work.

## Allowed files

- `core/src/packlab_core/openmvs_conversion.py`
- `tests/core/test_openmvs_conversion.py`
- `coordination/sessions/M07-C001/PL-0174_CODEX_LOG_V02.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, V01 prompt/criteria/
log/audit, accepted PL-0166 through PL-0173 files, schemas, dependency/lock
files, generated artifacts, binaries, secrets, private scans, signing
material, UI code, engine binaries, or PL-0175+ code.

## Validation and publication

Run and record each exact check with expected result, failure condition, actual
result, and exit status:

- focused PL-0174 V02 tests plus the accepted sparse-export, sparse-mapping,
  sparse-diagnostics, reconstruction, reconstruction-process, engine,
  capability, feature, matcher, and preset boundary suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on every changed Python path;
- targeted mypy on the changed implementation path, reporting unchanged
  repository debt if the repository-wide check remains non-clean;
- compileall on every changed Python implementation/test path;
- `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets,
  generated, binary, and remote-visibility checks.

Use a separate implementation/evidence commit and log-only commit, push only
`origin main`, verify remote visibility, create exactly
`PL-0174_CODEX_LOG_V02.md`, and end that log exactly with:

`AWAITING_AUDIT`

Stop after handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0175.
