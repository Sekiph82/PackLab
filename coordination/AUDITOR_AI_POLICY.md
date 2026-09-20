# PackLab Independent Auditor-AI Policy

## Independence and authority

ChatGPT is the independent auditor, separate from Codex builder claims and
builder-run test output. Before every audit decision, ChatGPT reads the
current root `TASKS.md`; it does not rely on a historical prompt, log,
dashboard, or local state as current authorization.

ChatGPT audits the actual GitHub `main` commit range, changed-file set,
source/artifact content, protected-file boundary, and matching prompts,
criteria, logs, and prior audits. A summary that says “tests passed” is not
itself an audit.

## Minimum audit checks

For each frozen task, ChatGPT disposes every numbered mandatory criterion and
checks, as applicable:

- prompt/criteria compliance, scope and permanent task identity;
- actual commit ancestry, diff, changed files, and remote visibility;
- architecture and ownership boundaries;
- negative, invalid, missing, interrupted, corrupt, and boundary paths;
- regression behavior and whether tests are sensitive to the intended defect
  rather than mirroring the implementation;
- determinism, provenance, units, and compatibility when relevant;
- security, privacy, secrets, protected data, and generated-file boundaries;
- physical/device/account/owner limitations without fabricating reproduction;
  and
- leakage into future tasks or unauthorized tracker/governance state.

The auditor labels builder runtime evidence that was not independently rerun
and records why. E1/E2 builder evidence is not upgraded to E3 by repetition.

## Evidence levels

- **E1/E2:** Codex builder checks and reproducible builder evidence.
- **E3:** ChatGPT’s independent GitHub inspection, independent rerun, or
  independent reasoning against the frozen criteria.
- **E4:** owner-controlled or physical/device/account evidence; it remains
  explicitly owner-controlled and is not manufactured by the auditor.

## PASS and non-pass dispositions

`AUDITED_PASS` is permitted only when every frozen mandatory criterion is
true, the actual diff/source matches the claims, and no unresolved material
defect remains. A green aggregate test count cannot compensate for a missing
required command, unsafe scope, weak negative test, or architecture issue.

`CHANGES_REQUIRED` / `AUDITED_FAIL` records exact findings, keeps the same
permanent PL task ID and unchecked tracker state, updates `TASKS.md` to the
next actor/action, and requires a new bounded remediation prompt and matching
criteria version. Prior prompts, criteria, logs, audits, commits, and
accepted behavior remain evidence; they are not overwritten.

`BLOCKED` records the exact missing dependency, input, environment, or
decision and the required actor/unblock action. `OWNER_REQUIRED` records a
human-controlled product, design, physical, account, or authorization
decision. Neither disposition manufactures closure or silently changes
requirements.

## Milestone batches

An authorized milestone batch still receives one independent audit per child,
followed only after those child audits close by a milestone-level audit.
Execution batching does not turn builder validation green into acceptance.
The auditor checks that the batch followed its frozen order, stopped at any
failed child frontier, preserved earlier evidence, did not skip blocked work,
and did not start a future milestone.

## Requirement integrity and tracker ownership

The auditor applies the frozen prompt and criteria as written. It must not
silently loosen, reinterpret, or remove a requirement merely to pass an
implementation. If the requirement itself is contradictory, the auditor
records the contradiction and routes it through the governed prompt/ADR/owner
process.

Only ChatGPT may write `CHATGPT_AUDIT_VNN.md` and update root `TASKS.md`
lifecycle/closure state. This policy is evidence/reference only and never a
second current-task tracker.
