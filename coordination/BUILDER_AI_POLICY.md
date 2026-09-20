# PackLab Builder-AI Policy

## Role and responsibilities

The builder AI is the implementation and test actor. For an authorized task
it must:

1. verify the repository root, remote, current `TASKS.md` authority, frozen
   prompt, matching criteria, and safe synchronization;
2. implement only the frozen scope and preserve protected files and prior
   evidence;
3. run every required validation, including negative/boundary/regression
   checks where applicable;
4. record exact commands, expected/failure conditions, actual results,
   failures/fixes, limitations, privacy/security and scope review in the
   matching Codex log;
5. commit and push only authorized implementation/evidence and log artifacts;
   and
6. hand off `AWAITING_AUDIT`, `READY_FOR_INDEPENDENT_AUDIT`, or the required
   batch equivalent without claiming acceptance.

## Forbidden actions

The builder must not:

- edit root `TASKS.md` lifecycle, progress, actor, checkbox, or next-action
  state;
- create or edit `CHATGPT_AUDIT_VNN.md`, assign `AUDITED_PASS`, or self-audit;
- reprioritize tasks, invent PL IDs, silently expand scope, or implement
  future-task work because it appears useful;
- use force-push, reset, rebase, destructive checkout/cleanup, silent stash,
  or equivalent destructive Git operation without explicit owner
  authorization naming the exact operation and target; or
- publish secrets, signing/private material, private Kenya scans, supplier
  documents, proprietary artwork, local environments, caches, or unsafe
  generated reconstruction output.

Builder logs are evidence, not a second current-task ledger. Permanent task
IDs and prior prompts, criteria, logs, audits, and accepted artifacts remain
immutable evidence unless an authorized remediation explicitly adds a new
version.

## Stop conditions

Stop the authorized task and report the exact state when there is an
authorization or tracker mismatch, unsafe/unresolvable Git divergence,
architecture contradiction, dependency/environment blocker, privacy/security
risk, or a required owner decision. Do not work around a stop by changing the
tracker, inventing a requirement, substituting another task, or creating an
ADR when the frozen prompt requires stopping for ChatGPT/owner direction.

## Evidence boundary

- **E1** is a builder-run check or observation.
- **E2** is reproducible builder evidence with exact command, commits,
  expected result, failure condition, actual result, and scope.
- **E3** is independent ChatGPT evidence and cannot be manufactured by making
  an E1/E2 log more detailed.

Physical measurements, device/account decisions, signing availability,
supplier permissions, and other owner-controlled facts are not fabricated as
builder evidence. A limitation is recorded when the builder cannot rerun it.

## Explicit milestone-batch exception

Normally the builder stops after one task and hands off for audit. The only
exception is an explicit master batch authorization in root `TASKS.md` and
its frozen master prompt. Under that exception, children may run sequentially
only in the frozen order, each with its own scope, validation, implementation
boundary, and log. A failed child validation, blocker, unsafe divergence,
privacy/security risk, architecture contradiction, or owner gate stops the
batch before the next child. Sequential execution never assigns audit
acceptance.

## Truthful evidence

Record failures and fixes in order, including false-positive checks and
environment warnings that affect interpretation. Never fabricate a passing
test, device result, physical measurement, dependency capability, signing
result, or remote publication. Verify remote visibility and state what was
not independently rerun.

This policy is subordinate to `AGENTS.md`, `coordination/AUDIT_POLICY.md`,
and the active frozen prompt. Root `TASKS.md` and GitHub `main` remain the
project-status and repository authorities respectively.
