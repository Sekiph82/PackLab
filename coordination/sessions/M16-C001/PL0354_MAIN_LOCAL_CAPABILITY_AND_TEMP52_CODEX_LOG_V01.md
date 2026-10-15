# PL0354 Main Windows TEMP52 and Local XCTest Capability — Codex Log V01

Date: 2026-10-16 (Europe/Istanbul)  
Status: `TEMP52_CLEANUP_PARTIAL_WITH_EXACT_BLOCKERS`; `PL0354_205_XCTEST=BLOCKED_MACOS_XCODE_REQUIRED`; `AWAITING_AUDIT`

## Scope and synchronization

- Repository: private `Sekiph82/PackLab`; publication target: `main`.
- Active instruction: `coordination/sessions/M16-C001/PL0354_MAIN_WINDOWS_TEMP52_AND_LOCAL_XCTEST_CAPABILITY_CODEX_PROMPT_V01.md`.
- Read the prompt and governing repository instructions from GitHub main.
- Desktop checkout started at `e2cb34f26cb5774c2b895131a4fc5a3f6bf166f0`, branch `main`; origin is `https://github.com/Sekiph82/PackLab.git`.
- `git fetch origin main` completed. Remote main before log publication: `430a4cc06dd4e833a2f59981fe3fd7e588ce7724`; the previously authorized offline merge `99473edf892e1f714bad3fffda99d10f0233468d` is an ancestor. The local checkout is 1,043 commits behind and has owner changes, so no checkout synchronization, merge, reset, or source edits were made.
- Existing owner state preserved: modified `core/src/packlab_core/geometry_adapter.py`; untracked `core/src/packlab_core/scan_design_heatmap.py` and `tests/core/test_scan_design_heatmap.py`. No TASKS.md edits.
- No local worktree created. No source files changed. No PR. No Actions or paid CI invoked. No workflow dispatch/rerun. No native OCCT/OCP or Installer build.

## TEMP52 inspection and cleanup

Both `%TEMP%` and `%LOCALAPPDATA%\Temp` resolve to `C:\Users\sekip\AppData\Local\Temp`. One bounded direct-child enumeration found 52 names containing PackLab. Every candidate was owned by `SEKIPH\sekip`; no process command line referenced a candidate; exclusive-open lock probes had zero failures; there were zero reparse points and no candidate directory was a Git root. Candidate creation/last-write times, type, logical bytes and file counts were captured. No candidate was active. The owner explicitly authorized deletion of inactive PackLab-labelled TEMP items despite unknown original task ownership.

Before deletion, the physical-volume free-byte query (`Win32_LogicalDisk`, `DeviceID=C:`) recorded T0 at 2026-10-16 01:36:29.1067734 +03:00: **116,691,873,792 bytes**. The small T0 note was written outside TEMP at `C:\Users\sekip\Desktop\PackLab\PL0354_TEMP52_T0_20261016.txt`.

Five exact in-scope children were removed using bounded, non-forced `Remove-Item -LiteralPath` calls after rechecking paths and reparse status:

- `PackLab`: empty container (four empty directories, zero files).
- `packlab-pl0350-run-38504978407-inspect`: exact duplicate of retained `packlab-pl0350-run-38504978407` (file path/size/hash tree digest `7DFC1DFEDCEC76A980C030EFFF549F9C7D006F9B429F464B945FE70D557FC775`).
- `PackLab-PL0350-Final-Preflight-20261012`: exact duplicate of retained `PackLab-PL0350-Verified-Generated-Source-Patch` (1,275 files; tree digest `A1482F4129BEC6AD74CB189A16FB38B920E923F43D62096F9B9EBC417ED67438`). The separate preflight manifest remains.
- `packlab-pywrap-9251940.tar.gz`: byte-identical duplicate of retained hash-qualified archive (SHA-256 `B88B0F2B9C7D2AE72A7399EFC44951659FB1A28EA607D962BA1F507CE754BA48`).
- `packlab-disk-preflight.json`: old 415-byte transient preflight record.

Immediately after those deletions, the same TEMP scope was re-enumerated (47 PackLab-labelled entries remain) and C: free bytes were **116,763,336,704** at 2026-10-16 01:36:29.6332659 +03:00. Measured T0→T1 net increase: **71,462,912 bytes (about 68.15 MiB)**. The deleted file payload total was 67,906,637 bytes; the reported recovery is the actual volume free-byte delta, not the logical-size sum. Concurrent filesystem allocation can affect free-byte deltas.

The 47 retained entries below were classified `IN_USE_OR_PROTECTED_BLOCKED` due to the exact unique owner/native/source/compliance/provenance/run evidence described. These are protected-content dispositions, not claims that a process held them open. No reparse points or OS/policy deletion failures occurred. Original owner uncertainty did not block the five deletions.

| TEMP child | Type | Bytes | Files | Created / modified (local) | Classification and reason |
|---|---:|---:|---:|---|---|
| `PackLab` | dir | 0 | 0 | 2026-10-09T14:55:00 / 2026-10-09T17:18:55 | PACKLAB_TEMP_TASK_UNKNOWN_OWNER_DELETE_AUTHORIZED: Empty PackLab temp container; 4 empty descendant directories, 0 files. |
| `packlab-controlled-runtime-38476209485` | dir | 144383005 | 53 | 2026-10-13T22:35:54 / 2026-10-13T22:35:56 | IN_USE_OR_PROTECTED_BLOCKED: OCP compiled runtime and distinct provenance manifests; retained as protected native evidence. |
| `packlab-ocp-38468367218` | dir | 144383005 | 53 | 2026-10-13T21:34:55 / 2026-10-13T21:34:57 | IN_USE_OR_PROTECTED_BLOCKED: OCP compiled runtime and distinct provenance manifests; retained as protected native evidence. |
| `PackLab-PL0350-Final-Preflight-20261012` | dir | 62311345 | 1275 | 2026-10-12T10:58:58 / 2026-10-12T10:58:58 | PACKLAB_TEMP_TASK_UNKNOWN_OWNER_DELETE_AUTHORIZED: Inactive exact duplicate of retained Verified-Generated-Source-Patch tree; 1,275 file hashes matched. |
| `packlab-pl0350-ocp-38504978407` | dir | 144383005 | 53 | 2026-10-14T13:20:46 / 2026-10-14T13:21:04 | IN_USE_OR_PROTECTED_BLOCKED: OCP compiled runtime and distinct provenance manifests; retained as protected native evidence. |
| `packlab-pl0350-run-38504978407` | dir | 8287 | 4 | 2026-10-14T13:17:25 / 2026-10-14T13:17:27 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run diagnostic/Qt surface output; not the exact duplicate removed. |
| `packlab-pl0350-run-38504978407-inspect` | dir | 8287 | 4 | 2026-10-14T13:17:37 / 2026-10-14T13:17:39 | PACKLAB_TEMP_TASK_UNKNOWN_OWNER_DELETE_AUTHORIZED: Inactive exact duplicate of retained run tree; full path/size/SHA-256 inventory matched. |
| `packlab-pl0350-run-38571979341-inspect` | dir | 8533 | 4 | 2026-10-14T13:47:28 / 2026-10-14T13:47:30 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run diagnostic/Qt surface output; not the exact duplicate removed. |
| `packlab-pl0350-v04-hosted-fba0b3cf36994107adcc984798ed87bd` | dir | 182980 | 41 | 2026-10-06T14:44:54 / 2026-10-06T14:44:56 | IN_USE_OR_PROTECTED_BLOCKED: Unique Windows compliance/hosted-run evidence; retained. |
| `packlab-pl0350-v04-hosted-run-37481126993` | dir | 6723 | 7 | 2026-10-06T14:44:28 / 2026-10-06T14:44:28 | IN_USE_OR_PROTECTED_BLOCKED: Unique Windows compliance/hosted-run evidence; retained. |
| `packlab-pl0350-v05-01df2fe7` | dir | 1112082 | 126 | 2026-10-08T07:33:06 / 2026-10-08T07:33:08 | IN_USE_OR_PROTECTED_BLOCKED: Distinct third-party license/compliance inventory; tree SHA-256 differs despite matching size/count. |
| `packlab-pl0350-v05-68ead2cd` | dir | 1112082 | 126 | 2026-10-08T07:37:20 / 2026-10-08T07:37:23 | IN_USE_OR_PROTECTED_BLOCKED: Distinct third-party license/compliance inventory; tree SHA-256 differs despite matching size/count. |
| `PackLab-PL0350-Verified-Generated-Source-Patch` | dir | 62311345 | 1275 | 2026-10-12T10:27:57 / 2026-10-12T10:27:57 | IN_USE_OR_PROTECTED_BLOCKED: Retained exact duplicate source-tree copy; protected generated OCP source evidence. |
| `packlab-precompile-38468367218` | dir | 538985 | 5 | 2026-10-13T21:36:15 / 2026-10-13T21:36:15 | IN_USE_OR_PROTECTED_BLOCKED: Retained SDK/precompile inspection evidence and policy manifests. |
| `packlab-smoke-38479890772` | dir | 990 | 2 | 2026-10-13T23:06:17 / 2026-10-13T23:06:18 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-smoke-38485779244` | dir | 990 | 2 | 2026-10-14T00:00:38 / 2026-10-14T00:00:39 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-studio-smoke-38432790664` | dir | 933 | 2 | 2026-10-13T17:09:27 / 2026-10-13T17:09:27 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-studio-smoke-38441105399` | dir | 1022 | 2 | 2026-10-13T18:08:42 / 2026-10-13T18:08:42 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-studio-smoke-38445028184` | dir | 1029 | 2 | 2026-10-13T18:33:09 / 2026-10-13T18:33:09 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-studio-smoke-38448279380` | dir | 944 | 2 | 2026-10-13T18:57:45 / 2026-10-13T18:57:45 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-studio-smoke-38452152233` | dir | 968 | 2 | 2026-10-13T19:26:48 / 2026-10-13T19:26:48 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-studio-smoke-38456005294` | dir | 968 | 2 | 2026-10-13T19:58:43 / 2026-10-13T19:58:43 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-studio-smoke-38460065727` | dir | 968 | 2 | 2026-10-13T20:34:13 / 2026-10-13T20:34:13 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-studio-smoke-38464557706` | dir | 968 | 2 | 2026-10-13T21:03:06 / 2026-10-13T21:03:06 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-studio-smoke-38468367218` | dir | 1023 | 2 | 2026-10-13T21:34:34 / 2026-10-13T21:34:34 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-studio-smoke-38472299194` | dir | 929 | 2 | 2026-10-13T22:03:30 / 2026-10-13T22:03:30 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-studio-smoke-38476209485-attempt3` | dir | 977 | 2 | 2026-10-13T22:40:07 / 2026-10-13T22:40:07 | IN_USE_OR_PROTECTED_BLOCKED: Unique per-run Qt staged-surface/smoke diagnostic; hashes differ across runs, retained as evidence. |
| `packlab-disk-preflight.json` | file | 415 | 1 | 2026-10-09T16:04:02 / 2026-10-09T16:04:02 | PACKLAB_TEMP_TASK_UNKNOWN_OWNER_DELETE_AUTHORIZED: 415-byte old transient disk preflight record; not owner or unique checkpoint data. |
| `packlab-local-open3d-pe-dependencies.json` | file | 7029 | 1 | 2026-10-14T01:35:50 / 2026-10-14T02:42:39 | IN_USE_OR_PROTECTED_BLOCKED: Unique local dependency/PE diagnostic evidence. |
| `packlab-ocp-bindings-win.lock` | file | 92229 | 1 | 2026-10-08T09:57:05 / 2026-10-08T09:57:06 | IN_USE_OR_PROTECTED_BLOCKED: OCP dependency lock/recipe/source input; retained as unique provenance; no rebuild performed. |
| `packlab-ocp-bindings-win.yml` | file | 375 | 1 | 2026-10-08T09:56:52 / 2026-10-08T09:56:52 | IN_USE_OR_PROTECTED_BLOCKED: OCP dependency lock/recipe/source input; retained as unique provenance; no rebuild performed. |
| `packlab-ocp-build-win.lock` | file | 97667 | 1 | 2026-10-08T09:53:25 / 2026-10-08T09:53:26 | IN_USE_OR_PROTECTED_BLOCKED: OCP dependency lock/recipe/source input; retained as unique provenance; no rebuild performed. |
| `packlab-ocp-build-win.yml` | file | 312 | 1 | 2026-10-08T09:50:03 / 2026-10-08T09:50:03 | IN_USE_OR_PROTECTED_BLOCKED: OCP dependency lock/recipe/source input; retained as unique provenance; no rebuild performed. |
| `packlab-ocp-d69b064a3a604ebf245b1f3b14fb54c835a3a571.tar.gz` | file | 3728128 | 1 | 2026-10-08T12:47:20 / 2026-10-08T12:47:20 | IN_USE_OR_PROTECTED_BLOCKED: OCP dependency lock/recipe/source input; retained as unique provenance; no rebuild performed. |
| `packlab-ocp-win-64.lock` | file | 22159 | 1 | 2026-10-08T10:35:14 / 2026-10-08T10:35:14 | IN_USE_OR_PROTECTED_BLOCKED: OCP dependency lock/recipe/source input; retained as unique provenance; no rebuild performed. |
| `packlab-owner-desktop-startup-gate.ps1` | file | 4573 | 1 | 2026-10-08T10:37:17 / 2026-10-08T16:26:37 | IN_USE_OR_PROTECTED_BLOCKED: Owner startup/OwnerDev diagnostic/launcher data; protected. |
| `packlab-ownerdev-dryrun.json` | file | 6787 | 1 | 2026-10-09T16:14:16 / 2026-10-09T16:14:16 | IN_USE_OR_PROTECTED_BLOCKED: Owner startup/OwnerDev diagnostic/launcher data; protected. |
| `PackLab-PL0350-Final-Preflight-20261012-manifest.json` | file | 511468 | 1 | 2026-10-12T10:59:01 / 2026-10-12T10:59:01 | IN_USE_OR_PROTECTED_BLOCKED: Unique generated-source/preflight manifest or inspection evidence; protected. |
| `packlab-pl0350-ocp-generated-source-inspection.zip` | file | 6481047 | 1 | 2026-10-12T10:25:42 / 2026-10-12T10:25:42 | IN_USE_OR_PROTECTED_BLOCKED: Unique generated-source/preflight manifest or inspection evidence; protected. |
| `PackLab-PL0350-R01-git-commit.json` | file | 444 | 1 | 2026-10-12T13:37:03 / 2026-10-12T13:37:03 | IN_USE_OR_PROTECTED_BLOCKED: Unique R01 commit/build workflow source evidence; protected pending owner confirmation of durable counterpart. |
| `PackLab-PL0350-R01-windows-studio-build-canonical.yml` | file | 55318 | 1 | 2026-10-12T13:36:26 / 2026-10-12T13:36:26 | IN_USE_OR_PROTECTED_BLOCKED: Unique R01 commit/build workflow source evidence; protected pending owner confirmation of durable counterpart. |
| `PackLab-PL0350-R01-workflow-test-canonical.py` | file | 7623 | 1 | 2026-10-12T13:36:26 / 2026-10-12T13:36:26 | IN_USE_OR_PROTECTED_BLOCKED: Unique R01 commit/build workflow source evidence; protected pending owner confirmation of durable counterpart. |
| `PackLab-PL0350-Verified-Generated-Source-Patch-manifest.json` | file | 257758 | 1 | 2026-10-12T10:27:58 / 2026-10-12T10:27:58 | IN_USE_OR_PROTECTED_BLOCKED: Unique generated-source/preflight manifest or inspection evidence; protected. |
| `packlab-pywrap-9251940.tar.gz` | file | 5586590 | 1 | 2026-10-13T16:08:30 / 2026-10-13T16:08:31 | PACKLAB_TEMP_TASK_UNKNOWN_OWNER_DELETE_AUTHORIZED: Inactive byte-identical archive duplicate; retained hash-qualified archive. |
| `packlab-pywrap-92519409a57f9ec3f2c005b8057006fdb4752c23.tar.gz` | file | 5586590 | 1 | 2026-10-08T11:54:39 / 2026-10-08T11:54:40 | IN_USE_OR_PROTECTED_BLOCKED: One archive copy retained after proving the other exact duplicate. |
| `packlab-r05-fmt-12.1.0-source.tar.gz` | file | 711419 | 1 | 2026-10-13T08:03:34 / 2026-10-13T08:03:34 | IN_USE_OR_PROTECTED_BLOCKED: Distinct R05 source input and recipe; preserved as another task's unique input. |
| `packlab-r05-fmt-recipe-437ad8fba6cc830bd16eef7f98aeb2d76c9ff060.yaml` | file | 1580 | 1 | 2026-10-13T08:03:53 / 2026-10-13T08:03:53 | IN_USE_OR_PROTECTED_BLOCKED: Distinct R05 source input and recipe; preserved as another task's unique input. |
| `packlab-rerun-38476209485-package.log` | file | 45525 | 1 | 2026-10-13T22:35:03 / 2026-10-13T22:35:03 | IN_USE_OR_PROTECTED_BLOCKED: Unique historical hosted runner log; retained as execution evidence. |
| `packlab-run-38468367218-package.log` | file | 141088 | 1 | 2026-10-13T21:34:35 / 2026-10-13T21:34:35 | IN_USE_OR_PROTECTED_BLOCKED: Unique historical hosted runner log; retained as execution evidence. |
| `packlab-run-38472299194-package.log` | file | 141052 | 1 | 2026-10-13T22:04:00 / 2026-10-13T22:04:00 | IN_USE_OR_PROTECTED_BLOCKED: Unique historical hosted runner log; retained as execution evidence. |
| `packlab-run-38476209485-package.log` | file | 54123 | 1 | 2026-10-13T22:31:22 / 2026-10-13T22:31:22 | IN_USE_OR_PROTECTED_BLOCKED: Unique historical hosted runner log; retained as execution evidence. |
| `PackLabOwnerLauncher-check.exe` | file | 71168 | 1 | 2026-10-08T07:20:52 / 2026-10-08T07:20:52 | IN_USE_OR_PROTECTED_BLOCKED: Owner startup/OwnerDev diagnostic/launcher data; protected. |

## Local XCTest feasibility (205 cases)

- Read-only source inventory on fetched `origin/main`: `apps/ios-capture/PackLabCaptureTests/PackLabCaptureTests.swift` defines **205** named `func test…` methods. This is a static inventory only, not test execution.
- Project/scheme: `apps/ios-capture/PackLabCapture.xcodeproj`, shared `PackLabCapture` scheme; iOS deployment target 17.0.
- Host is Windows 11 Home Single Language (10.0.26300). `Get-Command xcodebuild` and `Get-Command xcrun` both returned unavailable. This host cannot provide Xcode, iOS SDK, or iOS Simulator.
- Genuine local iOS XCTest execution is therefore blocked: `PL0354_205_XCTEST=BLOCKED_MACOS_XCODE_REQUIRED`. No Windows test was substituted or represented as XCTest; no remote Mac was accessed. No tests were run.

## Workflow and publication boundary

- Read the current main workflow inventory (9 workflow files) and push path filters. The log path under `coordination/sessions/M16-C001/` is outside all push path filters; no broad push-trigger workflow matches it. Thus direct documentation publication does not schedule an Actions run.
- This single small Codex log is the only repository file to publish. It contains no secrets, owner scans, local cache content, or generated native payload.
- Publication is a direct GitHub Contents API write to private `main`, with `[skip ci]` in the commit message; no branch, PR, workflow, or source-code write is involved. The API response provides the publication commit SHA.
- `AWAITING_AUDIT`: implementation/evidence report only; no release-readiness or hosted-verification claim.

## TEMP inventory

All 52 originally enumerated direct children are listed in the table. Table sizes are pre-cleanup logical bytes; directories were traversed without following reparse points. Empty directories have zero file bytes. Owner was `SEKIPH\sekip` for each; process refs=0, lock-probe failures=0, reparse count=0 for every entry. Modified time and file count are included per item above.
