# PL-0170 - Codex Remediation Work Order V02

Task: **Sparse mapper stage and registered-image statistics**

Repository:
https://github.com/Sekiph82/PackLab

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CHATGPT_AUDIT_V01.md

Prior prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CODEX_PROMPT_V01.md

Prior criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CHATGPT_AUDIT_CRITERIA_V01.md

Prior log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CODEX_LOG_V01.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CODEX_LOG_V02.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`CHANGES_REQUIRED` / `CODEX` for this PL-0170 V02 remediation and point to
this prompt and criteria. PL-0169 must remain accepted, PL-0068 must remain
`OWNER_REQUIRED`, and PL-0171 and later must remain unauthorized. If the live
tracker does not match, stop with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the V01
prompt/criteria/log/audit, the accepted OpenReality architecture, the PL-0163
reconstruction contract, and the M07 engine baseline before editing. Preserve
all valid V01 behavior, immutable PackScan authority, backend neutrality,
explicit engine provenance, and the existing bounded/redacted process seam.

## Frozen remediation scope

Correct only the V01 audit findings in the sparse-mapping result and summary
boundary:

1. Translate `OverflowError`, invalid numeric conversion, and equivalent
   non-finite/ambiguous ratio inputs into the PackLab-owned
   `SparseMappingSummaryError` boundary. Do not allow raw conversion errors to
   escape the public parser or normalizer.
2. Validate the normalized stage result before reporting success: the stage ID
   must be exactly `sparse-mapping`; status, `cancelled`, and success exit-code
   semantics must be mutually consistent. Wrong-stage or contradictory
   results must fail closed and expose no sparse output.
3. Require one valid repository-relative sparse-output identity in the
   documented machine-readable summary. Accept the supported alias only when
   it agrees with the canonical field; reject missing, null, conflicting,
   mismatched, unsafe, or otherwise ambiguous output identities. Preserve the
   configured output path as the expected identity, but do not claim filesystem
   materialization that remains outside this task.
4. Enforce the successful `SparseMappingRun` invariants at the public result
   type as well as in `normalize_sparse_mapping_result`: exact request-image
   count, valid statistics, correct stage identity/status, and the expected
   output identity. Failed/cancelled results must expose neither statistics nor
   sparse output.
5. Add behavior-sensitive public-boundary tests for huge numeric ratios, wrong
   stage IDs, contradictory cancellation flags, inconsistent success exits,
   missing/null/conflicting output identities, direct-result invariant
   construction, and the existing valid success/failure/cancellation paths.

Preserve valid request/configuration construction, canonical serialization and
digests, explicit COLMAP 3.12.6 command/probe checking, redacted process
evidence, and all existing regression behavior.

Do not implement PL-0171 diagnosis, PL-0172 export, PL-0173 preset
orchestration, OpenMVS/dense stages, feature extraction, matcher changes,
image/pixel processing, camera solving, segmentation, mask lifting, UI,
neural/generative models, metric calibration, schema changes,
dependency/lock changes, physical/native-device acceptance, or PL-0171+ work.

## Allowed files

- `core/src/packlab_core/sparse_mapping.py`
- `tests/core/test_sparse_mapping.py`
- `coordination/sessions/M07-C001/PL-0170_CODEX_LOG_V02.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, V01 evidence, prior
prompts/criteria/logs/audits, accepted PL-0166 through PL-0169 files, schemas,
dependency/lock files, generated artifacts, binaries, secrets, private scans,
signing material, UI code, engine binaries, or PL-0171+ code. Do not broaden
the allowed-file list without stopping for a task-state/specification
mismatch.

## Validation and publication

Run and record every required check with the exact command, expected result,
failure condition, actual result, and exit status:

- focused PL-0170 V02 tests and the relevant reconstruction/process/engine and
  accepted feature/matcher boundary suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff on every changed Python implementation/test path;
- targeted mypy on the changed Python implementation path, reporting the
  unchanged repository debt without adding errors;
- `python -m compileall -q` on every changed Python implementation path;
- `git diff --check` and protected-file/scope/privacy/secrets/generated/
  binary checks.

Review the actual changed-file set. Use separate implementation/evidence and
log-only commits, push only `origin main`, verify remote visibility, create
exactly `PL-0170_CODEX_LOG_V02.md`, and end it exactly with:

`AWAITING_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0171.
