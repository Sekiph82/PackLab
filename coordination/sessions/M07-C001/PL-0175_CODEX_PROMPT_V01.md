# PL-0175 - Codex Work Order V01

Task: **Implement the OpenMVS dense point-cloud stage**

Repository:
https://github.com/Sekiph82/PackLab

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CHATGPT_AUDIT_V03.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`READY` / `CODEX` for PL-0175 and point to this prompt and criteria. Preserve
PL-0174 as `AUDITED_PASS`, PL-0068 as `OWNER_REQUIRED`, and PL-0176 and later
as unauthorized. If the live tracker does not match, stop with
`TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
PL-0174 V03 prompt/criteria/log/audit, the accepted sparse-mapping,
reconstruction-process, engine-probe, reconstruction, and conversion source
contracts/tests, the PL-0163 reconstruction contract, the M07 engine baseline,
and the OpenReality architecture before editing. Read the pinned OpenMVS
2.4.0 `DensifyPointCloud` command semantics at:

https://github.com/cdcseacave/openMVS/blob/v2.4.0/apps/DensifyPointCloud/DensifyPointCloud.cpp

## Frozen scope

Create a PackLab-owned, backend-neutral dense point-cloud adapter over the
accepted `OpenMVSSceneConversionPlan`. This is the first executing OpenMVS
stage. It must:

1. accept an immutable, provenance-bound dense-stage request derived from one
   accepted conversion plan, with safe relative input/output asset IDs,
   source/plan/configuration digests, and the pinned OpenMVS `2.4.0` identity;
2. map PackLab-owned semantic configuration to the exact pinned
   `DensifyPointCloud` argv at one adapter boundary, with tests asserting the
   complete argv and rejecting unsupported or caller-controlled options;
3. require an explicit, already-probed OpenMVS dense executable and prove that
   the supplied probe is valid, version `2.4.0`, for the same executable;
4. execute only through the existing `run_reconstruction_stage` /
   `run_process` boundary with `shell=False`, bounded redacted stdout/stderr,
   timeout and cancellation propagation, and no filesystem discovery or
   engine installation;
5. normalize success, failure, cancellation, exit code, stage identity,
   output identity, and provenance into an immutable typed result. Failed or
   cancelled runs must not expose a successful dense output;
6. preserve the reconstruction authority model: outputs are
   `RECONSTRUCTION_OBSERVATION`, use `RELATIVE` or
   `METRIC_UNVERIFIED` scale only, never `METRIC_VERIFIED`, and do not claim
   Scan Master, CAD, measurement, or engineering authority;
7. retain exact input plan/configuration identity and portable stage evidence
   without parsing arbitrary engine output as geometry or silently inferring
   point counts. Output preservation and later mesh/refinement/texture stages
   remain separate contracts.

Use the existing PackLab process, stage-result, engine-probe, asset-ID,
digest, cancellation, and redaction conventions. The adapter may be tested
with a fake stage runner; no OpenMVS executable is required for repository
validation.

Do not implement mesh reconstruction, mesh refinement, texturing, output
preservation/manifests beyond the bounded dense-stage result, orchestration,
engine discovery, installation, downloading, feature extraction, matching,
sparse mapping, camera solving, segmentation, mask lifting, UI, neural or
generative models, metric calibration, filesystem health/materialization,
schema/dependency/lock changes, physical/native-device acceptance, or
PL-0176+ work.

## Allowed files

- `core/src/packlab_core/dense_reconstruction.py`
- `tests/core/test_dense_reconstruction.py`
- `coordination/sessions/M07-C001/PL-0175_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, PL-0174 or accepted
PL-0166 through PL-0174 files, schemas, dependency/lock files, generated
artifacts, binaries, secrets, private scans, signing material, UI code,
engine binaries, or PL-0176+ code. Do not broaden the allowed-file list
without stopping for a task-state/specification mismatch.

## Validation and publication

Run and record each exact check with expected result, failure condition, actual
result, and exit status:

- focused PL-0175 tests plus the accepted PL-0174 conversion, sparse-mapping,
  reconstruction-process, engine-probe, reconstruction, capability, and
  preset boundary suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on every changed Python path;
- targeted mypy on the changed implementation path, reporting unchanged
  repository debt if the repository-wide check remains non-clean;
- compileall on every changed Python implementation/test path;
- `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets,
  generated, binary, and remote-visibility checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0175_CODEX_LOG_V01.md`, and end that log exactly with:

`AWAITING_AUDIT`

Stop after handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0176.
