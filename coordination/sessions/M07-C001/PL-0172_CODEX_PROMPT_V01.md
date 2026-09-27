# PL-0172 - Codex Work Order V01

Task: **Export sparse model/cameras in formats needed by OpenMVS and debugging**

Repository:
https://github.com/Sekiph82/PackLab

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0171_CHATGPT_AUDIT_V01.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`READY` / `CODEX` for PL-0172 and point to this prompt and criteria. PL-0171
must remain independently accepted, PL-0068 must remain `OWNER_REQUIRED`, and
PL-0173 and later must remain unauthorized. If the live tracker does not match,
stop with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
PL-0171 prompt/criteria/audit/log, the accepted PL-0170 prompt/criteria/audit,
the OpenReality architecture, the PL-0163 reconstruction contract, and the M07
engine baseline before editing. Preserve immutable PackScan authority,
backend-neutral reconstruction semantics, explicit engine provenance, the
bounded/redacted process seam, and the accepted PL-0166 through PL-0171
contracts.

## Frozen scope

Implement a PackLab-owned, backend-neutral sparse-export boundary that produces
deterministic in-memory export artifacts for later OpenMVS conversion and
debugging. The boundary must:

1. accept only an explicitly supplied, validated successful `SparseMappingRun`
   and an explicit immutable export payload; do not infer cameras, points,
   registration, paths, or file contents from stdout/stderr or from an asset
   identity;
2. validate finite camera/image/point values, unique positive record IDs,
   camera references, image names, track references, RGB bounds, and the
   declared source/revision/request/output provenance before export;
3. emit the documented COLMAP text artifacts `cameras.txt`, `images.txt`, and
   `points3D.txt` with exact stable field ordering, deterministic numeric
   formatting, sorted records, required two-line image records, and comments
   that do not contain private paths or credentials;
4. emit a deterministic machine-readable debug manifest that records the
   export contract/version, source and request identity, engine identity,
   camera convention, record counts, relative artifact names, and explicit
   limitations. The manifest must not claim external filesystem materialization,
   metric calibration, dense reconstruction, or engineering/CAD authority;
5. return an immutable bundle of relative artifact names and UTF-8 contents,
   without writing arbitrary paths, discovering engines, invoking COLMAP or
   OpenMVS, or modifying the `SparseMappingRun` or its payload;
6. fail closed for failed/cancelled/invalid runs, missing or contradictory
   provenance, unsafe names/paths, duplicate or dangling IDs, non-finite
   numbers, malformed tracks, invalid camera models/parameters, or unsupported
   export options.

Use the accepted PL-0170 `SparseMappingRun`, `SparseMappingRequest`, and
PackLab reconstruction/process contracts. Keep COLMAP/OpenMVS details inside
the export boundary; do not leak raw third-party CLI syntax into callers.

Do not implement PL-0173 preset orchestration, OpenMVS/dense stages or scene
conversion, feature extraction, matcher changes, image/pixel processing, camera
solving, segmentation, mask lifting, UI, neural/generative models, metric
calibration, filesystem health probing, schema changes, dependency/lock
changes, physical/native-device acceptance, or PL-0173+ work.

## Allowed files

- `core/src/packlab_core/sparse_export.py`
- `tests/core/test_sparse_export.py`
- `coordination/sessions/M07-C001/PL-0172_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, accepted PL-0166
through PL-0171 files, schemas, dependency/lock files, generated artifacts,
binaries, secrets, private scans, signing material, UI code, engine binaries,
or PL-0173+ code. Do not broaden the allowed-file list without stopping for a
task-state/specification mismatch.

## Validation and publication

Run and record every required check with the exact command, expected result and
failure condition, actual result, and exit status:

- focused PL-0172 tests plus `test_sparse_mapping.py`,
  `test_sparse_diagnostics.py`, and the relevant reconstruction/process/engine
  and accepted feature/matcher boundary suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff on every changed Python implementation/test path;
- targeted mypy on the changed Python implementation path, reporting the
  unchanged repository debt without adding errors;
- `python -m compileall -q` on every changed Python implementation path;
- `git diff --check` and protected-file/scope/privacy/secrets/generated/
  binary checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0172_CODEX_LOG_V01.md`, and end it exactly with:

`AWAITING_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0173.
