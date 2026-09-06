# PackLab - Implementation Guide

> Companion to TASKS.md. TASKS.md answers WHAT and tracks completion. This file answers WHY, HOW, ACCEPTANCE, and AUDIT FOCUS for every task.
>
> Execution authority remains claude.md. A builder reads handoff.md first, then TASKS.md, then the matching entry here. A builder never ticks its own task.

## Product Objective

PackLab is a personal packaging digital-twin system for the Kenya project.

Primary flow:

iPhone 16 Standard -> PackLab Capture -> .packscan -> PackLab Studio -> COLMAP -> OpenMVS -> Open3D -> Scan Master -> Parametric Design Model -> OpenCascade BREP/STEP -> Label/Material/Blender -> Kenya Packaging Library

## Core Technical Principles

1. No LiDAR dependency. iPhone 16 Standard capture is image-based photogrammetry with ARKit/CoreMotion as supporting metadata.
2. Capture originals are immutable evidence.
3. Scan Mesh and Design Model are different concepts.
4. COLMAP owns SfM/sparse reconstruction; OpenMVS owns the primary dense/mesh/refine/texture chain.
5. Open3D owns mesh/point-cloud analysis and cleanup.
6. Editable geometry is parameter-driven and later expressed as OpenCascade BREP where engineering export is required.
7. Blender owns repeatable rendering/UV/material presentation, never dimensional truth.
8. Millimetres are the canonical engineering unit.
9. Every external engine is accessed through an adapter with version/capability diagnostics.
10. The GitHub repository is public; secrets and private Kenya assets remain outside Git.
11. Every task requires independent audit before TASKS.md is checked.
12. Prefer deterministic, inspectable algorithms and recorded thresholds over unexplained AI scores.

## Global Task Implementation Pattern

For every task:
1. Read handoff.md and verify the exact Current Task ID.
2. Read the TASKS.md line and this task entry.
3. Inspect dependencies and existing implementation.
4. Make the smallest complete change.
5. Add tests/fixtures/evidence.
6. Run required validation.
7. Update handoff.md to AUDIT-PENDING.
8. Independent auditor writes AUDIT.md.
9. Only PASS permits the checkbox to become [x].


---

# M00 - Governance & Architecture

## Milestone intent

Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

## Technical method

Prefer short canonical Markdown specifications and ADRs. Every rule must have one owner/source-of-truth, be testable where possible, and describe what requires an ADR instead of silent architectural drift.

## Milestone exit gate

The repository has unambiguous architecture, licensing, security, task, audit and handoff rules.


## Sprint M00-S01 - Repository governance

### PL-0001 - Create canonical repository structure specification and ownership rules.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0001; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0002 - Create project glossary covering Scan Mesh, Design Model, Digital Twin, PackScan, Label Zone, BREP, SfM and MVS.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling. Isolate the chosen Python binding behind a CAD adapter, use millimetres consistently, validate solids after booleans/lofts and keep tessellation as a derived preview. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback. Keep Label Zone geometry, artwork and package body separate. Dielines must carry real units and include a scale-verification feature.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics. Validate solid topology and round-trip units/dimensions. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0001; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0003 - Create Architecture Decision Record (ADR) process and first ADR for the monorepo.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0002; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0004 - Document supported host/device baseline: Windows Acer laptop + iPhone 16 Standard, no LiDAR assumption.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0003; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0005 - Create dependency/license register for NextLevel, COLMAP, OpenMVS, Open3D, OpenCV, PyTorch, OpenCascade bindings, Blender and PySide6.

**Why:**  Licensing must be explicit because PackLab combines permissive and copyleft/open-source components, including OpenMVS, and the repository is public. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Integrate through Swift Package Manager at a pinned tested revision/version and wrap NextLevel behind PackLab-owned camera interfaces so a future camera-layer change does not leak across the app. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan. Keep Scan Master immutable once promoted; cleanup produces derived versions and all tolerance-sensitive operations expose parameters. Isolate the chosen Python binding behind a CAD adapter, use millimetres consistently, validate solids after booleans/lofts and keep tessellation as a derived preview. Run Blender headlessly from generated scripts/data, pin or record version, avoid manual-only scene steps, and treat Blender output as visualization rather than engineering truth.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata. Validate solid topology and round-trip units/dimensions.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0004; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0006 - Define semantic versioning rules for PackLab Studio, PackLab Capture and PackScan schema.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0005; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0007 - Define source-control conventions: branches, commits, task IDs, pull-request naming and generated-file policy.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0006; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0008 - Define secrets policy so Apple credentials, signing certificates and tokens never enter Git.

**Why:**  This protects a public repository from credential leakage while keeping personal-device installation possible. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0007; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0009 - Define Definition of Done, audit gates and evidence requirements for every task.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0008; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0010 - Create project risk register with technical, licensing, capture-quality, signing and hardware risks.

**Why:**  This protects a public repository from credential leakage while keeping personal-device installation possible. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0009; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M00-S02 - AI execution protocol

### PL-0011 - Validate handoff.md -> IMPLEMENTATION_GUIDE.md -> task -> AUDIT.md -> TASKS.md workflow with a no-code dry run.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0010; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0012 - Define builder-AI responsibilities and forbidden actions.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0011; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0013 - Define independent auditor-AI responsibilities, minimum checks and PASS/FAIL criteria.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0012; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0014 - Define audit evidence format including commands, test output, inspected files and residual risks.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0013; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0015 - Define handoff update format for current task, changed files, tests, blockers and next action.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0014; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0016 - Add protocol for failed audits: reopen same task, preserve checkbox, remediate findings, re-audit.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0015; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0017 - Add protocol for blocked tasks and dependency escalation without silently skipping work.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0016; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0018 - Add protocol for architecture changes that require an ADR before implementation.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the project governable before code exists. PackLab spans iOS capture, Windows CV/CAD, external reconstruction engines and public-repository CI; without explicit contracts, AI agents can produce locally plausible but mutually incompatible work.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0017; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M01 - Monorepo & Development Foundations

## Milestone intent

Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

## Technical method

Keep the monorepo modular. Python business logic belongs in reusable core packages; PySide6 is a UI shell. Swift code is split into camera/AR/motion/storage services. External binaries are discovered through adapters, never scattered subprocess calls.

## Milestone exit gate

Fresh environments can bootstrap, diagnose capabilities, lint and run smoke tests without private assets.


## Sprint M01-S01 - Base monorepo

### PL-0019 - Create top-level folders: apps/ios-capture, apps/windows-studio, core, schemas, docs, tools, tests, assets.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0018; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0020 - Add root README with product mission, architecture diagram, quick-start and repository map.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0019; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0021 - Add Windows/macOS/Linux-safe .gitignore covering Python, Xcode, SwiftPM, Blender, COLMAP/OpenMVS outputs and local scans.

**Why:**  COLMAP is the SfM source of camera registration and sparse geometry for the primary reconstruction path. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan. Run Blender headlessly from generated scripts/data, pin or record version, avoid manual-only scene steps, and treat Blender output as visualization rather than engineering truth.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0020; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0022 - Add .editorconfig and line-ending policy to prevent Windows/macOS churn.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0021; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0023 - Define generated-artifact directories and Git LFS policy for sample images/meshes that genuinely belong in source control.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0022; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0024 - Create local environment diagnostics script that reports OS, CPU, RAM, GPU, CUDA availability, Python and external tool versions.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0023; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0025 - Create root task-runner strategy for common bootstrap, test, lint and build commands.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0024; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0026 - Establish local cache directories outside tracked source for reconstruction intermediates.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0025; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M01-S02 - Python/Windows foundation

### PL-0027 - Choose and pin a Python version after compatibility validation across PySide6/Open3D/OpenCV/PyTorch/OpenCascade binding.

**Why:**  Open3D provides geometry-analysis operations without turning the Scan Master into an opaque CAD object. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Run a focused decision spike with explicit candidates, compatibility constraints, measurable criteria and recorded evidence. Record the decision and rejected alternatives; if the choice changes architecture, add/update an ADR before production implementation. Keep Scan Master immutable once promoted; cleanup produces derived versions and all tolerance-sensitive operations expose parameters. Isolate the chosen Python binding behind a CAD adapter, use millimetres consistently, validate solids after booleans/lofts and keep tessellation as a derived preview.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Validate solid topology and round-trip units/dimensions.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0026; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0028 - Create Python package/workspace layout for PackLab core and Windows Studio.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0027; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0029 - Add dependency locking and reproducible Windows bootstrap.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0028; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0030 - Configure Ruff/formatter/type-check strategy and baseline configuration.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0029; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0031 - Configure pytest with unit/integration/slow-test markers.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0030; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0032 - Add structured logging with session/task correlation IDs.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0031; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0033 - Add application configuration system with user config, project config and environment overrides.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0032; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0034 - Add capability registry for optional engines such as CUDA, COLMAP, OpenMVS, Blender and OpenCascade.

**Why:**  COLMAP is the SfM source of camera registration and sparse geometry for the primary reconstruction path. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan. Isolate the chosen Python binding behind a CAD adapter, use millimetres consistently, validate solids after booleans/lofts and keep tessellation as a derived preview. Run Blender headlessly from generated scripts/data, pin or record version, avoid manual-only scene steps, and treat Blender output as visualization rather than engineering truth.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data. Validate solid topology and round-trip units/dimensions.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0033; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0035 - Add safe subprocess runner with cancellation, timeout, stdout/stderr streaming and exit-code capture.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0034; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M01-S03 - Swift/iOS foundation

### PL-0036 - Create SwiftUI iOS application project targeting the user's iPhone 16 and a documented minimum iOS version.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0035; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0037 - Add NextLevel through Swift Package Manager with a pinned tested version.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Integrate through Swift Package Manager at a pinned tested revision/version and wrap NextLevel behind PackLab-owned camera interfaces so a future camera-layer change does not leak across the app.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0036; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0038 - Add project modules/services for Camera, AR Tracking, Motion, Capture Quality, Storage and Transfer.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0037; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0039 - Configure Swift 6 strict concurrency and project warning policy.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0038; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0040 - Add camera/photo-library/local-network permission descriptions actually required by the product.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0039; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0041 - Add iOS logging and diagnostics export.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0040; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0042 - Create simulator-safe fallbacks so CI can build without physical camera hardware.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0041; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0043 - Add unit-test target and initial smoke test.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Create reproducible foundations on Windows and macOS so later geometry failures are not confused with environment failures.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0042; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M02 - PackScan Data Contract & Calibration

## Milestone intent

Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

## Technical method

Use a versioned ZIP container with JSON Schema, immutable originals, explicit coordinate systems, checksums and calibration provenance. Swift and Python must validate the same fixtures.

## Milestone exit gate

A PackScan created by Swift can be verified and read by Python without assumptions or undocumented fields.


## Sprint M02-S01 - PackScan schema

### PL-0044 - Specify .packscan as a versioned ZIP container with deterministic directory layout.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0043; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0045 - Define manifest.json JSON Schema including schema version, capture ID, device, mode, timestamps and checksums.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0044; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0046 - Define per-photo metadata schema: filename, orientation, focal data, exposure, ISO, white balance, dimensions and capture sequence.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0045; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0047 - Define camera-intrinsics representation including calibration matrix, reference dimensions and lens identity.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0046; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0048 - Define ARKit pose representation with coordinate-system conventions and confidence/availability markers.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use standard world tracking supported by iPhone 16 Standard; never call LiDAR-only APIs as a required path. Timestamp transforms and tracking quality so Windows can judge whether metadata is usable. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0047; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0049 - Define CoreMotion metadata representation and timestamp synchronization rules.

**Why:**  Pose/motion metadata improves guidance and diagnostics even though the final geometry is solved by photogrammetry. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use a monotonic timestamp mapping so motion samples can be associated with capture events without assuming identical framework clocks.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0048; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0050 - Define optional object-mask representation and image/mask pixel-coordinate contract.

**Why:**  Packaging scans often contain backgrounds and turntable scenery that can confuse matching; object masks reduce that contamination. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Keep masks pixel-aligned with the exact working image; version them independently and include visual overlay fixtures to catch coordinate flips/resizes.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0049; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0051 - Define calibration-marker observations and real-world unit representation in millimetres.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0050; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0052 - Define capture-mode metadata for Freehand, Guided Orbit and Turntable modes.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0051; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0053 - Define preview, thumbnail and diagnostics payloads.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0052; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0054 - Define SHA-256 integrity checks and partial/corrupt package handling.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0053; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0055 - Create schema validation fixtures: valid, old-version, future-version, corrupt and incomplete samples.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0054; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0056 - Implement Python PackScan reader/writer/validator.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0055; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0057 - Implement Swift PackScan writer compatible with the same fixtures.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0056; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0058 - Add cross-language contract tests ensuring Swift output validates in Python.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0057; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M02-S02 - Calibration system

### PL-0059 - Select marker family and IDs for PackLab calibration mat using OpenCV-supported AprilTag/ArUco dictionaries.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Run a focused decision spike with explicit candidates, compatibility constraints, measurable criteria and recorded evidence. Record the decision and rejected alternatives; if the choice changes architecture, add/update an ADR before production implementation. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0058; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0060 - Design printable A4/A3 PackLab calibration mat with precise reference distances and print-at-100% instructions.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0059; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0061 - Add printed-mat verification procedure using ruler/caliper measurements before first use.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0060; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0062 - Implement marker detection and corner refinement in OpenCV.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0061; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0063 - Implement scale estimation from known marker geometry.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0062; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0064 - Implement calibration confidence score and rejection thresholds.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0063; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0065 - Define camera-calibration procedure for iPhone main camera when higher accuracy than EXIF/intrinsics requires it.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0064; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0066 - Store calibration profile by device/lens/resolution and invalidate incompatible profiles.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0065; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0067 - Build synthetic calibration tests with known ground-truth dimensions.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0066; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0068 - Build first physical calibration benchmark and record measured error.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Establish PackScan as the stable contract between iPhone Capture and Windows Studio and establish how real-world millimetres enter the system.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0067; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M03 - iOS Capture Foundation

## Milestone intent

Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

## Technical method

Use SwiftUI for UX, NextLevel/AVFoundation for high-resolution camera control, ARKit world tracking for supporting pose metadata and CoreMotion for motion evidence. Never treat ARKit pose as a replacement for photogrammetry.

## Milestone exit gate

A real iPhone 16 can capture high-resolution, metadata-rich, resumable scan sessions safely.


## Sprint M03-S01 - Camera control

### PL-0069 - Integrate NextLevel preview into SwiftUI using a controlled UIKit bridge where required.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Integrate through Swift Package Manager at a pinned tested revision/version and wrap NextLevel behind PackLab-owned camera interfaces so a future camera-layer change does not leak across the app.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0068; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0070 - Enumerate iPhone 16 rear-camera devices and select the intended main lens deterministically.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Prefer high-resolution still capture for accepted reconstruction frames; live video frames are for preview/quality analysis. Persist focal/exposure/ISO/white-balance/orientation metadata with the accepted still.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0069; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0071 - Implement high-resolution still-photo capture for reconstruction source images.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0070; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0072 - Preserve original capture metadata without destructive resizing or social-media style processing.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0071; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0073 - Implement focus control with guided autofocus followed by optional focus lock.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0072; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0074 - Implement exposure metering and optional exposure lock for consistent image sets.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0073; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0075 - Implement white-balance stabilization/lock for texture consistency.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0074; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0076 - Capture and persist camera metadata for every accepted still.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Prefer high-resolution still capture for accepted reconstruction frames; live video frames are for preview/quality analysis. Persist focal/exposure/ISO/white-balance/orientation metadata with the accepted still.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0075; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0077 - Add camera-error recovery for interruption, permission denial and session restart.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Prefer high-resolution still capture for accepted reconstruction frames; live video frames are for preview/quality analysis. Persist focal/exposure/ISO/white-balance/orientation metadata with the accepted still.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0076; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0078 - Add thermal/storage/battery warnings before and during long captures.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0077; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M03-S02 - ARKit & motion tracking

### PL-0079 - Create ARKit world-tracking session without relying on LiDAR.

**Why:**  Pose/motion metadata improves guidance and diagnostics even though the final geometry is solved by photogrammetry. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use standard world tracking supported by iPhone 16 Standard; never call LiDAR-only APIs as a required path. Timestamp transforms and tracking quality so Windows can judge whether metadata is usable.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0078; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0080 - Record camera transform and tracking state aligned to capture timestamps.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Prefer high-resolution still capture for accepted reconstruction frames; live video frames are for preview/quality analysis. Persist focal/exposure/ISO/white-balance/orientation metadata with the accepted still.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0079; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0081 - Record CoreMotion attitude/rotation-rate data with timestamp alignment.

**Why:**  Pose/motion metadata improves guidance and diagnostics even though the final geometry is solved by photogrammetry. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use a monotonic timestamp mapping so motion samples can be associated with capture events without assuming identical framework clocks.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0080; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0082 - Define app-local coordinate frame and conversion into PackScan coordinates.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0081; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0083 - Detect AR tracking degradation and surface a user-visible warning.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0082; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0084 - Implement capture-session reset/relocalization behavior.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0083; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0085 - Create pose visualizer/debug overlay for development.

**Why:**  Pose/motion metadata improves guidance and diagnostics even though the final geometry is solved by photogrammetry. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0084; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0086 - Export pose diagnostics for Windows-side analysis.

**Why:**  Pose/motion metadata improves guidance and diagnostics even though the final geometry is solved by photogrammetry. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0085; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M03-S03 - Capture project lifecycle

### PL-0087 - Implement New Scan wizard: package name, package type, capture mode and optional notes.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0086; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0088 - Create scan-session storage with crash-safe incremental writes.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0087; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0089 - Add photo gallery for accepted frames with delete/retake controls.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0088; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0090 - Add session resume after app termination.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0089; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0091 - Add session finalization that validates minimum data before creating .packscan.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0090; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0092 - Add local scan history with preview, date, package type and export state.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0091; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0093 - Add safe deletion requiring confirmation and cleaning all associated data.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Make the iPhone 16 Standard a reliable data-acquisition instrument even though it has no LiDAR.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0092; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M04 - Guided Capture & Quality Intelligence

## Milestone intent

Prevent bad image sets before they reach expensive reconstruction.

## Technical method

Compute explainable quality metrics on live/candidate frames, guide the user through coverage bins, and trigger high-resolution stills only when quality and novelty thresholds are met. Packaging presets change guidance, not the core data contract.

## Milestone exit gate

Capture can explain missing sectors and reject/flag blur, clipping, poor framing and unsuitable reflective conditions.


## Sprint M04-S01 - Live quality metrics

### PL-0094 - Implement frame sharpness metric and calibrate thresholds for packaging capture.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0093; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0095 - Implement motion-blur warning using frame analysis plus CoreMotion.

**Why:**  Pose/motion metadata improves guidance and diagnostics even though the final geometry is solved by photogrammetry. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use a monotonic timestamp mapping so motion samples can be associated with capture events without assuming identical framework clocks.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0094; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0096 - Implement exposure/highlight clipping analysis for glossy plastic.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0095; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0097 - Implement underexposure/shadow clipping analysis.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0096; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0098 - Implement object-size/framing score so the package fills an appropriate image area.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0097; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0099 - Implement background-complexity warning for poor photogrammetry setups.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0098; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0100 - Combine metrics into deterministic per-frame ACCEPT/REJECT decision with explainable reasons.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0099; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0101 - Log quality metrics for every candidate/accepted frame for later tuning.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0100; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M04-S02 - Guided orbit capture

### PL-0102 - Define orbit-coverage model with azimuth/elevation bins around the object.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0101; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0103 - Implement visual coverage globe/rings showing captured and missing sectors.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0102; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0104 - Implement automatic still capture when pose, overlap and quality thresholds are satisfied.

**Why:**  Pose/motion metadata improves guidance and diagnostics even though the final geometry is solved by photogrammetry. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0103; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0105 - Prevent near-duplicate captures that add storage without useful parallax.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0104; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0106 - Require lower, middle and upper capture rings for standard bottle mode.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0105; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0107 - Add top/neck detail pass for closures and shoulders.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0106; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0108 - Add bottom/base detail pass where physically possible.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0107; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0109 - Add completion score and explicit missing-area guidance.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0108; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0110 - Add manual-capture override while retaining quality warnings.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0109; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M04-S03 - Packaging-specific modes

### PL-0111 - Implement Matte/HDPE capture preset.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0110; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0112 - Implement Glossy/PET preset emphasizing highlight control and denser coverage.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0111; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0113 - Implement Transparent packaging warning mode with instructions for temporary scanning treatment/background preparation.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0112; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0114 - Implement Asymmetric/Jerrycan mode with stronger front/back/handle coverage requirements.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0113; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0115 - Implement Closure/Cap macro-detail mode.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0114; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0116 - Implement Turntable mode with angle-indexed capture and object/background masking assumptions.

**Why:**  Packaging scans often contain backgrounds and turntable scenery that can confuse matching; object masks reduce that contamination. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep masks pixel-aligned with the exact working image; version them independently and include visual overlay fixtures to catch coordinate flips/resizes.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0115; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0117 - Add capture protocol screen explaining lighting, matte background, reflections and object preparation per preset.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0116; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0118 - Add scan-suitability preflight before capture starts.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Prevent bad image sets before they reach expensive reconstruction.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0117; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M05 - Transfer & Ingest

## Milestone intent

Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

## Technical method

Support both simple file export and authenticated local-LAN transfer. Validate checksums before ingest and preserve an immutable raw copy.

## Milestone exit gate

Interrupted or corrupt transfers fail safely; valid captures import reproducibly.


## Sprint M05-S01 - Export from iPhone

### PL-0119 - Implement .packscan package finalization with checksums and atomic rename.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0118; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0120 - Implement iOS share-sheet export to Files/iCloud/other installed destinations.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0119; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0121 - Implement local-network transfer protocol from Capture to PackLab Studio.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0120; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0122 - Add QR/pairing-code workflow so the iPhone connects to the correct Windows Studio instance.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0121; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0123 - Encrypt/authenticate local transfer sufficiently to prevent accidental cross-device ingestion.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0122; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0124 - Support resumable transfer for large scan packages.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0123; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0125 - Verify checksum after transfer before marking export complete.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0124; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0126 - Add transfer progress, cancel and retry UI.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0125; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M05-S02 - Windows ingest

### PL-0127 - Implement drag/drop and file-picker import for .packscan.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0126; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0128 - Implement network receiver for paired iPhone transfers.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0127; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0129 - Validate schema version and checksums before extraction.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0128; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0130 - Quarantine corrupt/unsupported scans instead of partially importing them.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0129; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0131 - Create immutable raw-ingest copy so original capture evidence is never silently modified.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0130; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0132 - Generate import report summarizing images, metadata, calibration and warnings.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0131; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0133 - Deduplicate imports by capture ID/checksum.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0132; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0134 - Add ingest tests for interrupted transfer, corrupt ZIP, missing photo and bad manifest.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Move large scan packages from iPhone to Windows without corruption, duplication or accidental mutation.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0133; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M06 - PackLab Studio Foundation

## Milestone intent

Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

## Technical method

PySide6 owns desktop UX while reusable Python services own domain logic. Project folders distinguish raw, working, derived and exported data. Long jobs are cancellable and observable.

## Milestone exit gate

Studio can open/import projects, recover state, run jobs and visualize large 3D assets without tying domain logic to widgets.


## Sprint M06-S01 - PySide6 shell

### PL-0135 - Create PackLab Studio PySide6 application shell.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0134; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0136 - Implement main navigation: Library, Capture Inbox, Reconstruction, Editor and Settings.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0135; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0137 - Create dockable/logical workspace layout suitable for 3D/CAD work.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0136; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0138 - Implement persistent window/workspace preferences.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0137; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0139 - Add global job/activity panel for long-running reconstruction work.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0138; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0140 - Add cancellation and safe shutdown behavior for active subprocesses.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0139; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0141 - Add crash report/log bundle creation.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0140; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0142 - Add application update/version information screen without requiring an online service.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0141; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M06-S02 - Project lifecycle

### PL-0143 - Define PackLab project directory layout separating raw, working, derived and export data.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0142; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0144 - Implement New/Open/Close project lifecycle.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0143; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0145 - Implement project metadata and revision identifiers.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0144; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0146 - Implement autosave for editable project state.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0145; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0147 - Implement non-destructive operation history for user edits.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0146; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0148 - Implement project recovery after interrupted processing.

**Why:**  Physical package samples and scan sessions can be expensive or impossible to recreate, so recoverability is a product requirement. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0147; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0149 - Add derived-artifact invalidation when upstream inputs change.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0148; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0150 - Add project portability check that identifies missing external assets.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0149; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M06-S03 - 3D viewport

### PL-0151 - Select and document the PySide6-compatible 3D viewport approach after a focused performance spike.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Run a focused decision spike with explicit candidates, compatibility constraints, measurable criteria and recorded evidence. Record the decision and rejected alternatives; if the choice changes architecture, add/update an ADR before production implementation.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0150; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0152 - Implement mesh/point-cloud loading and camera orbit/pan/zoom.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0151; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0153 - Implement world grid, axes and millimetre scale cues.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0152; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0154 - Implement object selection and visibility toggles for Scan Mesh, Design Model, cap, label and reference geometry.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback. Keep Label Zone geometry, artwork and package body separate. Dielines must carry real units and include a scale-verification feature.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0153; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0155 - Implement wireframe/normals/point-cloud debug modes.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0154; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0156 - Implement screenshot/export preview for audit evidence.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0155; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0157 - Add large-mesh performance benchmark and viewport LOD strategy.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Provide a stable desktop workbench for long-running CV/CAD jobs and non-destructive project editing.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0156; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M07 - Photogrammetry Reconstruction

## Milestone intent

Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

## Technical method

COLMAP performs SfM, camera registration and sparse reconstruction. OpenMVS consumes that result for dense cloud, mesh, refinement and texturing. Use isolated CLI adapters, pinned tested versions, complete logs and preserved intermediates.

## Milestone exit gate

One action can reproducibly produce a textured scan or an actionable stage-specific failure report.


## Sprint M07-S01 - Engine installation and adapters

### PL-0158 - Define tested COLMAP version, installation source and license record.

**Why:**  Licensing must be explicit because PackLab combines permissive and copyleft/open-source components, including OpenMVS, and the repository is public. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0157; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0159 - Define tested OpenMVS version, Windows build/binary source and AGPL license record.

**Why:**  Licensing must be explicit because PackLab combines permissive and copyleft/open-source components, including OpenMVS, and the repository is public. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0158; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0160 - Implement COLMAP capability probe and version parser.

**Why:**  COLMAP is the SfM source of camera registration and sparse geometry for the primary reconstruction path. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0159; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0161 - Implement OpenMVS capability probe and version parser.

**Why:**  OpenMVS fills the dense-reconstruction half of the pipeline and is where point density, surface reconstruction, refinement and texturing are produced. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0160; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0162 - Implement engine executable discovery/configuration with explicit paths and diagnostics.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0161; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0163 - Create normalized reconstruction job model independent of specific engine command syntax.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0162; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0164 - Implement per-stage stdout/stderr capture and machine-readable stage result records.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0163; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0165 - Add reconstruction workspace isolation so retries cannot corrupt the source scan.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0164; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M07-S02 - COLMAP SfM

### PL-0166 - Implement photo preprocessing into a COLMAP-safe working set while preserving originals.

**Why:**  COLMAP is the SfM source of camera registration and sparse geometry for the primary reconstruction path. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0165; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0167 - Import/use known camera intrinsics when valid and allow COLMAP refinement under controlled rules.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0166; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0168 - Implement feature-extraction configuration optimized first for packaged consumer goods.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0167; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0169 - Implement matcher selection for ordered orbit datasets.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0168; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0170 - Implement sparse mapper stage and capture registered-image statistics.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0169; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0171 - Detect failed/fragmented sparse models and produce actionable diagnostics.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0170; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0172 - Export sparse model/cameras in formats needed by OpenMVS and debugging.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0171; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0173 - Build a tunable reconstruction preset system rather than hardcoding CLI flags.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0172; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M07-S03 - OpenMVS dense reconstruction

### PL-0174 - Implement COLMAP-to-OpenMVS scene conversion.

**Why:**  COLMAP is the SfM source of camera registration and sparse geometry for the primary reconstruction path. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0173; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0175 - Implement OpenMVS dense point-cloud stage.

**Why:**  OpenMVS fills the dense-reconstruction half of the pipeline and is where point density, surface reconstruction, refinement and texturing are produced. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0174; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0176 - Implement OpenMVS mesh-reconstruction stage.

**Why:**  OpenMVS fills the dense-reconstruction half of the pipeline and is where point density, surface reconstruction, refinement and texturing are produced. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0175; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0177 - Implement OpenMVS mesh-refinement stage.

**Why:**  OpenMVS fills the dense-reconstruction half of the pipeline and is where point density, surface reconstruction, refinement and texturing are produced. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0176; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0178 - Implement OpenMVS texture stage.

**Why:**  OpenMVS fills the dense-reconstruction half of the pipeline and is where point density, surface reconstruction, refinement and texturing are produced. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0177; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0179 - Preserve all stage outputs and logs for reproducibility.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0178; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0180 - Add CPU/GPU-aware presets and memory-safety limits.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0179; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0181 - Add one-click Reconstruct Scan orchestration across COLMAP and OpenMVS.

**Why:**  COLMAP is the SfM source of camera registration and sparse geometry for the primary reconstruction path. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0180; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0182 - Add reconstruction cancellation that leaves the project recoverable.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0181; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0183 - Convert final textured mesh to PackLab-supported preview/export format without losing the master source.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Build the primary photogrammetry chain that converts iPhone photographs into a textured reference scan.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0182; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M08 - Segmentation, Masks & Reconstruction QA

## Milestone intent

Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

## Technical method

Use replaceable PyTorch segmentation behind an interface, version masks separately, feed compatible masks into reconstruction, and compute transparent QA metrics rather than a single unexplained score.

## Milestone exit gate

Poor scans are blocked from parametric fitting with reasons and targeted recapture advice.


## Sprint M08-S01 - Object segmentation

### PL-0184 - Define segmentation-backend interface so the model can be replaced without rewriting the pipeline.

**Why:**  Packaging scans often contain backgrounds and turntable scenery that can confuse matching; object masks reduce that contamination. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0183; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0185 - Benchmark candidate local segmentation model(s) against bottle, jerrycan, cap and transparent/glossy examples.

**Why:**  Packaging scans often contain backgrounds and turntable scenery that can confuse matching; object masks reduce that contamination. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Run a focused decision spike with explicit candidates, compatibility constraints, measurable criteria and recorded evidence. Record the decision and rejected alternatives; if the choice changes architecture, add/update an ADR before production implementation. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0184; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0186 - Implement selected PyTorch segmentation backend.

**Why:**  Packaging scans often contain backgrounds and turntable scenery that can confuse matching; object masks reduce that contamination. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0185; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0187 - Implement mask post-processing: hole filling, edge cleanup and small-component removal.

**Why:**  Packaging scans often contain backgrounds and turntable scenery that can confuse matching; object masks reduce that contamination. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep masks pixel-aligned with the exact working image; version them independently and include visual overlay fixtures to catch coordinate flips/resizes.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0186; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0188 - Add manual mask-correction UI for difficult frames.

**Why:**  Packaging scans often contain backgrounds and turntable scenery that can confuse matching; object masks reduce that contamination. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep masks pixel-aligned with the exact working image; version them independently and include visual overlay fixtures to catch coordinate flips/resizes.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0187; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0189 - Version masks separately from immutable source photos.

**Why:**  Packaging scans often contain backgrounds and turntable scenery that can confuse matching; object masks reduce that contamination. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Keep masks pixel-aligned with the exact working image; version them independently and include visual overlay fixtures to catch coordinate flips/resizes.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0188; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0190 - Feed masks into COLMAP/OpenMVS where supported and validate coordinate conventions.

**Why:**  COLMAP is the SfM source of camera registration and sparse geometry for the primary reconstruction path. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan. Keep masks pixel-aligned with the exact working image; version them independently and include visual overlay fixtures to catch coordinate flips/resizes.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0189; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0191 - Add mask-quality overlays and contact-sheet review.

**Why:**  Packaging scans often contain backgrounds and turntable scenery that can confuse matching; object masks reduce that contamination. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep masks pixel-aligned with the exact working image; version them independently and include visual overlay fixtures to catch coordinate flips/resizes.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0190; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M08-S02 - Photo/reconstruction QA

### PL-0192 - Build pre-reconstruction QA report using sharpness, exposure, coverage and metadata consistency.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0191; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0193 - Detect duplicate/near-duplicate photos on Windows as a second safety layer.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0192; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0194 - Detect inconsistent focal/lens usage and warn before reconstruction.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0193; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0195 - Calculate registered-photo ratio after COLMAP.

**Why:**  COLMAP is the SfM source of camera registration and sparse geometry for the primary reconstruction path. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0194; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0196 - Calculate sparse-cloud connectivity/fragmentation indicators.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0195; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0197 - Calculate dense-cloud density and surface-coverage indicators.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0196; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0198 - Detect obvious reconstruction artifacts and floating components.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0197; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0199 - Produce overall reconstruction confidence with component scores, not a black-box number.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0198; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0200 - Gate downstream parametric fitting when scan quality is below minimum acceptance thresholds.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0199; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0201 - Suggest targeted recapture sectors instead of demanding a complete rescan when possible.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Focus reconstruction on the package and quantify whether the scan is trustworthy enough for fitting.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0200; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M09 - Scale, Calibration & Measurement

## Milestone intent

Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

## Technical method

Fuse marker observations with reconstruction, track scale uncertainty/provenance, normalize axes non-destructively and provide measurement tools with explicit limitations.

## Milestone exit gate

Ground-truth benchmark dimensions fall inside documented tolerances and every measurement identifies its source.


## Sprint M09-S01 - Coordinate and scale normalization

### PL-0202 - Detect calibration markers in source imagery and associate observations with reconstructed cameras.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0201; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0203 - Estimate global scale from marker geometry and reject inconsistent observations.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0202; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0204 - Establish canonical PackLab axes: Z up, front direction, millimetres.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0203; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0205 - Implement object ground-plane/base detection with user override.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0204; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0206 - Implement automatic upright alignment with manual correction.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0205; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0207 - Implement front-direction selection and persist it as project metadata.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0206; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0208 - Apply scale/alignment as non-destructive transform before baking a normalized scan.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0207; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0209 - Record scale provenance and uncertainty.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0208; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M09-S02 - Measurement tools

### PL-0210 - Implement bounding dimensions: height, width and depth.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0209; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0211 - Implement two-point distance measurement with snapping.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0210; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0212 - Implement diameter/radius measurement from selected cross-sections.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0211; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0213 - Implement horizontal cross-section extraction at arbitrary Z.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0212; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0214 - Implement vertical profile/silhouette extraction.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0213; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0215 - Implement neck/finish candidate measurement.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0214; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0216 - Implement capacity-estimation groundwork using watertight interior assumptions, clearly separating estimate from certified volume.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0215; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0217 - Display measurement uncertainty/confidence where known.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0216; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0218 - Export measurement report with units and provenance.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0217; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M09-S03 - Accuracy benchmarks

### PL-0219 - Define physical benchmark set with caliper-measured ground truth.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0218; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0220 - Measure dimension error across at least matte bottle, glossy bottle and jerrycan.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0219; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0221 - Establish V1 acceptance thresholds for overall dimensions and key features.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0220; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0222 - Add repeat-scan reproducibility test for the same object.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0221; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0223 - Add calibration-mat print-scale sensitivity test.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0222; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0224 - Document conditions under which PackLab measurements must not be used for mold manufacturing.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Turn arbitrary reconstruction coordinates into a real-size, upright, front-oriented millimetre model.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0223; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M10 - Mesh Processing & Scan Master

## Milestone intent

Create a clean Scan Master while preserving the raw reconstruction as evidence.

## Technical method

Use Open3D for component filtering, normals, holes, proxy decimation, registration and deviation analysis. Every destructive-looking operation creates a derived version.

## Milestone exit gate

A promoted Scan Master is reproducible, traceable and suitable as the fitting reference.


## Sprint M10-S01 - Open3D processing

### PL-0225 - Integrate Open3D as the primary point-cloud/mesh analysis utility layer.

**Why:**  Open3D provides geometry-analysis operations without turning the Scan Master into an opaque CAD object. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep Scan Master immutable once promoted; cleanup produces derived versions and all tolerance-sensitive operations expose parameters.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0224; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0226 - Remove isolated floating components with configurable safeguards.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0225; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0227 - Implement normal estimation/orientation repair.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0226; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0228 - Implement conservative smoothing that preserves packaging edges.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0227; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0229 - Implement hole detection and report hole size/location before any repair.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0228; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0230 - Implement optional hole filling with non-destructive before/after versions.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0229; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0231 - Implement decimation for viewport/proxy meshes while preserving the Scan Master.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0230; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0232 - Compute geometric statistics needed by later fitting stages.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0231; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0233 - Create Scan Master asset with provenance pointing back to reconstruction settings.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0232; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M10-S02 - Scan comparison and revisions

### PL-0234 - Implement point-cloud/mesh registration for comparing repeat scans.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0233; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0235 - Implement distance heatmap between scan and fitted Design Model.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0234; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0236 - Implement cross-section comparison overlay.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0235; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0237 - Record reconstruction versions and allow switching between them.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0236; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0238 - Add Promote to Scan Master action with audit metadata.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0237; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0239 - Prevent downstream Design Model from silently changing when reconstruction is rerun.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0238; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0240 - Add Scan Master export as PLY/OBJ/GLB plus original texture assets.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create a clean Scan Master while preserving the raw reconstruction as evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0239; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M11 - Parametric Geometry Engine V1

## Milestone intent

Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

## Technical method

Represent profiles, cross-sections, zones and dimensions as a versioned parameter graph. Generate preview meshes from parameters and compare them quantitatively to the Scan Master.

## Milestone exit gate

A bottle/jar can be edited by dimensions and control points while deviation to the scan remains measurable.


## Sprint M11-S01 - Common parametric kernel

### PL-0241 - Define Design Model parameter graph separate from triangle-mesh data.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0240; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0242 - Define feature IDs and stable references for body, base, shoulder, neck, finish and cap.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0241; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0243 - Implement spline/profile primitives with millimetre coordinates.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0242; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0244 - Implement editable cross-section primitive with symmetry options.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0243; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0245 - Implement loft/revolve abstraction independent of final CAD backend.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0244; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0246 - Implement parameter validation and impossible-geometry rejection.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0245; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0247 - Implement undo/redo command model for parametric edits.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0246; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0248 - Serialize Design Model parameters in a versioned human-readable project format.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0247; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0249 - Generate tessellated preview mesh from parameters for interactive viewport use.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0248; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M11-S02 - Bottle/jar fitting

### PL-0250 - Detect rotational/symmetry characteristics and choose bottle fitting strategy.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0249; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0251 - Extract robust vertical body profile from normalized Scan Master.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0250; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0252 - Fit smoothed profile while preserving shoulder/base transitions.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0251; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0253 - Detect body, shoulder, neck and base zones with editable boundaries.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0252; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0254 - Generate revolved Design Model for axisymmetric bottle/jar.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0253; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0255 - Fit non-circular but symmetric body using stacked cross-sections and lofting.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0254; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0256 - Add front/back and left/right symmetry constraints with user toggle.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0255; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0257 - Calculate scan-to-design deviation and expose problem regions.

**Why:**  Pose/motion metadata improves guidance and diagnostics even though the final geometry is solved by photogrammetry. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0256; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0258 - Allow user to edit height/width/depth while maintaining parameter relationships.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0257; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0259 - Allow direct profile/cross-section control-point editing.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0258; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0260 - Save fitting preset and parameters independently of the raw scan.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0259; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M11-S03 - Caps and closures V1

### PL-0261 - Separate cap/closure from body when scan evidence allows.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0260; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0262 - Fit basic cylindrical screw-cap exterior.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0261; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0263 - Fit flip-top/simple closure exterior as an editable component.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0262; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0264 - Define neck/closure mating reference planes and axes.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0263; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0265 - Add cap visibility/replacement workflow.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0264; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0266 - Add closure dimensions to measurement report.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0265; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0267 - Validate bottle/cap assembly transforms on export.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Convert scan geometry into editable packaging parameters rather than leaving the user with millions of triangles.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0266; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M12 - Advanced Packaging Geometry

## Milestone intent

Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

## Technical method

Combine stacked sections, constrained handles/voids, reusable assemblies and limited freeform cages. Keep reusable triggers/pumps separate from bottle geometry.

## Milestone exit gate

Representative jerrycan, trigger assembly and tube/flexible examples are editable as structured components.


## Sprint M12-S01 - Jerrycans and handles

### PL-0268 - Implement asymmetric/symmetric jerrycan body fitting from stacked cross-sections.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0267; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0269 - Detect handle-void candidate and isolate it from body silhouette.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0268; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0270 - Model handle opening as editable constrained feature rather than baked scan triangles.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0269; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0271 - Implement local grip/indent feature representation.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0270; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0272 - Add cage/freeform deformation layer for details not captured by simple parameters.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0271; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0273 - Constrain cage edits to preserve key dimensions and symmetry when enabled.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0272; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0274 - Quantify Design Model deviation around handles/indentations.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0273; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0275 - Validate 2 L/5 L style jerrycan benchmark objects.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0274; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M12-S02 - Trigger/pump assemblies

### PL-0276 - Define assembly graph for body, closure, trigger/pump and dip tube.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0275; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0277 - Support importing a reusable trigger/pump library component.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0276; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0278 - Align library closure component to detected neck reference.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0277; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0279 - Model dip tube as parameterized length/diameter path.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0278; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0280 - Add assembly collision/basic interference diagnostics.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0279; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0281 - Allow swapping trigger/pump variants without modifying bottle geometry.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0280; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0282 - Export assembly hierarchy to formats that support components.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0281; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M12-S03 - Tubes, sachets and flexible packs

### PL-0283 - Define tube parametric family: body, shoulder, neck, cap and crimp.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0282; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0284 - Implement tube fitting from scan/reference dimensions.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0283; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0285 - Define sachet/pouch simplified Design Model focused on artwork and overall dimensions rather than mold-grade surfaces.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0284; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0286 - Implement front/back flexible-pack surface and seal-zone representation.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0285; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0287 - Explicitly mark flexible-pack geometry as visualization/design geometry with appropriate accuracy limitations.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0286; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0288 - Add package-family selection and conversion safeguards.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Extend the editable model beyond simple rotational bottles to the package families used by the Kenya project.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0287; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M13 - CAD/BREP & Engineering Export

## Milestone intent

Produce actual engineering geometry and interoperable exports from the Design Model.

## Technical method

Use an isolated OpenCascade binding for BREP creation/validation, export STEP in millimetres, round-trip test dimensions, and derive orthographic drawings from the same model.

## Milestone exit gate

Exported STEP reopens with consistent dimensions and drawings numerically agree with the Design Model.


## Sprint M13-S01 - OpenCascade integration

### PL-0289 - Benchmark/select supported Python OpenCascade binding for Windows packaging.

**Why:**  STEP/CAD interoperability requires valid solid geometry rather than only render meshes. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Run a focused decision spike with explicit candidates, compatibility constraints, measurable criteria and recorded evidence. Record the decision and rejected alternatives; if the choice changes architecture, add/update an ADR before production implementation. Isolate the chosen Python binding behind a CAD adapter, use millimetres consistently, validate solids after booleans/lofts and keep tessellation as a derived preview.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Validate solid topology and round-trip units/dimensions.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0288; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0290 - Implement CAD capability adapter and version diagnostics.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0289; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0291 - Convert profile/revolve Design Models into OpenCascade BREP solids.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Isolate the chosen Python binding behind a CAD adapter, use millimetres consistently, validate solids after booleans/lofts and keep tessellation as a derived preview. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation. Validate solid topology and round-trip units/dimensions. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0290; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0292 - Convert lofted cross-section Design Models into BREP solids.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Isolate the chosen Python binding behind a CAD adapter, use millimetres consistently, validate solids after booleans/lofts and keep tessellation as a derived preview. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation. Validate solid topology and round-trip units/dimensions. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0291; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0293 - Implement boolean feature support needed for handle openings and simple indentations.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0292; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0294 - Validate solid topology and report non-manifold/invalid BREP failures.

**Why:**  STEP/CAD interoperability requires valid solid geometry rather than only render meshes. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Isolate the chosen Python binding behind a CAD adapter, use millimetres consistently, validate solids after booleans/lofts and keep tessellation as a derived preview.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Validate solid topology and round-trip units/dimensions.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0293; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0295 - Preserve named feature references where practical across regeneration.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0294; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0296 - Tessellate BREP back to preview mesh with controlled tolerance.

**Why:**  STEP/CAD interoperability requires valid solid geometry rather than only render meshes. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Isolate the chosen Python binding behind a CAD adapter, use millimetres consistently, validate solids after booleans/lofts and keep tessellation as a derived preview.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Validate solid topology and round-trip units/dimensions.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0295; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M13-S02 - STEP/STL/mesh export

### PL-0297 - Export Design Model/assembly to STEP with millimetre units.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. After export, reopen the STEP file with the CAD layer and compare bounding/key dimensions to the source Design Model within defined tolerances. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Round-trip dimensional validation passes. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Validate solid topology and round-trip units/dimensions. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0296; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0298 - Export printable STL with explicit unit handling and mesh-quality options.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0297; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0299 - Export OBJ and GLB from Design Model with part naming.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0298; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0300 - Add export manifest recording source project, revision, scale and software versions.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0299; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0301 - Add round-trip validation that reopens exported STEP and rechecks bounding dimensions.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. After export, reopen the STEP file with the CAD layer and compare bounding/key dimensions to the source Design Model within defined tolerances.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable. Round-trip dimensional validation passes.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Validate solid topology and round-trip units/dimensions.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0300; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0302 - Add export UI with clear distinction between Scan Mesh and editable Design Model.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0301; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M13-S03 - Technical drawings

### PL-0303 - Generate front/side/top orthographic views from Design Model.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0302; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0304 - Generate section views at user-selected heights/planes.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0303; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0305 - Add dimension annotations for overall H/W/D, neck and selected features.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0304; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0306 - Add title block with package ID, revision, units and disclaimer.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0305; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0307 - Export drawing to SVG and DXF.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0306; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0308 - Export PDF drawing if a stable PDF path is available without compromising vector source.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0307; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0309 - Validate drawing dimensions against Design Model numerical values.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Produce actual engineering geometry and interoperable exports from the Design Model.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable. Repository scan/review finds no committed credential or private signing material. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0308; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M14 - Labels, Materials & Rendering

## Milestone intent

Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

## Technical method

Label Zones are separate entities with real-size dielines. PBR material assignments are component metadata. Blender runs headlessly for deterministic UV/material/render tasks.

## Milestone exit gate

One geometry can accept artwork/material variants and render standard views without altering its engineering dimensions.


## Sprint M14-S01 - Label zones and dielines

### PL-0310 - Define Label Zone entity independent of artwork image.

**Why:**  Reusing one package geometry across multiple POVU SKUs depends on keeping artwork independent from the physical body. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Keep Label Zone geometry, artwork and package body separate. Dielines must carry real units and include a scale-verification feature.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0309; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0311 - Implement manual front/back/wrap Label Zone placement on Design Model.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback. Keep Label Zone geometry, artwork and package body separate. Dielines must carry real units and include a scale-verification feature.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0310; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0312 - Implement curvature/slope analysis to suggest label-safe regions.

**Why:**  Reusing one package geometry across multiple POVU SKUs depends on keeping artwork independent from the physical body. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep Label Zone geometry, artwork and package body separate. Dielines must carry real units and include a scale-verification feature.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0311; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0313 - Generate 2D label boundary/dieline in millimetres.

**Why:**  Reusing one package geometry across multiple POVU SKUs depends on keeping artwork independent from the physical body. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep Label Zone geometry, artwork and package body separate. Dielines must carry real units and include a scale-verification feature.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0312; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0314 - Add safe-margin/bleed metadata.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0313; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0315 - Import SVG/PNG artwork and map it non-destructively to a Label Zone.

**Why:**  Reusing one package geometry across multiple POVU SKUs depends on keeping artwork independent from the physical body. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep Label Zone geometry, artwork and package body separate. Dielines must carry real units and include a scale-verification feature.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0314; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0316 - Support front/back artwork variants and wrap labels.

**Why:**  Reusing one package geometry across multiple POVU SKUs depends on keeping artwork independent from the physical body. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep Label Zone geometry, artwork and package body separate. Dielines must carry real units and include a scale-verification feature.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0315; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0317 - Export label-dieline SVG with scale-verification marks.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep Label Zone geometry, artwork and package body separate. Dielines must carry real units and include a scale-verification feature.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0316; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M14-S02 - Material system

### PL-0318 - Define material-library schema for HDPE, PET, PP and other packaging materials.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0317; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0319 - Separate geometry material from product liquid/content appearance.

**Why:**  Presentation-quality mockups need a dedicated visual layer that does not become the dimensional source of truth. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0318; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0320 - Implement PBR parameters: base color, roughness, transmission/opacity, IOR and normal detail where supported.

**Why:**  Presentation-quality mockups need a dedicated visual layer that does not become the dimensional source of truth. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0319; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0321 - Create starter materials: natural HDPE, white HDPE, clear PET, colored PET, PP cap.

**Why:**  Presentation-quality mockups need a dedicated visual layer that does not become the dimensional source of truth. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0320; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0322 - Add PCR metadata and visual variants without implying certified material properties.

**Why:**  Presentation-quality mockups need a dedicated visual layer that does not become the dimensional source of truth. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0321; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0323 - Persist material assignments per component.

**Why:**  Presentation-quality mockups need a dedicated visual layer that does not become the dimensional source of truth. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0322; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M14-S03 - Blender rendering

### PL-0324 - Integrate Blender headless executable discovery and version probe.

**Why:**  Presentation-quality mockups need a dedicated visual layer that does not become the dimensional source of truth. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Run Blender headlessly from generated scripts/data, pin or record version, avoid manual-only scene steps, and treat Blender output as visualization rather than engineering truth.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0323; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0325 - Create deterministic Blender scene-generation script from PackLab project data.

**Why:**  Presentation-quality mockups need a dedicated visual layer that does not become the dimensional source of truth. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Run Blender headlessly from generated scripts/data, pin or record version, avoid manual-only scene steps, and treat Blender output as visualization rather than engineering truth.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0324; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0326 - Import Design Model, materials and artwork into render scene.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0325; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0327 - Create standard studio-lighting/camera presets for packaging mockups.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0326; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0328 - Render transparent-background product image.

**Why:**  Presentation-quality mockups need a dedicated visual layer that does not become the dimensional source of truth. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0327; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0329 - Render front/three-quarter/back standard views.

**Why:**  Presentation-quality mockups need a dedicated visual layer that does not become the dimensional source of truth. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0328; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0330 - Export GLB with materials/textures for lightweight viewing.

**Why:**  Presentation-quality mockups need a dedicated visual layer that does not become the dimensional source of truth. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0329; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0331 - Record render settings and Blender version for reproducibility.

**Why:**  Presentation-quality mockups need a dedicated visual layer that does not become the dimensional source of truth. Turn engineering geometry into usable packaging artwork and visual mockups without mixing visual appearance with dimensional truth.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Run Blender headlessly from generated scripts/data, pin or record version, avoid manual-only scene steps, and treat Blender output as visualization rather than engineering truth. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0330; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M15 - Kenya Packaging Library

## Milestone intent

Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

## Technical method

Use stable asset IDs, provenance-aware metadata and links among scans, Scan Masters, Design Model revisions, components and multiple POVU SKUs.

## Milestone exit gate

A user can find an asset, inspect dimensions/revisions and create a new SKU by reusing existing geometry.


## Sprint M15-S01 - Digital-twin metadata

### PL-0332 - Define Packaging Asset schema with internal ID, family, nominal volume, supplier, material, weight and neck/closure metadata.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0331; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0333 - Separate factual supplier fields from PackLab-estimated fields and label provenance.

**Why:**  Reusing one package geometry across multiple POVU SKUs depends on keeping artwork independent from the physical body. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep Label Zone geometry, artwork and package body separate. Dielines must carry real units and include a scale-verification feature.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0332; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0334 - Link one Packaging Asset to raw Scan(s), one promoted Scan Master and multiple Design Model revisions.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0333; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0335 - Link compatible caps/triggers/pumps as reusable components.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0334; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0336 - Link multiple POVU artworks/SKUs to one physical geometry.

**Why:**  Reusing one package geometry across multiple POVU SKUs depends on keeping artwork independent from the physical body. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0335; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0337 - Add attachments for supplier drawings, quotations and notes without forcing them into Git.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0336; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0338 - Add audit trail for asset-metadata edits.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0337; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M15-S02 - Library UI

### PL-0339 - Implement grid/list library browser with thumbnail.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0338; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0340 - Implement search by ID/name/supplier/package family.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0339; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0341 - Implement filters for volume, material, closure and status.

**Why:**  Presentation-quality mockups need a dedicated visual layer that does not become the dimensional source of truth. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0340; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0342 - Implement asset-detail page with 3D preview, dimensions, revisions and linked artwork.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0341; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0343 - Implement duplicate/variant relationship display.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0342; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0344 - Add Create new SKU from existing geometry workflow.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0343; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0345 - Add library backup/export and restore validation.

**Why:**  Physical package samples and scan sessions can be expensive or impossible to recreate, so recoverability is a product requirement. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0344; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0346 - Add thumbnails/contact-sheet export for supplier discussions.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Create the Kenya factory's searchable digital packaging archive rather than a folder of unrelated meshes.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0345; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M16 - CI/CD, Signing & Distribution

## Milestone intent

Make builds repeatable from the public GitHub repository with a free-first strategy.

## Technical method

Windows Actions build/test Studio; macOS Actions build/test Capture. Keep simulator builds secret-free and make device signing optional, secret-backed and clearly distinguished from unsigned/free-sideload artifacts.

## Milestone exit gate

GitHub produces auditable Windows and iOS artifacts without committing Apple or GitHub secrets.


## Sprint M16-S01 - GitHub Actions Windows

### PL-0347 - Create Windows CI workflow for Python lint/type/unit tests.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0346; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0348 - Add cached dependency installation without caching secrets or mutable reconstruction outputs.

**Why:**  This protects a public repository from credential leakage while keeping personal-device installation possible. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0347; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0349 - Add Windows PackLab Studio build job.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0348; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0350 - Produce versioned PackLabStudio.exe/installer artifact.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0349; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0351 - Add smoke test against packaged Windows application.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0350; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0352 - Add artifact-retention policy suitable for a public repository.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0351; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0353 - Ensure CI can run without proprietary sample scans.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0352; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M16-S02 - GitHub Actions macOS/iOS

### PL-0354 - Create macOS GitHub Actions workflow for Swift build and unit tests.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0353; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0355 - Resolve/cache Swift Package Manager dependencies including NextLevel.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Integrate through Swift Package Manager at a pinned tested revision/version and wrap NextLevel behind PackLab-owned camera interfaces so a future camera-layer change does not leak across the app. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0354; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0356 - Build simulator target on every relevant change with no signing secrets.

**Why:**  This protects a public repository from credential leakage while keeping personal-device installation possible. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0355; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0357 - Create device archive job for PackLab Capture.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0356; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0358 - Implement secret-safe optional code-signing path for a signed IPA when credentials/provisioning are available.

**Why:**  This protects a public repository from credential leakage while keeping personal-device installation possible. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0357; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0359 - Implement free-first fallback artifact path when CI signing is unavailable, documenting Windows-side sideload/sign route.

**Why:**  This protects a public repository from credential leakage while keeping personal-device installation possible. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0358; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0360 - Ensure no Apple certificate/profile/private key is ever committed to the public repository.

**Why:**  This protects a public repository from credential leakage while keeping personal-device installation possible. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0359; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0361 - Publish build artifacts with clear signed/unsigned provenance.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0360; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0362 - Document exact iPhone 16 installation/reinstallation procedure.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0361; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M16-S03 - Releases

### PL-0363 - Define coordinated release numbering across Studio, Capture and PackScan schema.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0362; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0364 - Add release manifest with dependency versions and schema compatibility.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0363; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0365 - Add changelog-generation rules tied to task IDs.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0364; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0366 - Create release checklist requiring both Windows and iOS audit passes.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0365; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0367 - Add rollback instructions for incompatible Capture/Studio versions.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0366; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0368 - Create first internal V0.1 release only after acceptance gates in M17 are satisfied.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Make builds repeatable from the public GitHub repository with a free-first strategy.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0367; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M17 - Validation, Benchmarking & Reliability

## Milestone intent

Replace subjective 'looks good' claims with measured regression and failure evidence.

## Technical method

Maintain redistributable CI fixtures plus private local real-package benchmarks, record ground truth/tolerances, test failure recovery and require end-to-end demonstrations for V1.

## Milestone exit gate

V1 passes defined accuracy, recovery, security and end-to-end gates.


## Sprint M17-S01 - Golden datasets

### PL-0369 - Create small redistributable synthetic/public golden dataset for CI.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0368; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0370 - Create private local Kenya benchmark dataset outside Git for real packaging validation.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0369; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0371 - Store ground-truth dimensions and capture conditions for benchmark objects.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0370; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0372 - Store expected reconstruction metrics with tolerance bands.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0371; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0373 - Store expected parametric-fit metrics with tolerance bands.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0372; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0374 - Add regression harness that compares new engine results to benchmark ranges.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0373; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M17-S02 - Failure and recovery testing

### PL-0375 - Test low-texture white HDPE failure behavior.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0374; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0376 - Test glossy PET failure behavior.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0375; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0377 - Test transparent PET limitation/warning behavior.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0376; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0378 - Test missing-capture sector and targeted-recapture workflow.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0377; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0379 - Test corrupt .packscan import and quarantine.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0378; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0380 - Test interrupted COLMAP/OpenMVS job and resume/retry.

**Why:**  COLMAP is the SfM source of camera registration and sparse geometry for the primary reconstruction path. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0379; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0381 - Test disk-full/low-space handling.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0380; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0382 - Test application crash/restart with project recovery.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0381; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0383 - Test external-engine missing/wrong-version diagnostics.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0382; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0384 - Test project migration across schema/app versions.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0383; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M17-S03 - V1 acceptance gates

### PL-0385 - Demonstrate iPhone 16 -> .packscan -> Windows import end-to-end.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0384; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0386 - Demonstrate COLMAP -> OpenMVS textured Scan Master on at least three package families.

**Why:**  COLMAP is the SfM source of camera registration and sparse geometry for the primary reconstruction path. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Invoke COLMAP through the shared subprocess adapter in an isolated workspace, record exact flags/version, preserve database/sparse outputs and expose registered-image statistics. Consume the COLMAP camera/sparse result via the supported OpenMVS interface/converter, run dense/mesh/refine/texture stages separately, preserve stage logs and never overwrite the immutable source scan.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Capability detection reports missing/wrong versions clearly and the tested external version is recorded. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect exact command construction, path quoting on Windows, cancellation behavior, stage isolation, logs and preservation of source/intermediate data.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0385; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0387 - Demonstrate real-scale dimensions within documented V1 tolerance.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0386; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0388 - Demonstrate editable parametric bottle Design Model fitted to Scan Master.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0387; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0389 - Demonstrate editable jerrycan/handle Design Model at accepted deviation.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0388; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0390 - Demonstrate STEP export round-trip with dimensional consistency.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. After export, reopen the STEP file with the CAD layer and compare bounding/key dimensions to the source Design Model within defined tolerances.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable. Round-trip dimensional validation passes. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Validate solid topology and round-trip units/dimensions.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0389; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0391 - Demonstrate label dieline + artwork + rendered product mockup.

**Why:**  Reusing one package geometry across multiple POVU SKUs depends on keeping artwork independent from the physical body. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Keep Label Zone geometry, artwork and package body separate. Dielines must carry real units and include a scale-verification feature.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0390; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0392 - Demonstrate one geometry reused by multiple POVU SKUs.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0391; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0393 - Demonstrate Windows GitHub Actions artifact and macOS/iOS Actions artifact.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0392; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0394 - Complete security/secrets audit of public repository.

**Why:**  This protects a public repository from credential leakage while keeping personal-device installation possible. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0393; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0395 - Freeze V1 limitations and not-for-direct-mold-manufacture statement.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Replace subjective 'looks good' claims with measured regression and failure evidence.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0394; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M18 - Kenya Production Onboarding

## Milestone intent

Convert the software into a repeatable Kenya packaging digitization process.

## Technical method

Standardize the physical scan station, naming, prioritization, SOP, revisions and backup. Digitize representative high-value package families first and reuse geometry across SKUs.

## Milestone exit gate

A full production asset can move from physical sample to audited library entry using the documented SOP without developer improvisation.


## Sprint M18-S01 - Scan station

### PL-0396 - Define low-cost physical scan-station bill of materials: turntable, matte background, lights, tripod/phone mount and calibration mat.

**Why:**  Photogrammetry alone does not guarantee physical scale, so this is required for trustworthy millimetre measurements. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Use known printed geometry in millimetres, reject inconsistent marker observations and record print verification plus calibration uncertainty.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Recompute at least one known dimension or synthetic case and verify units/uncertainty.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0395; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0397 - Define repeatable lighting positions/distances and camera distance.

**Why:**  Reconstruction quality is capped by capture quality, so camera behavior and metadata must be deterministic enough for repeatable scans. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Check that no LiDAR-only assumption exists and that accepted reconstruction images are high-resolution stills with coherent metadata.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0396; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0398 - Evaluate cross-polarized lighting option for glossy packaging.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Run a focused decision spike with explicit candidates, compatibility constraints, measurable criteria and recorded evidence. Record the decision and rejected alternatives; if the choice changes architecture, add/update an ADR before production implementation.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0397; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0399 - Define safe removable scanning-treatment procedure for difficult reflective/transparent samples when acceptable.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0398; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0400 - Create printed operator checklist for object cleaning, label handling, reflections and capture sequence.

**Why:**  Reusing one package geometry across multiple POVU SKUs depends on keeping artwork independent from the physical body. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Keep Label Zone geometry, artwork and package body separate. Dielines must carry real units and include a scale-verification feature.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0399; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0401 - Validate scan-station repeatability across multiple sessions.

**Why:**  This converts an assumption into auditable evidence and prevents quality regressions from being accepted by appearance alone. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. The result includes explicit pass/fail criteria and recorded output, not a verbal assertion.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0400; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M18-S02 - Kenya library population

### PL-0402 - Define canonical naming/ID scheme for Kenya packaging assets.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0401; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0403 - Inventory all physical bottles, jerrycans, jars, tubes, sachets, caps, triggers and pumps to digitize.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0402; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0404 - Prioritize inventory by POVU launch relevance and reuse across SKUs.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0403; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0405 - Digitize first 1 L bottle as production reference asset.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0404; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0406 - Digitize first 5 L jerrycan as production reference asset.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0405; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0407 - Digitize first trigger bottle/assembly as production reference asset.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0406; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0408 - Digitize first tube as production reference asset.

**Why:**  These are real Kenya package families whose geometry cannot be represented reliably by a simple surface of revolution. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0407; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0409 - Digitize representative cap/closure library.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0408; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0410 - Attach verified dimensions, material/supplier metadata and artwork to each accepted asset.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0409; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0411 - Run duplicate-geometry review so one physical package is not rescanned for every SKU.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0410; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0412 - Back up accepted Kenya library and verify restore on a clean environment.

**Why:**  Physical package samples and scan sessions can be expensive or impossible to recreate, so recoverability is a product requirement. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0411; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M18-S03 - Operating procedure

### PL-0413 - Create SOP: receive physical sample -> clean -> calibrate -> capture -> reconstruct -> fit -> audit -> publish to library.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0412; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0414 - Create rescan/recapture decision tree based on QA metrics.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0413; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0415 - Create supplier-change revision process so old geometry remains traceable.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0414; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0416 - Create artwork-only change process that reuses geometry.

**Why:**  Reusing one package geometry across multiple POVU SKUs depends on keeping artwork independent from the physical body. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0415; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0417 - Create packaging-geometry change process requiring a new scan/design revision.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0416; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0418 - Define backup cadence and off-machine copy policy for irreplaceable scans.

**Why:**  Physical package samples and scan sessions can be expensive or impossible to recreate, so recoverability is a product requirement. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Create one canonical, reviewable artifact in the repository. State scope, inputs, outputs, invariants, failure cases and ownership; cross-link related ADR/schema/test locations and avoid duplicating the same rule in multiple files.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0417; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0419 - Complete first full Kenya production run using the SOP without developer intervention.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Convert the software into a repeatable Kenya packaging digitization process.

**How:** Define ground truth and pass/fail thresholds before running the check. Execute on the required fixture/device/object, save reproducible commands/settings and summarize numerical or observable results in the task evidence.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0418; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# M19 - Advanced Automation Backlog

## Milestone intent

Capture valuable automation ideas without destabilizing the core product before V1.

## Technical method

Prototype only after V1 contracts are stable. AI suggestions remain optional and confirmable; hardware automation records deterministic metadata; advanced visualization consumes existing data models.

## Milestone exit gate

No backlog feature compromises V1 reliability or becomes an undocumented dependency.


## Sprint M19-S01 - AI-assisted geometry

### PL-0420 - Research learned feature recognition for shoulder/base/handle segmentation.

**Why:**  Packaging scans often contain backgrounds and turntable scenery that can confuse matching; object masks reduce that contamination. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Run a focused decision spike with explicit candidates, compatibility constraints, measurable criteria and recorded evidence. Record the decision and rejected alternatives; if the choice changes architecture, add/update an ADR before production implementation. Prefer constrained sections/features for the main form; use freeform/cage deformation only for residual detail and quantify scan-to-design deviation around the handle.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0419; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0421 - Add optional AI suggestion layer for package-family classification.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0420; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0422 - Add optional AI proposal for parametric-section placement, requiring user confirmation.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Verify the result is truly parameter-driven, not merely a renamed mesh edit, and review scan-to-design deviation.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0421; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0423 - Add fit-parameter optimizer constrained by measured dimensions and scan deviation.

**Why:**  The Kenya use case requires dimensions that can be compared, reused and communicated, not merely visually plausible meshes. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Numerical tolerance/uncertainty and physical or synthetic ground truth are stated where applicable.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0422; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0424 - Add anomaly detector that identifies likely reconstruction defects before fitting.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0423; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M19-S02 - Capture automation

### PL-0425 - Prototype Bluetooth-controlled turntable integration.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0424; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0426 - Synchronize turntable-angle events into PackScan metadata.

**Why:**  This is a cross-platform contract; ambiguity here would make iOS and Windows silently disagree about the same capture. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement the stated behavior in the component that owns it, define its contract explicitly, cover success and failure paths, and add evidence that downstream code can rely on the result. Use explicit schema versions, JSON Schema where applicable, normalized paths, UTF-8 JSON, millimetre units, SHA-256 checksums and forward/unsupported-version handling.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Valid fixtures pass; malformed/unsupported fixtures fail with a deliberate error rather than partial interpretation.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Cross-check Swift/Python field names, units, optionality, version behavior and checksum semantics.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0425; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0427 - Add automatic multi-ring scan-station capture recipe.

**Why:**  Reproducible cloud builds remove dependence on owning a Mac and make regressions visible. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Keep public-repo workflows secret-free by default, pin actions where practical, cache only reproducible dependencies and upload diagnostic logs on failure.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0426; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0428 - Add adaptive angle density based on geometry complexity.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0427; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0429 - Add remote iPhone capture control from Windows Studio on trusted LAN.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0428; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


## Sprint M19-S03 - Advanced visualization and reporting

### PL-0430 - Add AR preview of edited package geometry on iPhone.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Simulator/CI evidence is not enough when physical-device behavior is part of the task; a real-iPhone check must be recorded when required.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0429; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0431 - Add side-by-side/ghosted Scan Master vs Design Model review mode.

**Why:**  The central product promise is editability; triangle meshes alone cannot provide stable dimension-driven packaging edits. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures. Separate unsigned/simulator builds from optional device signing. Signing material must come only from protected CI secrets or local secure storage; document the free-first sideload fallback.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence. Repository scan/review finds no committed credential or private signing material.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in. Inspect workflow logs/config for secret exposure and distinguish signed from unsigned artifacts.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0430; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0432 - Add shelf-lineup visualization for multiple POVU SKUs.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0431; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0433 - Add supplier-comparison report for alternative packages.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0432; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.

### PL-0434 - Add automated packaging technical-dossier export after V1 data model is stable.

**Why:**  Completing this task removes a specific ambiguity or missing capability required by its sprint and gives downstream tasks a stable dependency. Capture valuable automation ideas without destabilizing the core product before V1.

**How:** Implement through the narrowest domain adapter/service that owns the behavior, keep UI orchestration separate from core logic, validate inputs, return actionable errors, make writes atomic/non-destructive where data is valuable, and add focused automated tests plus fixtures.

**Acceptance:** The requested artifact/behavior exists in its canonical location, is referenced by the project where needed, has no unresolved mandatory test failure, and handoff.md records reproducible evidence.

**Audit focus:** Confirm scope matches the task, implementation is in the correct layer, failure paths are covered, tests/evidence are reproducible, and no unrelated architecture change was smuggled in.

**Dependency rule:** Default dependency is all earlier non-deferred tasks through PL-0433; a documented ADR/user-approved exception in handoff.md is required to bypass ordering.


---

# Guide Maintenance Rules

- Task IDs are permanent. Never recycle an ID.
- If task scope changes materially, update TASKS.md and this file together and record the architecture reason.
- If a task is split, keep the original ID as parent and add new IDs after PL-0434 rather than renumbering history.
- Acceptance criteria may become stricter as benchmarks mature; never weaken them only to make an audit pass.
- A new dependency must be added to the dependency/license register and capability diagnostics before broad use.
- Physical accuracy claims require recorded physical measurements. Visual similarity is not evidence of dimensional accuracy.
