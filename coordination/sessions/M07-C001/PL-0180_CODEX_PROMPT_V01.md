# PL-0180 - Codex Work Order V01

Task: **Add CPU/GPU-aware presets and memory-safety limits**

Repository:
https://github.com/Sekiph82/PackLab

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CHATGPT_AUDIT_V03.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0180_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0180_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`READY` / `CODEX` for PL-0180 V01 and point to this prompt and criteria.
Preserve PL-0179 as `AUDITED_PASS`, preserve PL-0068 as `OWNER_REQUIRED`, and
keep PL-0181 and later unauthorized. If the live tracker does not match, stop
with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination/audit policies,
the accepted PL-0173 preset audit/log and source/tests, the capability
contract, and the shared reconstruction/job contracts before editing.

## Frozen implementation scope

Extend the existing backend-neutral reconstruction preset boundary with one
immutable, deterministic resource-policy layer. The policy must:

1. Define a PackLab-owned execution mode with exactly `cpu-only`,
   `gpu-preferred`, and `gpu-required` values. GPU selection must consume an
   explicit capability snapshot; do not infer CUDA from a driver label or
   launch a probe from the policy layer. `gpu-preferred` falls back to CPU
   with an explicit reason when direct CUDA capability is unavailable or
   unknown. `gpu-required` fails closed in that state.
2. Define bounded memory-safety limits for input bytes, working-set bytes,
   retained-output bytes, and parallel worker count. Values must be immutable,
   positive bounded integers where applicable, reject booleans and overflow,
   and reject internally inconsistent relationships. No unbounded or silently
   clamped value is accepted.
3. Provide named CPU-safe and GPU-aware resource presets with explicit
   versioned identities, truthful limitations, and stable canonical
   serialization/digests. Defaults are configuration starting points only;
   they are not physical benchmarks, engine performance guarantees, or
   universal hardware recommendations.
4. Resolve a resource plan from one preset, explicit capability records, and
   explicit input/work/output estimates. Reject any estimate over its limit
   before execution, preserve the selected mode and capability provenance,
   and distinguish CPU fallback, GPU selection, GPU-unavailable, and
   over-budget outcomes through PackLab-owned result/error types.
5. Keep the existing reconstruction preset fields, component defaults,
   backend-neutral authority, and deterministic provenance intact. Expose the
   resource policy through the existing preset configuration/provenance view
   without adding engine-specific CLI flags or changing COLMAP/OpenMVS adapter
   spelling/order.
6. Keep this pass declarative and preflight-only. Do not launch processes,
   discover/install/download engines, inspect live hardware from the policy
   object, reserve memory, add orchestration, alter output retention,
   implement cancellation, parse reconstruction output, or claim metric/CAD/
   Scan Master/physical/native-device authority.

Do not implement PL-0181+ work, change schemas/dependencies/locks, edit UI,
modify accepted reconstruction-stage contracts, or redesign PL-0179 evidence
retention.

## Allowed files

- `core/src/packlab_core/reconstruction_preset.py`
- `tests/core/test_reconstruction_preset.py`
- `coordination/sessions/M07-C001/PL-0180_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any ChatGPT audit artifact, accepted PL-0166 through
PL-0179 files, schemas, dependency/lock files, generated artifacts, binaries,
secrets, private scans, signing material, UI code, engine binaries, or
PL-0181+ code. Do not broaden this file list without stopping for a
task-state or specification mismatch.

## Validation and publication

Run and record every required check with exact command, expected result,
failure condition, actual result, and exit status:

- focused preset/resource-policy tests plus accepted feature-extraction,
  capability, reconstruction, process, stage-result, and PL-0179 retention
  suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on every changed Python path;
- targeted mypy on the changed implementation path, reporting unchanged
  repository-wide debt if the aggregate check remains non-clean;
- compileall on every changed Python implementation/test path;
- `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets,
  generated, binary, and remote-visibility checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0180_CODEX_LOG_V01.md`, and end that log exactly with:

`AWAITING_AUDIT`

Stop after handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0181.
