# M08-C001 - Master Remediation Codex Work Order V01

Milestone: **M08 - Segmentation, Object Extraction & Reconstruction QA**  
Remediation scope: **PL-0184 V02, then PL-0185 V02 only**

Repository: https://github.com/Sekiph82/PackLab  
Branch: `main`  
Tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Source batch audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/M08-C001_CHATGPT_AUDIT_V01.md
Master criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V01.md
Required master log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/MASTER_REMEDIATION_CODEX_LOG_V01.md

## Authorization and synchronization

Start only when live `TASKS.md` explicitly authorizes the M08-C001 remediation
batch with `Current Task Status: CHANGES_REQUIRED`, `Required Actor: CODEX`,
and points to this exact master prompt and criteria. M07 must remain
`AUDITED_PASS`, PL-0068 must remain `OWNER_REQUIRED`, and PL-0186 through
PL-0201 plus M09 must remain unauthorized.

Before material work and before each child, fetch `origin/main`, verify the
PackLab root/remote/branch, compare divergence, and proceed only from a clean
equal or safely fast-forwardable checkout. Never reset, clean, stash, rebase,
force-push, destructive-checkout, overwrite owner work, or edit `TASKS.md` or
ChatGPT artifacts.

## Exact remediation order and gates

1. Execute PL-0184 V02 from its frozen prompt and criteria. Do not continue if
   its validation is not green or its handoff is not remotely visible.
2. Execute PL-0185 V02 from its frozen prompt and criteria. Preserve its
   explicit `NO_SELECTION_LICENSE_OR_CHECKPOINT_BLOCKER`; do not install or
   select a model to bypass that blocker.

Each child requires a separate implementation/evidence boundary, separate
log-only publication, exact tests and `READY_FOR_INDEPENDENT_AUDIT`. Stop the
entire remediation batch on any validation failure, authorization mismatch,
privacy/security issue, architecture contradiction, unresolved predecessor, or
need to start PL-0186+. The master remediation log must index both children,
record the exact frontier and end with `AWAITING_MILESTONE_AUDIT`.

## Frozen scope

Apply only the two published child remediations:

- PL-0184 V02: recursively immutable/mutation-safe prompt data and sensitive
  tests proving artifact/revision serialization and digests cannot silently
  diverge.
- PL-0185 V02: immutable/mutation-safe benchmark predictions and sensitive
  tests proving report serialization and `report_digest` cannot silently
  diverge.

Preserve all prior accepted behavior, source immutability, provenance and
workspace boundaries. Do not add model/runtime/dependencies, private data,
RAW_CAPTURE changes, UI truth, native/physical acceptance, or later-child
implementation.

## Required validation and handoff

Run every child prompt's focused and regression tests, exact locked full suite,
Ruff/format, targeted/relevant mypy, compileall, `git diff --check`, protected
file/scope, dependency/license, privacy/secrets/generated/binary and remote
visibility checks. Record expected results, failure conditions, actual results,
limitations, exact SHAs and URLs. Create the separate master log only after the
last executed child or the stop frontier. Do not create ChatGPT audit files.

End response only after publishing the master log:

`AWAITING_MILESTONE_AUDIT`
