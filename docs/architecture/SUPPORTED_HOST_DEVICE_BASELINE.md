# PackLab Supported Host and Device Baseline

## Scope and evidence

This document records the current PackLab development/capture baseline and architectural assumptions for the owner workflow. It is not a universal minimum-system-requirements specification, a performance guarantee, or a certification of production metrology or mold-manufacturing readiness.

The Windows host facts in this document were observed locally on 2026-09-17 with the read-only PowerShell queries recorded in the matching PL-0004 Codex log. They describe the current primary development/runtime host, not every supported or future machine. The iPhone device status is owner-declared; official Apple device facts are separately identified and linked below.

PackLab’s ownership and dependency rules remain defined by [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md), and its terminology remains defined by [GLOSSARY.md](GLOSSARY.md). This baseline does not replace those contracts or root TASKS.md.

## Current primary Windows host

### Observed host facts

| Field | Observed value | Evidence/qualification |
| --- | --- | --- |
| Manufacturer | Acer | Read from Win32_ComputerSystem; this matches the PL-0004 Acer host assumption. |
| Model | Swift SF514-56T | Read from Win32_ComputerSystem. |
| Windows edition | Microsoft Windows 11 Home Single Language | Read from Win32_OperatingSystem. |
| Windows version | 10.0.26200 | Read from Win32_OperatingSystem. |
| Windows build | 26200 | Read from Win32_OperatingSystem. |
| OS architecture | 64-bit | Read from Win32_OperatingSystem. |
| CPU | 12th Gen Intel(R) Core(TM) i7-1260P | Read from Win32_Processor. |
| Physical CPU cores | 12 | Read from Win32_Processor. |
| Logical processors | 16 | Read from Win32_Processor. |
| Total physical RAM | 16,870,006,784 bytes, approximately 15.7 GiB (16 GB class) | Read from Win32_ComputerSystem and converted to a human-readable unit. |
| GPU | Intel(R) Iris(R) Xe Graphics | Read from Win32_VideoController. |
| Reported adapter memory | 1,073,741,824 bytes, approximately 1 GiB reported | This is the operating system’s adapter-memory field for integrated graphics; it is not treated as dedicated VRAM or as a CUDA-capable memory guarantee. |
| GPU driver | 31.0.101.3616 | Read from Win32_VideoController. |
| Canonical local workspace | C:\Users\sekip\Desktop\PackLab | PackLab repository workspace defined by the project contract. |

No serial number, BIOS serial, UUID, product key, username, hostname, network identifier, account identifier, or credential is part of this baseline.

### Architectural role

This Acer Windows laptop is the current primary development and local runtime host for the owner’s PackLab Studio workflow. PackLab Studio is Windows-first for this workflow. Python and PySide6 presentation/application integration, plus heavy local processing, are intended to run on the Windows side.

The current Windows/Studio capability boundary includes the following planned capabilities:

- COLMAP for the SfM/sparse reconstruction boundary;
- OpenMVS for dense reconstruction, mesh, refinement, and texturing;
- Open3D for point-cloud/mesh analysis, cleanup, registration, and measurement support;
- an OpenCascade binding for engineering BREP/CAD operations;
- PyTorch and OpenCV where applicable to analysis and processing; and
- Blender for Windows-side visual/material/render automation.

Listing a capability here does not claim that it is installed, correctly versioned, licensed for every use, or operational on this host. Exact dependency and version compatibility remains later work, including PL-0005, PL-0027, and engine-specific milestones. Capability discovery and failure reporting remain required architecture behavior.

## Current capture device: iPhone 16 Standard

### Device status and official facts

The current capture baseline is the owner-declared **iPhone 16 Standard**. It is not an iPhone 16 Pro or iPhone 16 Pro Max baseline. The owner’s declaration establishes the current PackLab device target; the following hardware facts are official Apple specifications relevant to planning:

- A18 chip.
- 48 MP Fusion Main camera.
- 12 MP Ultra Wide camera.
- HEIF and JPEG still-image formats.
- USB-C connector.

Official references:

- [Apple iPhone 16 technical specifications](https://www.apple.com/iphone-16/specs/)
- [Apple ARKit configuration support guidance](https://developer.apple.com/documentation/arkit/arconfiguration/issupported)

The iPhone 16 generation is treated as an ARKit-capable capture generation for PackLab planning, but the app must check the applicable ARKit configuration support API at runtime. Device-family planning is not a substitute for an availability check on the actual runtime configuration.

### Non-LiDAR architecture constraint

PackLab Capture must not require LiDAR. This is an intentional architecture constraint for the standard iPhone 16 capture baseline, not an error state or a temporary workaround.

The core path is image-based photogrammetry:

1. PackLab Capture records controlled high-resolution still photographs and applicable metadata.
2. ARKit camera pose/world tracking and CoreMotion provide supporting pose, motion, and guidance metadata.
3. The Windows PackLab Studio pipeline uses COLMAP for the planned SfM/sparse stage and OpenMVS for planned dense reconstruction.
4. Scan/reference outputs remain separate from the editable Design Model and engineering CAD layers.

No core PackLab Capture workflow may depend on LiDAR-only depth, range, scene-reconstruction, or mesh APIs. ARKit pose and CoreMotion signals support capture and reconstruction alignment; neither one alone supplies final photogrammetric geometry, certified metric scale, or certified dimensional accuracy.

Optional future LiDAR acceleration or enhancement on another device is classified as OPTIONAL / FUTURE. It would require a later audited task and ADR if it changes an architecture boundary, and it must preserve the standard non-LiDAR path unless the owner explicitly changes the product baseline.

## Capture-camera policy boundary

PL-0004 establishes hardware assumptions only. It does not freeze final camera tuning or a capture recipe.

- Accepted reconstruction inputs are intended to be controlled high-resolution still photographs.
- Preview or video frames may later support live quality analysis and automatic-trigger logic; they are not hereby declared the final reconstruction input.
- Final lens selection belongs to later iOS camera tasks.
- Final capture resolution and mode belong to later iOS camera tasks.
- Focus, exposure, and white-balance policy belong to later iOS camera tasks.
- NextLevel/AVFoundation implementation details belong to later iOS integration tasks.

PL-0004 does not make a 48 MP mode mandatory, does not make RAW mandatory, does not freeze an exact photo count, does not freeze an exposure strategy, and does not freeze a reconstruction-accuracy target. Those decisions require later implementation evidence and, where architectural, an audited ADR.

## CI and macOS boundary

The selected build/test architecture is:

~~~text
GitHub main
  ├─ GitHub Actions Windows -> PackLab Studio build/test/package
  └─ GitHub Actions macOS   -> PackLab Capture Swift/iOS build/test/archive
~~~

GitHub Actions Windows is the supported CI path for PackLab Studio build, test, and packaging work. GitHub Actions macOS is the supported CI path for PackLab Capture Swift/iOS build, test, and archive work.

The owner does not need to own a Mac for this selected CI architecture. Native iOS builds require an Apple/Xcode/macOS build environment, which is supplied by the macOS Actions runner for the applicable workflow. Windows is not represented as a native Xcode host and is not a substitute for macOS in the iOS build chain.

Simulator build/test and optional physical-device signing are separate concerns. Signing and provisioning implementation remains deferred to PL-0357+ and later distribution tasks. This baseline does not claim that signing credentials, provisioning profiles, or a device archive are currently available.

## Support and capability classification

These classes describe the role of a capability in the current architecture:

- **REQUIRED BASELINE** — part of the current owner-declared PackLab baseline.
- **SUPPORTED PRIMARY PATH** — the intended supported route for a workflow, without implying that every local developer owns every host involved.
- **OPTIONAL / FUTURE** — useful or possible later capability, not required by the core architecture.
- **NOT ASSUMED** — deliberately not required or not available as a baseline assumption.

| Capability or condition | Classification | PackLab meaning |
| --- | --- | --- |
| Current Acer Windows host | REQUIRED BASELINE | Current primary owner development/runtime host for PackLab Studio; observed facts are not universal minimums. |
| iPhone 16 Standard | REQUIRED BASELINE; SUPPORTED PRIMARY PATH | Current owner-declared PackLab Capture device and standard non-LiDAR capture target. |
| LiDAR | NOT ASSUMED | Core Capture/reconstruction works without LiDAR; optional future use needs audited scope/ADR and must preserve the non-LiDAR path. |
| Discrete NVIDIA/CUDA acceleration | OPTIONAL / FUTURE | May improve performance if later compatibility work supports it; CUDA is not mandatory for the core architecture. |
| Mac hardware owned by the user | NOT ASSUMED | Not required by the selected GitHub Actions macOS CI architecture. |
| Internet/cloud connection during local reconstruction | NOT ASSUMED | Local reconstruction is not architecturally dependent on permanent internet or cloud connectivity; setup/downloads may have separate operational needs. |
| GitHub Actions Windows | SUPPORTED PRIMARY PATH | PackLab Studio build/test/package CI environment. |
| GitHub Actions macOS | SUPPORTED PRIMARY PATH | PackLab Capture Swift/iOS build/test/archive CI environment. |

Performance can vary with host load, driver state, storage, memory pressure, external-engine versions, and optional acceleration. A capability classification is not a promise of a particular processing time or reconstruction quality.

## Claims, limitations, and future validation

PL-0004 documents the current supported baseline and architectural assumptions; it does not certify production-grade minimum system requirements. The observed Acer hardware is evidence about one machine and is not a guarantee that every PackLab stage will meet a future performance target.

The following remain future validation work:

- actual compatibility and installation behavior for COLMAP, OpenMVS, Open3D, OpenCascade bindings, PyTorch, OpenCV, Blender, Python, PySide6, Swift, Xcode, and related versions;
- physical iPhone capture behavior, lens/camera tuning, thermal/storage behavior, and ARKit runtime configuration availability;
- reconstruction quality and failure behavior across packaging materials and capture conditions;
- calibration, scale, measurement, and physical dimensional accuracy; and
- CI artifact, simulator, archive, signing, and distribution behavior.

Actual external-engine compatibility, physical camera/capture behavior, reconstruction quality, and measurement accuracy are validated later through their dedicated implementation, benchmark, and acceptance tasks.

No direct mold-manufacturing claim, certified metrology claim, or certified dimensional-accuracy claim is created by this baseline. A successful build or render does not prove physical capture accuracy, reconstruction quality, or engineering suitability.
