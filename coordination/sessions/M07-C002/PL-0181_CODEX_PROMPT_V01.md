# PL-0181 - Codex Work Order V01

Task: **Add one-click Reconstruct Scan orchestration across COLMAP and OpenMVS**

Repository: https://github.com/Sekiph82/PackLab
Cycle: `M07-C002`

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0181_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0181_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0181_CODEX_LOG_V01.md

## Authorization gate

Before editing, live `TASKS.md` must authorize the complete `M07-C002`
milestone batch with Required Actor `CODEX`, and the master prompt and
criteria above must be visible on `origin/main`. Preserve PL-0180 as
`AUDITED_PASS`, PL-0068 as `OWNER_REQUIRED`, and keep PL-0182, PL-0183, M08,
and later work within this frozen order. Stop on mismatch.

Read the repository rules, M07 architecture/ADR, accepted predecessor
audits/logs, `ReconstructionBackend`, `ReconstructionJobSpec`, preset/resource
policy, stage modules, process runner, reconstruction workspace, provenance,
job, and evidence-retention contracts before implementation.

## Frozen scope

Implement one PackLab-owned, backend-neutral public orchestration service for
the existing COLMAP/OpenMVS lane. The public boundary must:

1. accept one validated reconstruction job/input/workspace and explicit
   configuration/provenance;
2. execute the existing ordered stage contracts from COLMAP feature/matching
   and sparse outputs through OpenMVS dense, mesh, refinement, and texture
   outputs, without duplicating engine-specific parsing or option ownership;
3. stop downstream execution after a failed, cancelled, unavailable, invalid,
   or missing-output stage and return a coherent normalized run/result;
4. preserve stage results, output identities, source/revision/configuration
   digests, backend provenance, scale state, authority class, and bounded
   evidence through the existing authorities;
5. expose deterministic stage order and a single application-service entry
   point suitable for Studio's one-click action, without moving reconstruction
   truth into a Qt widget.

Use existing capability probes/configuration and explicit engine paths. No
automatic installation/download/discovery beyond the accepted explicit
configuration seam. Use the existing cancellation token only as the current
boundary; PL-0182 owns cancellation recovery changes.

## Allowed change boundary

- the existing backend-neutral reconstruction module or one dedicated
  `core/src/packlab_core/reconstruction_orchestrator.py` module;
- only the minimal existing Studio service/job wiring required to invoke that
  public boundary, if needed;
- dedicated core/Studio tests for this child;
- `coordination/sessions/M07-C002/PL-0181_CODEX_LOG_V01.md`.

Do not modify `TASKS.md`, ChatGPT artifacts, schemas, dependencies/locks,
accepted evidence, raw/source data, UI-owned pipeline logic, PL-0182/0183
production behavior, M08 code, or private/generated reconstruction output.

## Required validation and handoff

Run focused orchestration and predecessor suites, exact locked full pytest,
Ruff/format, targeted mypy, compileall, diff/protected/scope,
dependency/privacy/secrets/generated/binary, and remote-visibility checks.
Record exact commands, expected result, explicit failure condition, actual
result, and exit status. Use separate implementation and log-only commits.
Create exactly the matching child log, end it exactly with
`READY_FOR_INDEPENDENT_AUDIT`, and stop. Do not start PL-0182 until this
child is validation-green.
