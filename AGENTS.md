# PackLab Agent Instructions

## Canonical project truth

PackLab is GitHub-first.

- Repository: `Sekiph82/PackLab`
- Canonical branch: `main`
- GitHub `main` is authoritative repository truth.
- Root `TASKS.md` is the **only live project-status tracker** and only H!veAI current-state surface.
- Local workspace: `C:\Users\sekip\Desktop\PackLab`
- Local files are execution workspace, not project truth.

Do not create or use a second current-task/progress/milestone/actor ledger.

## Role ownership

Codex is the implementation/test actor.

ChatGPT is the independent auditor, Codex prompt/criteria author, audit-memory owner, and **sole writer of root `TASKS.md` lifecycle/progress/task-closure state**.

Codex must not edit root `TASKS.md`, must not create ChatGPT audit verdicts, and must not advance to a new task after implementation.

Full policy:
- `coordination/README.md`
- `coordination/AUDIT_POLICY.md`
- `coordination/AUDIT_INDEX.md`

## H!veAI parser contract

Read project state from the explicit `## Project Status` section at the top of root `TASKS.md`.

Preserve these fields and their meanings:

- `Current Milestone`
- `Current Sprint`
- `Current Task`
- `Current Task Status`
- `Next Task/Action`
- `Required Actor`
- `Tracking Repository`
- `Tracking Branch`

Never infer the current task by scanning for the first unchecked checkbox.

`TASKS.md` is the only live state. `AUDIT.md`, `handoff.md`, `IMPLEMENTATION_GUIDE.md`, coordination artifacts, logs and historical prompts are evidence/reference only.

## Session-based execution

Codex does not invent its own work order.

For the task authorized by `TASKS.md`, Codex must execute the active versioned prompt under:

`coordination/sessions/<CYCLE_ID>/CODEX_PROMPT_VNN.md`

and read the matching:

`coordination/sessions/<CYCLE_ID>/CHATGPT_AUDIT_CRITERIA_VNN.md`

The prompt defines exact scope, allowed files, validation commands and expected log path.

After implementation Codex writes exactly the matching:

`coordination/sessions/<CYCLE_ID>/CODEX_LOG_VNN.md`

then commits/pushes authorized implementation/evidence, returns `AWAITING_AUDIT`, and stops.

Codex must never create or edit:

`coordination/sessions/<CYCLE_ID>/CHATGPT_AUDIT_VNN.md`

ChatGPT creates the audit after inspecting the log and actual GitHub state.

## Synchronization

### One-time owner-authorized bootstrap

The owner has explicitly declared GitHub `origin/main` correct for the first alignment of `C:\Users\sekip\Desktop\PackLab`.

Only when the active Codex prompt explicitly authorizes the bootstrap:

1. confirm the Git root is PackLab;
2. confirm `origin` points to `Sekiph82/PackLab`;
3. fetch `origin/main`;
4. align tracked local state exactly to `origin/main` using the prompt's commands;
5. remove only non-ignored untracked files when explicitly instructed;
6. never use `git clean -fdx`.

This bootstrap exception ends once the local checkout is proven equal to GitHub `main`.

### Normal sessions after bootstrap

1. `git fetch origin main`
2. compare local HEAD with `origin/main`;
3. fast-forward only when safe;
4. stop and report unexpected local divergence or conflicting tracked changes.

Do not reset, rebase, force-push, destructive-checkout or silently stash in normal sessions unless a later owner-authorized prompt explicitly permits it.

## Scope discipline

- Work only on the frozen active prompt.
- Preserve permanent `PL-xxxx` IDs.
- Do not implement future tasks opportunistically.
- Do not mark tasks complete.
- Do not invent progress percentages.
- Do not rewrite governance/audit files unless the active prompt explicitly authorizes the exact file.
- If actual repository state contradicts the prompt or TASKS.md, stop and report the mismatch.

## Evidence requirements

Codex runtime checks are implementer evidence, not independent audit proof.

The matching `CODEX_LOG_VNN.md` must include:
- starting and final commit;
- synchronization result;
- prompt/criteria read;
- files changed;
- implementation details;
- exact commands/tests;
- expected result and failure condition for material checks;
- actual results;
- failures/fixes;
- negative/boundary/regression coverage;
- known limitations/unverified assumptions;
- secrets/privacy review;
- commit/push evidence;
- `AWAITING_AUDIT` handoff.

## Completion

A Codex implementation pass is not project completion.

After `AWAITING_AUDIT`:
1. Codex stops.
2. ChatGPT audits GitHub source/diff/evidence against the frozen criteria.
3. ChatGPT writes `CHATGPT_AUDIT_VNN.md`.
4. ChatGPT updates root `TASKS.md` to audited truth after every audit.
5. PASS advances/closes only proven tasks.
6. CHANGES_REQUIRED keeps the task open and causes ChatGPT to issue VNN+1 prompt/criteria.

## Safety

Never commit:
- secrets or credentials;
- Apple signing private material;
- GitHub/API tokens;
- private Kenya scans;
- confidential supplier files;
- local caches/environments;
- generated reconstruction intermediates unless a specific task explicitly defines a safe fixture.

Prefer bounded, reversible implementation changes and explicit failure reporting.
