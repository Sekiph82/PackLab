# PL-0004-C001 — Codex Prompt V01

Status: **ISSUED**

Task: **PL-0004 — Document supported host/device baseline: Windows Acer laptop + iPhone 16 Standard, no LiDAR assumption.**

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
6. `docs/architecture/adr/README.md`
7. `docs/architecture/adr/ADR-0001-monorepo-architecture.md`
8. `coordination/README.md`
9. `coordination/AUDIT_POLICY.md`
10. `coordination/AUDIT_INDEX.md`
11. `coordination/sessions/PL-0003-C001/CHATGPT_AUDIT_V01.md`
12. this prompt
13. `coordination/sessions/PL-0004-C001/CHATGPT_AUDIT_CRITERIA_V01.md`

If root `TASKS.md` does not declare PL-0004 as the current authorized task for Codex, STOP and report `TASK_STATE_MISMATCH`.

## Phase 0 — Safe synchronization

The one-time destructive bootstrap is complete. Use normal safe synchronization only.

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
- historical untracked `.hiveai/` state may remain local, but must never be staged or treated as project truth;
- if tracked state is clean and local is only behind, use `git merge --ff-only origin/main`;
- if local is ahead, diverged, or has unexpected tracked changes, STOP and report exact state;
- do not reset, rebase, force-push, destructive checkout, silent stash, or `git clean`;
- before implementation prove local HEAD equals `origin/main` and root `TASKS.md` authorizes PL-0004.

## Phase 1 — Collect the current Windows host facts safely

The current PackLab Windows workspace is the owner's Acer Windows laptop. Record only non-sensitive hardware/software facts useful to PackLab support and reproducibility.

Run read-only PowerShell queries equivalent to:

```powershell
Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,TotalPhysicalMemory
Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors
Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture
```

You may use additional **read-only** commands only if needed to clarify these same fields.

Privacy rules:

- DO NOT record serial number, BIOS serial, UUID, Windows product key, username, computer/device name, MAC address, IP address, Wi-Fi SSID, account identifiers, filesystem user profile details beyond the already canonical workspace path, or any secret/token.
- If Manufacturer does not identify Acer, or if the machine identity materially conflicts with the task title, STOP and report `HOST_IDENTITY_MISMATCH`; do not rewrite the task or fabricate Acer.
- If a hardware field cannot be obtained reliably, write `Unknown / not verified` rather than guessing.
- Treat observed machine specifications as the **current primary development/runtime host**, not as universal PackLab minimum requirements.

## Phase 2 — Create the supported host/device baseline document

Create exactly:

`docs/architecture/SUPPORTED_HOST_DEVICE_BASELINE.md`

The document must distinguish:

1. **Current primary Windows host** — the owner’s verified Acer Windows laptop used for local PackLab Studio development/runtime.
2. **Current capture device** — owner-declared iPhone 16 Standard used for PackLab Capture.
3. **CI build hosts** — GitHub Actions Windows for PackLab Studio and GitHub Actions macOS for PackLab Capture/iOS build/test/archive work.
4. **Future support targets** — explicitly not frozen as universal minimum hardware by PL-0004.

### Windows host section

Record the verified non-sensitive facts from Phase 1:

- manufacturer;
- model;
- Windows edition/version/build/architecture;
- CPU model and core/logical-processor counts;
- total physical RAM in a human-readable unit;
- GPU name(s), reported adapter memory when reliable, and driver version when available;
- canonical PackLab local workspace `C:\Users\sekip\Desktop\PackLab`.

Then define the architectural role:

- PackLab Studio is Windows-first for this owner workflow;
- Python/PySide6 and heavy processing live on Windows;
- COLMAP, OpenMVS, Open3D, OpenCascade binding, PyTorch/OpenCV and Blender are Windows-side/Studio capabilities unless a later ADR changes responsibility;
- exact compatibility/version installation remains later dependency/tooling tasks, especially PL-0005, PL-0027 and engine-specific milestones;
- PL-0004 must not claim all external engines are already installed or operational.

### iPhone 16 Standard section

Treat **iPhone 16 Standard**, not Pro/Pro Max, as the capture baseline.

Use these official Apple sources as external factual references and include them in the document:

- Apple iPhone 16 technical specifications: `https://www.apple.com/iphone-16/specs/`
- Apple ARKit device/configuration support guidance: `https://developer.apple.com/documentation/arkit/arconfiguration/issupported`

The baseline may record official iPhone 16 facts relevant to PackLab, including:

- A18 chip;
- 48 MP Fusion Main camera;
- 12 MP Ultra Wide camera;
- HEIF and JPEG still-image formats;
- USB-C;
- ARKit-capable iPhone generation, while runtime AR configuration support must still be checked using Apple APIs.

Most important rule:

**PackLab Capture must not require LiDAR.**

Document this as an architecture constraint, not as a workaround:

- the baseline is standard iPhone 16;
- the capture/reconstruction design is image-based photogrammetry;
- ARKit camera pose/world tracking and CoreMotion are supporting metadata/guidance;
- dense reconstruction remains the Windows COLMAP/OpenMVS pipeline;
- no core PackLab Capture workflow may depend on LiDAR-only depth, scene reconstruction, mesh, or range APIs;
- optional future LiDAR acceleration/enhancement on another device would require a later audited task/ADR and must preserve a non-LiDAR path unless the owner changes the product baseline.

Do not claim that ARKit pose alone provides final photogrammetric geometry or certified dimensional accuracy.

### Capture-camera policy boundary

Document that PL-0004 establishes hardware assumptions only, not final camera tuning.

State explicitly:

- accepted reconstruction inputs are intended to be controlled high-resolution still photographs;
- preview/video frames may later be used for live quality analysis and auto-trigger logic;
- final lens selection, resolution, focus/exposure/white-balance policy and NextLevel/AVFoundation implementation belong to later iOS tasks;
- do not freeze a 48 MP capture mode, RAW workflow, exact photo count, exposure strategy, or reconstruction accuracy target in PL-0004.

### CI / macOS boundary

Document:

```text
GitHub main
  ├─ GitHub Actions Windows -> PackLab Studio build/test/package
  └─ GitHub Actions macOS   -> PackLab Capture Swift/iOS build/test/archive
```

State clearly:

- the owner does not need to own a Mac for the selected CI architecture;
- native iOS builds require an Apple/Xcode/macOS build environment, provided here by GitHub Actions macOS;
- Windows is not represented as a native Xcode host;
- simulator build and optional device signing are separate concerns;
- signing/provisioning policy remains PL-0357+ and later distribution tasks, not PL-0004.

### Support / capability classification

Include a small table with at least these capability classes:

- REQUIRED BASELINE
- SUPPORTED PRIMARY PATH
- OPTIONAL / FUTURE
- NOT ASSUMED

It must classify at least:

- Windows host;
- iPhone 16 Standard;
- LiDAR;
- discrete NVIDIA/CUDA acceleration;
- Mac hardware owned by the user;
- internet/cloud connection during local reconstruction;
- GitHub Actions Windows/macOS.

Important: do not make CUDA, LiDAR, a user-owned Mac, or permanent internet access mandatory for the core architecture unless a later audited decision explicitly does so. Performance may vary and later compatibility tasks may establish stronger requirements.

### Claims and limitations

The document must say:

- PL-0004 documents the current supported baseline and architectural assumptions, not production-grade minimum system requirements;
- current observed host hardware is evidence about one machine, not a guarantee every PackLab stage will meet performance targets;
- actual external-engine compatibility is validated later;
- physical camera/reconstruction/measurement accuracy is validated later;
- no direct mold-manufacturing/metrology claim is created by this baseline.

## Scope boundaries

Authorized changes:

- add `docs/architecture/SUPPORTED_HOST_DEVICE_BASELINE.md`;
- add matching `coordination/sessions/PL-0004-C001/CODEX_LOG_V01.md`.

Do not modify:

- root `TASKS.md`;
- `AGENTS.md`;
- `CLAUDE.md`;
- `IMPLEMENTATION_GUIDE.md`;
- repository structure/glossary/ADR files;
- coordination policy/index;
- prior session evidence;
- this prompt or its criteria;
- root `AUDIT.md` or `handoff.md`;
- application/source/schema/runtime files.

Do not implement PL-0005+.

## Validation

Run and record:

```powershell
git diff --check
```

For the new baseline file, use a diff that can actually see an untracked file, for example:

```powershell
git add -N docs/architecture/SUPPORTED_HOST_DEVICE_BASELINE.md
git diff -- docs/architecture/SUPPORTED_HOST_DEVICE_BASELINE.md
```

Perform explicit checks proving:

- no prohibited sensitive host identifiers appear;
- manufacturer/model facts come from the local read-only query rather than guesswork;
- iPhone baseline says **iPhone 16 Standard**;
- LiDAR is NOT required;
- image-based photogrammetry is the primary capture/reconstruction assumption;
- ARKit/CoreMotion are supporting signals rather than geometry truth;
- Windows/macOS CI roles are distinct;
- Windows is not claimed to host Xcode natively;
- CUDA is not mandatory;
- no owned Mac is required by the selected architecture;
- exact dependency compatibility remains later work;
- no future-task source/runtime implementation is added;
- all protected files remain unchanged.

No application test suite is required for this documentation task.

## Required Codex log

Write:

`coordination/sessions/PL-0004-C001/CODEX_LOG_V01.md`

Record:

- prompt/criteria paths;
- synchronized starting commit;
- implementation commit;
- synchronization commands/results;
- inputs read;
- sanitized Windows host-fact commands/results;
- files added/modified/deleted;
- implementation summary;
- exact validation commands, expected results, failure conditions and actual results;
- new-file diff-review evidence;
- failures/fixes;
- privacy/sensitive-identifier check;
- scope check;
- push/remote visibility evidence;
- known limitations/unverified assumptions;
- final `AWAITING_AUDIT`.

### Commit-SHA metadata rule

Following audit learning AL-PL-0007:

- record `startingCommit` and `implementationCommit`;
- **do not predeclare a `finalCommit` SHA for the future commit that will contain this log**;
- ChatGPT will independently record the actual log commit / audited head after the log is pushed.

## Commit / push

Commit only the authorized baseline document and matching Codex log.

Push safely to `origin/main` and verify remote visibility.

## Final response

Return only a concise handoff containing:

- `PL-0004-C001`;
- implementation commit information;
- log GitHub path/URL;
- `AWAITING_AUDIT`.

Then STOP. Do not begin PL-0005.
