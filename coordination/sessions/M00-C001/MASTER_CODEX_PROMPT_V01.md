# M00-C001 - PackLab M00 Remaining-Tasks Master Codex Work Order V01

Milestone: **M00 - Governance & Architecture**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Canonical local workspace: `C:\Users\sekip\Desktop\PackLab`

## Mission

Execute all remaining M00 tasks **PL-0006 through PL-0018** sequentially in one owner-authorized milestone batch while preserving separate task scope, separate frozen criteria, separate commits, and separate logs.

Do not start M01.

This master work order supersedes the previously issued but unexecuted PL-0006-C002 standalone work order for live execution. Historical files remain evidence and must not be deleted or rewritten.

## Canonical authority

Repository:
https://github.com/Sekiph82/PackLab

Current tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

Agent rules:
https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md

Milestone batch protocol:
https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md

Audit policy:
https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md

Audit memory:
https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_INDEX.md

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization gate

Before any material work, root `TASKS.md` must explicitly authorize:

- Current Milestone: M00
- Current Task: M00-BATCH-001 - Complete remaining M00 tasks PL-0006 through PL-0018
- Current Task Status: READY
- Required Actor: CODEX
- Next Task/Action pointing to this master prompt

If not, STOP with `TASK_STATE_MISMATCH`.

## One-time batch synchronization

Before the first child task:

```powershell
cd C:\Users\sekip\Desktop\PackLab
git rev-parse --show-toplevel
git remote -v
git status --porcelain
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
```

Rules:

- verify PackLab root and https://github.com/Sekiph82/PackLab.git origin;
- tracked local changes => STOP;
- ahead/diverged => STOP;
- behind-only => `git merge --ff-only origin/main`;
- then prove HEAD equals origin/main and ahead/behind is `0 0`;
- historical untracked local `.hiveai/` may remain but must never be staged;
- never use reset, rebase, force-push, destructive checkout, silent stash, or `git clean`.

Before every later child task, run at minimum:

```powershell
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
git status --porcelain
```

The expected relation is `0 0` and no unexpected tracked changes.

## Child execution order

Execute exactly this order:

1. PL-0006
2. PL-0007
3. PL-0008
4. PL-0009
5. PL-0010
6. PL-0011
7. PL-0012
8. PL-0013
9. PL-0014
10. PL-0015
11. PL-0016
12. PL-0017
13. PL-0018

Each child has a frozen prompt and criteria under:
https://github.com/Sekiph82/PackLab/tree/main/coordination/sessions/M00-C001

## Child prompt URLs

PL-0006:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0006_CODEX_PROMPT_V01.md

PL-0007:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0007_CODEX_PROMPT_V01.md

PL-0008:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0008_CODEX_PROMPT_V01.md

PL-0009:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0009_CODEX_PROMPT_V01.md

PL-0010:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0010_CODEX_PROMPT_V01.md

PL-0011:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0011_CODEX_PROMPT_V01.md

PL-0012:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0012_CODEX_PROMPT_V01.md

PL-0013:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0013_CODEX_PROMPT_V01.md

PL-0014:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0014_CODEX_PROMPT_V01.md

PL-0015:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0015_CODEX_PROMPT_V01.md

PL-0016:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0016_CODEX_PROMPT_V01.md

PL-0017:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0017_CODEX_PROMPT_V01.md

PL-0018:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0018_CODEX_PROMPT_V01.md

## Child criteria

For every child, read the matching:
`PL-xxxx_CHATGPT_AUDIT_CRITERIA_V01.md`
from:
https://github.com/Sekiph82/PackLab/tree/main/coordination/sessions/M00-C001

Every criterion is mandatory for Codex self-validation readiness, but Codex does not assign the final audit verdict.

## Child logging and commits

For each child:

1. execute only its frozen prompt;
2. run all required checks;
3. commit its implementation/evidence;
4. create `coordination/sessions/M00-C001/PL-xxxx_CODEX_LOG_V01.md`;
5. commit/push the child log;
6. verify remote visibility;
7. continue only if all child validations are green and no STOP condition exists.

Use one implementation/evidence commit plus one log-only commit per child where practical.

Do not edit root `TASKS.md`.

Do not create any `CHATGPT_AUDIT` file.

Do not mark any task `[x]`.

## Batch stop behavior

If any child cannot satisfy its frozen prompt/criteria:

- stop at that child;
- do not start later child tasks;
- publish that child log honestly;
- publish the master log with `BATCH_STOPPED`;
- identify the exact blocker/failure and last completed child;
- return `AWAITING_MILESTONE_AUDIT`;
- stop.

## Master log

After all 13 child logs are pushed, create:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_LOG_V01.md

It must include a table with, for every PL-0006..PL-0018:

- task ID;
- task prompt URL;
- criteria URL;
- implementation/evidence commit;
- child log commit;
- child log URL;
- files changed;
- validation summary;
- failures/fixes;
- residual limitations.

Also record:

- initial batch synchronization evidence;
- final repository HEAD;
- final `git diff --check`;
- final protected-file review;
- proof root `TASKS.md` was not modified by Codex;
- proof M01 was not started;
- public-repository privacy/security review;
- `BATCH_COMPLETED` or `BATCH_STOPPED`;
- final `AWAITING_MILESTONE_AUDIT`.

Do not predeclare the future commit SHA that contains the final master log.

## Final response

If completed, return only:

`M00-C001`

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_LOG_V01.md

`AWAITING_MILESTONE_AUDIT`

Then stop.
