# PL-0178 - Codex Work Order V01

Task: **Implement the OpenMVS texture stage**

Repository:
https://github.com/Sekiph82/PackLab

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0177_CHATGPT_AUDIT_V01.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0178_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0178_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`READY` / `CODEX` for PL-0178 V01 and point to this prompt and criteria.
Preserve PL-0177 as `AUDITED_PASS`, preserve PL-0068 as `OWNER_REQUIRED`, and
keep PL-0179 and later unauthorized. If the live tracker does not match, stop
with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
accepted PL-0177 V01 audit/log and refinement source/tests, the accepted mesh
and shared reconstruction/process/result/probe contracts, and the pinned
OpenMVS v2.4.0 `TextureMesh.cpp` option declarations before editing:

https://github.com/cdcseacave/openMVS/blob/v2.4.0/apps/TextureMesh/TextureMesh.cpp

## Frozen implementation scope

Add one PackLab-owned, backend-specific texture-stage boundary in a new
`texture_reconstruction.py` module and its public tests. The boundary must:

1. Accept only a successful `MeshRefinementRun` with a non-null refined mesh
   output identity. Derive and validate the predecessor reconstruction scene
   identity from the accepted predecessor chain. Preserve source
   revision/digest, plan digest, dense and mesh request digests, refinement
   configuration/request digests, reconstruction authority, and predecessor
   scale state. The textured result remains
   `RECONSTRUCTION_OBSERVATION`; it must not claim `METRIC_VERIFIED`, Scan
   Master, CAD, measurement, or engineering authority.
2. Define immutable semantic configuration for the safe pinned OpenMVS
   `TextureMesh` options only:
   - `textured_mesh_output_asset_id`: safe relative identity, distinct from the
     refined mesh and scene identities;
   - `export_type`: exactly `ply`, `obj`, `glb`, or `gltf`;
   - `decimate`: finite float in `[0, 1]` (`0` is auto and `1` is disabled);
   - `close_holes`, `resolution_level`, `min_resolution`,
     `virtual_face_images`, and `texture_size_multiple`: non-negative integers,
     rejecting booleans;
   - `outlier_threshold` and `sharpness_weight`: finite non-negative floats;
   - `cost_smoothness_ratio`: finite float in `[0, 1]`;
   - `global_seam_leveling` and `local_seam_leveling`: strict booleans;
   - `patch_packing_heuristic`: non-negative integer in `[0, 100]`, rejecting
     booleans;
   - `empty_color`: integer in `[0, 0xFFFFFFFF]`, rejecting booleans;
   - `ignore_mask_label`: `-2`, `-1`, or a non-negative integer, rejecting
     booleans; and
   - `max_texture_size`: non-negative integer, rejecting booleans.
   Reject unknown/caller-controlled options and unsafe/colliding asset IDs
   through PackLab-owned errors before command construction.
3. Use a deterministic default textured output identity distinct from every
   predecessor input identity, and include canonical configuration and request
   digests in serialized request/result provenance.
4. Build the exact shell-free `TextureMesh` argv using the explicit
   `--input-file`, `--mesh-file`, `--output-file`, and `--export-type` values,
   followed by the semantic texture options in the pinned declaration order.
   Do not expose `--views-file`, `--orthographic-image-resolution`, CUDA,
   archive/process/verbosity controls, arbitrary argv passthrough, output
   preservation, or any hidden installation/discovery path.
5. Require an explicit matching valid `openmvs.TextureMesh` probe at version
   `2.4.0`, and delegate execution to the existing bounded, redacted,
   shell-free `run_reconstruction_stage` seam with timeout, cancellation, cwd,
   and environment propagation.
6. Normalize success, failure, cancellation, malformed stage identity/status,
   exit-code/duration/output, and non-boolean cancellation values fail-closed.
   Only a coherent successful result may expose the configured textured output
   identity. Never expose output on failure, cancellation, or malformed input.

Do not materialize or parse meshes/textures, infer texture quality or coverage,
preserve output files/logs, add orchestration, implement PL-0179 output
retention, add CPU/GPU presets, change accepted mesh/refinement/shared
contracts, add discovery/installation/downloads, change schemas/dependencies/
locks, edit UI, claim physical/native-device acceptance, or start PL-0179+ work.

## Allowed files

- `core/src/packlab_core/texture_reconstruction.py`
- `tests/core/test_texture_reconstruction.py`
- `coordination/sessions/M07-C001/PL-0178_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any ChatGPT audit artifact, accepted PL-0166 through
PL-0177 files, schemas, dependency/lock files, generated artifacts, binaries,
secrets, private scans, signing material, UI code, engine binaries, or
PL-0179+ code. Do not broaden the allowed-file list without stopping for a
task-state or specification mismatch.

## Validation and publication

Run and record every required check with exact command, expected result,
failure condition, actual result, and exit status:

- focused PL-0178 tests plus accepted PL-0177 refinement, PL-0176 mesh,
  PL-0175 dense-stage, and shared conversion, process, probe, reconstruction,
  capability, and preset suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on every changed Python path;
- targeted mypy on the changed implementation path, reporting unchanged
  repository-wide debt if the aggregate check remains non-clean;
- compileall on every changed Python implementation/test path;
- `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets,
  generated, binary, and remote-visibility checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0178_CODEX_LOG_V01.md`, and end that log exactly with:

`AWAITING_AUDIT`

Stop after handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0179.
