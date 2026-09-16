# PL-0001-C001 — Codex Prompt V01

Status: **ISSUED**

Task: **PL-0001 — Create canonical repository structure specification and ownership rules.**

Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Local workspace: `C:\Users\sekip\Desktop\PackLab`

## Mandatory inputs

Read before material implementation:

1. root `AGENTS.md`
2. root `TASKS.md`
3. `IMPLEMENTATION_GUIDE.md`
4. `coordination/README.md`
5. `coordination/AUDIT_POLICY.md`
6. `coordination/AUDIT_INDEX.md`
7. this prompt
8. `coordination/sessions/PL-0001-C001/CHATGPT_AUDIT_CRITERIA_V01.md`

If root `TASKS.md` no longer declares PL-0001 as the current authorized task, STOP and report `TASK_STATE_MISMATCH`. Do not implement.

## Phase 0 — One-time owner-authorized GitHub -> local bootstrap

The owner explicitly states that GitHub `Sekiph82/PackLab` `main` currently contains the correct files and that the local PackLab folder has not yet received those GitHub-side changes.

For this first synchronization only, GitHub wins over conflicting local tracked/non-ignored content.

Before any destructive command:

1. `cd C:\Users\sekip\Desktop\PackLab`
2. confirm this is a Git working tree;
3. confirm repository root is exactly the intended PackLab workspace;
4. inspect `git remote -v` and confirm `origin` resolves to `Sekiph82/PackLab`;
5. if repository identity/remote is wrong or ambiguous, STOP. Do not delete/reset anything.

If identity is correct, run:

```powershell
git fetch origin main --prune
git checkout -B main origin/main --force
git reset --hard origin/main
git clean -fd
```

Do **not** run `git clean -fdx`.

Then prove bootstrap state:

```powershell
git rev-parse HEAD
git rev-parse origin/main
git status --porcelain
git rev-list --left-right --count HEAD...origin/main
```

Required before implementation:
- local HEAD == origin/main;
- ahead/behind == `0 0`;
- tracked/non-ignored working tree clean;
- current GitHub control/coordination files exist locally.

Record exact pre/post sync evidence in the Codex log.

After this bootstrap succeeds, do not use reset/clean again during normal implementation unless required to recover Codex's own changes before commit.

## Phase 1 — Implement PL-0001 only

Create the canonical repository structure and ownership specification at:

`docs/architecture/REPOSITORY_STRUCTURE.md`

Do **not** create the future application/core directory tree itself. Physical top-level folder creation is PL-0019. PL-0001 is a governance/specification task.

The document must define at minimum:

### A. Planned canonical monorepo map

Document intended ownership/purpose for:

```text
apps/
  ios-capture/
  windows-studio/
core/
schemas/
assets/
tests/
tools/
docs/
  architecture/
coordination/
  sessions/
```

Also describe generated/runtime locations that must remain outside Git or be explicitly ignored later, including local scan data, reconstruction intermediates, Python environments/caches, Xcode/Swift build products, Blender temporary output and private Kenya/supplier assets.

### B. Source-of-truth ownership boundaries

Define clearly:

- GitHub `main` = repository truth;
- root `TASKS.md` = only live H!veAI/project-state tracker;
- ChatGPT = prompt/criteria author, independent auditor and sole TASKS lifecycle writer;
- Codex = implementer/test runner and `CODEX_LOG_VNN.md` writer;
- session artifacts = work orders/evidence, not live project state;
- PackLab Capture vs PackLab Studio ownership;
- reusable Python/domain core vs PySide6 UI ownership;
- `.packscan` schema ownership;
- COLMAP/OpenMVS/Open3D/OpenCascade/Blender adapter boundaries;
- immutable source scan vs derived Scan Master vs editable Design Model ownership;
- artwork/material separation from engineering geometry.

### C. Dependency direction rules

At minimum freeze these intended directions:

- UI may depend on PackLab-owned domain/application services; domain logic must not depend on PySide6 widgets.
- Swift capture UI may depend on PackLab-owned capture services; PackLab domain contracts must not depend directly on NextLevel internals.
- external engines are behind PackLab adapters/capability probes.
- reconstruction/scan artifacts do not become CAD truth automatically.
- Design Model may derive from Scan Master; Scan Master must not depend on Design Model.
- rendering may consume design/material/artwork data; rendering must not become engineering source of truth.

### D. File/data ownership and mutability

Document which classes of data are:

- immutable source evidence;
- regenerable derived data;
- editable project/design data;
- export artifacts;
- private/local-only data;
- safe public fixtures.

### E. Naming and future structure constraints

Define stable naming principles without prematurely implementing PL-0007 source-control conventions or PL-0021 `.gitignore`.

The document should explicitly say later tasks may refine structure through audited ADRs but must not silently invert these ownership boundaries.

## Scope boundaries

Authorized product/docs change for PL-0001:

- add `docs/architecture/REPOSITORY_STRUCTURE.md`;
- add the matching Codex implementation log for this session.

Do not modify:

- `TASKS.md`;
- `AGENTS.md`;
- `CLAUDE.md`;
- `IMPLEMENTATION_GUIDE.md`;
- `coordination/README.md`;
- `coordination/AUDIT_POLICY.md`;
- `coordination/AUDIT_INDEX.md`;
- `CHATGPT_AUDIT_CRITERIA_V01.md`;
- any `CHATGPT_AUDIT_*` artifact;
- `handoff.md` or root `AUDIT.md`;
- future app/core/source files.

If a governance contradiction makes PL-0001 impossible without editing a protected file, STOP and record the conflict. Do not self-resolve by changing governance.

## Validation

Run and record individually:

```powershell
git diff --check
```

Also perform explicit content checks proving `docs/architecture/REPOSITORY_STRUCTURE.md` contains:

- all planned canonical top-level areas;
- ownership model;
- dependency-direction rules;
- data mutability/provenance classes;
- GitHub/TASKS/ChatGPT/Codex authority model;
- Capture/Studio and external-engine boundaries;
- no claim that PL-0019 folder creation is already complete.

Review:

```powershell
git status --short
git diff -- docs/architecture/REPOSITORY_STRUCTURE.md
```

No general automated test suite exists yet; do not invent one for PL-0001.

## Required Codex log

Write:

`coordination/sessions/PL-0001-C001/CODEX_LOG_V01.md`

The log must follow `coordination/AUDIT_POLICY.md` and contain:

- prompt/criteria paths;
- starting remote commit after bootstrap;
- bootstrap commands and exact results;
- confirmation local matched GitHub before implementation;
- inputs read;
- document created;
- requirement-by-requirement summary;
- validation commands/results;
- failures/fixes if any;
- scope/protected-file check;
- secrets/privacy check;
- final commit SHA and push result;
- known limitations/unverified assumptions;
- final `AWAITING_AUDIT` handoff.

## Commit/push

Commit only the authorized PL-0001 document and matching `CODEX_LOG_V01.md`.

Push safely to `origin/main`.

Verify the pushed commit is visible as remote `origin/main` before handoff.

## Final response

Return only a concise handoff containing:

- task/cycle ID;
- final commit SHA;
- log GitHub path/URL;
- `AWAITING_AUDIT`.

Then STOP. Do not begin PL-0002.
