# PackLab — Canonical GitHub Task State

This root TASKS.md is the only authoritative project-status tracker consumed by H!veAI. GitHub repository metadata and the latest commit are the remaining project-truth inputs. Hidden .hiveai control-plane files are historical only and are not read for current project state.

## Project Status

- Current Milestone: M15
- Current Sprint: M15-C001 — Kenya Packaging Library
- Current Task: M15-C001 — ordered batch PL-0332 through PL-0346
- Current Task Status: READY
- Next Task/Action: Execute https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/MASTER_CODEX_PROMPT_V01.md against https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md. Run PL-0332 through PL-0346 in exact order while green; preserve supplier-vs-estimate provenance, path-free portable library authority, local-only attachment storage, and existing PackLab project/revision authority. Stop truthfully on any real blocker. Do not start M16.
- Required Actor: CODEX
- Latest Milestone Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/M14-C001_CHATGPT_AUDIT_V01.md — AUDITED_PASS; M14-C001 and M14 complete, 22/22 children accepted.
- Latest M08 Owner Decision: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md — ACCEPTED on 2026-10-01; V1 segmentation backend is Meta SAM 2.1 Hiera Base+, local PyTorch only, official checkpoint source only, no runtime auto-download, checkpoint SHA-256 required before acceptance.
- Latest PL-0186 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_V02.md - AUDITED_PASS; V03 independently closed expected-vs-observed SAM 2 runtime identity and executed-Hydra-config provenance findings.
- Latest PL-0187 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CHATGPT_AUDIT_V02.md - AUDITED_PASS; V03 independently closed parent raster/digest integrity before derivation.
- Latest M08 Remaining-Batch Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/MASTER_REMAINING_CHATGPT_AUDIT_V01.md — AUDITED_PASS for PL-0188 through PL-0201.
- Active M09 Batch Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_PROMPT_V01.md — batch stopped truthfully at PL-0220 OWNER_REQUIRED. Master criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md
- Latest M09 Accepted Frontier: PL-0202 through PL-0219 AUDITED_PASS; PL-0220 owner gate confirmed by https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0220_CHATGPT_AUDIT_V01.md
- M09 Physical Validation Deferral: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/M09_PHYSICAL_VALIDATION_DEFERRAL_OWNER_DECISION_V01.md — owner explicitly deferred PL-0220 through PL-0224 until printer/benchmark objects are available; no physical PASS is implied.
- M09 Owner Print-Capture Status: A4 v1.0.0 print had correct physical scale but a canonical ID 2 marker encoding defect; capture acceptance revoked. Corrected A4/A3 source v1.0.1 requires reprint and new owner verification. PL-0220 through PL-0224 remain DEFERRED_OWNER_VALIDATION.
- Active M10 Batch Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/MASTER_CODEX_PROMPT_V01.md — original ordered PL-0225 through PL-0240 batch.
- Latest M10 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/M10-C001_CHATGPT_AUDIT_V01.md — AUDITED_PASS; 16/16 M10 children accepted.
- Latest M11 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/M11-C001_CHATGPT_AUDIT_V01.md — AUDITED_PASS; 27/27 M11 children accepted.
- Active M12 Batch Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/MASTER_CODEX_PROMPT_V01.md — original batch stopped at PL-0269 after unrelated locked-suite cancellation failure.
- Latest M12 Partial Audit: PL-0268 AUDITED_PASS; PL-0269 child-scope source review PASS but global suite gate blocked by deterministic pre-set cancellation race. Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0269_CHATGPT_AUDIT_V01.md
- Active M12 Remediation/Continuation: superseded after successful PL-0269 remediation and continuation through PL-0282.
- Latest M12 Accepted Frontier: PL-0268 through PL-0282 AUDITED_PASS. Partial audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/M12-C001_CHATGPT_PARTIAL_AUDIT_V02.md
- M12 Authority Resolution: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md — explicit STANDALONE_DESIGN_GEOMETRY root added alongside captured Scan Master binding.
- Active M12 R02 Continuation: completed and superseded by final audit.
- Latest M12 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/M12-C001_CHATGPT_AUDIT_V01.md — AUDITED_PASS; 21/21 M12 children accepted.
- Active M13 Batch Master: original batch stopped correctly at PL-0299 V01 authority conflict.
- Latest M13 Partial Audit: PL-0289 through PL-0298 AUDITED_PASS; PL-0299 V01 blocker accepted. https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/M13-C001_CHATGPT_PARTIAL_AUDIT_V01.md
- M13 R01 Continuation: completed; PL-0299 V02 through PL-0309 implementations are independently accepted. Original continuation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_PL0299_CONTINUATION_CODEX_PROMPT_V02.md
- Latest M13 Milestone Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/M13-C001-R02_CHATGPT_AUDIT_V01.md — AUDITED_PASS; F01 closed, 21/21 M13 children accepted, M13 complete.
- M13 R02 Evidence Closure: completed and independently accepted.
- M14 Original Batch Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/MASTER_CODEX_PROMPT_V01.md — historical; authority stops/remediations preserved.
- M14 R01/R02/R03 continuations: completed. PL-0310 through PL-0331 are independently accepted.
- Latest M14 Milestone Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/M14-C001_CHATGPT_AUDIT_V01.md — AUDITED_PASS; 22/22 children accepted, M14 complete.
- Active M15 Batch Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/MASTER_CODEX_PROMPT_V01.md — ordered PL-0332 through PL-0346; criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md
- Latest M06 Partial Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/CHATGPT_AUDIT_V01.md — CHANGES_REQUIRED; accepted PL-0135, PL-0136, PL-0137, PL-0139, PL-0142, PL-0143.
- Latest M06 R01 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/M06-R01_CHATGPT_AUDIT_V01.md — AUDITED_PASS; PL-0135 through PL-0149 are independently accepted.
- Latest M06 C002 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/CHATGPT_AUDIT_V01.md — superseded by R02 closure.
- Latest M06 R02 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/M06-R02_CHATGPT_AUDIT_V01.md — AUDITED_PASS; M06 complete.
- OpenReality Architecture Decision: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0003-object-centric-reconstruction-authority.md — accepted. Master integration architecture: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md.
- Latest M07 C001 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/CHATGPT_AUDIT_V01.md — CHANGES_REQUIRED partial audit; PL-0160 and PL-0161 were subsequently closed by the independent M07-C001-R01 V04 audit.
- Latest M07 C001 R01 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/M07-C001-R01_CHATGPT_AUDIT_V04.md — AUDITED_PASS; PL-0160 and PL-0161 are independently accepted after the V04 evidence-boundary correction.
- Latest PL-0166 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0166_CHATGPT_AUDIT_V01.md — AUDITED_PASS; the revision-scoped byte-preserving working-set seam is independently accepted.
- Latest PL-0167 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CHATGPT_AUDIT_V02.md — AUDITED_PASS; V02 closed the generic prior-binding and permanent duplicate-metadata ambiguity findings.
- Latest PL-0168 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CHATGPT_AUDIT_V02.md — AUDITED_PASS; V02 independently verified deterministic alias normalization, conflict rejection, regression behavior, scope, and publication evidence.
- Latest PL-0169 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0169_CHATGPT_AUDIT_V01.md — AUDITED_PASS; the ordered guided-orbit matcher-selection boundary, turntable separation, deterministic provenance, regression evidence, and scope were independently accepted.
- Latest PL-0170 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0170_CHATGPT_AUDIT_V02.md — AUDITED_PASS; V02 independently closed the numeric-overflow, stage-result consistency, sparse-output identity, direct-result invariant, and boundary-test findings.
- Latest PL-0171 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0171_CHATGPT_AUDIT_V01.md — AUDITED_PASS; the deterministic sparse-diagnostic policy, result classifications, threshold boundaries, fail-closed behavior, safe report serialization, and scope were independently accepted.
- Latest PL-0172 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0172_CHATGPT_AUDIT_V02.md — AUDITED_PASS; V02 closed the missing cancelled-run public-boundary coverage without changing the accepted exporter implementation.
- Latest PL-0173 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0173_CHATGPT_AUDIT_V01.md — AUDITED_PASS; the immutable backend-neutral reconstruction preset boundary, deterministic provenance, rejection paths, regression suite, and scope were independently accepted.
- Latest PL-0174 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0174_CHATGPT_AUDIT_V03.md — AUDITED_PASS; V03 independently closed the model-specific focal-parameter and valid zero-observation compatibility findings.
- Latest PL-0175 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0175_CHATGPT_AUDIT_V02.md — AUDITED_PASS; V02 independently closed the documented OpenMVS semantic option-domain finding while preserving the accepted dense-stage architecture and predecessor contracts.
- Latest PL-0176 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0176_CHATGPT_AUDIT_V02.md — AUDITED_PASS; V02 independently closed numeric-overflow error translation and runtime-boolean cancellation validation. PL-0177 V01 is now authorized; PL-0178+ remains unauthorized.
- Latest PL-0177 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0177_CHATGPT_AUDIT_V01.md — AUDITED_PASS; the OpenMVS mesh-refinement boundary, provenance/authority/scale invariants, pinned command/probe mapping, fail-closed results, regression evidence, and publication scope were independently accepted. PL-0178 V01 is now authorized; PL-0179+ remains unauthorized.
- Latest PL-0178 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0178_CHATGPT_AUDIT_V01.md — AUDITED_PASS; the OpenMVS texture boundary, pinned command/probe mapping, provenance/authority/scale invariants, fail-closed results, regression evidence, and publication scope were independently accepted. PL-0179 V01 is now authorized; PL-0180+ remains unauthorized.
- Latest PL-0179 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0179_CHATGPT_AUDIT_V03.md — AUDITED_PASS; V03 independently verified atomic stage/run publication, collision preservation, failure-injection cleanup, retained-byte integrity, regression behavior, scope, and publication evidence. PL-0180 V01 is now authorized; PL-0181+ remains unauthorized.
- Latest PL-0180 Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0180_CHATGPT_AUDIT_V01.md — AUDITED_PASS; the immutable backend-neutral CPU/GPU resource-policy boundary, explicit capability selection/fallback, bounded memory/worker limits, deterministic provenance, regression evidence, and publication scope were independently accepted. M07-C002 is now authorized for PL-0181 through PL-0183 in order.
- Open Owner Gate: PL-0068 remains unchecked / OWNER_REQUIRED because no printer is currently available. Owner previously authorized continued implementation while this physical-evidence gate remains open.
- Tracking Repository: Sekiph82/PackLab
- Tracking Branch: main

## Tasks
# PackLab - Master Task Plan

> Canonical execution tracker.
> Every implementation task has a permanent PL-xxxx ID.
> A task may be checked [x] only after the matching independent `coordination/sessions/<CYCLE_ID>/CHATGPT_AUDIT_VNN.md` returns `AUDITED_PASS` and ChatGPT updates this file.

## Status Legend

- READY - authorized for the Required Actor; may be a single task or an explicitly named milestone batch
- [ ] Not completed / not audit-approved
- [x] Implemented, independently audited, and accepted
- BLOCKED - dependency or external requirement is missing
- DEFERRED - intentionally postponed with reason recorded by ChatGPT in this tracker and supporting evidence
- AUDIT-PENDING - implementation/log exists but independent ChatGPT audit has not yet closed the task
- CHANGES_REQUIRED - independent audit found mandatory corrections; task remains unchecked
- OWNER_REQUIRED - human-controlled decision/evidence is required before closure

## Milestones

| Milestone | Name | Primary Outcome | Status |
|---|---|---|---|
| M00 | Governance & Architecture | Reproducible rules, repo contract, AI workflow | [x] |
| M01 | Monorepo & Development Foundations | iOS + Windows project skeletons, local tooling | [x] |
| M02 | PackScan Data Contract & Calibration | Versioned .packscan format and real-world scale contract | [ ] |
| M03 | iOS Capture Foundation | SwiftUI/NextLevel/ARKit app runs on iPhone 16 | [x] |
| M04 | Guided Capture & Quality Intelligence | Reliable, guided, high-resolution packaging capture | [x] |
| M05 | Transfer & Ingest | .packscan moves safely from iPhone to Windows | [x] |
| M06 | PackLab Studio Foundation | PySide6 desktop shell and project lifecycle | [x] |
| M07 | Reconstruction Backends & Photogrammetry | Backend-neutral reconstruction contract with COLMAP -> OpenMVS as the V1 production lane | [x] |
| M08 | Segmentation, Object Extraction & Reconstruction QA | Versioned masks, visibility-aware object-only captured geometry and quality diagnostics | [ ] |
| M09 | Scale, Calibration & Measurement | Real-size geometry with measurable accuracy | [ ] |
| M10 | Mesh Processing & Scan Master | Clean, aligned, optimized reference scan assets | [ ] |
| M11 | Parametric Geometry Engine V1 | Editable bottles, jars, caps and cylindrical packaging | [ ] |
| M12 | Advanced Packaging Geometry | Jerrycans, grips, asymmetry, triggers, pumps and tubes | [ ] |
| M13 | CAD/BREP & Engineering Export | Editable solids, STEP/DXF/SVG/STL exports | [x] |
| M14 | Labels, Materials & Rendering | Artwork zones, PBR materials and production mockups | [ ] |
| M15 | Kenya Packaging Library | Searchable digital-twin library and metadata | [ ] |
| M16 | CI/CD, Signing & Distribution | Free-first Windows/macOS GitHub Actions pipeline | [ ] |
| M17 | Validation, Benchmarking & Reliability | Measured accuracy, regression datasets and recovery | [ ] |
| M18 | Kenya Production Onboarding | Real packaging digitization workflow in daily use | [ ] |
| M19 | Advanced Automation Backlog | Optional AI/automation enhancements after stable V1 | [ ] |

---

# M00 - Governance & Architecture

## Sprint M00-S01 - Repository governance

- [x] **PL-0001** Create canonical repository structure specification and ownership rules.
- [x] **PL-0002** Create project glossary covering Scan Mesh, Design Model, Digital Twin, PackScan, Label Zone, BREP, SfM and MVS.
- [x] **PL-0003** Create Architecture Decision Record (ADR) process and first ADR for the monorepo.
- [x] **PL-0004** Document supported host/device baseline: Windows Acer laptop + iPhone 16 Standard, no LiDAR assumption.
- [x] **PL-0005** Create dependency/license register for NextLevel, COLMAP, OpenMVS, Open3D, OpenCV, PyTorch, OpenCascade bindings, Blender and PySide6.
- [x] **PL-0006** Define semantic versioning rules for PackLab Studio, PackLab Capture and PackScan schema.
- [x] **PL-0007** Define source-control conventions: branches, commits, task IDs, pull-request naming and generated-file policy.
- [x] **PL-0008** Define secrets policy so Apple credentials, signing certificates and tokens never enter Git.
- [x] **PL-0009** Define Definition of Done, audit gates and evidence requirements for every task.
- [x] **PL-0010** Create project risk register with technical, licensing, capture-quality, signing and hardware risks.

## Sprint M00-S02 - AI execution protocol

- [x] **PL-0011** Validate the canonical session workflow: TASKS.md -> CODEX_PROMPT/AUDIT_CRITERIA -> CODEX_LOG -> CHATGPT_AUDIT -> ChatGPT TASKS.md update.
- [x] **PL-0012** Define builder-AI responsibilities and forbidden actions.
- [x] **PL-0013** Define independent auditor-AI responsibilities, minimum checks and PASS/FAIL criteria.
- [x] **PL-0014** Define audit evidence format including commands, test output, inspected files and residual risks.
- [x] **PL-0015** Define Codex implementation-log and `AWAITING_AUDIT` handoff format for current task, changed files, tests, blockers and next audit action.
- [x] **PL-0016** Add protocol for failed audits: reopen same task, preserve checkbox, remediate findings, re-audit.
- [x] **PL-0017** Add protocol for blocked tasks and dependency escalation without silently skipping work.
- [x] **PL-0018** Add protocol for architecture changes that require an ADR before implementation.

---

# M01 - Monorepo & Development Foundations

## Sprint M01-S01 - Base monorepo

- [x] **PL-0019** Create top-level folders: apps/ios-capture, apps/windows-studio, core, schemas, docs, tools, tests, assets.
- [x] **PL-0020** Add root README with product mission, architecture diagram, quick-start and repository map.
- [x] **PL-0021** Add Windows/macOS/Linux-safe .gitignore covering Python, Xcode, SwiftPM, Blender, COLMAP/OpenMVS outputs and local scans.
- [x] **PL-0022** Add .editorconfig and line-ending policy to prevent Windows/macOS churn.
- [x] **PL-0023** Define generated-artifact directories and Git LFS policy for sample images/meshes that genuinely belong in source control.
- [x] **PL-0024** Create local environment diagnostics script that reports OS, CPU, RAM, GPU, CUDA availability, Python and external tool versions.
- [x] **PL-0025** Create root task-runner strategy for common bootstrap, test, lint and build commands.
- [x] **PL-0026** Establish local cache directories outside tracked source for reconstruction intermediates.

## Sprint M01-S02 - Python/Windows foundation

- [x] **PL-0027** Choose and pin a Python version after compatibility validation across PySide6/Open3D/OpenCV/PyTorch/OpenCascade binding.
- [x] **PL-0028** Create Python package/workspace layout for PackLab core and Windows Studio.
- [x] **PL-0029** Add dependency locking and reproducible Windows bootstrap.
- [x] **PL-0030** Configure Ruff/formatter/type-check strategy and baseline configuration.
- [x] **PL-0031** Configure pytest with unit/integration/slow-test markers.
- [x] **PL-0032** Add structured logging with session/task correlation IDs.
- [x] **PL-0033** Add application configuration system with user config, project config and environment overrides.
- [x] **PL-0034** Add capability registry for optional engines such as CUDA, COLMAP, OpenMVS, Blender and OpenCascade.
- [x] **PL-0035** Add safe subprocess runner with cancellation, timeout, stdout/stderr streaming and exit-code capture.

## Sprint M01-S03 - Swift/iOS foundation

- [x] **PL-0036** Create SwiftUI iOS application project targeting the user's iPhone 16 and a documented minimum iOS version.
- [x] **PL-0037** Add NextLevel through Swift Package Manager with a pinned tested version.
- [x] **PL-0038** Add project modules/services for Camera, AR Tracking, Motion, Capture Quality, Storage and Transfer.
- [x] **PL-0039** Configure Swift 6 strict concurrency and project warning policy.
- [x] **PL-0040** Add camera/photo-library/local-network permission descriptions actually required by the product.
- [x] **PL-0041** Add iOS logging and diagnostics export.
- [x] **PL-0042** Create simulator-safe fallbacks so CI can build without physical camera hardware.
- [x] **PL-0043** Add unit-test target and initial smoke test.

---

# M02 - PackScan Data Contract & Calibration

## Sprint M02-S01 - PackScan schema

- [x] **PL-0044** Specify .packscan as a versioned ZIP container with deterministic directory layout.
- [x] **PL-0045** Define manifest.json JSON Schema including schema version, capture ID, device, mode, timestamps and checksums.
- [x] **PL-0046** Define per-photo metadata schema: filename, orientation, focal data, exposure, ISO, white balance, dimensions and capture sequence.
- [x] **PL-0047** Define camera-intrinsics representation including calibration matrix, reference dimensions and lens identity.
- [x] **PL-0048** Define ARKit pose representation with coordinate-system conventions and confidence/availability markers.
- [x] **PL-0049** Define CoreMotion metadata representation and timestamp synchronization rules.
- [x] **PL-0050** Define optional object-mask representation and image/mask pixel-coordinate contract.
- [x] **PL-0051** Define calibration-marker observations and real-world unit representation in millimetres.
- [x] **PL-0052** Define capture-mode metadata for Freehand, Guided Orbit and Turntable modes.
- [x] **PL-0053** Define preview, thumbnail and diagnostics payloads.
- [x] **PL-0054** Define SHA-256 integrity checks and partial/corrupt package handling.
- [x] **PL-0055** Create schema validation fixtures: valid, old-version, future-version, corrupt and incomplete samples.
- [x] **PL-0056** Implement Python PackScan reader/writer/validator.
- [x] **PL-0057** Implement Swift PackScan writer compatible with the same fixtures.
- [x] **PL-0058** Add cross-language contract tests ensuring Swift output validates in Python.

## Sprint M02-S02 - Calibration system

- [x] **PL-0059** Select marker family and IDs for PackLab calibration mat using OpenCV-supported AprilTag/ArUco dictionaries.
- [x] **PL-0060** Design printable A4/A3 PackLab calibration mat with precise reference distances and print-at-100% instructions.
- [x] **PL-0061** Add printed-mat verification procedure using ruler/caliper measurements before first use.
- [x] **PL-0062** Implement marker detection and corner refinement in OpenCV.
- [x] **PL-0063** Implement scale estimation from known marker geometry.
- [x] **PL-0064** Implement calibration confidence score and rejection thresholds.
- [x] **PL-0065** Define camera-calibration procedure for iPhone main camera when higher accuracy than EXIF/intrinsics requires it.
- [x] **PL-0066** Store calibration profile by device/lens/resolution and invalidate incompatible profiles.
- [x] **PL-0067** Build synthetic calibration tests with known ground-truth dimensions.
- [ ] **PL-0068** Build first physical calibration benchmark and record measured error. **OWNER_REQUIRED:** physical printed-mat verification is pending because no printer is currently available; owner authorized M03 continuation without closing this task.

---

# M03 - iOS Capture Foundation

## Sprint M03-S01 - Camera control

- [x] **PL-0069** Integrate NextLevel preview into SwiftUI using a controlled UIKit bridge where required.
- [x] **PL-0070** Enumerate iPhone 16 rear-camera devices and select the intended main lens deterministically.
- [x] **PL-0071** Implement high-resolution still-photo capture for reconstruction source images.
- [x] **PL-0072** Preserve original capture metadata without destructive resizing or social-media style processing.
- [x] **PL-0073** Implement focus control with guided autofocus followed by optional focus lock.
- [x] **PL-0074** Implement exposure metering and optional exposure lock for consistent image sets.
- [x] **PL-0075** Implement white-balance stabilization/lock for texture consistency.
- [x] **PL-0076** Capture and persist camera metadata for every accepted still.
- [x] **PL-0077** Add camera-error recovery for interruption, permission denial and session restart.
- [x] **PL-0078** Add thermal/storage/battery warnings before and during long captures.

## Sprint M03-S02 - ARKit & motion tracking

- [x] **PL-0079** Create ARKit world-tracking session without relying on LiDAR.
- [x] **PL-0080** Record camera transform and tracking state aligned to capture timestamps.
- [x] **PL-0081** Record CoreMotion attitude/rotation-rate data with timestamp alignment.
- [x] **PL-0082** Define app-local coordinate frame and conversion into PackScan coordinates.
- [x] **PL-0083** Detect AR tracking degradation and surface a user-visible warning.
- [x] **PL-0084** Implement capture-session reset/relocalization behavior.
- [x] **PL-0085** Create pose visualizer/debug overlay for development.
- [x] **PL-0086** Export pose diagnostics for Windows-side analysis.

## Sprint M03-S03 - Capture project lifecycle

- [x] **PL-0087** Implement New Scan wizard: package name, package type, capture mode and optional notes.
- [x] **PL-0088** Create scan-session storage with crash-safe incremental writes.
- [x] **PL-0089** Add photo gallery for accepted frames with delete/retake controls.
- [x] **PL-0090** Add session resume after app termination.
- [x] **PL-0091** Add session finalization that validates minimum data before creating .packscan.
- [x] **PL-0092** Add local scan history with preview, date, package type and export state.
- [x] **PL-0093** Add safe deletion requiring confirmation and cleaning all associated data.

---

# M04 - Guided Capture & Quality Intelligence

## Sprint M04-S01 - Live quality metrics

- [x] **PL-0094** Implement frame sharpness metric and calibrate thresholds for packaging capture.
- [x] **PL-0095** Implement motion-blur warning using frame analysis plus CoreMotion.
- [x] **PL-0096** Implement exposure/highlight clipping analysis for glossy plastic.
- [x] **PL-0097** Implement underexposure/shadow clipping analysis.
- [x] **PL-0098** Implement object-size/framing score so the package fills an appropriate image area.
- [x] **PL-0099** Implement background-complexity warning for poor photogrammetry setups.
- [x] **PL-0100** Combine metrics into deterministic per-frame ACCEPT/REJECT decision with explainable reasons.
- [x] **PL-0101** Log quality metrics for every candidate/accepted frame for later tuning.

## Sprint M04-S02 - Guided orbit capture

- [x] **PL-0102** Define orbit-coverage model with azimuth/elevation bins around the object.
- [x] **PL-0103** Implement visual coverage globe/rings showing captured and missing sectors.
- [x] **PL-0104** Implement automatic still capture when pose, overlap and quality thresholds are satisfied.
- [x] **PL-0105** Prevent near-duplicate captures that add storage without useful parallax.
- [x] **PL-0106** Require lower, middle and upper capture rings for standard bottle mode.
- [x] **PL-0107** Add top/neck detail pass for closures and shoulders.
- [x] **PL-0108** Add bottom/base detail pass where physically possible.
- [x] **PL-0109** Add completion score and explicit missing-area guidance.
- [x] **PL-0110** Add manual-capture override while retaining quality warnings.

## Sprint M04-S03 - Packaging-specific modes

- [x] **PL-0111** Implement Matte/HDPE capture preset.
- [x] **PL-0112** Implement Glossy/PET preset emphasizing highlight control and denser coverage.
- [x] **PL-0113** Implement Transparent packaging warning mode with instructions for temporary scanning treatment/background preparation.
- [x] **PL-0114** Implement Asymmetric/Jerrycan mode with stronger front/back/handle coverage requirements.
- [x] **PL-0115** Implement Closure/Cap macro-detail mode.
- [x] **PL-0116** Implement Turntable mode with angle-indexed capture and object/background masking assumptions.
- [x] **PL-0117** Add capture protocol screen explaining lighting, matte background, reflections and object preparation per preset.
- [x] **PL-0118** Add scan-suitability preflight before capture starts.

---

# M05 - Transfer & Ingest

## Sprint M05-S01 - Export from iPhone

- [x] **PL-0119** Implement .packscan package finalization with checksums and atomic rename.
- [x] **PL-0120** Implement iOS share-sheet export to Files/iCloud/other installed destinations.
- [x] **PL-0121** Implement local-network transfer protocol from Capture to PackLab Studio.
- [x] **PL-0122** Add QR/pairing-code workflow so the iPhone connects to the correct Windows Studio instance.
- [x] **PL-0123** Encrypt/authenticate local transfer sufficiently to prevent accidental cross-device ingestion.
- [x] **PL-0124** Support resumable transfer for large scan packages.
- [x] **PL-0125** Verify checksum after transfer before marking export complete.
- [x] **PL-0126** Add transfer progress, cancel and retry UI.

## Sprint M05-S02 - Windows ingest

- [x] **PL-0127** Implement drag/drop and file-picker import for .packscan.
- [x] **PL-0128** Implement network receiver for paired iPhone transfers.
- [x] **PL-0129** Validate schema version and checksums before extraction.
- [x] **PL-0130** Quarantine corrupt/unsupported scans instead of partially importing them.
- [x] **PL-0131** Create immutable raw-ingest copy so original capture evidence is never silently modified.
- [x] **PL-0132** Generate import report summarizing images, metadata, calibration and warnings.
- [x] **PL-0133** Deduplicate imports by capture ID/checksum.
- [x] **PL-0134** Add ingest tests for interrupted transfer, corrupt ZIP, missing photo and bad manifest.

---

# M06 - PackLab Studio Foundation

## Sprint M06-S01 - PySide6 shell

- [x] **PL-0135** Create PackLab Studio PySide6 application shell.
- [x] **PL-0136** Implement main navigation: Library, Capture Inbox, Reconstruction, Editor and Settings.
- [x] **PL-0137** Create dockable/logical workspace layout suitable for 3D/CAD work.
- [x] **PL-0138** Implement persistent window/workspace preferences.
- [x] **PL-0139** Add global job/activity panel for long-running reconstruction work.
- [x] **PL-0140** Add cancellation and safe shutdown behavior for active subprocesses.
- [x] **PL-0141** Add crash report/log bundle creation.
- [x] **PL-0142** Add application update/version information screen without requiring an online service.

## Sprint M06-S02 - Project lifecycle

- [x] **PL-0143** Define PackLab project directory layout separating raw, working, derived and export data.
- [x] **PL-0144** Implement New/Open/Close project lifecycle.
- [x] **PL-0145** Implement project metadata and revision identifiers.
- [x] **PL-0146** Implement autosave for editable project state.
- [x] **PL-0147** Implement non-destructive operation history for user edits.
- [x] **PL-0148** Implement project recovery after interrupted processing.
- [x] **PL-0149** Add derived-artifact invalidation when upstream inputs change.
- [x] **PL-0150** Add project portability check that identifies missing external assets.

## Sprint M06-S03 - 3D viewport

- [x] **PL-0151** Select and document the PySide6-compatible 3D viewport approach after a focused performance spike.
- [x] **PL-0152** Implement mesh/point-cloud loading and camera orbit/pan/zoom.
- [x] **PL-0153** Implement world grid, axes and millimetre scale cues.
- [x] **PL-0154** Implement object selection and visibility toggles for Scan Mesh, Design Model, cap, label and reference geometry.
- [x] **PL-0155** Implement wireframe/normals/point-cloud debug modes.
- [x] **PL-0156** Implement screenshot/export preview for audit evidence.
- [x] **PL-0157** Add large-mesh performance benchmark and viewport LOD strategy.

---

# M07 - Reconstruction Backends & Photogrammetry

## Sprint M07-S01 - Engine installation and adapters

- [x] **PL-0158** Define tested COLMAP version, installation source and license record.
- [x] **PL-0159** Define tested OpenMVS version, Windows build/binary source and AGPL license record.
- [x] **PL-0160** Implement COLMAP capability probe and version parser.
- [x] **PL-0161** Implement OpenMVS capability probe and version parser.
- [x] **PL-0162** Implement reconstruction-engine discovery/configuration with explicit paths and diagnostics; preserve a backend-neutral capability boundary so future model runtimes cannot leak into Studio/domain code.
- [x] **PL-0163** Create the normalized PackLab `ReconstructionBackend` job/output contract independent of specific engine/model syntax; V1 composes COLMAP/OpenMVS while future neural engines remain replaceable. **Mandatory pre-read:** https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0163_RECONSTRUCTION_BACKEND_CONTRACT.md
- [x] **PL-0164** Implement per-stage stdout/stderr capture and machine-readable stage result records.
- [x] **PL-0165** Add reconstruction workspace isolation so retries cannot corrupt the source scan.

## Sprint M07-S02 - COLMAP SfM

- [x] **PL-0166** Implement photo preprocessing into a reconstruction-safe working set while preserving originals; keep full-image evidence available for camera solving and never overwrite PackScan source images.
- [x] **PL-0167** Import/use valid PackScan camera intrinsics and capture pose priors under explicit fixed/initialization/refinement rules; reject inconsistent priors rather than silently treating ARKit/capture metadata as metrology truth. **AUDITED_PASS:** V02 closed the generic source/revision binding and permanent duplicate-metadata ambiguity findings.
- [x] **PL-0168** Implement feature-extraction configuration optimized first for packaged consumer goods. **AUDITED_PASS:** V02 closed the order-dependent conflicting threshold-alias normalization finding; equivalent mappings now produce deterministic configuration values and digests, and conflicting aliases fail closed.
- [x] **PL-0169** Implement matcher selection for ordered orbit datasets. **AUDITED_PASS:** V01 independently accepted the ordered guided-orbit boundary, turntable separation, deterministic provenance, regression evidence, and scope.
- [x] **PL-0170** Implement sparse mapper stage and capture registered-image statistics. **AUDITED_PASS:** V02 independently verified the fail-closed numeric-summary, stage-result, sparse-output identity, direct-result invariant, regression, and publication boundaries.
- [x] **PL-0171** Detect failed/fragmented sparse models and produce actionable diagnostics. **AUDITED_PASS:** V01 independently accepted the deterministic policy, failed/cancelled/empty/fragmented/complete classifications, inclusive threshold boundaries, fail-closed result checks, safe report serialization, regression evidence, and scope.
- [x] **PL-0172** Export sparse model/cameras in formats needed by OpenMVS and debugging. **AUDITED_PASS:** V02 closed the missing cancelled-run public-boundary coverage without changing the accepted exporter implementation.
- [x] **PL-0173** Build a tunable reconstruction preset system rather than hardcoding CLI flags. **AUDITED_PASS:** V01 independently accepted the immutable backend-neutral preset composition, deterministic serialization/digest, fail-closed override and provenance boundaries, regression evidence, and scope.

## Sprint M07-S03 - OpenMVS dense reconstruction

- [x] **PL-0174** Implement COLMAP-to-OpenMVS scene conversion. **AUDITED_PASS:** V03 independently closed the model-specific focal-parameter and valid zero-observation compatibility findings while preserving the accepted conversion boundary.
- [x] **PL-0175** Implement OpenMVS dense point-cloud stage. **AUDITED_PASS:** V02 independently closed the documented OpenMVS semantic option-domain finding while preserving the accepted dense-stage architecture and predecessor contracts.
- [x] **PL-0176** Implement OpenMVS mesh-reconstruction stage. **AUDITED_PASS:** V02 independently closed raw numeric-overflow escape and non-boolean cancellation values not failing closed; the accepted mesh-stage boundary and predecessor contracts remain intact.
- [x] **PL-0177** Implement OpenMVS mesh-refinement stage. **AUDITED_PASS:** V01 independently accepted the refinement boundary, pinned command/probe mapping, provenance/authority/scale invariants, fail-closed result normalization, regression evidence, and scope.
- [x] **PL-0178** Implement OpenMVS texture stage. **AUDITED_PASS:** V01 independently accepted the texture boundary, pinned command/probe mapping, provenance/authority/scale invariants, fail-closed result normalization, regression evidence, and publication scope.
- [x] **PL-0179** Preserve all stage outputs and logs for reproducibility. **AUDITED_PASS:** V03 independently verified atomic stage/run publication, collision preservation, failure-injection cleanup, retained-byte integrity, regression behavior, scope, and publication evidence.
- [x] **PL-0180** Add CPU/GPU-aware presets and memory-safety limits. **AUDITED_PASS:** V01 independently accepted the immutable backend-neutral resource-policy boundary, explicit capability selection/fallback, bounded limits, deterministic provenance, regression evidence, and scope.
- [x] **PL-0181** Add one-click Reconstruct Scan orchestration across COLMAP and OpenMVS. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0181_CHATGPT_AUDIT_V01.md
- [x] **PL-0182** Add reconstruction cancellation that leaves the project recoverable. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0182_CHATGPT_AUDIT_V01.md
- [x] **PL-0183** Convert final textured mesh to PackLab-supported preview/export format without losing the master source. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C002/PL-0183_CHATGPT_AUDIT_V01.md

---

# M08 - Segmentation, Object Extraction & Reconstruction QA

## Sprint M08-S01 - Object segmentation

- [x] **PL-0184** Define PackLab `SegmentationBackend` and versioned `MaskArtifact` contracts so the model can be replaced without rewriting object extraction. **Mandatory pre-read:** https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md **AUDITED_PASS:** V03 independently closed the recursive mutation/digest-integrity finding: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0184_CHATGPT_AUDIT_V03.md
- [x] **PL-0185** Benchmark candidate local segmentation model(s) against bottle, jerrycan, cap and transparent/glossy examples. **AUDITED_PASS:** V02 independently closed the benchmark prediction/report-digest integrity finding; the later PL-0186 production model decision was resolved and independently accepted: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0185_CHATGPT_AUDIT_V02.md
- [x] **PL-0186** Implement selected PyTorch segmentation backend. **AUDITED_PASS:** SAM 2.1 Hiera Base+ local backend accepted after V03 runtime/config provenance remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0186_CHATGPT_AUDIT_V02.md
- [x] **PL-0187** Implement mask post-processing: hole filling, edge cleanup and small-component removal. **AUDITED_PASS:** V03 independently closed parent raster/digest integrity while preserving deterministic V02 algorithms: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0187_CHATGPT_AUDIT_V02.md
- [x] **PL-0188** Add manual mask-correction UI for difficult frames. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0188_CHATGPT_AUDIT_V01.md
- [x] **PL-0189** Version masks separately from immutable source photos and make mask revision changes invalidate downstream object-capture geometry. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0189_CHATGPT_AUDIT_V01.md
- [x] **PL-0190** Feed masks into reconstruction stages where supported **and** implement visibility-aware mask-to-3D lifting with multiview consensus to create `OBJECT_CAPTURE_GEOMETRY`; validate camera/image coordinate conventions. **Mandatory pre-read:** https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0190_OBJECT_MASK_LIFT_MULTIVIEW_FUSION.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0190_CHATGPT_AUDIT_V01.md
- [x] **PL-0191** Add mask-quality overlays and contact-sheet review. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0191_CHATGPT_AUDIT_V01.md

## Sprint M08-S02 - Photo/reconstruction QA

- [x] **PL-0192** Build pre-reconstruction QA report using sharpness, exposure, coverage and metadata consistency. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0192_CHATGPT_AUDIT_V01.md
- [x] **PL-0193** Detect duplicate/near-duplicate photos on Windows as a second safety layer. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0193_CHATGPT_AUDIT_V01.md
- [x] **PL-0194** Detect inconsistent focal/lens usage and warn before reconstruction. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0194_CHATGPT_AUDIT_V01.md
- [x] **PL-0195** Calculate registered-photo ratio after COLMAP. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0195_CHATGPT_AUDIT_V01.md
- [x] **PL-0196** Calculate sparse-cloud connectivity/fragmentation indicators. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0196_CHATGPT_AUDIT_V01.md
- [x] **PL-0197** Calculate dense/object-cloud density and surface-coverage indicators, including multiview support statistics for `OBJECT_CAPTURE_GEOMETRY`. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0197_CHATGPT_AUDIT_V01.md
- [x] **PL-0198** Detect obvious reconstruction artifacts and floating components. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0198_CHATGPT_AUDIT_V01.md
- [x] **PL-0199** Produce overall reconstruction confidence with component scores, not a black-box number. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0199_CHATGPT_AUDIT_V01.md
- [x] **PL-0200** Gate downstream parametric fitting when captured-geometry quality is below minimum acceptance thresholds; `AI_VISUAL_REFERENCE` can never satisfy this gate. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0200_CHATGPT_AUDIT_V01.md
- [x] **PL-0201** Suggest targeted recapture sectors instead of demanding a complete rescan when possible. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0201_CHATGPT_AUDIT_V01.md

---

# M09 - Scale, Calibration & Measurement

## Sprint M09-S01 - Coordinate and scale normalization

- [x] **PL-0202** Detect calibration markers in source imagery and associate observations with reconstructed cameras. **ACTIVE BATCH CHILD:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0202_CODEX_PROMPT_V01.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0202_CHATGPT_AUDIT_V01.md
- [x] **PL-0203** Estimate global scale from marker geometry and reject inconsistent observations. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0203_CHATGPT_AUDIT_V01.md
- [x] **PL-0204** Establish canonical PackLab axes: Z up, front direction, millimetres. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0204_CHATGPT_AUDIT_V01.md
- [x] **PL-0205** Implement object ground-plane/base detection with user override. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0205_CHATGPT_AUDIT_V01.md
- [x] **PL-0206** Implement automatic upright alignment with manual correction. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0206_CHATGPT_AUDIT_V01.md
- [x] **PL-0207** Implement front-direction selection and persist it as project metadata. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0207_CHATGPT_AUDIT_V01.md
- [x] **PL-0208** Apply scale/alignment as non-destructive transform before baking a normalized scan. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0208_CHATGPT_AUDIT_V01.md
- [x] **PL-0209** Record scale provenance, uncertainty and explicit RELATIVE/METRIC_UNVERIFIED/METRIC_VERIFIED state. **Mandatory pre-read:** https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0209_CHATGPT_AUDIT_V01.md

## Sprint M09-S02 - Measurement tools

- [x] **PL-0210** Implement bounding dimensions: height, width and depth. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0210_CHATGPT_AUDIT_V01.md
- [x] **PL-0211** Implement two-point distance measurement with snapping. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0211_CHATGPT_AUDIT_V01.md
- [x] **PL-0212** Implement diameter/radius measurement from selected cross-sections. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0212_CHATGPT_AUDIT_V01.md
- [x] **PL-0213** Implement horizontal cross-section extraction at arbitrary Z. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0213_CHATGPT_AUDIT_V01.md
- [x] **PL-0214** Implement vertical profile/silhouette extraction. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0214_CHATGPT_AUDIT_V01.md
- [x] **PL-0215** Implement neck/finish candidate measurement. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0215_CHATGPT_AUDIT_V01.md
- [x] **PL-0216** Implement capacity-estimation groundwork using watertight interior assumptions, clearly separating estimate from certified volume. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0216_CHATGPT_AUDIT_V01.md
- [x] **PL-0217** Display measurement uncertainty/confidence where known. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0217_CHATGPT_AUDIT_V01.md
- [x] **PL-0218** Export measurement report with units and provenance. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0218_CHATGPT_AUDIT_V01.md

## Sprint M09-S03 - Accuracy benchmarks

- [x] **PL-0219** Define physical benchmark set with caliper-measured ground truth. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0219_CHATGPT_AUDIT_V01.md
- [ ] **PL-0220** Measure dimension error across at least matte bottle, glossy bottle and jerrycan. **DEFERRED_OWNER_VALIDATION:** printer/benchmark objects unavailable; resume later from existing PL-0220 prompt. No PASS implied.
- [ ] **PL-0221** Establish V1 acceptance thresholds for overall dimensions and key features. **BLOCKED_BY_PL-0220_OWNER_GATE** **DEFERRED_OWNER_VALIDATION:** dependent physical benchmark evidence postponed by owner.
- [ ] **PL-0222** Add repeat-scan reproducibility test for the same object. **BLOCKED_BY_PL-0220_OWNER_GATE** **DEFERRED_OWNER_VALIDATION:** dependent physical benchmark evidence postponed by owner.
- [ ] **PL-0223** Add calibration-mat print-scale sensitivity test. **BLOCKED_BY_PL-0220_OWNER_GATE** **DEFERRED_OWNER_VALIDATION:** dependent physical benchmark evidence postponed by owner.
- [ ] **PL-0224** Document conditions under which PackLab measurements must not be used for mold manufacturing. **BLOCKED_BY_PL-0220_OWNER_GATE** **DEFERRED_OWNER_VALIDATION:** dependent physical benchmark evidence postponed by owner.

---

# M10 - Mesh Processing & Scan Master

## Sprint M10-S01 - Open3D processing

- [x] **PL-0225** Integrate Open3D as the primary point-cloud/mesh analysis utility layer. **ACTIVE BATCH CHILD:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0225_CODEX_PROMPT_V01.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0225_CHATGPT_AUDIT_V01.md
- [x] **PL-0226** Remove isolated floating components with configurable safeguards. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0226_CHATGPT_AUDIT_V01.md
- [x] **PL-0227** Implement normal estimation/orientation repair. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0227_CHATGPT_AUDIT_V01.md
- [x] **PL-0228** Implement conservative smoothing that preserves packaging edges. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0228_CHATGPT_AUDIT_V01.md
- [x] **PL-0229** Implement hole detection and report hole size/location before any repair. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0229_CHATGPT_AUDIT_V01.md
- [x] **PL-0230** Implement optional hole filling with non-destructive before/after versions. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0230_CHATGPT_AUDIT_V01.md
- [x] **PL-0231** Implement decimation for viewport/proxy meshes while preserving the Scan Master. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0231_CHATGPT_AUDIT_V01.md
- [x] **PL-0232** Compute geometric statistics needed by later fitting stages. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0232_CHATGPT_AUDIT_V01.md
- [x] **PL-0233** Create Scan Master asset with captured-evidence-only ancestry and provenance back to PackScan, reconstruction, masks, scale and cleanup settings; generated AI geometry is ineligible. **Mandatory pre-read:** https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0233_SCAN_MASTER_AUTHORITY.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0233_CHATGPT_AUDIT_V01.md

## Sprint M10-S02 - Scan comparison and revisions

- [x] **PL-0234** Implement point-cloud/mesh registration for comparing repeat scans. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0234_CHATGPT_AUDIT_V01.md
- [x] **PL-0235** Implement distance heatmap between scan and fitted Design Model. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0235_CHATGPT_AUDIT_V01.md
- [x] **PL-0236** Implement cross-section comparison overlay. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0236_CHATGPT_AUDIT_V01.md
- [x] **PL-0237** Record reconstruction versions and allow switching between them. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0237_CHATGPT_AUDIT_V01.md
- [x] **PL-0238** Add Promote to Scan Master action with audit metadata and a hard authority gate rejecting generated/AI-visual-reference assets. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0238_CHATGPT_AUDIT_V01.md
- [x] **PL-0239** Prevent downstream Design Model from silently changing when reconstruction is rerun. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0239_CHATGPT_AUDIT_V01.md
- [x] **PL-0240** Add Scan Master export as PLY/OBJ/GLB plus original texture assets. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0240_CHATGPT_AUDIT_V01.md

---

# M11 - Parametric Geometry Engine V1

## Sprint M11-S01 - Common parametric kernel

- [x] **PL-0241** Define Design Model parameter graph separate from triangle-mesh data. **ACTIVE BATCH CHILD:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0241_CODEX_PROMPT_V01.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0241_CHATGPT_AUDIT_V01.md
- [x] **PL-0242** Define feature IDs and stable references for body, base, shoulder, neck, finish and cap. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0242_CHATGPT_AUDIT_V01.md
- [x] **PL-0243** Implement spline/profile primitives with millimetre coordinates. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0243_CHATGPT_AUDIT_V01.md
- [x] **PL-0244** Implement editable cross-section primitive with symmetry options. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0244_CHATGPT_AUDIT_V01.md
- [x] **PL-0245** Implement loft/revolve abstraction independent of final CAD backend. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0245_CHATGPT_AUDIT_V01.md
- [x] **PL-0246** Implement parameter validation and impossible-geometry rejection. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0246_CHATGPT_AUDIT_V01.md
- [x] **PL-0247** Implement undo/redo command model for parametric edits. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0247_CHATGPT_AUDIT_V01.md
- [x] **PL-0248** Serialize Design Model parameters in a versioned human-readable project format. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0248_CHATGPT_AUDIT_V01.md
- [x] **PL-0249** Generate tessellated preview mesh from parameters for interactive viewport use. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0249_CHATGPT_AUDIT_V01.md

## Sprint M11-S02 - Bottle/jar fitting

- [x] **PL-0250** Detect rotational/symmetry characteristics and choose bottle fitting strategy. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0250_CHATGPT_AUDIT_V01.md
- [x] **PL-0251** Extract robust vertical body profile from normalized Scan Master. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0251_CHATGPT_AUDIT_V01.md
- [x] **PL-0252** Fit smoothed profile while preserving shoulder/base transitions. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0252_CHATGPT_AUDIT_V01.md
- [x] **PL-0253** Detect body, shoulder, neck and base zones with editable boundaries. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0253_CHATGPT_AUDIT_V01.md
- [x] **PL-0254** Generate revolved Design Model for axisymmetric bottle/jar. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0254_CHATGPT_AUDIT_V01.md
- [x] **PL-0255** Fit non-circular but symmetric body using stacked cross-sections and lofting. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0255_CHATGPT_AUDIT_V01.md
- [x] **PL-0256** Add front/back and left/right symmetry constraints with user toggle. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0256_CHATGPT_AUDIT_V01.md
- [x] **PL-0257** Calculate scan-to-design deviation and expose problem regions. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0257_CHATGPT_AUDIT_V01.md
- [x] **PL-0258** Allow user to edit height/width/depth while maintaining parameter relationships. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0258_CHATGPT_AUDIT_V01.md
- [x] **PL-0259** Allow direct profile/cross-section control-point editing. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0259_CHATGPT_AUDIT_V01.md
- [x] **PL-0260** Save fitting preset and parameters independently of the raw scan. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0260_CHATGPT_AUDIT_V01.md

## Sprint M11-S03 - Caps and closures V1

- [x] **PL-0261** Separate cap/closure from body when scan evidence allows. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0261_CHATGPT_AUDIT_V01.md
- [x] **PL-0262** Fit basic cylindrical screw-cap exterior. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0262_CHATGPT_AUDIT_V01.md
- [x] **PL-0263** Fit flip-top/simple closure exterior as an editable component. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0263_CHATGPT_AUDIT_V01.md
- [x] **PL-0264** Define neck/closure mating reference planes and axes. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0264_CHATGPT_AUDIT_V01.md
- [x] **PL-0265** Add cap visibility/replacement workflow. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0265_CHATGPT_AUDIT_V01.md
- [x] **PL-0266** Add closure dimensions to measurement report. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0266_CHATGPT_AUDIT_V01.md
- [x] **PL-0267** Validate bottle/cap assembly transforms on export. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0267_CHATGPT_AUDIT_V01.md

---

# M12 - Advanced Packaging Geometry

## Sprint M12-S01 - Jerrycans and handles

- [x] **PL-0268** Implement asymmetric/symmetric jerrycan body fitting from stacked cross-sections. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0268_CHATGPT_AUDIT_V01.md
- [x] **PL-0269** Detect handle-void candidate and isolate it from body silhouette. **BLOCKED_BY_GLOBAL_SUITE_DETERMINISM:** implementation retained at `c6f935fc0308256af528cc596ff01e55d3242763`; close via M12 remediation/continuation V02. Audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0269_CHATGPT_AUDIT_V01.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0269_CHATGPT_AUDIT_V02.md
- [x] **PL-0270** Model handle opening as editable constrained feature rather than baked scan triangles. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0270_CHATGPT_AUDIT_V01.md
- [x] **PL-0271** Implement local grip/indent feature representation. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0271_CHATGPT_AUDIT_V01.md
- [x] **PL-0272** Add cage/freeform deformation layer for details not captured by simple parameters. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0272_CHATGPT_AUDIT_V01.md
- [x] **PL-0273** Constrain cage edits to preserve key dimensions and symmetry when enabled. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0273_CHATGPT_AUDIT_V01.md
- [x] **PL-0274** Quantify Design Model deviation around handles/indentations. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0274_CHATGPT_AUDIT_V01.md
- [x] **PL-0275** Validate 2 L/5 L style jerrycan benchmark objects. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0275_CHATGPT_AUDIT_V01.md

## Sprint M12-S02 - Trigger/pump assemblies

- [x] **PL-0276** Define assembly graph for body, closure, trigger/pump and dip tube. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0276_CHATGPT_AUDIT_V01.md
- [x] **PL-0277** Support importing a reusable trigger/pump library component. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0277_CHATGPT_AUDIT_V01.md
- [x] **PL-0278** Align library closure component to detected neck reference. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0278_CHATGPT_AUDIT_V01.md
- [x] **PL-0279** Model dip tube as parameterized length/diameter path. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0279_CHATGPT_AUDIT_V01.md
- [x] **PL-0280** Add assembly collision/basic interference diagnostics. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0280_CHATGPT_AUDIT_V01.md
- [x] **PL-0281** Allow swapping trigger/pump variants without modifying bottle geometry. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0281_CHATGPT_AUDIT_V01.md
- [x] **PL-0282** Export assembly hierarchy to formats that support components. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0282_CHATGPT_AUDIT_V01.md

## Sprint M12-S03 - Tubes, sachets and flexible packs

- [x] **PL-0283** Define tube parametric family: body, shoulder, neck, cap and crimp. **V02 ACTIVE:** standalone Design Geometry authority resolution + tube family. https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0283_CODEX_PROMPT_V02.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0283_CHATGPT_AUDIT_V02.md
- [x] **PL-0284** Implement tube fitting from scan/reference dimensions. **V02 AUTHORIZED AFTER PREDECESSOR:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0284_CODEX_PROMPT_V02.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0284_CHATGPT_AUDIT_V02.md
- [x] **PL-0285** Define sachet/pouch simplified Design Model focused on artwork and overall dimensions rather than mold-grade surfaces. **V02 AUTHORIZED AFTER PREDECESSOR:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0285_CODEX_PROMPT_V02.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0285_CHATGPT_AUDIT_V02.md
- [x] **PL-0286** Implement front/back flexible-pack surface and seal-zone representation. **V02 AUTHORIZED AFTER PREDECESSOR:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0286_CODEX_PROMPT_V02.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0286_CHATGPT_AUDIT_V02.md
- [x] **PL-0287** Explicitly mark flexible-pack geometry as visualization/design geometry with appropriate accuracy limitations. **V02 AUTHORIZED AFTER PREDECESSOR:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0287_CODEX_PROMPT_V02.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0287_CHATGPT_AUDIT_V02.md
- [x] **PL-0288** Add package-family selection and conversion safeguards. **V02 AUTHORIZED AFTER PREDECESSOR:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0288_CODEX_PROMPT_V02.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0288_CHATGPT_AUDIT_V02.md

---

# M13 - CAD/BREP & Engineering Export

## Sprint M13-S01 - OpenCascade integration

- [x] **PL-0289** Benchmark/select supported Python OpenCascade binding for Windows packaging. **ACTIVE BATCH CHILD:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0289_CODEX_PROMPT_V01.md **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0289_CHATGPT_AUDIT_V01.md
- [x] **PL-0290** Implement CAD capability adapter and version diagnostics. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0290_CHATGPT_AUDIT_V01.md
- [x] **PL-0291** Convert profile/revolve Design Models into OpenCascade BREP solids. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0291_CHATGPT_AUDIT_V01.md
- [x] **PL-0292** Convert lofted cross-section Design Models into BREP solids. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0292_CHATGPT_AUDIT_V01.md
- [x] **PL-0293** Implement boolean feature support needed for handle openings and simple indentations. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0293_CHATGPT_AUDIT_V01.md
- [x] **PL-0294** Validate solid topology and report non-manifold/invalid BREP failures. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0294_CHATGPT_AUDIT_V01.md
- [x] **PL-0295** Preserve named feature references where practical across regeneration. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0295_CHATGPT_AUDIT_V01.md
- [x] **PL-0296** Tessellate BREP back to preview mesh with controlled tolerance. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0296_CHATGPT_AUDIT_V01.md

## Sprint M13-S02 - STEP/STL/mesh export

- [x] **PL-0297** Export Design Model/assembly to STEP with millimetre units. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CHATGPT_AUDIT_V01.md
- [x] **PL-0298** Export printable STL with explicit unit handling and mesh-quality options. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0298_CHATGPT_AUDIT_V01.md
- [x] **PL-0299** Export OBJ and GLB from Design Model with part naming. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CHATGPT_AUDIT_V02.md
- [x] **PL-0300** Add export manifest recording source project, revision, scale and software versions. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0300_CHATGPT_AUDIT_V01.md
- [x] **PL-0301** Add round-trip validation that reopens exported STEP and rechecks bounding dimensions. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0301_CHATGPT_AUDIT_V01.md
- [x] **PL-0302** Add export UI with clear distinction between Scan Mesh and editable Design Model. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0302_CHATGPT_AUDIT_V01.md

## Sprint M13-S03 - Technical drawings

- [x] **PL-0303** Generate front/side/top orthographic views from Design Model. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0303_CHATGPT_AUDIT_V01.md
- [x] **PL-0304** Generate section views at user-selected heights/planes. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0304_CHATGPT_AUDIT_V01.md
- [x] **PL-0305** Add dimension annotations for overall H/W/D, neck and selected features. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0305_CHATGPT_AUDIT_V01.md
- [x] **PL-0306** Add title block with package ID, revision, units and disclaimer. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0306_CHATGPT_AUDIT_V01.md
- [x] **PL-0307** Export drawing to SVG and DXF. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0307_CHATGPT_AUDIT_V01.md
- [x] **PL-0308** Export PDF drawing if a stable PDF path is available without compromising vector source. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0308_CHATGPT_AUDIT_V01.md
- [x] **PL-0309** Validate drawing dimensions against Design Model numerical values. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0309_CHATGPT_AUDIT_V01.md

---

# M14 - Labels, Materials & Rendering

## Sprint M14-S01 - Label zones and dielines

- [x] **PL-0310** Define Label Zone entity independent of artwork image. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0310_CHATGPT_AUDIT_V01.md
- [x] **PL-0311** Implement manual front/back/wrap Label Zone placement on Design Model. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0311_CHATGPT_AUDIT_V01.md
- [x] **PL-0312** Implement curvature/slope analysis to suggest label-safe regions. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0312_CHATGPT_AUDIT_V02.md
- [x] **PL-0313** Generate 2D label boundary/dieline in millimetres. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0313_CHATGPT_AUDIT_V02.md
- [x] **PL-0314** Add safe-margin/bleed metadata. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0314_CHATGPT_AUDIT_V01.md
- [x] **PL-0315** Import SVG/PNG artwork and map it non-destructively to a Label Zone. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0315_CHATGPT_AUDIT_V01.md
- [x] **PL-0316** Support front/back artwork variants and wrap labels. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0316_CHATGPT_AUDIT_V01.md
- [x] **PL-0317** Export label-dieline SVG with scale-verification marks. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0317_CHATGPT_AUDIT_V01.md

## Sprint M14-S02 - Material system

- [x] **PL-0318** Define material-library schema for HDPE, PET, PP and other packaging materials. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0318_CHATGPT_AUDIT_V01.md
- [x] **PL-0319** Separate geometry material from product liquid/content appearance. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0319_CHATGPT_AUDIT_V01.md
- [x] **PL-0320** Implement PBR parameters: base color, roughness, transmission/opacity, IOR and normal detail where supported. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0320_CHATGPT_AUDIT_V01.md
- [x] **PL-0321** Create starter materials: natural HDPE, white HDPE, clear PET, colored PET, PP cap. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0321_CHATGPT_AUDIT_V01.md
- [x] **PL-0322** Add PCR metadata and visual variants without implying certified material properties. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0322_CHATGPT_AUDIT_V01.md
- [x] **PL-0323** Persist material assignments per component. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0323_CHATGPT_AUDIT_V01.md

## Sprint M14-S03 - Blender rendering

- [x] **PL-0324** Integrate Blender headless executable discovery and version probe. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0324_CHATGPT_AUDIT_V01.md
- [x] **PL-0325** Create deterministic Blender scene-generation script from PackLab project data. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0325_CHATGPT_AUDIT_V01.md
- [x] **PL-0326** Import Design Model, materials and artwork into render scene. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0326_CHATGPT_AUDIT_V02.md
- [x] **PL-0327** Create standard studio-lighting/camera presets for packaging mockups. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0327_CHATGPT_AUDIT_V01.md
- [x] **PL-0328** Render transparent-background product image. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0328_CHATGPT_AUDIT_V01.md
- [x] **PL-0329** Render front/three-quarter/back standard views. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0329_CHATGPT_AUDIT_V01.md
- [x] **PL-0330** Export GLB with materials/textures for lightweight viewing. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0330_CHATGPT_AUDIT_V01.md
- [x] **PL-0331** Record render settings and Blender version for reproducibility. **AUDITED_PASS:** https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0331_CHATGPT_AUDIT_V01.md

---

# M15 - Kenya Packaging Library

## Sprint M15-S01 - Digital-twin metadata

- [ ] **PL-0332** Define Packaging Asset schema with internal ID, family, nominal volume, supplier, material, weight and neck/closure metadata.
- [ ] **PL-0333** Separate factual supplier fields from PackLab-estimated fields and label provenance.
- [ ] **PL-0334** Link one Packaging Asset to raw Scan(s), one promoted Scan Master and multiple Design Model revisions.
- [ ] **PL-0335** Link compatible caps/triggers/pumps as reusable components.
- [ ] **PL-0336** Link multiple POVU artworks/SKUs to one physical geometry.
- [ ] **PL-0337** Add attachments for supplier drawings, quotations and notes without forcing them into Git.
- [ ] **PL-0338** Add audit trail for asset-metadata edits.

## Sprint M15-S02 - Library UI

- [ ] **PL-0339** Implement grid/list library browser with thumbnail.
- [ ] **PL-0340** Implement search by ID/name/supplier/package family.
- [ ] **PL-0341** Implement filters for volume, material, closure and status.
- [ ] **PL-0342** Implement asset-detail page with 3D preview, dimensions, revisions and linked artwork.
- [ ] **PL-0343** Implement duplicate/variant relationship display.
- [ ] **PL-0344** Add Create new SKU from existing geometry workflow.
- [ ] **PL-0345** Add library backup/export and restore validation.
- [ ] **PL-0346** Add thumbnails/contact-sheet export for supplier discussions.

---

# M16 - CI/CD, Signing & Distribution

## Sprint M16-S01 - GitHub Actions Windows

- [ ] **PL-0347** Create Windows CI workflow for Python lint/type/unit tests.
- [ ] **PL-0348** Add cached dependency installation without caching secrets or mutable reconstruction outputs.
- [ ] **PL-0349** Add Windows PackLab Studio build job.
- [ ] **PL-0350** Produce versioned PackLabStudio.exe/installer artifact.
- [ ] **PL-0351** Add smoke test against packaged Windows application.
- [ ] **PL-0352** Add artifact-retention policy suitable for a public repository.
- [ ] **PL-0353** Ensure CI can run without proprietary sample scans.

## Sprint M16-S02 - GitHub Actions macOS/iOS

- [ ] **PL-0354** Create macOS GitHub Actions workflow for Swift build and unit tests.
- [ ] **PL-0355** Resolve/cache Swift Package Manager dependencies including NextLevel.
- [ ] **PL-0356** Build simulator target on every relevant change with no signing secrets.
- [ ] **PL-0357** Create device archive job for PackLab Capture.
- [ ] **PL-0358** Implement secret-safe optional code-signing path for a signed IPA when credentials/provisioning are available.
- [ ] **PL-0359** Implement free-first fallback artifact path when CI signing is unavailable, documenting Windows-side sideload/sign route.
- [ ] **PL-0360** Ensure no Apple certificate/profile/private key is ever committed to the public repository.
- [ ] **PL-0361** Publish build artifacts with clear signed/unsigned provenance.
- [ ] **PL-0362** Document exact iPhone 16 installation/reinstallation procedure.

## Sprint M16-S03 - Releases

- [ ] **PL-0363** Define coordinated release numbering across Studio, Capture and PackScan schema.
- [ ] **PL-0364** Add release manifest with dependency versions and schema compatibility.
- [ ] **PL-0365** Add changelog-generation rules tied to task IDs.
- [ ] **PL-0366** Create release checklist requiring both Windows and iOS audit passes.
- [ ] **PL-0367** Add rollback instructions for incompatible Capture/Studio versions.
- [ ] **PL-0368** Create first internal V0.1 release only after acceptance gates in M17 are satisfied.

---

# M17 - Validation, Benchmarking & Reliability

## Sprint M17-S01 - Golden datasets

- [ ] **PL-0369** Create small redistributable synthetic/public golden dataset for CI.
- [ ] **PL-0370** Create private local Kenya benchmark dataset outside Git for real packaging validation.
- [ ] **PL-0371** Store ground-truth dimensions and capture conditions for benchmark objects.
- [ ] **PL-0372** Store expected reconstruction metrics with tolerance bands.
- [ ] **PL-0373** Store expected parametric-fit metrics with tolerance bands.
- [ ] **PL-0374** Add regression harness that compares new engine results to benchmark ranges.

## Sprint M17-S02 - Failure and recovery testing

- [ ] **PL-0375** Test low-texture white HDPE failure behavior.
- [ ] **PL-0376** Test glossy PET failure behavior.
- [ ] **PL-0377** Test transparent PET limitation/warning behavior.
- [ ] **PL-0378** Test missing-capture sector and targeted-recapture workflow.
- [ ] **PL-0379** Test corrupt .packscan import and quarantine.
- [ ] **PL-0380** Test interrupted COLMAP/OpenMVS job and resume/retry.
- [ ] **PL-0381** Test disk-full/low-space handling.
- [ ] **PL-0382** Test application crash/restart with project recovery.
- [ ] **PL-0383** Test external-engine missing/wrong-version diagnostics.
- [ ] **PL-0384** Test project migration across schema/app versions.

## Sprint M17-S03 - V1 acceptance gates

- [ ] **PL-0385** Demonstrate iPhone 16 -> .packscan -> Windows import end-to-end.
- [ ] **PL-0386** Demonstrate COLMAP -> OpenMVS textured Scan Master on at least three package families.
- [ ] **PL-0387** Demonstrate real-scale dimensions within documented V1 tolerance.
- [ ] **PL-0388** Demonstrate editable parametric bottle Design Model fitted to Scan Master.
- [ ] **PL-0389** Demonstrate editable jerrycan/handle Design Model at accepted deviation.
- [ ] **PL-0390** Demonstrate STEP export round-trip with dimensional consistency.
- [ ] **PL-0391** Demonstrate label dieline + artwork + rendered product mockup.
- [ ] **PL-0392** Demonstrate one geometry reused by multiple POVU SKUs.
- [ ] **PL-0393** Demonstrate Windows GitHub Actions artifact and macOS/iOS Actions artifact.
- [ ] **PL-0394** Complete security/secrets audit of public repository.
- [ ] **PL-0395** Freeze V1 limitations and not-for-direct-mold-manufacture statement.

---

# M18 - Kenya Production Onboarding

## Sprint M18-S01 - Scan station

- [ ] **PL-0396** Define low-cost physical scan-station bill of materials: turntable, matte background, lights, tripod/phone mount and calibration mat.
- [ ] **PL-0397** Define repeatable lighting positions/distances and camera distance.
- [ ] **PL-0398** Evaluate cross-polarized lighting option for glossy packaging.
- [ ] **PL-0399** Define safe removable scanning-treatment procedure for difficult reflective/transparent samples when acceptable.
- [ ] **PL-0400** Create printed operator checklist for object cleaning, label handling, reflections and capture sequence.
- [ ] **PL-0401** Validate scan-station repeatability across multiple sessions.

## Sprint M18-S02 - Kenya library population

- [ ] **PL-0402** Define canonical naming/ID scheme for Kenya packaging assets.
- [ ] **PL-0403** Inventory all physical bottles, jerrycans, jars, tubes, sachets, caps, triggers and pumps to digitize.
- [ ] **PL-0404** Prioritize inventory by POVU launch relevance and reuse across SKUs.
- [ ] **PL-0405** Digitize first 1 L bottle as production reference asset.
- [ ] **PL-0406** Digitize first 5 L jerrycan as production reference asset.
- [ ] **PL-0407** Digitize first trigger bottle/assembly as production reference asset.
- [ ] **PL-0408** Digitize first tube as production reference asset.
- [ ] **PL-0409** Digitize representative cap/closure library.
- [ ] **PL-0410** Attach verified dimensions, material/supplier metadata and artwork to each accepted asset.
- [ ] **PL-0411** Run duplicate-geometry review so one physical package is not rescanned for every SKU.
- [ ] **PL-0412** Back up accepted Kenya library and verify restore on a clean environment.

## Sprint M18-S03 - Operating procedure

- [ ] **PL-0413** Create SOP: receive physical sample -> clean -> calibrate -> capture -> reconstruct -> fit -> audit -> publish to library.
- [ ] **PL-0414** Create rescan/recapture decision tree based on QA metrics.
- [ ] **PL-0415** Create supplier-change revision process so old geometry remains traceable.
- [ ] **PL-0416** Create artwork-only change process that reuses geometry.
- [ ] **PL-0417** Create packaging-geometry change process requiring a new scan/design revision.
- [ ] **PL-0418** Define backup cadence and off-machine copy policy for irreplaceable scans.
- [ ] **PL-0419** Complete first full Kenya production run using the SOP without developer intervention.

---

# M19 - Advanced Automation Backlog

> These tasks are intentionally after stable V1. Do not pull them forward unless an ADR explicitly changes priorities.

## Sprint M19-S01 - AI-assisted geometry

- [ ] **PL-0420** Research learned feature recognition for shoulder/base/handle segmentation.
- [ ] **PL-0421** Add optional AI suggestion layer for package-family classification.
- [ ] **PL-0422** Add optional AI proposal for parametric-section placement, requiring user confirmation.
- [ ] **PL-0423** Add fit-parameter optimizer constrained by measured dimensions and scan deviation.
- [ ] **PL-0424** Add anomaly detector that identifies likely reconstruction defects before fitting.

## Sprint M19-S02 - Capture automation

- [ ] **PL-0425** Prototype Bluetooth-controlled turntable integration.
- [ ] **PL-0426** Synchronize turntable-angle events into PackScan metadata.
- [ ] **PL-0427** Add automatic multi-ring scan-station capture recipe.
- [ ] **PL-0428** Add adaptive angle density based on geometry complexity.
- [ ] **PL-0429** Add remote iPhone capture control from Windows Studio on trusted LAN.

## Sprint M19-S03 - Advanced visualization and reporting

- [ ] **PL-0430** Add AR preview of edited package geometry on iPhone.
- [ ] **PL-0431** Add side-by-side/ghosted Scan Master vs Design Model review mode.
- [ ] **PL-0432** Add shelf-lineup visualization for multiple POVU SKUs.
- [ ] **PL-0433** Add supplier-comparison report for alternative packages.
- [ ] **PL-0434** Add automated packaging technical-dossier export after V1 data model is stable.

## Sprint M19-S04 - Experimental reconstruction and AI visual reference

- [ ] **PL-0435** Add an optional AI Visual Reference lane for generated object completion/visualization with hard isolation from measurement and Scan Master authority. **Mandatory pre-read:** https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0435_AI_VISUAL_REFERENCE_LANE.md
- [ ] **PL-0436** Prototype a commercially license-cleared neural reconstruction backend behind the PL-0163 contract; original non-commercial VGGT checkpoints are forbidden for commercial PackLab use. **Mandatory pre-read:** https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0436_COMMERCIAL_NEURAL_RECONSTRUCTION_RESEARCH.md
- [ ] **PL-0437** Run a controlled COLMAP/OpenMVS vs neural-backend benchmark on packaging classes with physical ground truth before any production-default change. **Mandatory pre-read:** https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0437_RECONSTRUCTION_BACKEND_BENCHMARK.md

---

# Execution Rules

1. GitHub `Sekiph82/PackLab` branch `main` is repository truth. Root `TASKS.md` is the only live H!veAI/project-status tracker.
2. ChatGPT is the sole writer of task lifecycle/progress/closure state in this file.
3. Codex reads this file to confirm authorization but must not edit it.
4. Exact implementation scope is frozen in `coordination/sessions/<CYCLE_ID>/CODEX_PROMPT_VNN.md` with matching `CHATGPT_AUDIT_CRITERIA_VNN.md`.
5. Codex implements only that frozen scope, runs every required check, writes the matching `CODEX_LOG_VNN.md`, commits/pushes authorized changes, returns `AWAITING_AUDIT`, and stops.
6. ChatGPT independently audits actual GitHub source/diff/evidence and writes the matching `CHATGPT_AUDIT_VNN.md`.
7. After every Codex log/audit cycle, ChatGPT updates this file to the audited truth whether the result is PASS, CHANGES_REQUIRED, BLOCKED, or OWNER_REQUIRED.
8. Only `AUDITED_PASS` permits ChatGPT to check the matching task `[x]` and advance the H!veAI frontier.
9. A failed audit keeps the task unchecked and produces the next versioned remediation prompt/criteria in the same cycle; prior evidence is never overwritten.
10. Session artifacts, `AUDIT.md`, `handoff.md`, `AUDIT_INDEX.md`, dashboards, and historical `.hiveai/*` files are evidence/guidance only and never competing live trackers.
11. Work proceeds in task-ID order unless the owner explicitly reprioritizes or an audited ADR records an approved dependency-safe exception.
12. No secret, private key, Apple credential, provisioning private material, private Kenya scan, confidential supplier asset, or other protected data may be committed to this public repository.
13. Owner-authorized milestone batches are permitted only when the Project Status block explicitly names the batch and points to a frozen master prompt/criteria. Each child PL task must retain separate prompt, criteria, implementation/evidence boundary and Codex log.
14. During an authorized milestone batch Codex may continue sequential child tasks without interim ChatGPT audit only while each child is validation-green and no STOP condition exists. Codex never marks child tasks complete, never edits this tracker, and must stop before the next milestone.
15. ChatGPT independently audits every batch child and only then writes the milestone audit and updates this tracker to the audited truth.
16. A task line containing `Mandatory pre-read` creates a binding implementation contract: Codex/Claude must read that linked file in full before material work, and the frozen prompt/audit criteria must preserve its architecture, authority, licensing, provenance and test requirements.
