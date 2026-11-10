# PackLab Canonical Session Workflow Validation

> **CURRENT OWNER DECISION: 2026-11-10 CLAUDE CODE EXCLUSIVE.** Claude, not Codex or ChatGPT, owns all new PackLab implementation, testing, independent peer-review coordination, GitHub Actions runs, `TASKS.md` updates and next-task selection. Earlier workflow texts below are dated history, not active stop/approval rules; genuine security, architecture, license, physical/owner/factory release gates remain binding. See root `CLAUDE.md`, `AGENTS.md`, `coordination/AUTONOMOUS_EXECUTION_POLICY.md`. 


> **ACTIVE OPERATING UPDATE 2026-11-04:** Owner has authorized Codex to complete and peer-review all remaining PL tasks, edit root `TASKS.md` after genuine verified review, re-enable GitHub Actions, select dependency-safe work across milestones and continue without a ChatGPT handoff. Older statements below forbidding these operations are HISTORICAL and superseded by root `AGENTS.md` and `coordination/AUTONOMOUS_EXECUTION_POLICY.md`. Preserve protected product architecture, license/security/privacy, real tests, real external/owner/physical/legal release gates, accepted evidence and safe non-destructive Git sync. Historical ChatGPT audit files are immutable. 


## Purpose and authority

This document validates the repository’s governed implementation-to-audit
workflow using existing PackLab evidence. It is evidence/reference, not a
second current-task tracker. Root [`TASKS.md`](../TASKS.md) remains the only
live project-status surface and GitHub `main` remains repository truth.

## Canonical lifecycle

The required lifecycle is:

```text
TASKS.md authorization
  -> Codex prompt + local validation criteria
  -> Codex implementation and required checks
  -> Codex log and truthful local/blocked handoff
  -> autonomous continuation to next eligible task
```

The prompt and criteria record scope before implementation. Codex reads the
current tracker, synchronizes safely, changes authorized PackLab scope, runs
checks, records exact evidence and limitations, and updates the tracker under
the owner delegation. Independent review may be advisory; it does not control
task order or require a stop.

## Historical evidence

The completed PL-0001 through PL-0005 cycles provide the historical pattern:

- PL-0001’s accepted audit covers the repository structure and ownership
  contract.
- PL-0002’s accepted audit covers the glossary and preserves the Scan Mesh /
  Design Model boundary.
- PL-0003’s accepted audit covers the ADR process and ADR-0001.
- PL-0004’s accepted audit covers the Windows/iPhone 16 Standard non-LiDAR
  baseline and its runtime limitations.
- PL-0005 V02’s accepted audit covers the dependency/license register after a
  synchronization-evidence remediation.

These are historical audit artifacts, not live authorization. PL-0006’s
earlier `PL-0006-C001` audit accurately records `CHANGES_REQUIRED` for a
synchronization-evidence defect, kept PL-0006 unchecked, and required a
versioned revalidation. The later standalone `PL-0006-C002` prompt remained
unexecuted for live work because the owner-authorized M00-C001 master order
superseded it. The M00-C001 batch therefore revalidates PL-0006 first while
preserving all prior prompt, criteria, log, and audit history.

## Milestone-batch behavior

The M00-C001 batch is execution batching only, not acceptance batching. Each
child PL task retains its own prompt, matching criteria, implementation scope,
validation, product/evidence commit, and child Codex log. A validation-green
child may be followed by the next frozen child only because root `TASKS.md`
explicitly authorizes this master batch. No child is accepted before its
independent ChatGPT audit.

The batch stops at a failed mandatory validation, authorization mismatch,
unsafe divergence, privacy/security issue, blocker, owner decision, or
architecture contradiction. Earlier evidence is preserved; later children
are not silently skipped or started. The master log records `BATCH_STOPPED`
or `BATCH_COMPLETED` and ends `AWAITING_MILESTONE_AUDIT`.

## Separation of duties

Codex may edit `TASKS.md`, update task state, and reprioritize tasks under the
active owner delegation. It may not fabricate independent verdicts or E3
hosted/device evidence.

An independent reviewer may inspect source, diffs, ancestry, changed files,
and evidence when requested. Historical audit artifacts remain immutable.

`CHANGES_REQUIRED` retains the same permanent PL task ID, unchecked state,
prior evidence and accepted behavior. ChatGPT publishes a new versioned
remediation prompt/criteria; neither actor overwrites the prior evidence or
silently advances to another task.

## Artifact naming and handoff

For a cycle `<CYCLE_ID>` and version `VNN`, expected artifacts are:

```text
coordination/sessions/<CYCLE_ID>/CODEX_PROMPT_VNN.md
coordination/sessions/<CYCLE_ID>/CHATGPT_AUDIT_CRITERIA_VNN.md
coordination/sessions/<CYCLE_ID>/CODEX_LOG_VNN.md
coordination/sessions/<CYCLE_ID>/CHATGPT_AUDIT_VNN.md
```

The matching log must provide full GitHub URLs for the prompt, criteria, log,
and relevant artifact/evidence. Handoff messages and master logs use full
GitHub links rather than local Windows paths or pasted evidence bodies. A
Codex log must not predeclare the SHA of the future commit that contains that
same log.

## Runtime and evidence limitations

Documentation and governance checks can be rerun locally, but a local
command is still builder E1/E2 evidence until ChatGPT independently checks
the GitHub state. Physical capture, device behavior, signing accounts,
external tools, and dimensional accuracy may not be independently rerunnable
from this checkout. Such limitations remain explicit; this document does not
fabricate runtime, physical, or owner acceptance.

## Validation result and boundary

The evidence referenced above demonstrates the naming, ownership, audit, and
tracker workflow. It does not create another tracker, alter `TASKS.md`,
implement application behavior, or start M01.
