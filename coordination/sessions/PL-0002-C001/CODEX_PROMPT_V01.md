# PL-0002-C001 — Codex Prompt V01

Status: **ISSUED**

Task: **PL-0002 — Create project glossary covering Scan Mesh, Design Model, Digital Twin, PackScan, Label Zone, BREP, SfM and MVS.**

Repository: https://github.com/Sekiph82/PackLab
Branch: `main`
Local workspace: `C:\Users\sekip\Desktop\PackLab`

## Mandatory inputs

Read before material implementation:

1. root `AGENTS.md`
2. root `TASKS.md`
3. `IMPLEMENTATION_GUIDE.md` section for PL-0002
4. `docs/architecture/REPOSITORY_STRUCTURE.md`
5. `coordination/README.md`
6. `coordination/AUDIT_POLICY.md`
7. `coordination/AUDIT_INDEX.md`
8. `coordination/sessions/PL-0001-C001/CHATGPT_AUDIT_V01.md`
9. this prompt
10. `coordination/sessions/PL-0002-C001/CHATGPT_AUDIT_CRITERIA_V01.md`

If root `TASKS.md` no longer declares PL-0002 as the current authorized task for Codex, STOP and report `TASK_STATE_MISMATCH`.

## Phase 0 — Safe synchronization

The one-time destructive bootstrap has already completed and must **not** be repeated.

Run safe synchronization only:

```powershell
cd C:\Users\sekip\Desktop\PackLab
git rev-parse --show-toplevel
git remote -v
git status --porcelain
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
```

Rules:

- verify the repository root and `origin` still identify `Sekiph82/PackLab`;
- if the tracked worktree is clean and local is only behind, fast-forward with:

```powershell
git merge --ff-only origin/main
```

- if local is ahead, diverged, or contains unexpected tracked changes, STOP and report the exact state;
- do not reset, rebase, force-push, destructive checkout, or silently stash;
- do not use `git clean` for this task.

Before implementation, prove local HEAD equals `origin/main` and root `TASKS.md` authorizes PL-0002.

## Phase 1 — Implement PL-0002 only

Create:

`docs/architecture/GLOSSARY.md`

This is a terminology-contract task. Do not implement schemas, source code, folders, data models, CAD logic, capture code, or reconstruction behavior.

The glossary must define at minimum:

1. **PackLab Capture**
2. **PackLab Studio**
3. **PackScan / `.packscan`**
4. **Source Evidence / Raw Capture**
5. **Reconstruction Intermediate**
6. **Scan Mesh**
7. **Scan Master**
8. **Design Model**
9. **Digital Twin**
10. **Parametric Geometry**
11. **Profile**
12. **Cross-Section**
13. **Feature / Parametric Feature**
14. **BREP / B-Rep**
15. **STEP**
16. **SfM — Structure from Motion**
17. **MVS — Multi-View Stereo**
18. **Camera Intrinsics**
19. **Camera Extrinsics / Pose**
20. **Calibration**
21. **Scale / Metric Scale**
22. **Coordinate System**
23. **Label Zone**
24. **Dieline**
25. **Artwork**
26. **Material Assignment / PBR Material**
27. **Packaging Asset**
28. **Component / Assembly**
29. **Provenance**
30. **Fixture / Public Test Fixture**

## Definition quality requirements

Every term must be PackLab-specific rather than a generic dictionary sentence.

For each material architectural term, state enough of the following to remove ambiguity:

- what the term means in PackLab;
- what owns or creates it;
- whether it is immutable, derived/regenerable, editable, or presentation-only;
- what it may depend on;
- what it must **not** be confused with.

The glossary must explicitly freeze these distinctions:

### Scan Mesh vs Scan Master vs Design Model

- a Scan Mesh is triangle/reference reconstruction geometry and is not editable CAD truth;
- a Scan Master is a deliberately promoted/normalized reference derived from reconstruction evidence;
- a Design Model is a separate editable, parameter-driven geometry representation;
- a Design Model may derive from a Scan Master, but editing the Design Model must not mutate the Scan Master.

### Digital Twin

For PackLab, Digital Twin must not mean only a pretty 3D mesh. Define it as the governed packaging asset/revision relationship that can include source evidence, promoted scan reference, editable Design Model, engineering exports, metadata, compatible components, labels/artwork/material assignments and provenance as applicable.

Do not claim every Digital Twin must already contain every optional layer. Distinguish asset identity from individual representations/revisions.

### PackScan

Define `.packscan` as the versioned Capture-to-Studio interchange/container concept. Do not prematurely freeze the exact ZIP/manifest schema that belongs to PL-0044+.

### SfM vs MVS

Freeze the conceptual division:

- SfM estimates camera relationships/poses and sparse scene structure from overlapping images;
- MVS uses calibrated/posed multi-view imagery to estimate dense geometry;
- in PackLab's planned primary pipeline COLMAP is the SfM/sparse boundary and OpenMVS is the dense MVS boundary;
- these algorithms do not by themselves establish engineering CAD truth or certified metric accuracy.

### BREP / STEP

Freeze that BREP is the engineering topological/geometric solid/surface representation layer used through the CAD boundary, while STEP is an interchange/export format. A STEP file is not itself the conceptual source-of-truth Design Model.

### Label Zone / Dieline / Artwork

Freeze that:

- Label Zone is a geometric placement/usable-region concept associated with packaging geometry;
- Dieline is a 2D dimensional boundary/template derived or defined for production/artwork use;
- Artwork is visual content mapped to a zone/dieline and remains separate from engineering body geometry.

### Material / rendering

Freeze that PBR/material assignments and rendered appearance are presentation/product-description layers and do not redefine engineering dimensions.

## Cross-reference requirements

- link or reference `docs/architecture/REPOSITORY_STRUCTURE.md` as the ownership/dependency specification;
- state that schema-level normative definitions will live in future `schemas/` contracts where applicable;
- state that this glossary is terminology guidance and does not override root `TASKS.md`, active session scope, schemas, or audited ADRs.

## Scope boundaries

Authorized changes:

- add `docs/architecture/GLOSSARY.md`;
- add the matching `coordination/sessions/PL-0002-C001/CODEX_LOG_V01.md`.

Do not modify:

- root `TASKS.md`;
- `AGENTS.md`;
- `CLAUDE.md`;
- `IMPLEMENTATION_GUIDE.md`;
- `docs/architecture/REPOSITORY_STRUCTURE.md`;
- coordination policy/index;
- any PL-0001 session artifact;
- this prompt or audit criteria;
- root `AUDIT.md` or `handoff.md`;
- application/source/schema files.

Do not opportunistically implement PL-0003+.

## Validation

Run and record individually:

```powershell
git diff --check
```

Perform explicit content checks proving:

- all 30 required glossary terms exist;
- Scan Mesh / Scan Master / Design Model distinctions are present;
- Digital Twin is not reduced to a mesh;
- PackScan does not prematurely define the future exact schema;
- SfM/MVS division and COLMAP/OpenMVS planned roles are correct;
- BREP vs STEP distinction is correct;
- Label Zone / Dieline / Artwork separation is correct;
- rendering/material is not dimensional truth;
- REPOSITORY_STRUCTURE is referenced;
- no protected file was modified.

Also inspect:

```powershell
git status --short
git diff -- docs/architecture/GLOSSARY.md
```

No general automated application test suite is required for this documentation-only task.

## Required Codex log

Write:

`coordination/sessions/PL-0002-C001/CODEX_LOG_V01.md`

Record:

- prompt/criteria paths;
- starting synchronized commit;
- safe synchronization commands/results;
- inputs read;
- files changed;
- requirement-by-requirement summary;
- exact validation commands, expected results, failure conditions and actual results;
- failures/fixes;
- scope check;
- secrets/privacy check;
- implementation commit and push evidence;
- limitations/unverified assumptions;
- final `AWAITING_AUDIT` handoff.

## Commit / push

Commit only the authorized glossary and matching Codex log.

Push safely to `origin/main` and verify remote visibility.

## Final response

Return only a concise handoff containing:

- `PL-0002-C001`;
- final implementation/log commit information;
- log GitHub path/URL;
- `AWAITING_AUDIT`.

Then STOP. Do not begin PL-0003.
