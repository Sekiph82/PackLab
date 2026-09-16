# PackLab Handoff Notes

> **Non-authoritative workflow aid.** Current project state is defined only by root `TASKS.md` on GitHub `main`.

This file may contain short human handoff notes when useful, but H!veAI, Codex, Claude, OpenCode, and other agents must not parse it as the source of current milestone, sprint, task, status, next action, required actor, or project progress.

## Canonical state

For the live project state, always read:

`TASKS.md`

The explicit `## Project Status` section in that file is authoritative.

Do not mirror the current task here. Avoid duplicated state that can drift.

## Recommended execution flow

1. Safely synchronize the local checkout with GitHub `main`.
2. Read root `TASKS.md`.
3. Work only on the explicitly active/assigned task.
4. Read `IMPLEMENTATION_GUIDE.md` or other docs only when relevant to that task.
5. Run required tests/checks and collect evidence.
6. Record independent audit evidence in `AUDIT.md` when the PackLab workflow requires it.
7. Update root `TASKS.md` only when the canonical project state legitimately changes.
8. Commit and push the synchronized result to `main` before claiming GitHub/H!veAI project completion.

## Notes policy

If a temporary handoff note is added here, keep it descriptive rather than state-defining. Do not create a second task ledger, progress counter, or next-task queue in this file.
