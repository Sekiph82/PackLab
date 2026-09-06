# claude.md - PackLab AI Execution Protocol

This file is the mandatory operating procedure for any AI that develops, reviews, audits, or coordinates work in this repository.

## 1. Non-negotiable execution order

For every work session, follow this exact order:

1. Read handoff.md FIRST.
2. Determine project state from handoff.md.
   - If Project State = NEW or no completed task exists, start from PL-0001.
   - If Project State = IN_PROGRESS, resume the Current Task ID.
   - If Project State = AUDIT-PENDING, do not start a new task. The task must be independently audited.
   - If Project State = AUDIT-FAILED, repair the same task. Do not advance.
   - If Project State = READY-FOR-NEXT, read TASKS.md and select the first unchecked eligible task in ID order.
3. Read TASKS.md to confirm the current Milestone, Sprint, task ID, prerequisites, and checkbox state.
4. Read the matching task definition in IMPLEMENTATION_GUIDE.md completely.
5. Inspect all repository files relevant to the task before changing anything.
6. Implement exactly one task unless IMPLEMENTATION_GUIDE.md explicitly says the task is an atomic multi-file operation.
7. Run the tests/checks/evidence required for that task.
8. Update handoff.md with implementation evidence and set Project State = AUDIT-PENDING.
9. STOP builder work. The builder AI must NOT mark the task complete in TASKS.md.
10. A SECOND, INDEPENDENT AI must perform the audit using the Auditor Protocol below.
11. The auditor writes its result to AUDIT.md.
12. After the audit is written, the coordinator/builder reads AUDIT.md.
13. If Verdict = PASS:
    - change only the audited task checkbox in TASKS.md from [ ] to [x];
    - update milestone/sprint status only when all required children are complete;
    - update handoff.md with Last Completed Task and Next Task;
    - set Project State = READY-FOR-NEXT.
14. If Verdict = FAIL:
    - leave TASKS.md checkbox unchecked;
    - copy audit findings into handoff.md;
    - set Project State = AUDIT-FAILED;
    - repair the SAME task;
    - submit it for a fresh independent audit.
15. If Verdict = BLOCKED:
    - leave the checkbox unchecked;
    - record blocker and required external action in handoff.md;
    - do not silently skip ahead unless the user explicitly approves an exception.

## 2. Roles

### Builder AI

The Builder AI implements one task.

Builder MUST:
- read handoff.md first;
- work on the exact Current Task ID;
- read the exact IMPLEMENTATION_GUIDE.md entry;
- preserve architecture boundaries;
- make the smallest complete change that satisfies acceptance criteria;
- add/update tests where required;
- run required validation;
- record changed files, commands, results and residual risks in handoff.md;
- set state to AUDIT-PENDING.

Builder MUST NOT:
- mark its own TASKS.md checkbox [x];
- self-declare PASS;
- modify AUDIT.md with a PASS verdict;
- hide failing tests;
- skip dependencies without recording an approved exception;
- commit credentials, private keys, Apple signing secrets, personal Apple credentials, private Kenya scans or proprietary supplier data to this public repository;
- replace a specified technology without an ADR when the change is architectural;
- rewrite unrelated code while performing a focused task.

### Auditor AI

The Auditor AI must be a separate AI agent/context from the builder.

Auditor MUST:
1. Read handoff.md.
2. Read TASKS.md.
3. Read the audited task entry in IMPLEMENTATION_GUIDE.md.
4. Inspect the actual repository diff/files produced for the task.
5. Independently run or verify the required tests/checks when possible.
6. Check architecture, security, data integrity, error handling, tests, documentation and task scope.
7. Look specifically for false-positive completion, hardcoded shortcuts, untested happy paths, secret leakage and accidental coupling.
8. Write the result into AUDIT.md using its required schema.
9. Never edit TASKS.md.
10. Never fix the implementation during the audit. It reports findings only. Repairs belong to the Builder AI.

### Coordinator

The Coordinator is the stage that consumes the independent audit.

Coordinator MUST:
- read AUDIT.md after the auditor finishes;
- verify Task ID matches handoff.md Current Task ID;
- verify audited commit/revision corresponds to the implementation;
- on PASS only, tick the exact task in TASKS.md;
- on FAIL/BLOCKED, leave it unchecked;
- update handoff.md state and next action.

The same AI may act as Builder and later Coordinator, but it may NOT act as both Builder and Auditor for the same task.

## 3. Definition of Done

A task is Done only when ALL are true:

1. Implementation matches the task scope.
2. Acceptance criteria in IMPLEMENTATION_GUIDE.md are satisfied.
3. Required automated tests pass.
4. Required manual/visual/physical-device check is documented when applicable.
5. No new known critical/high-severity defect is introduced.
6. No secret or private user data is committed.
7. handoff.md contains implementation evidence.
8. Independent auditor returns PASS in AUDIT.md.
9. Coordinator changes the matching TASKS.md checkbox to [x].

Code existing in the repository is NOT equivalent to task completion.

## 4. Audit states

AUDIT.md Verdict must be exactly one of:

- PENDING
- PASS
- FAIL
- BLOCKED

PASS means all required acceptance criteria are met.
FAIL means implementation is incorrect, incomplete, unsafe, untested or out of scope.
BLOCKED means audit cannot be completed because required evidence/environment/input is unavailable.

A PASS with unresolved mandatory findings is forbidden.

## 5. Task ordering

Default rule: execute PL-0001, PL-0002, PL-0003 ... in ascending order.

A later task may begin early only when:
- its dependencies are already complete;
- the user explicitly requests reprioritization or an approved ADR documents the exception;
- handoff.md records the exception and reason.

Never use an easy later task to bypass a difficult current task.

## 6. Repository architecture contract

Target architecture:

GitHub
|
+-- GitHub Actions Windows
|   +-- PackLab Studio
|       +-- PySide6 / Python Core
|       +-- OpenCV
|       +-- PyTorch
|       +-- COLMAP
|       +-- OpenMVS
|       +-- Open3D
|       +-- OpenCascade binding
|       +-- Blender
|
+-- GitHub Actions macOS
    +-- PackLab Capture
        +-- SwiftUI
        +-- NextLevel
        +-- ARKit
        +-- Vision
        +-- CoreMotion
        +-- signed IPA when signing material is available
        +-- free-first sideload fallback when it is not

Core data flow:

iPhone 16 -> PackLab Capture -> .packscan -> PackLab Studio -> COLMAP -> OpenMVS -> Open3D -> Scan Master -> Parametric Geometry Engine -> OpenCascade BREP/STEP -> Labels/Materials/Blender -> Kenya Packaging Library

Important architectural rules:
- iPhone 16 Standard is treated as a non-LiDAR device.
- NextLevel is the camera-control layer, not the 3D reconstruction engine.
- ARKit pose is supporting metadata, not the sole photogrammetry solution.
- COLMAP owns SfM/sparse reconstruction.
- OpenMVS owns dense cloud/mesh/refinement/texturing in the primary pipeline.
- Open3D owns point-cloud/mesh analysis, cleanup, registration and measurements.
- Scan Mesh and editable Design Model are different assets and must never be conflated.
- OpenCascade/BREP is the engineering CAD layer for editable solids and STEP.
- Blender is the UV/material/render automation layer, not the source of dimensional truth.
- Original .packscan input and source photos are immutable evidence after ingest.

## 7. Public repository security rules

This repository is public.

Never commit:
- Apple ID/password;
- app-specific Apple passwords;
- signing private keys;
- unencrypted .p12 certificates;
- provisioning secrets that expose private identity material;
- GitHub tokens;
- private API keys;
- personal device identifiers unless explicitly safe and required;
- private Kenya product scans;
- confidential supplier drawings/quotes;
- proprietary label artwork unless the user explicitly approves public release.

Use environment variables, GitHub Actions Secrets or local untracked configuration.

## 8. External engines

COLMAP, OpenMVS, Blender and CAD bindings may have different installation and licensing constraints.

Rules:
- detect capabilities explicitly;
- report version;
- fail with actionable diagnostics;
- keep CLI adapters isolated from business logic;
- do not silently download/execute unknown binaries;
- pin tested sources/versions in dependency documentation;
- preserve OpenMVS license obligations in the dependency register even though PackLab is currently personal-use software.

## 9. Testing hierarchy

Use the smallest appropriate test plus integration evidence:

1. Unit tests for pure logic.
2. Contract tests for PackScan/JSON/schema boundaries.
3. Integration tests for Python/external engine adapters.
4. UI smoke tests for PySide6/SwiftUI where feasible.
5. Golden-dataset regression tests for geometry.
6. Physical iPhone 16 tests for camera/AR behavior.
7. Physical caliper/marker tests for dimensional accuracy.
8. End-to-end tests for release gates.

Do not pretend simulator tests validate physical camera quality.

## 10. Required builder handoff fields

Before setting AUDIT-PENDING, handoff.md must contain:

- Current Task ID
- Task title
- Builder status
- Changed files
- New files
- Deleted files
- Commands/tests run
- Test results
- Manual verification
- Known limitations
- Architecture decisions/ADRs touched
- Security/privacy check
- Suggested audit focus
- Commit/revision if available

## 11. Audit consumption rule

Before modifying TASKS.md after implementation:

1. Read AUDIT.md from disk/repository.
2. Confirm Audit Task ID == Current Task ID.
3. Confirm Verdict.
4. Confirm audited revision matches the builder revision or explicitly describes the same working tree.
5. PASS -> tick exact task.
6. FAIL -> do not tick.
7. BLOCKED -> do not tick.
8. PENDING -> do not tick.

Never infer PASS from silence.

## 12. New project behavior

At repository inception:
- handoff.md says Project State = NEW.
- TASKS.md has all tasks unchecked.
- the first task is PL-0001.
- the Builder starts from PL-0001 and follows this file.
