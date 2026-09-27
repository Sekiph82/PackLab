# PL-0173 - Codex Work Order V01

Task: **Build a tunable reconstruction preset system rather than hardcoding CLI flags**

Repository:
https://github.com/Sekiph82/PackLab

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CHATGPT_AUDIT_V02.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0173_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0173_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`READY` / `CODEX` for PL-0173 and point to this prompt and criteria. Preserve
PL-0172 as `AUDITED_PASS`, PL-0068 as `OWNER_REQUIRED`, and PL-0174 and later
as unauthorized. If the live tracker does not match, stop with
`TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
PL-0172 prompt/criteria/log/audit, the accepted PL-0163 reconstruction
contract, the M07 engine baseline, and the accepted feature-extraction,
matcher, sparse-mapping, and sparse-export contracts before editing.

## Frozen scope

Create a PackLab-owned, backend-neutral, immutable reconstruction-preset
boundary that composes the already accepted configuration contracts without
leaking engine CLI syntax into domain callers. It must:

1. define a versioned `ReconstructionPreset` with a safe preset identity,
   explicit feature-extraction, matcher, and sparse-mapping configuration, and
   documented limitations; use the accepted component types rather than
   duplicating their fields or silently changing their defaults;
2. provide a named initial packaged-consumer-goods preset as an explicit
   starting configuration, while stating that it is not physical benchmark
   evidence or a universal optimum;
3. validate typed construction and bounded non-mutating overrides, reject
   unknown or unsupported fields, absolute/private paths, unsafe identities,
   non-finite values, conflicting aliases, and engine-specific CLI keys such as
   `SiftExtraction.*`, `SequentialMatching.*`, `Mapper.*`, or `--flag` forms;
4. serialize the complete PackLab-owned preset deterministically as UTF-8-safe
   canonical JSON and expose a stable SHA-256 configuration digest; equivalent
   values in different mapping insertion orders must produce identical
   serialization and digest;
5. expose a PackLab-owned configuration view that later stage adapters can
   consume, while keeping COLMAP/OpenMVS option mapping in the existing adapter
   functions and never discovering, installing, launching, or executing an
   external engine;
6. preserve source/revision/provenance boundaries and the distinction between
   relative reconstruction state and metric verification; the preset must not
   claim filesystem materialization, dense reconstruction, CAD authority, or
   `METRIC_VERIFIED` output;
7. remain compatible with the accepted `ReconstructionJobSpec` and sparse
   request identity model without modifying accepted PL-0166 through PL-0172
   behavior or implementing PL-0174+ orchestration.

Do not implement engine execution, preset orchestration, OpenMVS conversion,
dense/mesh/texture stages, feature extraction, matcher execution, image or
pixel processing, camera solving, segmentation, mask lifting, UI, neural or
generative models, metric calibration, filesystem health/materialization,
schema changes, dependency/lock changes, physical/native-device acceptance,
or PL-0174+ work.

## Allowed files

- `core/src/packlab_core/reconstruction_preset.py`
- `tests/core/test_reconstruction_preset.py`
- `coordination/sessions/M07-C001/PL-0173_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, accepted PL-0166
through PL-0172 files, existing feature/matcher/sparse/export source, schemas,
dependency/lock files, generated artifacts, binaries, secrets, private scans,
signing material, UI code, engine binaries, or PL-0174+ code. Do not broaden
the allowed-file list without stopping for a task-state/specification
mismatch.

## Validation and publication

Run and record each exact check with expected result, failure condition, actual
result, and exit status:

- focused PL-0173 tests plus the accepted feature, matcher, sparse-mapping,
  sparse-diagnostics, sparse-export, reconstruction/process, engine, and
  capability boundary suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on every changed Python path;
- targeted mypy on the changed implementation path, reporting unchanged
  repository debt if the repository-wide check remains non-clean;
- compileall on every changed Python implementation/test path;
- `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets,
  generated, binary, and remote-visibility checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0173_CODEX_LOG_V01.md`, and end the log exactly with:

`AWAITING_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0174.
