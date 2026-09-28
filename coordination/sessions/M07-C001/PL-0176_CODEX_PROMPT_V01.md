# PL-0176 - Codex Work Order V01

Task: **Implement the OpenMVS mesh-reconstruction stage**

Repository:
https://github.com/Sekiph82/PackLab

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CHATGPT_AUDIT_V02.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`READY` / `CODEX` for PL-0176 and point to this prompt and criteria. Preserve
PL-0175 as `AUDITED_PASS`, preserve PL-0068 as `OWNER_REQUIRED`, and keep
PL-0177 and later unauthorized. If the live tracker does not match, stop with
`TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
PL-0175 V02 prompt/criteria/log/audit, the accepted dense-stage source and
tests, the shared reconstruction-process/result/probe contracts, the OpenReality
architecture and ADR-0003, and the pinned OpenMVS v2.4.0
`ReconstructMesh.cpp` option declarations before editing:

https://github.com/cdcseacave/openMVS/blob/v2.4.0/apps/ReconstructMesh/ReconstructMesh.cpp

## Frozen scope

Create a PackLab-owned, backend-neutral mesh-reconstruction adapter for the
accepted dense point-cloud output identity. It must:

1. accept an immutable, provenance-bound mesh request derived from one
   successful dense-stage result, with safe relative input/output asset IDs,
   source/plan/configuration/request digests, and the pinned OpenMVS `2.4.0`
   identity;
2. map a small PackLab-owned semantic configuration to the exact pinned
   `ReconstructMesh` argv at one adapter boundary, with explicit validation of
   supported options and rejection of raw/caller-controlled CLI arguments;
3. require an explicit, already-probed OpenMVS `ReconstructMesh` executable and
   verify the supplied probe is valid, version `2.4.0`, and for the same
   executable;
4. execute only through the existing `run_reconstruction_stage` /
   `run_process` boundary with `shell=False`, bounded redacted output,
   timeout/cancellation propagation, and no filesystem discovery or engine
   installation;
5. normalize success, failure, cancellation, exit code, stage identity, mesh
   output identity, and provenance into an immutable typed result. Failed or
   cancelled runs must not expose a successful mesh output;
6. preserve the reconstruction authority model: output is
   `RECONSTRUCTION_OBSERVATION`, uses `RELATIVE` or `METRIC_UNVERIFIED` scale
   only, and never claims Scan Master, CAD, measurement, or engineering
   authority;
7. retain exact dense-input, source, plan, configuration, and request identity
   without parsing engine output as geometry or claiming mesh quality/counts.

Keep the initial configuration to the reconstruction options of the pinned
stage: input/output asset IDs plus validated finite/non-negative
`min_point_distance`, boolean `integrate_only_roi`, boolean `constant_weight`,
boolean `free_space_support`, finite/non-negative `thickness_factor`, and
finite/non-negative `quality_factor`, with defaults matching OpenMVS v2.4.0.
Do not include the pinned tool's cleaning, decimation, hole-closing, smoothing,
or mesh-export options; those belong to later contracts.

Use the existing PackLab process, stage-result, engine-probe, asset-ID, digest,
cancellation, and redaction conventions. The adapter may be tested with a
fake stage runner; no OpenMVS executable is required for repository validation.

Do not implement mesh refinement, texturing, output preservation/manifests
beyond the bounded mesh-stage result, orchestration, engine discovery,
installation, downloading, dense-stage changes, feature extraction, matching,
sparse mapping, camera solving, segmentation, UI, neural or generative models,
metric calibration, filesystem health/materialization, schema/dependency/lock
changes, physical/native-device acceptance, or PL-0177+ work.

## Allowed files

- `core/src/packlab_core/mesh_reconstruction.py`
- `tests/core/test_mesh_reconstruction.py`
- `coordination/sessions/M07-C001/PL-0176_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, PL-0175 or accepted
predecessor files, schemas, dependency/lock files, generated artifacts,
binaries, secrets, private scans, signing material, UI code, engine binaries,
or PL-0177+ code. Do not broaden the allowed-file list without stopping for a
task-state/specification mismatch.

## Validation and publication

Run and record each exact check with expected result, failure condition, actual
result, and exit status:

- focused PL-0176 tests plus the accepted PL-0175 dense-stage and shared
  conversion, process, probe, reconstruction, capability, and preset boundary
  suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on every changed Python path;
- targeted mypy on the changed implementation path, reporting unchanged
  repository debt if the repository-wide check remains non-clean;
- compileall on every changed Python implementation/test path;
- `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets,
  generated, binary, and remote-visibility checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0176_CODEX_LOG_V01.md`, and end that log exactly with:

`AWAITING_AUDIT`

Stop after handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0177.
