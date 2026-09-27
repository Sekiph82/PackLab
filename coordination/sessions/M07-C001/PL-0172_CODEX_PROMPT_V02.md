# PL-0172 - Codex Remediation Work Order V02

Task: **Close the missing cancelled-run public-boundary coverage**

Repository:
https://github.com/Sekiph82/PackLab

Failed audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CHATGPT_AUDIT_V01.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CODEX_LOG_V02.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`CHANGES_REQUIRED` / `CODEX` for PL-0172 and point to this V02 prompt and
criteria. Preserve PL-0171 as `AUDITED_PASS`, PL-0068 as `OWNER_REQUIRED`, and
PL-0173 and later as unauthorized. If the live tracker does not match, stop
with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
PL-0172 V01 prompt/criteria/log/audit, and the accepted reconstruction/run
contracts before editing. Preserve the V01 implementation and all accepted
V01 evidence.

## Frozen remediation scope

Add the missing public-boundary regression coverage for cancelled sparse runs:

1. Construct a valid cancelled `SparseMappingRun` using the accepted
   `RunStatus.CANCELLED`, `StageStatus.CANCELLED`, and cancellation/exit
   contract.
2. Supply the existing valid explicit `SparseExportPayload` fixture.
3. Assert `export_sparse_mapping` rejects the cancelled run and produces no
   export bundle.
4. Keep the test deterministic and independent of stdout/stderr, filesystem
   state, engine discovery, or external COLMAP/OpenMVS executables.

Do not change `core/src/packlab_core/sparse_export.py`; V01 source inspection
found the rejection boundary present, and this remediation closes the missing
test evidence only. Do not alter accepted V01 tests except for the imports or
minimal fixture wiring needed by the cancelled-run test.

## Allowed files

- `tests/core/test_sparse_export.py`
- `coordination/sessions/M07-C001/PL-0172_CODEX_LOG_V02.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, the V01 audit, accepted
PL-0166 through PL-0171 files, `core/src/packlab_core/sparse_export.py`,
schemas, dependency/lock files, generated artifacts, binaries, secrets,
private scans, signing material, UI code, engine binaries, or PL-0173+ code.

## Validation and publication

Run and record each exact check with expected result, failure condition,
actual result, and exit status:

- focused PL-0172 and accepted sparse/diagnostic/reconstruction/process/engine/
  feature/matcher suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on the changed test path;
- targeted mypy on the unchanged implementation path, reporting unchanged
  repository debt if the repository-wide check remains non-clean;
- compileall on the changed test path;
- `git diff --check`, protected-file/scope/privacy/secrets/generated/binary
  checks, and remote visibility.

Use separate test/evidence and log-only commits, push only `origin main`,
verify remote visibility, create exactly `PL-0172_CODEX_LOG_V02.md`, preserve
the V01 implementation commit as the baseline, and end the log exactly with:

`AWAITING_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0173.
