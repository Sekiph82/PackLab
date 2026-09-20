# PackLab Blocked-Task Protocol

## Evidence-based blocked state

`BLOCKED` is a governed state, not a vague status or a synonym for difficult.
It requires recorded evidence of the exact missing dependency, input,
environment, account/device capability, external tool, or owner decision that
prevents safe progress, plus the date/source of that evidence.

The record names the permanent PL task ID, current frontier, required actor,
concrete unblock action, and what evidence will prove that the task can
re-enter execution. A partial implementation or an inconvenient test is not
automatically a blocker.

## Tracker and frontier rules

Root `TASKS.md` retains the blocked task as the live frontier unless the owner
or an audited dependency-safe plan explicitly reprioritizes it. The tracker
must identify the Required Actor and concrete next unblock action. Only
ChatGPT writes that lifecycle state.

Blocked work must not be silently marked complete, checked, or described as
accepted. Later dependent tasks must not silently start. Partial logs,
commits, measurements, or experiments are preserved as evidence but are not
acceptance and do not authorize skipping the blocked task.

## State distinctions

- **BLOCKED:** an external dependency, input, environment, or decision is
  missing; the task cannot safely proceed.
- **CHANGES_REQUIRED:** an independent audit found a correctable defect in
  implemented scope; the same task receives bounded remediation and re-audit.
- **OWNER_REQUIRED:** a human-controlled product, physical, design, account,
  licensing, or authorization decision is needed.

These states remain open and must not be collapsed into a green result.

## PackLab examples

Examples include unavailable or incompatible COLMAP/OpenMVS/Open3D/OpenCascade
or Blender dependencies; an unavailable macOS/Xcode/Apple account or signing
credential; unsupported iPhone/ARKit runtime capability; missing approved
capture input or supplier/private Kenya provenance; absent legal/licensing
decision; insufficient disk or memory for a required reconstruction; and a
required owner decision about product baseline, physical measurement, or
distribution. Credentials and private data must not be supplied merely to
remove a blocker.

## Unblock and re-entry

The unblock action obtains or resolves the named dependency, input,
environment, or decision through its authorized owner/process, then records
fresh evidence. After unblocking, execution re-enters the same PL task with
the same identity and frozen scope unless the owner and independent audit
approve a changed plan. A prior partial result is not silently treated as a
completed task.

## Milestone-batch behavior

In an explicitly authorized milestone batch, a blocked child stops the batch
at that child frontier. Earlier child evidence is retained; later dependent
children do not start. The master log records the exact blocker, Required
Actor, unblock action, last completed child, and `BATCH_STOPPED` handoff.

This protocol is evidence/reference only. GitHub `main` remains repository
truth, root `TASKS.md` remains the sole live project-status tracker, and this
task does not implement dependency provisioning, signing, device support, or
reprioritization.
