# PackLab Definition of Done

## Two distinct completion states

`IMPLEMENTATION_COMPLETE` means the builder implemented the frozen scope,
ran the required checks, recorded truthful evidence, and published the
matching Codex log. It is not acceptance and does not authorize a checkbox
change.

`AUDITED_PASS` means ChatGPT independently inspected the actual GitHub
commit/diff/source and found no failed mandatory criterion or unresolved
material defect under the frozen criteria. Only ChatGPT may assign that
verdict and update task lifecycle state.

## Required implementation gate

Before implementation, the repository must contain a versioned frozen Codex
prompt and matching versioned ChatGPT audit criteria. The builder verifies the
current `TASKS.md` authorization, repository identity, safe synchronization,
scope, and protected-file boundary.

The implementation pass must:

1. stay within the prompt’s exact files and task ID;
2. run every required test and check, including negative or boundary checks
   where the scope makes them relevant;
3. review exact changed files, protected files, privacy, and security;
4. record failures and fixes in chronology rather than hiding them;
5. preserve known limitations, unverified assumptions, and physical/device or
   owner-controlled decisions; and
6. publish the matching Codex log with the required handoff before audit.

For a single task the handoff is `AWAITING_AUDIT`. In an explicitly
owner-authorized milestone batch, each child ends
`READY_FOR_INDEPENDENT_AUDIT` and the batch ends
`AWAITING_MILESTONE_AUDIT`. Neither handoff is an acceptance verdict.

## Independent audit gate

ChatGPT reads the current root `TASKS.md` before every decision, then inspects
the actual GitHub commit range, changed-file set, source/artifact content,
logs, and relevant tests. Builder claims and builder-run output are evidence,
not a substitute for independent review.

The audit checks, as applicable:

- exact prompt scope and every numbered frozen criterion;
- required commands, regression behavior, negative/boundary paths, and test
  sensitivity rather than tautological tests;
- architecture, determinism/provenance, privacy/security, and scope leakage;
- physical, device, account, signing, or owner limitations without inventing
  reproduction or acceptance; and
- whether earlier accepted behavior remains intact.

## Evidence levels and limitations

- **E1 — builder check:** a Codex-run command or observation with limited
  context.
- **E2 — reproducible builder evidence:** exact command, start/current commit,
  expected result, failure condition, actual result, and affected scope.
- **E3 — independent audit evidence:** ChatGPT’s own GitHub inspection or
  independently rerun/reasoned check, recorded in a ChatGPT audit artifact.
- **E4 — owner/physical evidence:** an owner-controlled product, device,
  account, physical measurement, or other decision that AI must not fabricate.

E1/E2 can establish implementation evidence but cannot become E3 merely by
being detailed. When a runtime, device, or physical check cannot be rerun,
the limitation remains visible and the audit labels the builder evidence
accordingly.

## Audit dispositions

- **AUDITED_PASS:** every mandatory criterion is satisfied and no material
  defect remains.
- **CHANGES_REQUIRED / AUDITED_FAIL:** a mandatory criterion or material
  requirement is false, incomplete, unsafe, or untested. ChatGPT keeps the
  task open, records exact findings, retains the task ID and evidence, updates
  `TASKS.md`, and issues bounded versioned remediation prompt/criteria.
- **BLOCKED:** a required dependency, input, environment, or external state
  prevents implementation or audit. The tracker records the exact blocker,
  required actor, and unblock action; no completion is manufactured.
- **OWNER_REQUIRED:** a human-controlled product, design, physical, account,
  or authorization decision is needed. The task remains open until the owner
  decides through the governed workflow.

These meanings follow `coordination/AUDIT_POLICY.md`; a builder may report
evidence or a blocker but cannot assign the audit dispositions.

## Tracker and task identity rules

Root `TASKS.md` is the sole live project-status tracker. ChatGPT alone updates
its lifecycle, progress, actor, and checkbox state after an audit decision.
The builder must not edit it, create a second tracker, mark a checkbox, or
advance work because a local artifact looks complete.

A task checkbox may be marked complete only after independent
`AUDITED_PASS`. A failed audit preserves the permanent PL ID, prior prompts,
criteria, logs, audits, and accepted behavior; it does not create a new task
or silently skip to another one.

## Milestone closure

Milestone-batch execution is an explicit throughput authorization, not
acceptance batching. Each child still has its own frozen prompt, criteria,
scope, validation, implementation/evidence boundary, and Codex log. The batch
may close only after every mandatory child task has been independently
accepted and the milestone-level audit has closed.

This document defines completion gates only. It does not change task state,
create a release, or authorize M01 work.
