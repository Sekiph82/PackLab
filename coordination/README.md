# PackLab Coordination Protocol

## Authority model

- Canonical repository: `Sekiph82/PackLab`.
- Canonical branch: `main`.
- GitHub `main` is repository truth.
- Root `TASKS.md` is the **only live project-status tracker** and the only H!veAI current-state surface.
- `AGENTS.md` and `CLAUDE.md` are operating manuals, not trackers.
- `coordination/AUDIT_POLICY.md` is the audit constitution.
- `coordination/AUDIT_INDEX.md` is ChatGPT-owned reusable audit memory, not live state.
- `coordination/sessions/<CYCLE_ID>/` contains immutable/versioned work orders and evidence.
- `handoff.md`, root `AUDIT.md`, session indexes, dashboards, and historical artifacts must never become competing live trackers.

## Roles

### Codex

Codex is the implementation and test actor.

Codex may:
- read root `TASKS.md`;
- read the active `CODEX_PROMPT_VNN.md` and matching `CHATGPT_AUDIT_CRITERIA_VNN.md`;
- modify only files authorized by the active prompt;
- run tests/checks;
- write the matching `CODEX_LOG_VNN.md`;
- commit and push authorized implementation/evidence changes.

Codex must **not**:
- edit root `TASKS.md`;
- create or edit `CHATGPT_AUDIT_*` files;
- create an audit verdict;
- self-close tasks;
- invent the next task;
- continue after returning `AWAITING_AUDIT`.

### ChatGPT

ChatGPT is the independent auditor, prompt/criteria author, and sole live-tracker writer.

ChatGPT owns:
- `CODEX_PROMPT_VNN.md`;
- `CHATGPT_AUDIT_CRITERIA_VNN.md`;
- `CHATGPT_AUDIT_VNN.md`;
- root `TASKS.md` lifecycle/progress/task closure;
- `coordination/AUDIT_INDEX.md` reusable audit learnings;
- correction/remediation prompt versions.

## Versioned cycle bundle

Each implementation cycle uses:

```text
coordination/sessions/<CYCLE_ID>/
  CODEX_PROMPT_V01.md
  CHATGPT_AUDIT_CRITERIA_V01.md
  CODEX_LOG_V01.md               # written by Codex
  CHATGPT_AUDIT_V01.md            # written by ChatGPT after log arrives
```

If audit fails or changes are required:

```text
  CODEX_PROMPT_V02.md
  CHATGPT_AUDIT_CRITERIA_V02.md
  CODEX_LOG_V02.md
  CHATGPT_AUDIT_V02.md
```

Continue V03, V04, etc. until closure. Never overwrite prior versions.

Cycle IDs normally use `<TASK_ID>-C001`, for example `PL-0001-C001`. A later independent cycle for the same task uses `PL-0001-C002`.

## Normal cycle flow

1. ChatGPT reads GitHub `main`, root `TASKS.md`, current source, prior session evidence, and relevant audit learnings.
2. ChatGPT freezes the implementation scope in `CODEX_PROMPT_VNN.md` and publishes matching strict criteria in `CHATGPT_AUDIT_CRITERIA_VNN.md`.
3. Codex synchronizes the local workspace according to the prompt and repository policy.
4. Codex confirms root `TASKS.md` still authorizes the task. If not, it stops without implementing.
5. Codex implements only the frozen prompt scope and runs every required validation command.
6. Codex writes a detailed matching `CODEX_LOG_VNN.md`, commits/pushes authorized changes, returns `AWAITING_AUDIT`, and stops.
7. ChatGPT reads the log and independently audits GitHub source/diff/evidence against the frozen criteria.
8. ChatGPT writes `CHATGPT_AUDIT_VNN.md`.
9. ChatGPT updates root `TASKS.md` to audited truth after **every** log/audit cycle.
10. PASS: ChatGPT closes only proven task rows and advances H!veAI state.
11. FAIL/CHANGES_REQUIRED: ChatGPT leaves the task open, records the exact state in `TASKS.md`, creates VNN+1 remediation prompt/criteria, and returns a short prompt link/instruction for Codex.
12. BLOCKED/OWNER_REQUIRED: ChatGPT records that state in `TASKS.md`; no AI silently bypasses it.

## One-time local bootstrap rule

Canonical local workspace:

`C:\Users\sekip\Desktop\PackLab`

The owner explicitly states that for the **first synchronization only**, GitHub `origin/main` is correct and local content is not authoritative. The active bootstrap-capable Codex prompt may therefore instruct a destructive tracked-file alignment to `origin/main` after verifying the repository/remote identity.

This is a one-time owner-authorized exception. After the local checkout is proven to match GitHub `main`, normal sessions must use safe fetch/compare/fast-forward behavior and must stop on unexpected local divergence unless a later owner instruction explicitly authorizes replacement.

Never use `git clean -fdx`; ignored local environments/caches must not be destroyed by the bootstrap alignment.

## Single-tracker rule

There is no second live tracker. Session files are work orders and evidence only. They never override `TASKS.md` current state.

## Canonical URLs

- Repository: https://github.com/Sekiph82/PackLab
- Tracker: https://github.com/Sekiph82/PackLab/blob/main/TASKS.md
- Coordination: https://github.com/Sekiph82/PackLab/tree/main/coordination
