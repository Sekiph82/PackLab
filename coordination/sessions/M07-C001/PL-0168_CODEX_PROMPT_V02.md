# PL-0168 - Codex Remediation Work Order V02

Task: **Feature-extraction configuration optimized first for packaged consumer goods**

Repository:
https://github.com/Sekiph82/PackLab

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CHATGPT_AUDIT_V01.md

Prior prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CODEX_PROMPT_V01.md

Prior criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CHATGPT_AUDIT_CRITERIA_V01.md

Prior log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CODEX_LOG_V01.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CODEX_LOG_V02.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`CHANGES_REQUIRED` / `CODEX` for this PL-0168 V02 remediation and point to
this prompt and criteria. PL-0158 through PL-0167 must remain accepted,
PL-0068 must remain `OWNER_REQUIRED`, and PL-0169 and later tasks must remain
unauthorized. If the live tracker does not match, stop with
`TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the V01
prompt/criteria/log/audit, the OpenReality architecture, the PL-0163 contract,
and the accepted M07 engine/configuration boundaries before editing. Preserve
all valid V01 behavior and the backend-neutral reconstruction boundary.

## Frozen remediation scope

Correct only the V01 audit finding in override normalization:

1. Make `FeatureExtractionConfig.from_overrides` and
   `FeatureExtractionConfig.with_overrides` deterministic when supported alias
   keys normalize to the same PackLab field. Equivalent mappings with the same
   key/value pairs must produce the same normalized configuration, serialization,
   and digest regardless of insertion order.
2. Do not silently let conflicting aliases overwrite one another. Reject
   conflicting `peak_threshold`/`contrast_threshold` combinations and
   conflicting canonical-plus-alias combinations explicitly, or implement a
   documented order-independent resolution that preserves provenance safety.
   Preserve valid single-key overrides and equivalent duplicate values.
3. Preserve immutability, bounds, finite-number checks, absolute-path checks,
   unsupported-option rejection, preset identity/defaults, canonical
   serialization, and COLMAP adapter mapping.
4. Add behavior-sensitive tests through the public PackLab boundary for equal
   mappings in opposite insertion orders, conflicting alias combinations,
   canonical-plus-alias combinations, serialization/digest equality, and
   non-mutation.

Do not implement feature-extraction execution, image processing, matching,
sparse mapping, camera solving, dense reconstruction, segmentation, mask
lifting, UI workflow, engine installation/execution, neural/generative models,
metric calibration, schema changes, dependency/lock changes, physical/native
device acceptance, or PL-0169+ work.

## Allowed files

- `core/src/packlab_core/feature_extraction.py`
- `tests/core/test_feature_extraction.py`
- `coordination/sessions/M07-C001/PL-0168_CODEX_LOG_V02.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, V01 evidence, prior
prompts/criteria/logs/audits, schemas, dependency/lock files, generated
artifacts, binaries, secrets, private scans, signing material, UI code, engine
executables, or PL-0169+ code.

## Validation and publication

Run and record every required check with exact command, expected result,
failure condition, actual result, and exit status:

- focused V02 tests and the relevant reconstruction-contract/engine-
  configuration boundaries;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff on every changed Python implementation/test path;
- targeted mypy on the changed Python implementation path, reporting the
  unchanged repository debt without adding errors;
- `python -m compileall -q` on every changed Python implementation path;
- `git diff --check` and protected-file/scope/privacy/secrets/generated/binary
  checks.

Review the actual changed-file set. Use separate implementation/evidence and
log-only commits, push only `origin main`, verify remote visibility, create
exactly `PL-0168_CODEX_LOG_V02.md`, and end it exactly with:

`READY_FOR_INDEPENDENT_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0169.
