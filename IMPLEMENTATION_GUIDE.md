# PackLab Implementation Guide

> Architecture and implementation guidance only. This file is **not** project state and does not authorize work.
>
> Root `TASKS.md` is the only live H!veAI/project-status tracker. Exact executable scope for each implementation pass is frozen by ChatGPT under `coordination/sessions/<CYCLE_ID>/CODEX_PROMPT_VNN.md` with matching `CHATGPT_AUDIT_CRITERIA_VNN.md`.

## 1. Product objective

PackLab is a personal packaging digital-twin system for the Kenya project.

Primary flow:

```text
iPhone 16 Standard
  -> PackLab Capture
  -> .packscan
  -> PackLab Studio
  -> ReconstructionBackend
       -> COLMAP + OpenMVS (V1 production lane)
       -> future license-cleared neural backend (experimental)
  -> SegmentationBackend / versioned masks
  -> visibility-aware mask-to-3D multiview object extraction
  -> Object Capture Geometry
  -> metric scale / alignment
  -> Open3D
  -> Scan Master
  -> Parametric Design Model
  -> OpenCascade BREP / STEP
  -> Labels / Materials / Blender
  -> Kenya Packaging Library
```

The goal is not merely to create attractive 3D scans. PackLab must preserve a measured reference scan and, where the package family supports it, derive a separate editable parameter-driven Design Model suitable for controlled dimensional editing and engineering export.

## 2. Canonical authority

Authority order:

1. GitHub repository `Sekiph82/PackLab`, branch `main`.
2. Root `TASKS.md` `## Project Status` for live milestone/sprint/task/status/actor/next-action state.
3. Active versioned session prompt and audit criteria for the exact implementation pass.
4. `AGENTS.md`, `coordination/README.md`, and `coordination/AUDIT_POLICY.md` for operating/audit rules.
5. This guide for architectural and implementation principles.
6. `coordination/AUDIT_INDEX.md` for reusable audit learnings.
7. Logs/audits/handoff/history as evidence only.

If prose in an older artifact conflicts with current `TASKS.md`, active prompt, or audit policy, the higher authority wins.

## 3. Session execution model

For every task, ChatGPT creates a cycle such as:

```text
coordination/sessions/PL-0001-C001/
  CODEX_PROMPT_V01.md
  CHATGPT_AUDIT_CRITERIA_V01.md
  CODEX_LOG_V01.md
  CHATGPT_AUDIT_V01.md
```

Ownership:

- ChatGPT writes prompts, criteria, independent audits, audit learnings, and root `TASKS.md` lifecycle state.
- Codex implements/tests only the active prompt and writes only the matching `CODEX_LOG_VNN.md` plus authorized product/docs/test changes.
- Codex does not edit `TASKS.md` and does not self-audit.
- ChatGPT updates `TASKS.md` after every received Codex log/audit cycle.

If corrections are required, ChatGPT issues V02 prompt/criteria. Prior artifacts remain immutable history. Never overwrite V01 to make history look clean.

## 4. Local/GitHub synchronization

Canonical local workspace:

`C:\Users\sekip\Desktop\PackLab`

GitHub `main` is always repository truth.

### Initial owner-authorized bootstrap

The owner explicitly states that current GitHub files are correct and the local workspace was not updated with those GitHub changes. Therefore the first bootstrap-capable Codex prompt may force the verified local PackLab checkout to match `origin/main` exactly for tracked/non-ignored content.

Requirements:

- verify Git root and `origin` identity first;
- fetch `origin/main`;
- use only commands explicitly authorized by the active prompt;
- never use `git clean -fdx`;
- verify local HEAD equals `origin/main` and working tree is clean before implementation starts.

This is a one-time synchronization exception, not a general destructive-sync policy.

### Normal sessions after bootstrap

Use fetch + comparison + safe fast-forward. Unexpected tracked local divergence must stop the session unless a later owner-authorized prompt explicitly says GitHub should replace it.

## 5. Core technical principles

1. **No LiDAR dependency.** iPhone 16 Standard is treated as a non-LiDAR device. Capture is image-based photogrammetry; ARKit/CoreMotion provide supporting pose/motion metadata.
2. **Immutable capture evidence.** Original photos and imported `.packscan` source are never silently rewritten.
3. **Scan Mesh != Design Model.** Dense reconstruction is reference geometry, not the final editable CAD truth.
4. **PackLab owns reconstruction semantics.** External reconstruction engines implement the PackLab `ReconstructionBackend`; backend-specific types/commands do not own project truth.
5. **COLMAP/OpenMVS is the V1 production lane.** COLMAP owns its SfM stages and OpenMVS owns its dense/mesh stages behind the PackLab adapter. Future neural engines remain experimental until license and physical benchmark gates pass.
6. **Open3D owns geometric analysis/cleanup.** Registration, normals, components, measurements, proxy decimation and deviation analysis remain non-destructive relative to promoted masters.
7. **OpenCascade owns engineering BREP.** STEP/solid exports come from validated parameter-driven geometry, not from relabeling a triangle mesh.
8. **Blender owns repeatable visual presentation.** UV/material/render output is visual, never dimensional source of truth.
9. **Millimetres are canonical engineering units.** Scale provenance and uncertainty must be carried where relevant.
10. **External engines use adapters.** Versions, capabilities, paths, command output, cancellation and failures are explicit.
11. **Public-repository safety.** Secrets, signing material, private Kenya scans and confidential supplier data stay outside Git.
12. **Deterministic evidence beats opaque scores.** AI can suggest, but core quality gates expose components, thresholds and provenance.
13. **Captured geometry and generated geometry are different authority classes.** `AI_VISUAL_REFERENCE` may never satisfy measurement, calibration, captured-geometry QA or Scan Master promotion.
14. **Object extraction is multiview and visibility-aware.** Background may assist camera solving, while versioned masks plus camera geometry determine which real 3D observations belong to the package.

## 6. Planned application architecture

### PackLab Capture, iPhone

Primary stack:

- SwiftUI
- NextLevel / AVFoundation camera layer
- ARKit
- Vision
- CoreMotion
- PackScan writer and transfer services

Responsibilities:

- controlled high-resolution still capture;
- live preview/quality analysis;
- focus/exposure/white-balance control where supported;
- capture metadata;
- AR/motion metadata;
- guided coverage;
- scan-session persistence;
- `.packscan` creation and transfer.

Do not move heavyweight dense reconstruction onto the phone unless a future audited task explicitly changes the architecture.

### PackLab Studio, Windows

Primary stack:

- PySide6
- Python Core
- OpenCV
- PyTorch
- COLMAP
- OpenMVS
- Open3D
- OpenCascade binding selected by audited compatibility task
- Blender headless automation

Responsibilities:

- ingest and immutable raw preservation;
- calibration/scale;
- backend-neutral reconstruction orchestration with COLMAP/OpenMVS as the V1 production lane;
- versioned segmentation masks, visibility-aware mask-to-3D object extraction and reconstruction QA;
- Scan Master creation;
- measurement;
- parametric fitting/editing;
- BREP/STEP and technical output;
- labels/materials/rendering;
- packaging digital-twin library.

## 7. Data model boundaries

### PackScan

Cross-platform capture container. It must be versioned, validated, checksummed and explicit about units/coordinate systems/optional metadata.

### Reconstruction Observation

Backend-derived cameras/geometry before package isolation. COLMAP/OpenMVS is the V1 source; future neural backends must use the same normalized contract. Reconstruction observations never silently become metric or engineering truth.

### Object Capture Geometry

`generated=false` geometry supported by real captured views after versioned masks are lifted into solved camera geometry and fused across views with visibility-aware consensus. It is the captured input to later M09/M10 authority, not automatically a Scan Master.

### AI Visual Reference

`generated=true` object completion/visualization from a future generative backend. It may help visualization or recapture planning but is ineligible for measurement, calibration and Scan Master promotion.

### Scan Master

A deliberately promoted, normalized reference scan with provenance to source capture and reconstruction settings.

### Design Model

Versioned parameter graph defining editable packaging geometry. Examples include dimensions, profiles, cross-sections, symmetry, neck/closure references, handles and constrained feature geometry.

### BREP/CAD representation

Engineering solid derived from the Design Model through OpenCascade. It is validated separately and may be tessellated into a preview mesh.

### Artwork/materials

Artwork, Label Zones and PBR material assignments remain separate from physical package geometry so one geometry can serve multiple POVU SKUs.

## 8. Testing and evidence hierarchy

Use the narrowest meaningful level and expand for integration risk:

1. unit tests for pure logic;
2. schema/contract tests across Swift and Python;
3. adapter/integration tests for external engines;
4. UI smoke tests;
5. golden-dataset geometry/reconstruction regressions;
6. physical iPhone 16 checks for camera/AR behavior;
7. physical marker/caliper benchmarks for scale/dimensions;
8. end-to-end V1 acceptance runs.

A simulator cannot prove camera quality. A rendered model cannot prove dimensional accuracy. A Codex-authored green test cannot by itself prove independent audit closure.

## 9. Task implementation requirements

Before Codex edits product files it must:

1. synchronize according to the active prompt;
2. read root `TASKS.md` and confirm the task is still authorized;
3. read `AGENTS.md` and required coordination policy;
4. read the exact `CODEX_PROMPT_VNN.md`;
5. read the matching `CHATGPT_AUDIT_CRITERIA_VNN.md`;
6. if the active `TASKS.md` row or prompt contains a **Mandatory pre-read** link, read that `docs/implementation/` file in full before material work;
7. read only additional references identified by the prompt.

During implementation Codex must:

- stay inside frozen scope;
- preserve architecture boundaries;
- validate inputs and failure paths;
- keep valuable source data non-destructive;
- add the tests/evidence required by the criteria;
- run every prompt-mandated validation command individually;
- record failures and fixes rather than hiding them.

After implementation Codex must:

1. write matching `CODEX_LOG_VNN.md`;
2. review diff/scope;
3. commit/push authorized implementation and log;
4. verify GitHub remote commit;
5. return `AWAITING_AUDIT`;
6. stop without editing `TASKS.md` or starting another task.

## 10. Independent audit requirements

ChatGPT audits against the frozen criteria, not against the implementer's confidence.

The audit inspects:

- active prompt and inherited scope;
- matching audit criteria;
- matching Codex log;
- actual GitHub commit/diff/files;
- architecture boundaries;
- test quality/sensitivity;
- negative/boundary cases;
- regression risk;
- secrets/privacy;
- scope leakage;
- runtime claims that could or could not be independently rerun.

ChatGPT writes `CHATGPT_AUDIT_VNN.md` and then updates `TASKS.md` to the audited truth after every log.

PASS closes only proven rows. Failure keeps rows open and produces the next remediation prompt/criteria version.

## 11. H!veAI compatibility

Root `TASKS.md` must always retain the explicit parser-facing `## Project Status` fields:

- Current Milestone
- Current Sprint
- Current Task
- Current Task Status
- Next Task/Action
- Required Actor
- Tracking Repository
- Tracking Branch

No coordination/session document may become a second tracker. Session files may contain cycle metadata and evidence but must not override H!veAI state.

## 12. Task-specific implementation detail

The permanent task inventory remains in root `TASKS.md` using `PL-xxxx` IDs.

This guide intentionally does not duplicate 434 live task entries. Detailed execution requirements are frozen **at the time each task is activated** in its versioned session prompt and audit criteria, using:

- the permanent TASKS title/scope;
- architecture rules in this guide;
- relevant prior audits/learnings;
- current repository state;
- current external dependency/API constraints where applicable.

This avoids stale per-task prose becoming a shadow tracker and gives every implementation pass an auditable frozen contract.

Historical versions of the former auto-generated per-task guide remain recoverable in Git history but are superseded by this session-based execution model.


## 13. Object-centric reconstruction reference

The accepted architecture derived from the OpenReality review is:

https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

Decision record:

https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0003-object-centric-reconstruction-authority.md

These documents define captured-vs-generated geometry authority, reconstruction/segmentation backend seams, mask-to-3D multiview extraction, metric-scale ownership and future neural/generative research boundaries.
