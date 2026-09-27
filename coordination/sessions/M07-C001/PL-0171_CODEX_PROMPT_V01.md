# PL-0171 - Codex Work Order V01

Task: **Detect failed/fragmented sparse models and produce actionable diagnostics**

Repository:
https://github.com/Sekiph82/PackLab

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CHATGPT_AUDIT_V02.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0171_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0171_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`READY` / `CODEX` for PL-0171 and point to this prompt and criteria. PL-0170
must remain independently accepted, PL-0068 must remain `OWNER_REQUIRED`, and
PL-0172 and later must remain unauthorized. If the live tracker does not match,
stop with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
PL-0170 prompt/criteria/audit/log, the accepted OpenReality architecture, the
PL-0163 reconstruction contract, and the M07 engine baseline before editing.
Preserve immutable PackScan authority, backend neutrality, explicit engine
provenance, the bounded redacted process seam, and the accepted PL-0170 result
contract.

## Frozen scope

Implement a PackLab-owned, backend-neutral diagnostic boundary for the
normalized `SparseMappingRun` produced by PL-0170. It must:

1. represent an immutable, explicitly configured diagnostic policy with
   validated registration thresholds; avoid hidden COLMAP CLI flags or
   engine-specific behavior;
2. classify failed, cancelled, successful-but-empty, and successful-but-
   fragmented registration outcomes deterministically, using stable diagnostic
   codes, severity, concise actionable message/remediation text, and the
   observed registration counts/ratio where available;
3. distinguish a healthy complete registration from a fragmented/insufficient
   registration using documented boundary semantics, including zero, exact
   threshold, just-below-threshold, and all-registered cases;
4. fail closed when a result has no usable statistics or violates the accepted
   PL-0170 status/output invariants; diagnostics must never turn a failed or
   cancelled run into a healthy result and must never claim a sparse model was
   materialized merely because an asset identity exists;
5. keep diagnostics deterministic and portable: no private absolute paths,
   credentials, raw unredacted process output, timestamps used as identity, or
   machine-specific engine discovery may enter the public report;
6. expose a stable machine-readable report suitable for later Studio/UI use,
   but do not implement UI, sparse export, filesystem materialization/health
   probing, OpenMVS/dense stages, or any later-task orchestration.

Use the existing `SparseMappingRun`, `RegisteredImageStatistics`, `RunStatus`,
and PackLab reconstruction/process contracts. If a stage failure reason is
surfaced, keep it bounded and redacted; prefer stable diagnostic codes over
copying arbitrary stdout/stderr.

Do not implement PL-0172 export, PL-0173 preset orchestration, OpenMVS/dense
stages, feature extraction, matcher changes, image/pixel processing, camera
solving, segmentation, mask lifting, UI, neural/generative models, metric
calibration, schema changes, dependency/lock changes, physical/native-device
acceptance, or PL-0172+ work.

## Allowed files

- `core/src/packlab_core/sparse_diagnostics.py`
- `tests/core/test_sparse_diagnostics.py`
- `coordination/sessions/M07-C001/PL-0171_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, accepted PL-0166
through PL-0170 files, schemas, dependency/lock files, generated artifacts,
binaries, secrets, private scans, signing material, UI code, engine binaries,
or PL-0172+ code. Do not broaden the allowed-file list without stopping for a
task-state/specification mismatch.

## Validation and publication

Run and record every required check with the exact command, expected result and
failure condition, actual result, and exit status:

- focused PL-0171 tests plus `test_sparse_mapping.py` and the relevant
  reconstruction/process/engine and accepted feature/matcher boundary suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff on every changed Python implementation/test path;
- targeted mypy on the changed Python implementation path, reporting the
  unchanged repository debt without adding errors;
- `python -m compileall -q` on every changed Python implementation path;
- `git diff --check` and protected-file/scope/privacy/secrets/generated/
  binary checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0171_CODEX_LOG_V01.md`, and end it exactly with:

`AWAITING_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0172.
