# PackLab Auxiliary Agent Instructions

PackLab uses a GitHub-first H!veAI tracking and session-coordination architecture.

## Authority

- Canonical repository: `Sekiph82/PackLab`
- Canonical branch: `main`
- GitHub `main` is repository truth.
- Root `TASKS.md` is the **only live project-status tracker**.
- ChatGPT is the sole writer of root `TASKS.md` lifecycle/progress/task-closure state.
- Session artifacts under `coordination/sessions/` are work orders/evidence, not live state.

## Current implementation actor

Codex is the default implementation/test actor unless the owner or root `TASKS.md` explicitly assigns another actor.

Codex work is governed primarily by `AGENTS.md`, `coordination/README.md`, and `coordination/AUDIT_POLICY.md`.

## Work-order model

For an authorized task, the implementer reads the active:

- `coordination/sessions/<CYCLE_ID>/CODEX_PROMPT_VNN.md`
- `coordination/sessions/<CYCLE_ID>/CHATGPT_AUDIT_CRITERIA_VNN.md`

The implementer writes only the matching implementation evidence:

- `coordination/sessions/<CYCLE_ID>/CODEX_LOG_VNN.md`

The implementer never writes the ChatGPT audit file and never edits `TASKS.md`.

After handoff `AWAITING_AUDIT`, ChatGPT audits the actual GitHub state, writes `CHATGPT_AUDIT_VNN.md`, updates `TASKS.md`, and either closes/advances the task or issues the next remediation prompt version.

## Synchronization

Local workspace: `C:\Users\sekip\Desktop\PackLab`.

The owner has authorized one initial GitHub-authoritative alignment. Only the active prompt may invoke that bootstrap exception. After bootstrap, normal synchronization is fetch/compare/fast-forward-only and unexpected divergence must stop the session unless the owner explicitly authorizes replacement.

## Supporting documents

- `IMPLEMENTATION_GUIDE.md` contains architecture and implementation guidance; it is not a state tracker.
- `coordination/AUDIT_INDEX.md` contains reusable audit learnings; it is not a state tracker.
- `AUDIT.md` and `handoff.md` are non-authoritative compatibility/reference files.

Never create a competing current milestone/task/progress/next-action ledger.
