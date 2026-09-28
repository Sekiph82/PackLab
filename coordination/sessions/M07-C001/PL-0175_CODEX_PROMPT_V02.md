# PL-0175 - Codex Remediation Work Order V02

Task: **Remediate the OpenMVS dense point-cloud semantic option boundary**

Repository:
https://github.com/Sekiph82/PackLab

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CHATGPT_AUDIT_V01.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CODEX_LOG_V02.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`CHANGES_REQUIRED` / `CODEX` for PL-0175 V02 and point to this prompt and
criteria. Preserve PL-0174 as `AUDITED_PASS`, preserve the V01 implementation,
log, and audit as immutable evidence, preserve PL-0068 as `OWNER_REQUIRED`,
and keep PL-0176 and later unauthorized. If the live tracker does not match,
stop with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
PL-0175 V01 prompt/criteria/log/audit, and the pinned OpenMVS v2.4.0
`DensifyPointCloud.cpp` option declarations before editing.

## Frozen remediation scope

Correct only the PackLab-owned semantic configuration validation in
`dense_reconstruction.py` and add behavior-sensitive public tests. The
validator must reject values outside the pinned OpenMVS domains before command
construction:

- `estimate_colors`: integer `0..2`;
- `estimate_normals`: integer `0..2`;
- `fusion_filter`: integer `0..2`; and
- `postprocess_dmaps`: a non-negative combination of supported flags `1`, `2`,
  and `4` only, with no unsupported bits (equivalently, `value & ~0b111 == 0`).

Preserve valid V01 defaults, complete argv spelling/order, request/result
provenance, authority/scale restrictions, probe matching, process-boundary
execution, output suppression, and all accepted predecessor behavior. Add
public tests through `DensePointCloudConfig.from_overrides` (and direct
construction where useful) proving each invalid boundary is rejected and
valid edge/composite values remain accepted.

Do not implement mesh/refinement/texture stages, output preservation,
orchestration, discovery, installation, downloads, schema/lock changes, UI,
metric calibration, physical/native-device acceptance, or PL-0176+ work.

## Allowed files

- `core/src/packlab_core/dense_reconstruction.py`
- `tests/core/test_dense_reconstruction.py`
- `coordination/sessions/M07-C001/PL-0175_CODEX_LOG_V02.md`

Do not edit `TASKS.md`, any ChatGPT audit artifact, V01 evidence, accepted
PL-0166 through PL-0174 files, schemas, dependency/lock files, generated
artifacts, binaries, secrets, private scans, signing material, UI code,
engine binaries, or PL-0176+ code.

## Validation and publication

Run and record each exact check with expected result, failure condition,
actual result, and exit status:

- focused PL-0175 tests plus the accepted predecessor boundary suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on every changed Python path;
- targeted mypy on the changed implementation path, reporting unchanged
  repository debt if the repository-wide check remains non-clean;
- compileall on every changed Python implementation/test path;
- `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets,
  generated/binary, and remote-visibility checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0175_CODEX_LOG_V02.md`, and end that log exactly with:

`AWAITING_AUDIT`

Stop after handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0176.
