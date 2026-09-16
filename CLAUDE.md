# PackLab Claude Instructions

PackLab uses the current H!veAI GitHub-first tracking architecture.

## Project authority

- Canonical repository: `Sekiph82/PackLab`
- Canonical branch: `main`
- Root `TASKS.md` is the **only authoritative project-status tracker**.
- GitHub `main` is project truth; a local checkout is only an execution workspace.

Do not read, create, restore, or update `.hiveai/*` files as current project state. The former `.hiveai` control-plane architecture is superseded.

Do not maintain current milestone, sprint, task, progress, next action, or required actor in this file or any other competing ledger.

## Start of work

1. Safely synchronize with `origin/main` using fetch plus fast-forward-only behavior.
2. Read root `TASKS.md` first.
3. Use the explicit `## Project Status` fields as authoritative; never infer the current task from the first unchecked checkbox.
4. Read only the extra files required by the explicitly active task.

Do not use reset, rebase, force-push, destructive checkout, or silent stash to resolve divergence.

## Supporting files

- `AUDIT.md` is audit evidence, not current project state.
- `handoff.md` is a non-authoritative workflow aid.
- `IMPLEMENTATION_GUIDE.md` is reference material and should be opened only as needed for the active task.
- A root `README.md` does not yet exist because its creation is planned as `PL-0020`; do not repeatedly search for it or create it early.

## Task discipline

- Work only on the task explicitly declared in root `TASKS.md` or directly assigned by the owner.
- Preserve permanent `PL-xxxx` task IDs.
- Do not invent project state or completion percentages.
- Do not mark a task complete without the audit/acceptance required by the PackLab task plan.
- Do not opportunistically implement later tasks.

When work changes repository files, run the required checks, review the diff, commit, push to `origin/main`, and verify remote synchronization before claiming completion.
