# PL-0176 - Codex Remediation Work Order V02

Task: **OpenMVS mesh-reconstruction stage fail-closed remediation**

Repository:
https://github.com/Sekiph82/PackLab

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CHATGPT_AUDIT_V01.md

Prior prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CODEX_PROMPT_V01.md

Prior criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CHATGPT_AUDIT_CRITERIA_V01.md

Prior log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CODEX_LOG_V01.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CODEX_LOG_V02.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`CHANGES_REQUIRED` / `CODEX` for this PL-0176 V02 remediation and point to
this prompt and criteria. Preserve PL-0175 as `AUDITED_PASS`, preserve
PL-0068 as `OWNER_REQUIRED`, and keep PL-0177 and later unauthorized. If the
live tracker does not match, stop with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
V01 prompt/criteria/log/audit, the accepted PL-0175 dense-stage boundary and
tests, the shared reconstruction-process/result contracts, and the pinned
OpenMVS v2.4.0 `ReconstructMesh.cpp` option declarations before editing.

## Frozen remediation scope

Correct only the two V01 audit findings at the public mesh-stage boundary:

1. Translate `OverflowError` and equivalent unrepresentable numeric input in
   the finite/non-negative mesh configuration validation into the PackLab-owned
   `InvalidMeshReconstructionRequest` boundary. No raw conversion exception
   may escape `MeshReconstructionConfig.from_overrides` or direct semantic
   configuration construction for `min_point_distance`, `thickness_factor`,
   or `quality_factor`.
2. Require the runtime `ReconstructionStageResult.cancelled` value to be an
   actual boolean before status normalization or direct `MeshReconstructionRun`
   invariant validation. Non-boolean falsey or truthy values must fail closed;
   they must not expose mesh output or claim a valid success/cancellation.
3. Add behavior-sensitive public tests for huge numeric values, non-boolean
   cancellation values on success/failure/cancellation paths, direct-result
   construction, output suppression, and the retained valid/default/edge and
   malformed-stage behavior.

Preserve all accepted V01 request/configuration behavior, pinned command and
probe mapping, provenance/authority/scale contract, shell-free bounded and
redacted process seam, failure/cancellation output suppression, and all
predecessor regressions.

Do not implement PL-0177 mesh refinement, texturing, output preservation,
orchestration, discovery, installation, dense-stage changes, feature
extraction, matching, sparse mapping, camera solving, segmentation, UI,
neural/generative models, metric calibration, filesystem materialization,
schema/dependency/lock changes, physical/native-device acceptance, or any
PL-0177+ work.

## Allowed files

- `core/src/packlab_core/mesh_reconstruction.py`
- `tests/core/test_mesh_reconstruction.py`
- `coordination/sessions/M07-C001/PL-0176_CODEX_LOG_V02.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, the V01 evidence,
prior prompts/criteria/logs/audits, PL-0175 or accepted predecessor files,
schemas, dependency/lock files, generated artifacts, binaries, secrets,
private scans, signing material, UI code, engine binaries, or PL-0177+ code.
Do not broaden the allowed-file list without stopping for a task-state or
specification mismatch.

## Validation and publication

Run and record every required check with exact command, expected result,
failure condition, actual result, and exit status:

- focused PL-0176 V02 tests plus the accepted PL-0175 dense-stage and shared
  conversion, process, probe, reconstruction, capability, and preset suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on every changed Python path;
- targeted mypy on the changed implementation path, reporting unchanged
  repository-wide debt if the aggregate check remains non-clean;
- compileall on every changed Python implementation/test path;
- `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets,
  generated, binary, and remote-visibility checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0176_CODEX_LOG_V02.md`, and end that log exactly with:

`AWAITING_AUDIT`

Stop after handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0177.
