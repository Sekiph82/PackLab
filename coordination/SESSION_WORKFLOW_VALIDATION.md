# PackLab Canonical Session Workflow Validation

## Purpose and authority

This document validates the repository’s governed implementation-to-audit
workflow using existing PackLab evidence. It is evidence/reference, not a
second current-task tracker. Root [`TASKS.md`](../TASKS.md) remains the only
live project-status surface and GitHub `main` remains repository truth.

## Canonical lifecycle

The required lifecycle is:

```text
TASKS.md authorization
  -> frozen Codex prompt + matching ChatGPT criteria
  -> Codex implementation and required checks
  -> Codex log and AWAITING_AUDIT (or child READY_FOR_INDEPENDENT_AUDIT)
  -> ChatGPT actual GitHub audit
  -> ChatGPT writes audit artifact and updates TASKS.md
```

The prompt and criteria freeze scope before implementation. Codex reads the
current tracker, synchronizes safely, changes only the authorized scope, runs
checks, records exact evidence and limitations, and publishes the matching
log. ChatGPT independently inspects the GitHub range/source/diff and every
mandatory criterion, then is the sole actor that writes lifecycle/closure
state back to `TASKS.md`.

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

Codex cannot edit `TASKS.md`, create ChatGPT audit files, assign
`AUDITED_PASS`, mark checkboxes, reprioritize tasks, or self-audit. It may
record E1/E2 builder evidence, truthful failures/fixes, and the required
handoff.

ChatGPT is the independent auditor and sole lifecycle/closure writer. It
reads current `TASKS.md` before each decision, inspects actual GitHub source,
diffs, commit ancestry, changed files and evidence, disposes every frozen
criterion, and writes `CHATGPT_AUDIT_VNN.md` plus any required tracker update.

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
