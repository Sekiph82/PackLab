# PL-0003-C001 — Codex Prompt V01

Status: **ISSUED**

Task: **PL-0003 — Create Architecture Decision Record (ADR) process and first ADR for the monorepo.**

Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Local workspace: `C:\Users\sekip\Desktop\PackLab`

## Mandatory inputs

Read before material implementation:

1. root `AGENTS.md`
2. root `TASKS.md`
3. `IMPLEMENTATION_GUIDE.md`
4. `docs/architecture/REPOSITORY_STRUCTURE.md`
5. `docs/architecture/GLOSSARY.md`
6. `coordination/README.md`
7. `coordination/AUDIT_POLICY.md`
8. `coordination/AUDIT_INDEX.md`
9. `coordination/sessions/PL-0001-C001/CHATGPT_AUDIT_V01.md`
10. `coordination/sessions/PL-0002-C001/CHATGPT_AUDIT_V01.md`
11. this prompt
12. `coordination/sessions/PL-0003-C001/CHATGPT_AUDIT_CRITERIA_V01.md`

If root `TASKS.md` does not declare PL-0003 as the current authorized task for Codex, STOP and report `TASK_STATE_MISMATCH`.

## Phase 0 — Safe synchronization

The destructive first bootstrap is complete. Use safe synchronization only.

Run:

```powershell
cd C:\Users\sekip\Desktop\PackLab
git rev-parse --show-toplevel
git remote -v
git status --porcelain
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
```

Rules:

- verify Git root and `origin` identify `Sekiph82/PackLab`;
- untracked historical `.hiveai/` state may remain local, but must not be staged or treated as project truth;
- if tracked worktree is clean and local is only behind, use:

```powershell
git merge --ff-only origin/main
```

- if local is ahead, diverged, or contains unexpected tracked changes, STOP and report exact state;
- do not reset, rebase, force-push, destructive checkout, silent stash, or `git clean`;
- before implementation prove local HEAD equals `origin/main` and `TASKS.md` authorizes PL-0003.

## Phase 1 — Implement the ADR process

Create:

`docs/architecture/adr/README.md`

This file is the canonical ADR process specification. It must define at minimum:

### ADR purpose

Explain when an ADR is required. At minimum, an ADR is required for a durable architectural choice that changes or freezes one or more of:

- repository/module boundaries;
- cross-platform contracts or ownership;
- major framework/runtime/tool selection;
- external-engine responsibility boundaries;
- persistence/storage architecture;
- geometry/CAD source-of-truth rules;
- security/trust boundaries;
- CI/build/distribution architecture;
- replacement of an already accepted architectural decision.

Clarify that routine implementation detail, typo fixes, ordinary refactors that preserve contracts, and task-status changes do not automatically require ADRs.

### ADR identity and file naming

Freeze a stable sequential scheme:

```text
ADR-0001-<lowercase-kebab-slug>.md
ADR-0002-<lowercase-kebab-slug>.md
...
```

Numbers are permanent and never reused, even if an ADR is rejected, deprecated, or superseded.

### ADR lifecycle/statuses

Define at least these statuses and semantics:

- `Proposed`
- `Accepted`
- `Rejected`
- `Deprecated`
- `Superseded`

The process must state:

- Codex may draft an ADR only when the active prompt authorizes it;
- Codex does not self-accept architecture decisions;
- acceptance must come through the PackLab audited task/session process and any explicitly required owner decision;
- accepted ADR history is preserved;
- a material change to an accepted ADR is normally a new ADR that supersedes it rather than silently rewriting history;
- typo/link/format corrections that do not change the decision may be made with traceable review.

### Required ADR fields/sections

Define a required structure containing at least:

1. ADR ID and title
2. Status
3. Date
4. Decision scope
5. Context / problem
6. Decision
7. Rationale
8. Alternatives considered
9. Consequences / trade-offs
10. Constraints / invariants
11. Supersedes / Superseded by
12. References / evidence

The process may include a Markdown template in `README.md`; do not create a separate template file unless necessary.

### Authority and relationship rules

State clearly:

- root `TASKS.md` remains the only live H!veAI tracker;
- ADRs record architecture decisions, not project progress;
- `REPOSITORY_STRUCTURE.md` and `GLOSSARY.md` remain architecture/terminology contracts and may be referenced by ADRs;
- an ADR cannot silently override a higher-authority active task/session scope;
- when a new accepted ADR intentionally changes an existing architecture contract, the same audited change or a specifically authorized follow-up task must reconcile the affected canonical documents;
- session prompts/audits provide decision evidence but are not themselves ADRs.

### ADR index behavior

`docs/architecture/adr/README.md` must contain an ADR index table with at least:

- ADR ID
- title
- status
- supersession relation if any

The first row must reference ADR-0001 created by this task.

## Phase 2 — Create the first ADR

Create:

`docs/architecture/adr/ADR-0001-monorepo-architecture.md`

Title/decision intent:

**Use one PackLab monorepo with explicit platform, domain, schema, architecture-documentation, and coordination boundaries.**

ADR-0001 must be `Accepted` because PL-0001 already established and independently audited this architecture. This ADR records that existing accepted architecture; it must not invent a conflicting new design.

ADR-0001 must record at minimum:

### Context

PackLab contains two platform products:

- PackLab Capture on iPhone/iOS;
- PackLab Studio on Windows;

and also requires shared cross-platform contracts, architecture documentation, test fixtures, tools, and AI coordination evidence. The products evolve together around the `.packscan` boundary and shared packaging terminology/ownership rules.

### Decision

Record the planned monorepo areas from the audited repository-structure contract:

```text
apps/ios-capture/
apps/windows-studio/
core/
schemas/
assets/
tests/
tools/
docs/architecture/
coordination/sessions/
```

Do **not** physically create the future app/core/schema/assets/tests/tools tree in this task; physical creation remains PL-0019.

Freeze these ownership/dependency decisions without broadening them:

- iOS-specific implementation belongs to PackLab Capture;
- Windows/PySide6 presentation belongs to PackLab Studio;
- reusable Python/domain/application logic remains separate from PySide6 widgets;
- cross-platform machine contracts belong at the future `schemas/` boundary;
- coordination evidence remains separate from product/runtime source;
- GitHub `main` remains repository truth and root `TASKS.md` remains live project-state truth;
- Scan/reference and editable Design Model ownership rules from PL-0001 remain unchanged.

### Rationale

Include concrete reasons relevant to PackLab, such as:

- coordinated evolution of Capture and Studio around PackScan;
- atomic cross-platform contract changes;
- one auditable architecture/history surface;
- simpler shared documentation/fixtures/tooling;
- easier coordination for a single-owner personal project;
- explicit boundaries still prevent UI/platform coupling despite one repository.

### Alternatives considered

Evaluate at least:

1. separate iOS and Windows repositories;
2. multiple repositories split by subsystem/core;
3. one repository without explicit ownership boundaries.

For each, state why it was not selected for the current PackLab context. Do not claim these alternatives are universally bad.

### Consequences / trade-offs

Include both positive and negative consequences. At minimum discuss:

- easier atomic schema/contract changes;
- centralized CI/documentation/audit history;
- risk of repository growth and unrelated-change coupling;
- need for path-scoped CI and clear module ownership later;
- public-repository privacy discipline for scans/supplier assets;
- no implication that every dependency/runtime must be installed for every subproject.

### Constraints / invariants

Preserve the audited PL-0001 architecture:

- UI must not become domain truth;
- NextLevel remains behind PackLab-owned capture interfaces;
- external engines remain behind PackLab adapters/capability boundaries;
- Scan Mesh/Scan Master do not become editable CAD truth;
- Design Model may derive from Scan Master but not mutate it;
- Blender/render output is not dimensional truth;
- private Kenya/supplier data stays out of the public source tree unless explicitly approved as safe public fixture material.

### References

Reference at least:

- `../REPOSITORY_STRUCTURE.md`
- `../GLOSSARY.md`
- PL-0001 independent audit artifact
- PL-0002 independent audit artifact

## Scope boundaries

Authorized changes:

- add `docs/architecture/adr/README.md`;
- add `docs/architecture/adr/ADR-0001-monorepo-architecture.md`;
- add matching `coordination/sessions/PL-0003-C001/CODEX_LOG_V01.md`.

Do not modify:

- root `TASKS.md`;
- `AGENTS.md`;
- `CLAUDE.md`;
- `IMPLEMENTATION_GUIDE.md`;
- `docs/architecture/REPOSITORY_STRUCTURE.md`;
- `docs/architecture/GLOSSARY.md`;
- coordination policy/index;
- prior PL-0001/PL-0002 session artifacts;
- this prompt or its audit criteria;
- root `AUDIT.md` or `handoff.md`;
- application/source/schema/runtime files.

Do not implement PL-0004+.

## Validation

Run and record:

```powershell
git diff --check
```

Because this task creates new files, do **not** rely on a plain unstaged `git diff -- <new-file>` as content-review evidence.

Use one of these auditable approaches before commit:

```powershell
git add -N docs/architecture/adr/README.md docs/architecture/adr/ADR-0001-monorepo-architecture.md
git diff -- docs/architecture/adr/README.md docs/architecture/adr/ADR-0001-monorepo-architecture.md
```

or deliberately stage the files and review:

```powershell
git diff --cached -- docs/architecture/adr/README.md docs/architecture/adr/ADR-0001-monorepo-architecture.md
```

Perform explicit content checks proving:

- ADR process statuses and lifecycle rules exist;
- required ADR fields/sections exist;
- numbering is permanent and sequential;
- root TASKS remains the live tracker;
- ADR history/supersession is non-destructive;
- README index includes ADR-0001;
- ADR-0001 status is Accepted;
- ADR-0001 records the planned monorepo without physically creating PL-0019 directories;
- required alternatives and trade-offs exist;
- PL-0001 ownership invariants are preserved;
- required references exist;
- no protected file is modified.

No general application test suite is required for this documentation/governance task.

## Required Codex log

Write:

`coordination/sessions/PL-0003-C001/CODEX_LOG_V01.md`

Record:

- prompt/criteria paths;
- starting synchronized commit;
- synchronization commands/results;
- inputs read;
- files added/modified/deleted;
- process and ADR implementation summary;
- exact validation commands, expected results, explicit failure conditions and actual results;
- new-file diff-review evidence;
- failures/fixes;
- scope/protected-file check;
- secrets/privacy check;
- implementation commit and push evidence;
- limitations/unverified assumptions;
- final `AWAITING_AUDIT` handoff.

## Commit / push

Commit only the two authorized ADR documents and matching Codex log.

Push safely to `origin/main` and verify remote visibility.

## Final response

Return only a concise handoff containing:

- `PL-0003-C001`;
- final implementation/log commit information;
- log GitHub path/URL;
- `AWAITING_AUDIT`.

Then STOP. Do not begin PL-0004.
