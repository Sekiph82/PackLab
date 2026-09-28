# PL-0177 - Codex Work Order V01

Task: **Implement the OpenMVS mesh-refinement stage**

Repository:
https://github.com/Sekiph82/PackLab

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CHATGPT_AUDIT_V02.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0177_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0177_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`READY` / `CODEX` for PL-0177 V01 and point to this prompt and criteria.
Preserve PL-0176 as `AUDITED_PASS`, preserve PL-0068 as `OWNER_REQUIRED`, and
keep PL-0178 and later unauthorized. If the live tracker does not match, stop
with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
accepted PL-0176 V02 audit/log, the accepted mesh-stage source and tests, the
shared reconstruction-process/result contracts, and the pinned OpenMVS v2.4.0
`ReconstructMesh.cpp` option declarations before editing:

https://github.com/cdcseacave/openMVS/blob/v2.4.0/apps/ReconstructMesh/ReconstructMesh.cpp

## Frozen implementation scope

Add one PackLab-owned, backend-specific mesh-refinement boundary in a new
`mesh_refinement.py` module and its public tests. The boundary must:

1. Accept only a successful `MeshReconstructionRun` with a non-null mesh
   output identity. Preserve source revision/digest, dense and mesh request
   digests, reconstruction authority, and the predecessor scale state. The
   refined result remains `RECONSTRUCTION_OBSERVATION`; it must not claim
   metric verification, Scan Master, CAD, measurement, or engineering
   authority.
2. Define immutable semantic configuration for the pinned OpenMVS v2.4.0
   cleaning/refinement options only:
   - `decimate`: finite float in `(0, 1]`;
   - `target_face_num`, `close_holes`, and `smooth`: non-negative integers,
     rejecting booleans;
   - `remove_spurious` and `edge_length`: finite non-negative floats;
   - `remove_spikes` and `crop_to_roi`: strict booleans; and
   - `roi_border`: a finite float, where zero is disabled and positive or
     negative values retain the pinned percentage/absolute semantics.
   Reject unknown/caller-controlled options and unsafe/colliding asset IDs
   through PackLab-owned errors before command construction.
3. Use a deterministic default refined output identity distinct from the
   predecessor mesh identity, and include canonical configuration and request
   digests in serialized request/result provenance.
4. Build the exact shell-free `ReconstructMesh` refinement argv using the
   explicit `--mesh-file` input, `--output-file` output, and the clean-option
   spellings/order declared by the pinned source. Do not add hidden mesh
   export, export-type, texture, discovery, installation, or arbitrary argv
   passthrough options.
5. Require an explicit matching valid `openmvs.ReconstructMesh` probe at
   version `2.4.0`, and delegate execution to the existing bounded,
   redacted, shell-free `run_reconstruction_stage` seam with timeout,
   cancellation, cwd, and environment propagation.
6. Normalize success, failure, cancellation, malformed stage identity/status,
   exit-code/duration/output, and non-boolean cancellation values fail-closed.
   Only a coherent successful result may expose the configured refined output
   identity. Never expose output on failure, cancellation, or malformed input.

Do not materialize or parse meshes, infer face counts/quality, preserve output
files/logs, add orchestration, implement texturing or later stages, modify the
accepted mesh stage/shared contracts, add discovery/installation/downloads,
change schemas/dependencies/locks, edit UI, claim physical/native-device
acceptance, or start PL-0178+ work.

## Allowed files

- `core/src/packlab_core/mesh_refinement.py`
- `tests/core/test_mesh_refinement.py`
- `coordination/sessions/M07-C001/PL-0177_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any ChatGPT audit artifact, accepted PL-0166 through
PL-0176 files, schemas, dependency/lock files, generated artifacts, binaries,
secrets, private scans, signing material, UI code, engine binaries, or
PL-0178+ code. Do not broaden the allowed-file list without stopping for a
task-state or specification mismatch.

## Validation and publication

Run and record every required check with exact command, expected result,
failure condition, actual result, and exit status:

- focused PL-0177 tests plus the accepted PL-0176 mesh, PL-0175 dense-stage,
  and shared conversion, process, probe, reconstruction, capability, and
  preset suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on every changed Python path;
- targeted mypy on the changed implementation path, reporting unchanged
  repository-wide debt if the aggregate check remains non-clean;
- compileall on every changed Python implementation/test path;
- `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets,
  generated, binary, and remote-visibility checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0177_CODEX_LOG_V01.md`, and end that log exactly with:

`AWAITING_AUDIT`

Stop after handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0178.
