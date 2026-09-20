# PackLab — Canonical GitHub Task State

This root TASKS.md is the only authoritative project-status tracker consumed by H!veAI. GitHub repository metadata and the latest commit are the remaining project-truth inputs. Hidden .hiveai control-plane files are historical only and are not read for current project state.

## Project Status

- Current Milestone: M00
- Current Sprint: M00-S01/S02 — Remaining M00 governance batch
- Current Task: M00-BATCH-001 — Complete remaining M00 tasks PL-0006 through PL-0018.
- Current Task Status: READY
- Next Task/Action: Execute the owner-authorized M00 milestone batch from https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_PROMPT_V01.md against https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md. Codex executes PL-0006 through PL-0018 sequentially using the frozen child prompts/criteria in https://github.com/Sekiph82/PackLab/tree/main/coordination/sessions/M00-C001, publishes one child log per task plus the master log, returns `AWAITING_MILESTONE_AUDIT`, and stops before M01.
- Required Actor: CODEX
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
| M00 | Governance & Architecture | Reproducible rules, repo contract, AI workflow | [ ] |
| M01 | Monorepo & Development Foundations | iOS + Windows project skeletons, local tooling | [ ] |
| M02 | PackScan Data Contract & Calibration | Versioned .packscan format and real-world scale contract | [ ] |
| M03 | iOS Capture Foundation | SwiftUI/NextLevel/ARKit app runs on iPhone 16 | [ ] |
| M04 | Guided Capture & Quality Intelligence | Reliable, guided, high-resolution packaging capture | [ ] |
| M05 | Transfer & Ingest | .packscan moves safely from iPhone to Windows | [ ] |
| M06 | PackLab Studio Foundation | PySide6 desktop shell and project lifecycle | [ ] |
| M07 | Photogrammetry Reconstruction | COLMAP -> OpenMVS textured scan pipeline | [ ] |
| M08 | Segmentation, Masks & Reconstruction QA | Object-only reconstruction with quality diagnostics | [ ] |
| M09 | Scale, Calibration & Measurement | Real-size geometry with measurable accuracy | [ ] |
| M10 | Mesh Processing & Scan Master | Clean, aligned, optimized reference scan assets | [ ] |
| M11 | Parametric Geometry Engine V1 | Editable bottles, jars, caps and cylindrical packaging | [ ] |
| M12 | Advanced Packaging Geometry | Jerrycans, grips, asymmetry, triggers, pumps and tubes | [ ] |
| M13 | CAD/BREP & Engineering Export | Editable solids, STEP/DXF/SVG/STL exports | [ ] |
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
- [ ] **PL-0006** Define semantic versioning rules for PackLab Studio, PackLab Capture and PackScan schema.
- [ ] **PL-0007** Define source-control conventions: branches, commits, task IDs, pull-request naming and generated-file policy.
- [ ] **PL-0008** Define secrets policy so Apple credentials, signing certificates and tokens never enter Git.
- [ ] **PL-0009** Define Definition of Done, audit gates and evidence requirements for every task.
- [ ] **PL-0010** Create project risk register with technical, licensing, capture-quality, signing and hardware risks.

## Sprint M00-S02 - AI execution protocol

- [ ] **PL-0011** Validate the canonical session workflow: TASKS.md -> CODEX_PROMPT/AUDIT_CRITERIA -> CODEX_LOG -> CHATGPT_AUDIT -> ChatGPT TASKS.md update.
- [ ] **PL-0012** Define builder-AI responsibilities and forbidden actions.
- [ ] **PL-0013** Define independent auditor-AI responsibilities, minimum checks and PASS/FAIL criteria.
- [ ] **PL-0014** Define audit evidence format including commands, test output, inspected files and residual risks.
- [ ] **PL-0015** Define Codex implementation-log and `AWAITING_AUDIT` handoff format for current task, changed files, tests, blockers and next audit action.
- [ ] **PL-0016** Add protocol for failed audits: reopen same task, preserve checkbox, remediate findings, re-audit.
- [ ] **PL-0017** Add protocol for blocked tasks and dependency escalation without silently skipping work.
- [ ] **PL-0018** Add protocol for architecture changes that require an ADR before implementation.

---

# M01 - Monorepo & Development Foundations

## Sprint M01-S01 - Base monorepo

- [ ] **PL-0019** Create top-level folders: apps/ios-capture, apps/windows-studio, core, schemas, docs, tools, tests, assets.
- [ ] **PL-0020** Add root README with product mission, architecture diagram, quick-start and repository map.
- [ ] **PL-0021** Add Windows/macOS/Linux-safe .gitignore covering Python, Xcode, SwiftPM, Blender, COLMAP/OpenMVS outputs and local scans.
- [ ] **PL-0022** Add .editorconfig and line-ending policy to prevent Windows/macOS churn.
- [ ] **PL-0023** Define generated-artifact directories and Git LFS policy for sample images/meshes that genuinely belong in source control.
- [ ] **PL-0024** Create local environment diagnostics script that reports OS, CPU, RAM, GPU, CUDA availability, Python and external tool versions.
- [ ] **PL-0025** Create root task-runner strategy for common bootstrap, test, lint and build commands.
- [ ] **PL-0026** Establish local cache directories outside tracked source for reconstruction intermediates.

## Sprint M01-S02 - Python/Windows foundation

- [ ] **PL-0027** Choose and pin a Python version after compatibility validation across PySide6/Open3D/OpenCV/PyTorch/OpenCascade binding.
- [ ] **PL-0028** Create Python package/workspace layout for PackLab core and Windows Studio.
- [ ] **PL-0029** Add dependency locking and reproducible Windows bootstrap.
- [ ] **PL-0030** Configure Ruff/formatter/type-check strategy and baseline configuration.
- [ ] **PL-0031** Configure pytest with unit/integration/slow-test markers.
- [ ] **PL-0032** Add structured logging with session/task correlation IDs.
- [ ] **PL-0033** Add application configuration system with user config, project config and environment overrides.
- [ ] **PL-0034** Add capability registry for optional engines such as CUDA, COLMAP, OpenMVS, Blender and OpenCascade.
- [ ] **PL-0035** Add safe subprocess runner with cancellation, timeout, stdout/stderr streaming and exit-code capture.

## Sprint M01-S03 - Swift/iOS foundation

- [ ] **PL-0036** Create SwiftUI iOS application project targeting the user's iPhone 16 and a documented minimum iOS version.
- [ ] **PL-0037** Add NextLevel through Swift Package Manager with a pinned tested version.
- [ ] **PL-0038** Add project modules/services for Camera, AR Tracking, Motion, Capture Quality, Storage and Transfer.
- [ ] **PL-0039** Configure Swift 6 strict concurrency and project warning policy.
- [ ] **PL-0040** Add camera/photo-library/local-network permission descriptions actually required by the product.
- [ ] **PL-0041** Add iOS logging and diagnostics export.
- [ ] **PL-0042** Create simulator-safe fallbacks so CI can build without physical camera hardware.
- [ ] **PL-0043** Add unit-test target and initial smoke test.

---

# M02 - PackScan Data Contract & Calibration

## Sprint M02-S01 - PackScan schema

- [ ] **PL-0044** Specify .packscan as a versioned ZIP container with deterministic directory layout.
- [ ] **PL-0045** Define manifest.json JSON Schema including schema version, capture ID, device, mode, timestamps and checksums.
- [ ] **PL-0046** Define per-photo metadata schema: filename, orientation, focal data, exposure, ISO, white balance, dimensions and capture sequence.
- [ ] **PL-0047** Define camera-intrinsics representation including calibration matrix, reference dimensions and lens identity.
- [ ] **PL-0048** Define ARKit pose representation with coordinate-system conventions and confidence/availability markers.
- [ ] **PL-0049** Define CoreMotion metadata representation and timestamp synchronization rules.
- [ ] **PL-0050** Define optional object-mask representation and image/mask pixel-coordinate contract.
- [ ] **PL-0051** Define calibration-marker observations and real-world unit representation in millimetres.
- [ ] **PL-0052** Define capture-mode metadata for Freehand, Guided Orbit and Turntable modes.
- [ ] **PL-0053** Define preview, thumbnail and diagnostics payloads.
- [ ] **PL-0054** Define SHA-256 integrity checks and partial/corrupt package handling.
- [ ] **PL-0055** Create schema validation fixtures: valid, old-version, future-version, corrupt and incomplete samples.
- [ ] **PL-0056** Implement Python PackScan reader/writer/validator.
- [ ] **PL-0057** Implement Swift PackScan writer compatible with the same fixtures.
- [ ] **PL-0058** Add cross-language contract tests ensuring Swift output validates in Python.

## Sprint M02-S02 - Calibration system

- [ ] **PL-0059** Select marker family and IDs for PackLab calibration mat using OpenCV-supported AprilTag/ArUco dictionaries.
- [ ] **PL-0060** Design printable A4/A3 PackLab calibration mat with precise reference distances and print-at-100% instructions.
- [ ] **PL-0061** Add printed-mat verification procedure using ruler/caliper measurements before first use.
- [ ] **PL-0062** Implement marker detection and corner refinement in OpenCV.
- [ ] **PL-0063** Implement scale estimation from known marker geometry.
- [ ] **PL-0064** Implement calibration confidence score and rejection thresholds.
- [ ] **PL-0065** Define camera-calibration procedure for iPhone main camera when higher accuracy than EXIF/intrinsics requires it.
- [ ] **PL-0066** Store calibration profile by device/lens/resolution and invalidate incompatible profiles.
- [ ] **PL-0067** Build synthetic calibration tests with known ground-truth dimensions.
- [ ] **PL-0068** Build first physical calibration benchmark and record measured error.

---

# M03 - iOS Capture Foundation

## Sprint M03-S01 - Camera control

- [ ] **PL-0069** Integrate NextLevel preview into SwiftUI using a controlled UIKit bridge where required.
- [ ] **PL-0070** Enumerate iPhone 16 rear-camera devices and select the intended main lens deterministically.
- [ ] **PL-0071** Implement high-resolution still-photo capture for reconstruction source images.
- [ ] **PL-0072** Preserve original capture metadata without destructive resizing or social-media style processing.
- [ ] **PL-0073** Implement focus control with guided autofocus followed by optional focus lock.
- [ ] **PL-0074** Implement exposure metering and optional exposure lock for consistent image sets.
- [ ] **PL-0075** Implement white-balance stabilization/lock for texture consistency.
- [ ] **PL-0076** Capture and persist camera metadata for every accepted still.
- [ ] **PL-0077** Add camera-error recovery for interruption, permission denial and session restart.
- [ ] **PL-0078** Add thermal/storage/battery warnings before and during long captures.

## Sprint M03-S02 - ARKit & motion tracking

- [ ] **PL-0079** Create ARKit world-tracking session without relying on LiDAR.
- [ ] **PL-0080** Record camera transform and tracking state aligned to capture timestamps.
- [ ] **PL-0081** Record CoreMotion attitude/rotation-rate data with timestamp alignment.
- [ ] **PL-0082** Define app-local coordinate frame and conversion into PackScan coordinates.
- [ ] **PL-0083** Detect AR tracking degradation and surface a user-visible warning.
- [ ] **PL-0084** Implement capture-session reset/relocalization behavior.
- [ ] **PL-0085** Create pose visualizer/debug overlay for development.
- [ ] **PL-0086** Export pose diagnostics for Windows-side analysis.

## Sprint M03-S03 - Capture project lifecycle

- [ ] **PL-0087** Implement New Scan wizard: package name, package type, capture mode and optional notes.
- [ ] **PL-0088** Create scan-session storage with crash-safe incremental writes.
- [ ] **PL-0089** Add photo gallery for accepted frames with delete/retake controls.
- [ ] **PL-0090** Add session resume after app termination.
- [ ] **PL-0091** Add session finalization that validates minimum data before creating .packscan.
- [ ] **PL-0092** Add local scan history with preview, date, package type and export state.
- [ ] **PL-0093** Add safe deletion requiring confirmation and cleaning all associated data.

---

# M04 - Guided Capture & Quality Intelligence

## Sprint M04-S01 - Live quality metrics

- [ ] **PL-0094** Implement frame sharpness metric and calibrate thresholds for packaging capture.
- [ ] **PL-0095** Implement motion-blur warning using frame analysis plus CoreMotion.
- [ ] **PL-0096** Implement exposure/highlight clipping analysis for glossy plastic.
- [ ] **PL-0097** Implement underexposure/shadow clipping analysis.
- [ ] **PL-0098** Implement object-size/framing score so the package fills an appropriate image area.
- [ ] **PL-0099** Implement background-complexity warning for poor photogrammetry setups.
- [ ] **PL-0100** Combine metrics into deterministic per-frame ACCEPT/REJECT decision with explainable reasons.
- [ ] **PL-0101** Log quality metrics for every candidate/accepted frame for later tuning.

## Sprint M04-S02 - Guided orbit capture

- [ ] **PL-0102** Define orbit-coverage model with azimuth/elevation bins around the object.
- [ ] **PL-0103** Implement visual coverage globe/rings showing captured and missing sectors.
- [ ] **PL-0104** Implement automatic still capture when pose, overlap and quality thresholds are satisfied.
- [ ] **PL-0105** Prevent near-duplicate captures that add storage without useful parallax.
- [ ] **PL-0106** Require lower, middle and upper capture rings for standard bottle mode.
- [ ] **PL-0107** Add top/neck detail pass for closures and shoulders.
- [ ] **PL-0108** Add bottom/base detail pass where physically possible.
- [ ] **PL-0109** Add completion score and explicit missing-area guidance.
- [ ] **PL-0110** Add manual-capture override while retaining quality warnings.

## Sprint M04-S03 - Packaging-specific modes

- [ ] **PL-0111** Implement Matte/HDPE capture preset.
- [ ] **PL-0112** Implement Glossy/PET preset emphasizing highlight control and denser coverage.
- [ ] **PL-0113** Implement Transparent packaging warning mode with instructions for temporary scanning treatment/background preparation.
- [ ] **PL-0114** Implement Asymmetric/Jerrycan mode with stronger front/back/handle coverage requirements.
- [ ] **PL-0115** Implement Closure/Cap macro-detail mode.
- [ ] **PL-0116** Implement Turntable mode with angle-indexed capture and object/background masking assumptions.
- [ ] **PL-0117** Add capture protocol screen explaining lighting, matte background, reflections and object preparation per preset.
- [ ] **PL-0118** Add scan-suitability preflight before capture starts.

---

# M05 - Transfer & Ingest

## Sprint M05-S01 - Export from iPhone

- [ ] **PL-0119** Implement .packscan package finalization with checksums and atomic rename.
- [ ] **PL-0120** Implement iOS share-sheet export to Files/iCloud/other installed destinations.
- [ ] **PL-0121** Implement local-network transfer protocol from Capture to PackLab Studio.
- [ ] **PL-0122** Add QR/pairing-code workflow so the iPhone connects to the correct Windows Studio instance.
- [ ] **PL-0123** Encrypt/authenticate local transfer sufficiently to prevent accidental cross-device ingestion.
- [ ] **PL-0124** Support resumable transfer for large scan packages.
- [ ] **PL-0125** Verify checksum after transfer before marking export complete.
- [ ] **PL-0126** Add transfer progress, cancel and retry UI.

## Sprint M05-S02 - Windows ingest

- [ ] **PL-0127** Implement drag/drop and file-picker import for .packscan.
- [ ] **PL-0128** Implement network receiver for paired iPhone transfers.
- [ ] **PL-0129** Validate schema version and checksums before extraction.
- [ ] **PL-0130** Quarantine corrupt/unsupported scans instead of partially importing them.
- [ ] **PL-0131** Create immutable raw-ingest copy so original capture evidence is never silently modified.
- [ ] **PL-0132** Generate import report summarizing images, metadata, calibration and warnings.
- [ ] **PL-0133** Deduplicate imports by capture ID/checksum.
- [ ] **PL-0134** Add ingest tests for interrupted transfer, corrupt ZIP, missing photo and bad manifest.

---

# M06 - PackLab Studio Foundation

## Sprint M06-S01 - PySide6 shell

- [ ] **PL-0135** Create PackLab Studio PySide6 application shell.
- [ ] **PL-0136** Implement main navigation: Library, Capture Inbox, Reconstruction, Editor and Settings.
- [ ] **PL-0137** Create dockable/logical workspace layout suitable for 3D/CAD work.
- [ ] **PL-0138** Implement persistent window/workspace preferences.
- [ ] **PL-0139** Add global job/activity panel for long-running reconstruction work.
- [ ] **PL-0140** Add cancellation and safe shutdown behavior for active subprocesses.
- [ ] **PL-0141** Add crash report/log bundle creation.
- [ ] **PL-0142** Add application update/version information screen without requiring an online service.

## Sprint M06-S02 - Project lifecycle

- [ ] **PL-0143** Define PackLab project directory layout separating raw, working, derived and export data.
- [ ] **PL-0144** Implement New/Open/Close project lifecycle.
- [ ] **PL-0145** Implement project metadata and revision identifiers.
- [ ] **PL-0146** Implement autosave for editable project state.
- [ ] **PL-0147** Implement non-destructive operation history for user edits.
- [ ] **PL-0148** Implement project recovery after interrupted processing.
- [ ] **PL-0149** Add derived-artifact invalidation when upstream inputs change.
- [ ] **PL-0150** Add project portability check that identifies missing external assets.

## Sprint M06-S03 - 3D viewport

- [ ] **PL-0151** Select and document the PySide6-compatible 3D viewport approach after a focused performance spike.
- [ ] **PL-0152** Implement mesh/point-cloud loading and camera orbit/pan/zoom.
- [ ] **PL-0153** Implement world grid, axes and millimetre scale cues.
- [ ] **PL-0154** Implement object selection and visibility toggles for Scan Mesh, Design Model, cap, label and reference geometry.
- [ ] **PL-0155** Implement wireframe/normals/point-cloud debug modes.
- [ ] **PL-0156** Implement screenshot/export preview for audit evidence.
- [ ] **PL-0157** Add large-mesh performance benchmark and viewport LOD strategy.

---

# M07 - Photogrammetry Reconstruction

## Sprint M07-S01 - Engine installation and adapters

- [ ] **PL-0158** Define tested COLMAP version, installation source and license record.
- [ ] **PL-0159** Define tested OpenMVS version, Windows build/binary source and AGPL license record.
- [ ] **PL-0160** Implement COLMAP capability probe and version parser.
- [ ] **PL-0161** Implement OpenMVS capability probe and version parser.
- [ ] **PL-0162** Implement engine executable discovery/configuration with explicit paths and diagnostics.
- [ ] **PL-0163** Create normalized reconstruction job model independent of specific engine command syntax.
- [ ] **PL-0164** Implement per-stage stdout/stderr capture and machine-readable stage result records.
- [ ] **PL-0165** Add reconstruction workspace isolation so retries cannot corrupt the source scan.

## Sprint M07-S02 - COLMAP SfM

- [ ] **PL-0166** Implement photo preprocessing into a COLMAP-safe working set while preserving originals.
- [ ] **PL-0167** Import/use known camera intrinsics when valid and allow COLMAP refinement under controlled rules.
- [ ] **PL-0168** Implement feature-extraction configuration optimized first for packaged consumer goods.
- [ ] **PL-0169** Implement matcher selection for ordered orbit datasets.
- [ ] **PL-0170** Implement sparse mapper stage and capture registered-image statistics.
- [ ] **PL-0171** Detect failed/fragmented sparse models and produce actionable diagnostics.
- [ ] **PL-0172** Export sparse model/cameras in formats needed by OpenMVS and debugging.
- [ ] **PL-0173** Build a tunable reconstruction preset system rather than hardcoding CLI flags.

## Sprint M07-S03 - OpenMVS dense reconstruction

- [ ] **PL-0174** Implement COLMAP-to-OpenMVS scene conversion.
- [ ] **PL-0175** Implement OpenMVS dense point-cloud stage.
- [ ] **PL-0176** Implement OpenMVS mesh-reconstruction stage.
- [ ] **PL-0177** Implement OpenMVS mesh-refinement stage.
- [ ] **PL-0178** Implement OpenMVS texture stage.
- [ ] **PL-0179** Preserve all stage outputs and logs for reproducibility.
- [ ] **PL-0180** Add CPU/GPU-aware presets and memory-safety limits.
- [ ] **PL-0181** Add one-click Reconstruct Scan orchestration across COLMAP and OpenMVS.
- [ ] **PL-0182** Add reconstruction cancellation that leaves the project recoverable.
- [ ] **PL-0183** Convert final textured mesh to PackLab-supported preview/export format without losing the master source.

---

# M08 - Segmentation, Masks & Reconstruction QA

## Sprint M08-S01 - Object segmentation

- [ ] **PL-0184** Define segmentation-backend interface so the model can be replaced without rewriting the pipeline.
- [ ] **PL-0185** Benchmark candidate local segmentation model(s) against bottle, jerrycan, cap and transparent/glossy examples.
- [ ] **PL-0186** Implement selected PyTorch segmentation backend.
- [ ] **PL-0187** Implement mask post-processing: hole filling, edge cleanup and small-component removal.
- [ ] **PL-0188** Add manual mask-correction UI for difficult frames.
- [ ] **PL-0189** Version masks separately from immutable source photos.
- [ ] **PL-0190** Feed masks into COLMAP/OpenMVS where supported and validate coordinate conventions.
- [ ] **PL-0191** Add mask-quality overlays and contact-sheet review.

## Sprint M08-S02 - Photo/reconstruction QA

- [ ] **PL-0192** Build pre-reconstruction QA report using sharpness, exposure, coverage and metadata consistency.
- [ ] **PL-0193** Detect duplicate/near-duplicate photos on Windows as a second safety layer.
- [ ] **PL-0194** Detect inconsistent focal/lens usage and warn before reconstruction.
- [ ] **PL-0195** Calculate registered-photo ratio after COLMAP.
- [ ] **PL-0196** Calculate sparse-cloud connectivity/fragmentation indicators.
- [ ] **PL-0197** Calculate dense-cloud density and surface-coverage indicators.
- [ ] **PL-0198** Detect obvious reconstruction artifacts and floating components.
- [ ] **PL-0199** Produce overall reconstruction confidence with component scores, not a black-box number.
- [ ] **PL-0200** Gate downstream parametric fitting when scan quality is below minimum acceptance thresholds.
- [ ] **PL-0201** Suggest targeted recapture sectors instead of demanding a complete rescan when possible.

---

# M09 - Scale, Calibration & Measurement

## Sprint M09-S01 - Coordinate and scale normalization

- [ ] **PL-0202** Detect calibration markers in source imagery and associate observations with reconstructed cameras.
- [ ] **PL-0203** Estimate global scale from marker geometry and reject inconsistent observations.
- [ ] **PL-0204** Establish canonical PackLab axes: Z up, front direction, millimetres.
- [ ] **PL-0205** Implement object ground-plane/base detection with user override.
- [ ] **PL-0206** Implement automatic upright alignment with manual correction.
- [ ] **PL-0207** Implement front-direction selection and persist it as project metadata.
- [ ] **PL-0208** Apply scale/alignment as non-destructive transform before baking a normalized scan.
- [ ] **PL-0209** Record scale provenance and uncertainty.

## Sprint M09-S02 - Measurement tools

- [ ] **PL-0210** Implement bounding dimensions: height, width and depth.
- [ ] **PL-0211** Implement two-point distance measurement with snapping.
- [ ] **PL-0212** Implement diameter/radius measurement from selected cross-sections.
- [ ] **PL-0213** Implement horizontal cross-section extraction at arbitrary Z.
- [ ] **PL-0214** Implement vertical profile/silhouette extraction.
- [ ] **PL-0215** Implement neck/finish candidate measurement.
- [ ] **PL-0216** Implement capacity-estimation groundwork using watertight interior assumptions, clearly separating estimate from certified volume.
- [ ] **PL-0217** Display measurement uncertainty/confidence where known.
- [ ] **PL-0218** Export measurement report with units and provenance.

## Sprint M09-S03 - Accuracy benchmarks

- [ ] **PL-0219** Define physical benchmark set with caliper-measured ground truth.
- [ ] **PL-0220** Measure dimension error across at least matte bottle, glossy bottle and jerrycan.
- [ ] **PL-0221** Establish V1 acceptance thresholds for overall dimensions and key features.
- [ ] **PL-0222** Add repeat-scan reproducibility test for the same object.
- [ ] **PL-0223** Add calibration-mat print-scale sensitivity test.
- [ ] **PL-0224** Document conditions under which PackLab measurements must not be used for mold manufacturing.

---

# M10 - Mesh Processing & Scan Master

## Sprint M10-S01 - Open3D processing

- [ ] **PL-0225** Integrate Open3D as the primary point-cloud/mesh analysis utility layer.
- [ ] **PL-0226** Remove isolated floating components with configurable safeguards.
- [ ] **PL-0227** Implement normal estimation/orientation repair.
- [ ] **PL-0228** Implement conservative smoothing that preserves packaging edges.
- [ ] **PL-0229** Implement hole detection and report hole size/location before any repair.
- [ ] **PL-0230** Implement optional hole filling with non-destructive before/after versions.
- [ ] **PL-0231** Implement decimation for viewport/proxy meshes while preserving the Scan Master.
- [ ] **PL-0232** Compute geometric statistics needed by later fitting stages.
- [ ] **PL-0233** Create Scan Master asset with provenance pointing back to reconstruction settings.

## Sprint M10-S02 - Scan comparison and revisions

- [ ] **PL-0234** Implement point-cloud/mesh registration for comparing repeat scans.
- [ ] **PL-0235** Implement distance heatmap between scan and fitted Design Model.
- [ ] **PL-0236** Implement cross-section comparison overlay.
- [ ] **PL-0237** Record reconstruction versions and allow switching between them.
- [ ] **PL-0238** Add Promote to Scan Master action with audit metadata.
- [ ] **PL-0239** Prevent downstream Design Model from silently changing when reconstruction is rerun.
- [ ] **PL-0240** Add Scan Master export as PLY/OBJ/GLB plus original texture assets.

---

# M11 - Parametric Geometry Engine V1

## Sprint M11-S01 - Common parametric kernel

- [ ] **PL-0241** Define Design Model parameter graph separate from triangle-mesh data.
- [ ] **PL-0242** Define feature IDs and stable references for body, base, shoulder, neck, finish and cap.
- [ ] **PL-0243** Implement spline/profile primitives with millimetre coordinates.
- [ ] **PL-0244** Implement editable cross-section primitive with symmetry options.
- [ ] **PL-0245** Implement loft/revolve abstraction independent of final CAD backend.
- [ ] **PL-0246** Implement parameter validation and impossible-geometry rejection.
- [ ] **PL-0247** Implement undo/redo command model for parametric edits.
- [ ] **PL-0248** Serialize Design Model parameters in a versioned human-readable project format.
- [ ] **PL-0249** Generate tessellated preview mesh from parameters for interactive viewport use.

## Sprint M11-S02 - Bottle/jar fitting

- [ ] **PL-0250** Detect rotational/symmetry characteristics and choose bottle fitting strategy.
- [ ] **PL-0251** Extract robust vertical body profile from normalized Scan Master.
- [ ] **PL-0252** Fit smoothed profile while preserving shoulder/base transitions.
- [ ] **PL-0253** Detect body, shoulder, neck and base zones with editable boundaries.
- [ ] **PL-0254** Generate revolved Design Model for axisymmetric bottle/jar.
- [ ] **PL-0255** Fit non-circular but symmetric body using stacked cross-sections and lofting.
- [ ] **PL-0256** Add front/back and left/right symmetry constraints with user toggle.
- [ ] **PL-0257** Calculate scan-to-design deviation and expose problem regions.
- [ ] **PL-0258** Allow user to edit height/width/depth while maintaining parameter relationships.
- [ ] **PL-0259** Allow direct profile/cross-section control-point editing.
- [ ] **PL-0260** Save fitting preset and parameters independently of the raw scan.

## Sprint M11-S03 - Caps and closures V1

- [ ] **PL-0261** Separate cap/closure from body when scan evidence allows.
- [ ] **PL-0262** Fit basic cylindrical screw-cap exterior.
- [ ] **PL-0263** Fit flip-top/simple closure exterior as an editable component.
- [ ] **PL-0264** Define neck/closure mating reference planes and axes.
- [ ] **PL-0265** Add cap visibility/replacement workflow.
- [ ] **PL-0266** Add closure dimensions to measurement report.
- [ ] **PL-0267** Validate bottle/cap assembly transforms on export.

---

# M12 - Advanced Packaging Geometry

## Sprint M12-S01 - Jerrycans and handles

- [ ] **PL-0268** Implement asymmetric/symmetric jerrycan body fitting from stacked cross-sections.
- [ ] **PL-0269** Detect handle-void candidate and isolate it from body silhouette.
- [ ] **PL-0270** Model handle opening as editable constrained feature rather than baked scan triangles.
- [ ] **PL-0271** Implement local grip/indent feature representation.
- [ ] **PL-0272** Add cage/freeform deformation layer for details not captured by simple parameters.
- [ ] **PL-0273** Constrain cage edits to preserve key dimensions and symmetry when enabled.
- [ ] **PL-0274** Quantify Design Model deviation around handles/indentations.
- [ ] **PL-0275** Validate 2 L/5 L style jerrycan benchmark objects.

## Sprint M12-S02 - Trigger/pump assemblies

- [ ] **PL-0276** Define assembly graph for body, closure, trigger/pump and dip tube.
- [ ] **PL-0277** Support importing a reusable trigger/pump library component.
- [ ] **PL-0278** Align library closure component to detected neck reference.
- [ ] **PL-0279** Model dip tube as parameterized length/diameter path.
- [ ] **PL-0280** Add assembly collision/basic interference diagnostics.
- [ ] **PL-0281** Allow swapping trigger/pump variants without modifying bottle geometry.
- [ ] **PL-0282** Export assembly hierarchy to formats that support components.

## Sprint M12-S03 - Tubes, sachets and flexible packs

- [ ] **PL-0283** Define tube parametric family: body, shoulder, neck, cap and crimp.
- [ ] **PL-0284** Implement tube fitting from scan/reference dimensions.
- [ ] **PL-0285** Define sachet/pouch simplified Design Model focused on artwork and overall dimensions rather than mold-grade surfaces.
- [ ] **PL-0286** Implement front/back flexible-pack surface and seal-zone representation.
- [ ] **PL-0287** Explicitly mark flexible-pack geometry as visualization/design geometry with appropriate accuracy limitations.
- [ ] **PL-0288** Add package-family selection and conversion safeguards.

---

# M13 - CAD/BREP & Engineering Export

## Sprint M13-S01 - OpenCascade integration

- [ ] **PL-0289** Benchmark/select supported Python OpenCascade binding for Windows packaging.
- [ ] **PL-0290** Implement CAD capability adapter and version diagnostics.
- [ ] **PL-0291** Convert profile/revolve Design Models into OpenCascade BREP solids.
- [ ] **PL-0292** Convert lofted cross-section Design Models into BREP solids.
- [ ] **PL-0293** Implement boolean feature support needed for handle openings and simple indentations.
- [ ] **PL-0294** Validate solid topology and report non-manifold/invalid BREP failures.
- [ ] **PL-0295** Preserve named feature references where practical across regeneration.
- [ ] **PL-0296** Tessellate BREP back to preview mesh with controlled tolerance.

## Sprint M13-S02 - STEP/STL/mesh export

- [ ] **PL-0297** Export Design Model/assembly to STEP with millimetre units.
- [ ] **PL-0298** Export printable STL with explicit unit handling and mesh-quality options.
- [ ] **PL-0299** Export OBJ and GLB from Design Model with part naming.
- [ ] **PL-0300** Add export manifest recording source project, revision, scale and software versions.
- [ ] **PL-0301** Add round-trip validation that reopens exported STEP and rechecks bounding dimensions.
- [ ] **PL-0302** Add export UI with clear distinction between Scan Mesh and editable Design Model.

## Sprint M13-S03 - Technical drawings

- [ ] **PL-0303** Generate front/side/top orthographic views from Design Model.
- [ ] **PL-0304** Generate section views at user-selected heights/planes.
- [ ] **PL-0305** Add dimension annotations for overall H/W/D, neck and selected features.
- [ ] **PL-0306** Add title block with package ID, revision, units and disclaimer.
- [ ] **PL-0307** Export drawing to SVG and DXF.
- [ ] **PL-0308** Export PDF drawing if a stable PDF path is available without compromising vector source.
- [ ] **PL-0309** Validate drawing dimensions against Design Model numerical values.

---

# M14 - Labels, Materials & Rendering

## Sprint M14-S01 - Label zones and dielines

- [ ] **PL-0310** Define Label Zone entity independent of artwork image.
- [ ] **PL-0311** Implement manual front/back/wrap Label Zone placement on Design Model.
- [ ] **PL-0312** Implement curvature/slope analysis to suggest label-safe regions.
- [ ] **PL-0313** Generate 2D label boundary/dieline in millimetres.
- [ ] **PL-0314** Add safe-margin/bleed metadata.
- [ ] **PL-0315** Import SVG/PNG artwork and map it non-destructively to a Label Zone.
- [ ] **PL-0316** Support front/back artwork variants and wrap labels.
- [ ] **PL-0317** Export label-dieline SVG with scale-verification marks.

## Sprint M14-S02 - Material system

- [ ] **PL-0318** Define material-library schema for HDPE, PET, PP and other packaging materials.
- [ ] **PL-0319** Separate geometry material from product liquid/content appearance.
- [ ] **PL-0320** Implement PBR parameters: base color, roughness, transmission/opacity, IOR and normal detail where supported.
- [ ] **PL-0321** Create starter materials: natural HDPE, white HDPE, clear PET, colored PET, PP cap.
- [ ] **PL-0322** Add PCR metadata and visual variants without implying certified material properties.
- [ ] **PL-0323** Persist material assignments per component.

## Sprint M14-S03 - Blender rendering

- [ ] **PL-0324** Integrate Blender headless executable discovery and version probe.
- [ ] **PL-0325** Create deterministic Blender scene-generation script from PackLab project data.
- [ ] **PL-0326** Import Design Model, materials and artwork into render scene.
- [ ] **PL-0327** Create standard studio-lighting/camera presets for packaging mockups.
- [ ] **PL-0328** Render transparent-background product image.
- [ ] **PL-0329** Render front/three-quarter/back standard views.
- [ ] **PL-0330** Export GLB with materials/textures for lightweight viewing.
- [ ] **PL-0331** Record render settings and Blender version for reproducibility.

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