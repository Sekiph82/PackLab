# PackLab Failed-Audit Protocol

## Preserve task identity and evidence

An audit failure does not create a replacement task. The same permanent
`PL-xxxx` ID remains the frontier and remains unchecked until a fresh
independent audit passes. Prior prompts, criteria, implementation commits,
logs, audits, findings, and accepted behavior are immutable evidence; a later
cycle adds a new version rather than overwriting history.

## Finding and remediation contract

ChatGPT records exact failed criteria, actual GitHub evidence, severity,
scope, expected correction, and any regression boundary. Remediation is
bounded to those authorized findings. A new versioned `CODEX_PROMPT_VNN` and
matching `CHATGPT_AUDIT_CRITERIA_VNN` define the correction; the builder fixes
only that scope, reruns relevant required checks and regressions, and creates
a new versioned Codex log.

Root `TASKS.md` must show `CHANGES_REQUIRED`, preserve the same task ID, and
name the next actor and concrete action. Only ChatGPT writes that tracker
state. A builder must not mark the checkbox, erase a finding, rewrite the
failed audit, or claim completion because a local correction looks plausible.

## Fresh independent re-audit

After remediation, ChatGPT independently inspects the new commit/diff/source,
the exact failed criteria, the new log, and the integrity of previously
accepted behavior. A remediation pass is not acceptance until the fresh audit
disposes every mandatory criterion and the tracker is updated. If it fails
again, the same task remains open with another versioned finding/remediation
cycle.

## Milestone-batch frontier

In an explicitly authorized milestone batch, a failed child validation or
failed audit stops the batch at that child frontier. Earlier independently
accepted child audits and their evidence are not discarded. Later child work
does not start silently, and a future milestone cannot be used to evade the
failed child. The master evidence identifies the frontier, retained earlier
results, exact blocker/findings, and next authorized action.

## No false completion or skipping

`CHANGES_REQUIRED` is distinct from `AUDITED_PASS`, `BLOCKED`, and
`OWNER_REQUIRED`. It is not permission to check a box, advance to another
task, or broaden the remediation. A task may be closed only by the authorized
independent audit process after all mandatory criteria pass. Evidence can be
preserved and partially useful without being acceptance.

This protocol is evidence/reference only. Root `TASKS.md` remains the sole
live project-status tracker, GitHub `main` remains repository truth, and this
task does not implement a remediation engine or change any current tracker
state.
