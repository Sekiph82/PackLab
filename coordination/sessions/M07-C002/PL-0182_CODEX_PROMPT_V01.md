# PL-0182 - Codex Work Order V01

Task: **Add reconstruction cancellation that leaves the project recoverable**

Repository: https://github.com/Sekiph82/PackLab
Cycle: `M07-C002`

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0182_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0182_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0182_CODEX_LOG_V01.md

## Authorization and predecessor gate

Start only after PL-0181 is validation-green inside the authorized M07-C002
batch, its log is published, and the live tracker still authorizes this
batch/child. Read all repository rules and the accepted PL-0181 evidence plus
the existing `CancelToken`, subprocess runner, stage-result, JobManager,
workspace-state, provenance, and retention contracts. Stop on mismatch.

## Frozen scope

Implement explicit, idempotent cancellation across the existing reconstruction
process/orchestration/job/workspace boundary. The behavior must:

1. propagate one cancellation request to the active stage/process boundary and
   normalize it as a cancelled stage/run/job rather than a generic failure;
2. tolerate repeated cancellation and cancellation/failure races deterministically;
3. avoid leaving an owned process running, an advertised successful output,
   a retained-success manifest, or a falsely `SUCCEEDED` workspace after
   cancellation;
4. preserve immutable RAW_CAPTURE/source bytes and existing accepted evidence;
5. leave a clear cancelled/recoverable revision state and allow a later retry
   to create a new safe reconstruction revision without reusing stale partial
   success identity;
6. keep bounded logs/provenance and existing JobManager ownership; no UI
   widget may become the source of cancellation truth.

Use failure injection/fake runners for deterministic tests. Do not require a
live COLMAP/OpenMVS executable, native device, physical capture, or owner
acceptance.

## Allowed change boundary

- existing `core/src/packlab_core/reconstruction_process.py`,
  `subprocess_runner.py`, reconstruction orchestration module, and only the
  minimal cancellation/workspace integration required;
- existing Studio job/workspace seam only where required to preserve one
  logical state machine;
- dedicated core/Studio cancellation/recovery tests;
- `coordination/sessions/M07-C002/PL-0182_CODEX_LOG_V01.md`.

Do not edit `TASKS.md`, ChatGPT artifacts, schemas, dependencies/locks,
accepted audit evidence, PL-0183 or M08 production code, raw/source data,
private/generated reconstruction output, or unrelated job types.

## Required validation and handoff

Run focused cancellation/process/orchestration/workspace/job suites, exact
locked full pytest, Ruff/format, targeted mypy, compileall,
diff/protected/scope, privacy/security/generated/binary, and remote checks.
Record negative/race/retry evidence and exact command results. Use separate
implementation and log-only commits. End the child log exactly with
`READY_FOR_INDEPENDENT_AUDIT`; continue to PL-0183 only if green.
