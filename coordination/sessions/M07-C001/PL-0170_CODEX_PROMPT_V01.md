# PL-0170 - Codex Implementation Work Order V01

Task: **Sparse mapper stage and registered-image statistics**

Repository:
https://github.com/Sekiph82/PackLab

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0169_CHATGPT_AUDIT_V01.md

Matching criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`READY` / `CODEX` for PL-0170 and point to this prompt and criteria. PL-0169
must remain accepted, PL-0068 must remain `OWNER_REQUIRED`, and PL-0171 and
later must remain unauthorized. If the live tracker does not match, stop with
`TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
accepted OpenReality architecture, the PL-0163 reconstruction contract, the
M07 engine baseline, and the accepted PL-0166 through PL-0169 boundaries
before editing. Preserve immutable PackScan source authority, backend
neutrality, explicit engine-version provenance, and the distinction between
implementation evidence and audit acceptance.

## Frozen scope

Implement only the PackLab-owned sparse-mapper stage boundary and registered-
image statistics needed after the accepted feature-extraction and matcher
selection boundaries:

1. Define an immutable sparse-mapper request/configuration value that binds the
   ordered input asset IDs, source revision/digest, matcher-selection digest,
   and the pinned COLMAP 3.12.6 engine identity. Validate repository-relative
   project asset IDs and reject missing, duplicate, unsafe, mismatched, or
   private absolute-path provenance.
2. Build an explicit COLMAP sparse-mapper command/configuration adapter for
   the existing PackLab reconstruction-stage runner. The adapter may execute
   only an explicitly supplied, already-probed executable through the existing
   bounded stage seam; it must not discover, install, download, or silently
   select an engine. Keep command construction separate from execution and
   redact portable stage evidence using the existing process boundary.
3. Normalize successful, failed, and cancelled stage outcomes into the
   existing PackLab `ReconstructionStageResult`/run semantics. Failure and
   cancellation must be deterministic, must preserve the immutable source
   evidence, and must not claim a successful sparse model when the process or
   output contract fails.
4. Capture deterministic registered-image statistics containing at minimum
   total input images, registered images, unregistered images, and a bounded
   registration ratio/count relationship. Parse only an explicit, documented
   machine-readable stage summary or injected test runner result; do not infer
   registration from image pixels or from an arbitrary human log sentence.
5. Expose backend-neutral values and canonical serialization/digest for the
   request and statistics. Map COLMAP names only in the adapter; do not add
   UI, sparse-model export, camera-file export, fragmented-model diagnosis,
   dense reconstruction, or later-task orchestration.
6. Add behavior-sensitive public-boundary tests for valid requests and exact
   source/order/provenance binding, command mapping, registered/unregistered
   statistics, malformed or inconsistent summaries, engine-version rejection,
   process failure/cancellation, non-mutation, redaction, and regression
   against the reconstruction/process/engine boundaries.

Do not implement failed/fragmented sparse-model diagnosis (PL-0171), sparse
model/camera export (PL-0172), preset orchestration (PL-0173), OpenMVS stages,
feature extraction, matcher selection changes, image processing, pixel/pair
computation, camera solving, segmentation, mask lifting, UI workflow, neural
or generative models, metric calibration, schema changes, dependency/lock
changes, physical/native-device acceptance, or PL-0171+ work.

## Allowed files

- `core/src/packlab_core/sparse_mapping.py`
- `tests/core/test_sparse_mapping.py`
- `core/src/packlab_core/reconstruction.py` only if a minimal additive type
  is required to carry the normalized sparse-stage result
- `core/src/packlab_core/reconstruction_process.py` only if a minimal additive
  redaction/runner seam is required and existing behavior remains unchanged
- `coordination/sessions/M07-C001/PL-0170_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, prior prompt, criteria,
log, or audit; accepted PL-0169 files; schemas; dependency/lock files;
generated artifacts; binaries; secrets; private scans; signing material; UI
code; engine binaries; or PL-0171+ code. Do not broaden the allowed-file list
without stopping for a task-state/specification mismatch.

## Validation and publication

Run and record every required check with the exact command, expected result,
failure condition, actual result, and exit status:

- focused PL-0170 tests and the relevant reconstruction/process/engine and
  accepted feature/matcher boundary suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff on every changed Python implementation/test path;
- targeted mypy on changed Python implementation paths, reporting unchanged
  repository debt without adding errors;
- `python -m compileall -q` on every changed Python implementation path;
- `git diff --check` and protected-file/scope/privacy/secrets/generated/
  binary checks.

Review the actual changed-file set. Use separate implementation/evidence and
log-only commits, push only `origin main`, verify remote visibility, create
exactly `PL-0170_CODEX_LOG_V01.md`, and end it exactly with:

`AWAITING_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0171.
