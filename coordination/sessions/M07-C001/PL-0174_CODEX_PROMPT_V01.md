# PL-0174 - Codex Work Order V01

Task: **Implement COLMAP-to-OpenMVS scene conversion**

Repository:
https://github.com/Sekiph82/PackLab

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0173_CHATGPT_AUDIT_V01.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`READY` / `CODEX` for PL-0174 and point to this prompt and criteria. Preserve
PL-0173 as `AUDITED_PASS`, PL-0068 as `OWNER_REQUIRED`, and PL-0175 and later
as unauthorized. If the live tracker does not match, stop with
`TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
PL-0173 prompt/criteria/log/audit, the accepted PL-0172 sparse-export
prompt/criteria/log/audit and source contract, the PL-0163 reconstruction
contract, the M07 engine baseline, and the OpenReality architecture before
editing. Preserve immutable PackScan authority, backend-neutral reconstruction
semantics, explicit engine provenance, and the accepted PL-0166 through
PL-0173 contracts.

## Frozen scope

Create a PackLab-owned, backend-neutral, deterministic COLMAP-to-OpenMVS scene
conversion boundary over the accepted in-memory `SparseExportBundle`. This is
the conversion-seam pass: it produces an immutable, machine-readable
`OpenMVSSceneConversionPlan` for a later explicitly owned OpenMVS execution
stage. It must not pretend to materialize an `.mvs` file or run an external
engine. The boundary must:

1. accept only an explicit valid `SparseExportBundle` with the four accepted
   COLMAP artifacts and its debug manifest; validate the manifest contract,
   artifact names, source/revision/request/output identity, record counts,
   engine identity, and declared limitations rather than inferring a scene
   from arbitrary text or filesystem paths;
2. define an immutable, typed conversion plan pinned to the accepted OpenMVS
   baseline `2.4.0`, carrying the source revision/digest, sparse request
   digest, input artifact identities/digests, camera convention, record
   counts, a safe PackLab-relative output scene asset ID, and explicit
   conversion limitations;
3. preserve the complete COLMAP artifact provenance and produce canonical
   UTF-8-safe JSON plus a stable SHA-256 plan/configuration digest; equivalent
   mapping insertion orders must serialize and digest identically;
4. reject missing or duplicate artifacts, malformed or contradictory manifests,
   mismatched counts/digests/identities, unsafe relative IDs, absolute/private
   paths, control characters, non-finite metadata, unsupported engine versions,
   and caller-controlled OpenMVS/CLI option injection;
5. expose only PackLab-owned semantic fields to callers. If an adapter helper
   is needed to describe a later executable invocation, keep any
   OpenMVS-specific command mapping inside that adapter boundary, do not run it,
   and do not place the executable path in portable plan JSON;
6. preserve the distinction between source evidence, relative reconstruction
   output, metric verification, and later dense/mesh/texture stages. The plan
   must not claim filesystem materialization, dense reconstruction, mesh,
   texture, CAD, Scan Master, or `METRIC_VERIFIED` authority;
7. remain compatible with the accepted `SparseExportBundle`,
   `ReconstructionJobSpec`, and request/output identity models without changing
   accepted PL-0166 through PL-0173 behavior.

Do not implement OpenMVS execution, engine discovery/installation, `.mvs`
binary writing, dense point-cloud/mesh/refinement/texture stages, orchestration,
feature extraction, matcher execution, image or pixel processing, camera
solving, segmentation, mask lifting, UI, neural or generative models, metric
calibration, filesystem health/materialization, schema changes,
dependency/lock changes, physical/native-device acceptance, or PL-0175+ work.

## Allowed files

- `core/src/packlab_core/openmvs_conversion.py`
- `tests/core/test_openmvs_conversion.py`
- `coordination/sessions/M07-C001/PL-0174_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, accepted PL-0166
through PL-0173 files, schemas, dependency/lock files, generated artifacts,
binaries, secrets, private scans, signing material, UI code, engine binaries,
or PL-0175+ code. Do not broaden the allowed-file list without stopping for a
task-state/specification mismatch.

## Validation and publication

Run and record each exact check with expected result, failure condition, actual
result, and exit status:

- focused PL-0174 tests plus the accepted sparse-export, sparse-mapping,
  sparse-diagnostics, reconstruction, reconstruction-process, engine,
  capability, feature, matcher, and preset boundary suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on every changed Python path;
- targeted mypy on the changed implementation path, reporting unchanged
  repository debt if the repository-wide check remains non-clean;
- compileall on every changed Python implementation/test path;
- `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets,
  generated, binary, and remote-visibility checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0174_CODEX_LOG_V01.md`, and end the log exactly with:

`AWAITING_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0175.
