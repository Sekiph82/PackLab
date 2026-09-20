# PackLab Risk Register

## Status and use

This register records risks and current evidence for planning. It is not a
live task tracker, a legal opinion, a performance guarantee, a metrology
certificate, or a claim that a future mitigation is already implemented.
Risk IDs are stable and must remain attached to their evidence history when a
risk changes.

Each risk uses these fields: **ID**, **category**, **description**,
**likelihood**, **impact**, **evidence/status**, **mitigation**,
**contingency**, **owner/actor**, and **related PL task IDs**. Likelihood and
impact are planning judgments (`Low`, `Medium`, or `High`) and must be
reassessed when new evidence arrives.

## Current risk register

| ID | Category | Description | Likelihood | Impact | Evidence/status | Mitigation | Contingency | Owner/actor | Related PL task IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RISK-0001 | Capture quality | Glossy, transparent, reflective, or low-texture packaging can defeat feature matching and produce incomplete or unstable photogrammetry. | High | High | Architecture risk; no broad physical benchmark is claimed. | Future controlled lighting, texture/feature planning, coverage checks, and benchmark evidence. | Flag capture as insufficient and require a revised capture rather than inventing geometry. | Capture owner / later Capture and reconstruction builders | PL-0112, PL-0113, PL-0117, PL-0118, PL-0375, PL-0376, PL-0377 |
| RISK-0002 | Scale/calibration | Visual similarity can coexist with metric-scale or calibration error; an attractive mesh is not dimensional evidence. | Medium | High | `VERSIONING_POLICY.md` and host/device baseline require explicit units and calibration; physical validation is future work. | Record calibration, known dimensions, units, tolerances, and provenance in an authorized measurement workflow. | Report dimensions as unverified and keep the result out of engineering acceptance. | Geometry/measurement owner; owner for physical evidence | PL-0051, PL-0063, PL-0068, PL-0371, PL-0387 |
| RISK-0003 | Device/runtime | The owner’s iPhone 16 Standard is non-LiDAR; ARKit support and runtime behavior can vary by OS, configuration, thermal state, and capture conditions. | Medium | High | Device baseline is owner-declared with official hardware references; runtime availability is not independently guaranteed here. | Check ARKit configuration support at runtime and retain the non-LiDAR photogrammetry path. | Degrade to supported still capture or stop with a diagnostic when runtime capability is unavailable. | Capture builder / owner device tester | PL-0079, PL-0083, PL-0084, PL-0385 |
| RISK-0004 | Host performance | Host GPU/CUDA availability, memory pressure, storage, and long-running reconstruction performance are uncertain. Integrated `AdapterRAM` is not dedicated VRAM and does not prove CUDA capability. | High | Medium | The baseline records an integrated Intel GPU and labels its reported memory conservatively; no CUDA promise exists. | Probe actual vendor/runtime capability and benchmark supported configurations. | Use CPU or reduced-workload paths, report performance limits, and avoid claiming CUDA support. | Studio/runtime builder | PL-0024, PL-0034, PL-0180 |
| RISK-0005 | Dependency | COLMAP, OpenMVS, Open3D, OpenCascade bindings, Blender, PySide6, Python, OpenCV, and PyTorch may vary in API, packaging, platform, or runtime compatibility. | Medium | High | Dependencies are architectural/planning inputs; installation and version compatibility remain unproven. | Pin and test supported combinations through later authorized dependency work with provenance. | Fail clearly, retain input evidence, and use an explicitly supported fallback or block the workflow. | Dependency/integration owner | PL-0027, PL-0029, PL-0158, PL-0159, PL-0162 |
| RISK-0006 | Licensing | OpenMVS is identified as AGPL-3.0/high license attention; other dependency, binding, Qt, Blender, OpenCV, PyTorch, and transitive obligations may differ. | Medium | High | `DEPENDENCY_LICENSE_REGISTER.md` records current research and uncertainty; it is not legal certification. | Maintain notices, source/offer obligations, binding distinctions, and legal review through the dependency process. | Do not distribute the affected combination until obligations and permitted use are resolved. | Owner plus legal/licensing reviewer | PL-0005, PL-0158, PL-0159 |
| RISK-0007 | Apple distribution | Apple signing, provisioning, free-first distribution, account limits, and device installation behavior are uncertain. | Medium | High | The host/device baseline explicitly defers signing and provisioning implementation. | Validate the intended free-first and signed distribution path in its authorized Apple task. | Use simulator or unsigned development evidence where allowed, or mark distribution blocked. | Apple/build owner / owner account holder | PL-0357, PL-0358, PL-0359, PL-0361, PL-0362 |
| RISK-0008 | Security/privacy | Secrets, signing material, tokens, private scans, supplier documents, or proprietary artwork could leak through public Git, logs, fixtures, screenshots, or generated output. | Medium | High | `SECRETS_POLICY.md` and source-control policy define prohibitions; no incident is asserted by this register. | Apply protected-file review, redaction, least privilege, and approved incident response before publication. | Stop, revoke/rotate, audit history, and use the approved purge process; do not merely delete the latest file. | Every builder; ChatGPT audit for evidence | PL-0007, PL-0008, PL-0021, PL-0360, PL-0394 |
| RISK-0009 | Compatibility | Studio/Capture and PackScan schema can drift, causing rejected, misread, or costly migrations across version domains. | Medium | High | `VERSIONING_POLICY.md` requires explicit capability checks, conservative schema bumps, and non-destructive migrations. | Declare read/write/migration support, preserve original `.packscan` evidence, and test old/new combinations. | Reject unsupported future MAJOR cleanly and retain the original input for a supported migration or upgrade. | Schema/application owner | PL-0006, PL-0044, PL-0045, PL-0055, PL-0056, PL-0384 |
| RISK-0010 | Provenance | Supplier/private Kenya assets may be unavailable, restricted, or missing redistribution provenance, weakening fixture and benchmark reproducibility. | Medium | High | Protected-data rules identify these materials as confidential; availability and permission are not assumed. | Use synthetic/public fixtures with recorded provenance and obtain owner authorization before any protected-data use. | Block the dependent benchmark and document the exact missing input; do not substitute unapproved assets silently. | Owner/supplier-data custodian | PL-0337, PL-0370, PL-0402, PL-0410, PL-0412 |
| RISK-0011 | Reliability/reproducibility | Reconstruction can fail after long runtimes because of disk exhaustion, memory pressure, process interruption, corrupted intermediates, or nondeterministic dependency behavior. | High | High | Current architecture identifies heavy local processing; no endurance benchmark or reproducibility guarantee is claimed. | Preflight capacity, use resumable checkpoints where authorized, record versions/seeds/inputs, and verify outputs. | Preserve immutable inputs, cleanly report failure, and rerun from a bounded checkpoint or fresh workspace. | Studio/reconstruction owner | PL-0035, PL-0148, PL-0165, PL-0179, PL-0380, PL-0381, PL-0382 |

## Interpretation rules

- `Evidence/status` must distinguish an observed fact, an owner declaration,
  a documented architecture assumption, an unresolved hypothesis, and a
  future validation requirement.
- `Mitigation` entries are planned controls unless another audited artifact
  proves implementation. This register does not turn a planned benchmark,
  probe, legal review, signing path, or fallback into an existing capability.
- Visual similarity, a self-consistent software result, or a successful render
  does not prove physical dimensional accuracy, metric scale, or suitability
  for mold manufacture.
- The non-LiDAR baseline is preserved. Optional future LiDAR, CUDA, cloud, or
  distribution capabilities require their own authorized scope and evidence.
- Risk IDs are not task IDs, semantic versions, audit verdicts, or tracker
  state. Root `TASKS.md` remains the sole live project-status surface.

## Review boundary

This M00 register records planning risks only. It does not implement capture,
reconstruction, measurement, dependency packaging, legal certification,
signing, CI, storage recovery, or production readiness.
