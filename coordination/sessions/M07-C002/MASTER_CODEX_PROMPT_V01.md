# M07-C002 - Codex Master Work Order V01

Milestone: **M07 - Reconstruction Backends & Photogrammetry**  
Ordered children: **PL-0181, PL-0182, PL-0183**  
Repository: https://github.com/Sekiph82/PackLab  
Branch: `main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

This prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/MASTER_CODEX_PROMPT_V01.md

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Required master log template:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/MASTER_CODEX_LOG_V01.md

Accepted predecessor:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0180_CHATGPT_AUDIT_V01.md

## Authorization and synchronization

Before material work, read the live `TASKS.md`. It must explicitly authorize
`M07-C002`, `READY`, `CODEX`, and this exact ordered batch. It must preserve
PL-0180 as `AUDITED_PASS`, PL-0068 as `OWNER_REQUIRED`, and keep M08 and all
later milestone work unauthorized. If the tracker, branch, or active prompt
does not match, stop with `TASK_STATE_MISMATCH`.

At the start of the batch and before every child:

1. confirm the Git root is `C:\Users\sekip\Desktop\PackLab`;
2. confirm `origin` is `https://github.com/Sekiph82/PackLab.git` and the branch is `main`;
3. run `git fetch origin main --prune`;
4. compare `HEAD...origin/main` and fast-forward only when clean and behind-only;
5. preserve owner/local work; never reset, clean, stash, rebase, force-push,
   destructive-checkout, or overwrite unrelated files.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
accepted M07 source/audits, the OpenReality architecture and ADR-0003, the
existing backend/job/process/workspace/stage-evidence contracts, and the
matching child prompt and criteria before each child.

## Exact child order and handoffs

Execute only this order. Each child has a separate implementation/evidence
boundary and a separate log-only publication boundary. A child must end with
`READY_FOR_INDEPENDENT_AUDIT`; the master log must end with
`AWAITING_MILESTONE_AUDIT`.

1. PL-0181 - one-click reconstruction orchestration
   - Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0181_CODEX_PROMPT_V01.md
   - Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0181_CHATGPT_AUDIT_CRITERIA_V01.md
   - Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0181_CODEX_LOG_V01.md
2. PL-0182 - recoverable reconstruction cancellation
   - Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0182_CODEX_PROMPT_V01.md
   - Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0182_CHATGPT_AUDIT_CRITERIA_V01.md
   - Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0182_CODEX_LOG_V01.md
3. PL-0183 - supported preview/export conversion with source preservation
   - Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0183_CODEX_PROMPT_V01.md
   - Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0183_CHATGPT_AUDIT_CRITERIA_V01.md
   - Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0183_CODEX_LOG_V01.md

## Batch evidence and commit rules

For every child, record exact commands, expected results, explicit failure
conditions, actual results, exit status, negative/boundary/regression tests,
changed files, protected-file review, privacy/secrets review, limitations,
and remote visibility. Use one implementation/evidence commit followed by a
separate child-log-only commit. Do not predeclare a future log commit SHA.

The master log must index each child, implementation SHA, log-only SHA, full
GitHub URLs, test results, limitations, and the final batch state. It is
evidence only; do not assign any ChatGPT audit verdict or edit `TASKS.md`.

## Architecture and scope boundary

Keep the PackLab-owned, backend-neutral reconstruction authority. Reuse the
existing `ReconstructionBackend`, `ReconstructionJobSpec`, `CancelToken`,
stage-result, reconstruction-workspace, provenance, job, and stage-evidence
contracts. Do not add OpenReality, VGGT, SAM 3D Objects, TRELLIS, neural
checkpoints, automatic engine installation/download, metric promotion,
object segmentation, Scan Master promotion, CAD/BREP, or physical/native
acceptance.

Do not modify root `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, accepted audit
files, schemas, dependency/lock files, private data, credentials, signing
material, generated reconstruction intermediates, or later-milestone code.

## Stop conditions

Stop the entire batch at the current child if any of the following occurs:

- tracker, branch, remote, or synchronization mismatch;
- a frozen mandatory validation fails and cannot be corrected within that
  child scope;
- a required architecture decision or schema/dependency change is needed;
- a process, engine, output, or cancellation boundary cannot preserve source
  immutability and provenance;
- a privacy/security/licensing issue, owner gate, unavailable dependency, or
  native/physical requirement blocks safe progress;
- work would need PL-0184 or any M08/later implementation.

On stop, finish the current child log and the master log with the exact
frontier, retained earlier evidence, blocker/failure, and `BATCH_STOPPED`,
then end the master log with `AWAITING_MILESTONE_AUDIT`.

## Final handoff

After PL-0183 is validation-green and its log is remotely visible, complete
the master log with `BATCH_COMPLETED`, publish it as a separate master-log-only
commit, verify `origin/main`, return `AWAITING_MILESTONE_AUDIT`, and stop.
Do not start M08 or any later task.
