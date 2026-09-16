# PackLab Agent Instructions

## Canonical project truth

PackLab follows the current H!veAI GitHub-first, root-`TASKS.md` tracking contract.

- Repository: `Sekiph82/PackLab`
- Canonical branch: `main`
- GitHub `main` is the authoritative repository state.
- Root `TASKS.md` is the **only authoritative project-status and task-tracking source**.
- Local folders are execution workspaces, not project truth.

Do not create, restore, or use `.hiveai/PROJECT.json`, `.hiveai/TASKS.md`, `.hiveai/RULES.md`, `.hiveai/EVENTS.jsonl`, `.hiveai/STATE.json`, `.hiveai/HANDOFF.md`, or any other `.hiveai` control-plane file as live project state. That architecture is superseded.

Do not maintain a competing current-task, progress, milestone, sprint, next-action, or handoff ledger in another file.

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

Task rows in `TASKS.md` use the repository's permanent `PL-xxxx` IDs and checkbox/status markers. Do not infer the current task by scanning for the first unchecked checkbox; the explicit Project Status section is authoritative.

Do not derive live project state from README files, prose, historical prompts, audit logs, builder logs, `IMPLEMENTATION_GUIDE.md`, `AUDIT.md`, `handoff.md`, or arbitrary Markdown discovery.

## Session start and synchronization

Before project work:

1. Confirm the Git root is this PackLab repository.
2. Run `git fetch origin main`.
3. Compare local HEAD with `origin/main` using `git rev-list --left-right --count HEAD...origin/main`.
4. If local HEAD is behind and the tracked worktree is safe to fast-forward, run `git merge --ff-only origin/main`.
5. Read root `TASKS.md` first.
6. Read only the additional project files that the active task actually requires.

Never use reset, force-push, destructive checkout, automatic rebase, or silent stash to manufacture synchronization. If a safe fast-forward is not possible, stop and report the exact divergence or conflicting tracked changes.

## Scope discipline

Work only on the task explicitly declared by `TASKS.md` or explicitly assigned by the owner.

- Preserve permanent `PL-xxxx` task IDs.
- Do not silently skip blocked tasks.
- Do not mark a task `[x]` merely because code was written. PackLab's task plan requires the applicable independent audit/acceptance gate before validated completion.
- Do not invent project progress percentages or state.
- Do not implement future tasks opportunistically.

The absence of a root `README.md` is currently intentional: creating it is planned as task `PL-0020`. Do not search repeatedly for a missing README or create it early unless the active task is `PL-0020` or the owner explicitly asks for it.

`IMPLEMENTATION_GUIDE.md` is a reference document, not an automatic session-start input. It is large; open only the sections relevant to the active task.

## Evidence and supporting documents

`AUDIT.md`, `handoff.md`, documentation, implementation guides, prompts, and logs may provide evidence or implementation context, but they do not override root `TASKS.md` as current project state.

- `AUDIT.md` records audit evidence/results.
- `handoff.md` is a non-authoritative workflow aid.
- Historical documents remain historical evidence and must not become a second tracker.

## Completion and GitHub synchronization

When repository work changes tracked files:

1. Run the task's required tests/checks.
2. Review the diff for scope and safety.
3. Commit the intended changes.
4. Push to `origin/main` unless the owner explicitly requested a different workflow.
5. Verify the remote state before claiming completion.

A local-only change is not a synchronized H!veAI project update.

If task state legitimately changes, root `TASKS.md` must remain truthful and parser-compatible. Do not create any parallel state store.

## Safety

- Never commit secrets, credentials, signing material, local caches, user data, generated reconstruction intermediates, or machine-specific runtime state.
- Do not overwrite unrelated user changes.
- Do not delete history or branches as a shortcut to resolve divergence.
- Prefer bounded, reversible changes and explicit failure reporting.
