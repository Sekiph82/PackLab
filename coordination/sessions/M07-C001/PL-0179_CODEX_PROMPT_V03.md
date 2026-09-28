# PL-0179 - Codex Work Order V03

Task: **Preserve all reconstruction stage outputs and logs for reproducibility**

Repository:
https://github.com/Sekiph82/PackLab

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CHATGPT_AUDIT_V02.md

Prior implementation/log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CODEX_LOG_V02.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CHATGPT_AUDIT_CRITERIA_V03.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CODEX_LOG_V03.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`CHANGES_REQUIRED` / `CODEX` for PL-0179 V03 and point to this prompt and
criteria. Preserve PL-0178 as `AUDITED_PASS`, preserve PL-0068 as
`OWNER_REQUIRED`, and keep PL-0180 and later unauthorized. If the live tracker
does not match, stop with `TASK_STATE_MISMATCH`.

Read the V01 and V02 prompts, criteria, Codex logs, V01 and V02 ChatGPT
audits, the coordination/audit policies, and the existing implementation/tests
before editing. Preserve all accepted V02 behavior.

## Frozen remediation scope

Modify only the existing PL-0179 final-publication boundary and its public
tests to close the V02 finding:

1. Make publication of the complete staged evidence directory atomic at the
   stage/run identity boundary, preferably by replacing the currently empty
   final identity with one same-filesystem directory rename/replacement after
   all staged children and the manifest have been written.
2. Preserve the pre-publication stage/run collision check and never replace or
   delete prior evidence for a same-identity collision.
3. If the implementation retains rollback rather than a single atomic
   directory publication, verify rollback success and fail closed without
   silently accepting or reporting an uncleared partial final identity. Do not
   use ignored best-effort cleanup as the publication guarantee.
4. Add or update a public failure-injection test that demonstrates the final
   identity is absent after an injected publication failure, while retaining
   the V02 collision, duplicate-basename, and retained-byte integrity tests.

Do not redesign the manifest, add cleanup/expiry, parse engine outputs, add
orchestration, discover/install engines, add presets, alter source/raw
authority, or implement PL-0180+ work.

## Allowed files

- `apps/windows-studio/src/packlab_studio/reconstruction_artifacts.py`
- `tests/studio/test_reconstruction_artifacts.py`
- `coordination/sessions/M07-C001/PL-0179_CODEX_LOG_V03.md`

Do not edit `TASKS.md`, any ChatGPT audit artifact, V01/V02 prompts,
criteria/logs, accepted PL-0166 through PL-0178 files, schemas,
dependency/lock files, generated artifacts, binaries, secrets, private scans,
signing material, UI code, engine binaries, or PL-0180+ code. Do not broaden
this file list without stopping for a task-state or specification mismatch.

## Validation and publication

Run and record every required check with exact command, expected result,
failure condition, actual result, and exit status:

- focused PL-0179 V03 tests plus the accepted reconstruction-workspace,
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
`PL-0179_CODEX_LOG_V03.md`, and end that log exactly with:

`AWAITING_AUDIT`

Stop after handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0180.
