# PackLab Codex Autonomous Queue

This directory stores automation instructions and per-task execution metadata. It is not a project-status tracker; root `TASKS.md` remains the only current-state authority.

## Authority and scope

- Repository: `Sekiph82/PackLab`; canonical branch: `main`.
- Workspace: `C:\Users\sekip\Desktop\PackLab`.
- Read the explicit `## Project Status` fields in `TASKS.md`; never infer the active task from checkbox order.
- The owner delegated PackLab implementation, local validation, task sequencing, and PackLab policy/tracker maintenance to Codex on 2026-10-22.
- Continue dependency-ready PackLab work without waiting for routine prompts or review. Do not access or modify other project workspaces.
- After each locally complete task, immediately select the next dependency-ready task and continue in the same run. Do not yield solely because a task or heartbeat cycle ended; yield only for a genuine gate or execution interruption.
- Do not open, start, or use a dashboard for queue control or monitoring. Read PackLab files and run scoped local commands directly.
- Preserve genuine owner, safety, security, legal, licensing, dependency, environment, device, and resource gates.

## Execution and evidence

- Create a versioned task prompt, validation criteria, and Codex log under `coordination/sessions/` for each new task.
- Keep each task's job metadata under `project-control/codex/jobs/<PL-ID>/job.json`.
- The queue validator reads only root `TASKS.md` and checks that its explicit current task matches one canonical ledger row.
- Record exact commands and results. Keep local validation, independent review, hosted checks, physical/device acceptance, and release readiness distinct.
- Update `TASKS.md` only to states supported by evidence. Keep historical prompts/logs/audits immutable.

## Operational limits

- Zero GitHub Actions and zero paid CI. Never dispatch, retry, rerun, or push a change that can trigger a workflow.
- No PRs, source pushes to `main`, native OCCT/OCP builds, Installer builds, or unapproved large downloads.
- Preserve owner Desktop and OwnerDev data. Delete only exact, verified task-owned temporary artifacts.
- Do not claim hosted verification, independent acceptance, or release readiness without evidence.

See `AUTOMATION-PROMPT.md` for the recurring queue prompt and root `AGENTS.md` for full workspace safeguards.
