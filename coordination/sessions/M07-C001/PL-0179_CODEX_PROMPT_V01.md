# PL-0179 - Codex Work Order V01

Task: **Preserve all reconstruction stage outputs and logs for reproducibility**

Repository:
https://github.com/Sekiph82/PackLab

Predecessor audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0178_CHATGPT_AUDIT_V01.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`READY` / `CODEX` for PL-0179 V01 and point to this prompt and criteria.
Preserve PL-0178 as `AUDITED_PASS`, preserve PL-0068 as `OWNER_REQUIRED`, and
keep PL-0180 and later unauthorized. If the live tracker does not match, stop
with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
accepted PL-0178 audit/log and texture source/tests, the shared reconstruction
workspace, provenance, process, stage-result, and project-layout contracts,
and the source-control, generated-artifact, and secrets policies before
editing.

## Frozen implementation scope

Add one local-only, PackLab-owned reconstruction-evidence retention boundary in
the existing Windows Studio workspace/provenance layer and its public tests.
The boundary must:

1. Accept an explicit reconstruction workspace, stage identity, run identity,
   stage result, and explicit output paths. Preserve successful, failed, and
   cancelled stage evidence, including partial outputs and bounded stdout/stderr
   logs, without deleting or silently replacing prior evidence.
2. Store retained evidence only below the revision-scoped local reconstruction
   workspace using safe relative paths. Reject absolute paths, traversal,
   private/supplier paths, symlink escapes, unsafe stage/run identities,
   collisions, and source/raw-path targets through PackLab-owned errors.
3. Write a deterministic machine-readable stage-evidence manifest containing
   the stage/run identity, source revision/digest, stage status, exit code,
   duration, redacted stdout/stderr, retained relative paths, byte sizes,
   SHA-256 digests, and retention-contract version. Do not parse or interpret
   mesh, texture, image, or engine-specific output contents.
4. Preserve provenance links to the reconstruction request/stage digests and
   output identities supplied by the caller. Repeated retention of identical
   evidence is idempotent; a same-identity byte or provenance mismatch fails
   closed and leaves the prior evidence unchanged.
5. Use atomic writes and bounded text handling consistent with the existing
   workspace/process contracts. A failed or cancelled run must retain its
   available logs and partial outputs, while a missing or unreadable explicit
   output is reported as a bounded retention failure rather than fabricated.
6. Keep retention local-only and regeneration-aware. Do not add Git-tracked
   reconstruction outputs, LFS rules, cleanup/expiry, orchestration, engine
   discovery/installation, CPU/GPU presets, mesh/texture parsing, quality or
   measurement claims, UI changes, schema/dependency/lock changes, or later
   PL-0180+ work.

## Allowed files

- `apps/windows-studio/src/packlab_studio/reconstruction_artifacts.py`
- `tests/studio/test_reconstruction_artifacts.py`
- `coordination/sessions/M07-C001/PL-0179_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any ChatGPT audit artifact, accepted PL-0166 through
PL-0178 files, schemas, dependency/lock files, generated artifacts, binaries,
secrets, private scans, signing material, UI code, engine binaries, or
PL-0180+ code. Do not broaden the allowed-file list without stopping for a
task-state or specification mismatch.

## Validation and publication

Run and record every required check with exact command, expected result,
failure condition, actual result, and exit status:

- focused PL-0179 tests plus the accepted reconstruction-workspace,
  provenance, process, result, capability, and preset suites;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff check and format check on every changed Python path;
- targeted mypy on the changed implementation path, reporting unchanged
  repository-wide debt if the aggregate check remains non-clean;
- compileall on every changed Python implementation/test path;
- `git diff --check`, protected-file/scope, dependency/lock, privacy/secrets,
  generated, binary, and remote-visibility checks.

Use separate implementation/evidence and log-only commits, push only
`origin main`, verify remote visibility, create exactly
`PL-0179_CODEX_LOG_V01.md`, and end that log exactly with:

`AWAITING_AUDIT`

Stop after handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0180.
