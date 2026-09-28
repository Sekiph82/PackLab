# PL-0179 - Codex Work Order V02

Task: **Preserve all reconstruction stage outputs and logs for reproducibility**

Repository:
https://github.com/Sekiph82/PackLab

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CHATGPT_AUDIT_V01.md

Prior implementation/log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CODEX_LOG_V01.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CODEX_LOG_V02.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`CHANGES_REQUIRED` / `CODEX` for PL-0179 V02 and point to this prompt and
criteria. Preserve PL-0178 as `AUDITED_PASS`, preserve PL-0068 as
`OWNER_REQUIRED`, and keep PL-0180 and later unauthorized. If the live tracker
does not match, stop with `TASK_STATE_MISMATCH`.

Read the V01 prompt, V01 criteria, V01 Codex log, V01 ChatGPT audit, the
coordination/audit policies, and the existing implementation/tests before
editing. Preserve all accepted V01 behavior not named in the findings below.

## Frozen remediation scope

Modify only the existing PL-0179 retention boundary and its public tests to
close the four V01 findings:

1. Detect and reject case-insensitive collisions in source paths, retained
   output paths, and stage/run evidence identities before any publication.
   Windows filesystem semantics are authoritative for this Windows Studio
   boundary. The rejection must use PackLab-owned collision/error types and
   must never silently replace one output with another.
2. In sequence-form `output_paths`, reject duplicate basenames before converting
   the sequence to an identity mapping. Do not silently discard an explicit
   path. Preserve the existing mapping-form contract.
3. Make final evidence publication atomic at the stage/run identity boundary,
   or guarantee that every failure during final publication removes the final
   identity and leaves no partial retained evidence directory. Preserve prior
   evidence on same-identity collision. Add a public failure-injection test
   that fails after at least one staged child has been moved.
4. On idempotent retry, validate every retained output/log file against the
   manifest-recorded relative path, byte size, and SHA-256 digest. If any
   retained byte, path, or provenance state differs, raise a PackLab-owned
   collision error and leave the prior evidence unchanged. Add a public test
   for tampered retained bytes.

Do not redesign the manifest, add cleanup/expiry, parse engine outputs, add
orchestration, discover/install engines, add presets, alter source/raw
authority, or implement PL-0180+ work.

## Allowed files

- `apps/windows-studio/src/packlab_studio/reconstruction_artifacts.py`
- `tests/studio/test_reconstruction_artifacts.py`
- `coordination/sessions/M07-C001/PL-0179_CODEX_LOG_V02.md`

Do not edit `TASKS.md`, any ChatGPT audit artifact, V01 prompt/criteria/log,
accepted PL-0166 through PL-0178 files, schemas, dependency/lock files,
generated artifacts, binaries, secrets, private scans, signing material, UI
code, engine binaries, or PL-0180+ code. Do not broaden this file list without
stopping for a task-state or specification mismatch.

## Validation and publication

Run and record every required check with exact command, expected result,
failure condition, actual result, and exit status:

- focused PL-0179 V02 tests plus the accepted reconstruction-workspace,
  provenance, process, result, capability, preset, and PL-0178 texture suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on every changed Python path;
- targeted mypy on the changed implementation path, reporting unchanged
  repository-wide debt if the aggregate check remains non-clean;
- compileall on every changed Python implementation/test path;
- `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets,
  generated, binary, and remote-visibility checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0179_CODEX_LOG_V02.md`, and end that log exactly with:

`AWAITING_AUDIT`

Stop after handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0180.
