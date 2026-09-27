# PL-0174 - Codex Work Order V03

Task: **Correct remaining COLMAP artifact contract compatibility at the OpenMVS conversion boundary**

Repository:
https://github.com/Sekiph82/PackLab

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CHATGPT_AUDIT_V02.md

Prior prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CODEX_PROMPT_V02.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CHATGPT_AUDIT_CRITERIA_V03.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CODEX_LOG_V03.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`CHANGES_REQUIRED` / `CODEX` for PL-0174 and point to this prompt and criteria.
Preserve PL-0173 as `AUDITED_PASS`, PL-0068 as `OWNER_REQUIRED`, and PL-0175
and later as unauthorized. If the live tracker does not match, stop with
`TASK_STATE_MISMATCH`.

Read the V02 audit, V02 prompt/criteria/log, the accepted sparse-export source
and tests, and the existing PL-0174 source/tests before editing. Preserve the
accepted PL-0166 through PL-0173 contracts and all V02 behavior that is not
explicitly corrected below.

## Frozen remediation scope

Correct only the two findings in `PL-0174_CHATGPT_AUDIT_V02.md`:

1. Apply the accepted `SparseExportCamera` model-specific positive focal-
   parameter rule at the public COLMAP camera-artifact parser. Preserve the
   supported model allowlist, exact parameter cardinality, positive integer
   dimensions, finite parameters, bounded IDs, and existing count/reference
   checks. Add a public-boundary regression proving non-positive focal data is
   rejected.
2. Parse `images.txt` header/observation pairs without discarding the
   meaningful blank observation line emitted by the accepted sparse exporter
   when an image has zero 2D observations. A valid accepted bundle with empty
   observation lists must convert successfully. Preserve rejection of odd or
   malformed image pairs, unsafe/duplicate names, invalid finite pose fields,
   invalid point IDs, exact counts, camera references, point references, and
   observation/track equality. Add a public-boundary regression for valid
   zero-observation export data.

Do not loosen control-character, UTF-8, artifact, manifest, provenance,
authority, path, count, or cross-file validation beyond what is required to
represent the accepted sparse-export contract.

Keep the immutable plan, canonical serialization/digest, COLMAP `3.12.6` and
OpenMVS `2.4.0` pins, authority limitations, no-execution boundary, and all
V02 malformed-record tests unchanged except for the bounded correction.

Do not implement OpenMVS execution/discovery, `.mvs` writing, dense/mesh/
texture stages, orchestration, feature/matcher/image/camera processing beyond
these two parser corrections, UI, neural/generative models, metric
calibration, filesystem materialization, schema/dependency/lock changes,
physical/native-device acceptance, or PL-0175+ work.

## Allowed files

- `core/src/packlab_core/openmvs_conversion.py`
- `tests/core/test_openmvs_conversion.py`
- `coordination/sessions/M07-C001/PL-0174_CODEX_LOG_V03.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, V01/V02 prompt,
criteria, log, or audit, accepted PL-0166 through PL-0173 files, schemas,
dependency/lock files, generated artifacts, binaries, secrets, private scans,
signing material, UI code, engine binaries, or PL-0175+ code.

## Validation and publication

Run and record each exact check with expected result, failure condition, actual
result, and exit status:

- focused PL-0174 V03 tests plus the accepted sparse-export, sparse-mapping,
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
`PL-0174_CODEX_LOG_V03.md`, and end that log exactly with:

`AWAITING_AUDIT`

Stop after handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0175.
