# PL-0350 Upstream Generated Source Read-Only Codex Log

Date: 2026-10-12
Status: **AWAITING_INDEPENDENT_AUDIT / OWNER_BUILD_APPROVAL_REQUIRED**

## Authority and synchronization

- Canonical repository/branch: [Sekiph82/PackLab `main`](https://github.com/Sekiph82/PackLab/tree/main).
- Starting commit after non-destructive fast-forward to fetched `origin/main`: `05b79b7ded977f4bc7fc892f51b07fd351747040`.
- The live `TASKS.md` at that commit explicitly authorized the bounded official release ZIP read-only inspection. Root `TASKS.md` was not edited.
- The supplied [read-only prompt](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_PROMPT.md) and matching [audit criteria](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_AUDIT_CRITERIA.md) were read in full, with the relevant source lock, runtime build contract, controlled builder, prior PL-0350 research, and coordination/audit policy.
- Work used a clean managed PackLab worktree. The user's Desktop checkout was 799 commits behind fetched `origin/main` and contained one modified tracked file plus two untracked files; those files were left untouched. The selected managed worktree was clean and six commits behind, so it was fast-forwarded with `git merge --ff-only origin/main`.

## Read-only work performed

1. Queried the official GitHub release API for CadQuery/OCP tag `7.9.3.1.1`. Confirmed tag target commit `d69b064a3a604ebf245b1f3b14fb54c835a3a571`, asset name `OCP_src_stubs_Windows.zip`, size `6,481,047`, API digest `sha256:290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`, and official release URL. `git ls-remote` confirmed the exact upstream tag commit. PackLab's source lock pins the same revision.
2. Downloaded only the specified official OCP release archive (no mirror, wheel, or additional release asset) to a unique temporary scratch directory. The measured size and SHA-256 matched. Inspected the central directory and member streams without extraction; the archive was 1,613 entries / 62,426,401 uncompressed bytes, rooted under `OCP_src_stubs_Windows/`, with no traversal, absolute-path, or symlink entries. Removed the temporary scratch after recording evidence.
3. Inspected generated source inventory, selected member hashes and content, `CMakeLists.txt`, `OCP.cpp` registrations/version, the C++ helper/header files, and nested stubs. Verified 319 generated module triplets (`.cpp`, `_pre.cpp`, `*_tmpl.hxx`) and 319 module pairs registered in `OCP.cpp` (638 enum/module calls), plus the extension entry point and stubs. The four `IVtk*` modules are VTK-specific.
4. Read the official upstream workflow and actions at workflow commit `81d357f678704c9cd33b7a4e1adf1dfd71bcbe18`, associated with [run 26501389469](https://github.com/CadQuery/ocp-build-system/actions/runs/26501389469). `PYWRAP=false` downloads and stages the released generated source; the separate build action compiles/links C++ without running pywrap. The upstream `novtk` branch patches out VTK and removes the four `IVtk*` modules and registrations, resulting in 315 modules, which conflicts with PackLab's frozen 319-module requirement. The unmodified ZIP CMake also requires VTK.
5. Compared source requirements against PackLab's pinned Windows 2022 / CPython 3.12.15 / SDK 10.0.26100.0 / CMake 3.31.8 / MSVC 19.44.35229.0 build contract, existing `novtk` OCCT configuration, runtime builder assumptions, and dynamically imported CAD module names. No compilation or runtime conclusion was inferred from static source inspection.

## Material findings

- Classification: **INCOMPATIBLE** with the current frozen PackLab no-VTK + all-319-modules contract. A different/updated contract could make the ZIP a pywrap bypass candidate, but no change or build is authorized by this check.
- Expected time reduction if later approved: avoid the prior approximately 5h04m pywrap source-generation stage. OCCT build remains approximately 42m40s from prior evidence; OCP C++ compile/link time is not established.
- Existing blocker remains: 79 OCP native redistribution rows and exact third-party DLL provenance are unknown. This asset does not clear Qt/PySide6, Open3D, notices, source availability, or legal gates.

## Files and validation

- Added only this Codex log and the [read-only inspection report](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_REPORT.md).
- No source code, tests, source lock, root tracker, audit file, OwnerDev runtime, Desktop executable, installer, or dependency was changed.
- Exact checks: `git fetch origin main --prune`; `git rev-list --left-right --count HEAD...origin/main`; `git status --porcelain=v1`; `git merge --ff-only origin/main`; PowerShell `Invoke-RestMethod` against the official release API; `git ls-remote` against the official OCP tag; bounded PowerShell ZIP central-directory and member-stream checks; SHA-256 of the archive and selected members; read-only source searches/inspection for the locked runtime builder, workflow, CMake inputs, module registration, version and import contract.
- Expected success condition: official asset metadata/revision/digest match, ZIP remains within the 200 MiB inspection bound and is safe to inspect, and exact compatibility/limitations are reported. Failure condition: mismatch, unsafe ZIP paths/types, or missing/insufficient module coverage stops the analysis and is reported without building. Actual result: provenance and ZIP integrity matched; 319 module inventory was present before the no-VTK exclusions; the official no-VTK recipe removes four, leaving 315, so compatibility with the frozen build contract fails.
- No code tests, native compilation, pywrap generation, long hosted run, package/installer build, or runtime smoke was run, as required by the read-only prompt.
- Privacy/secrets review: only public upstream source and PackLab public repository metadata/evidence were inspected. No credentials, private scans, supplier files, or private runtime artifacts were read or published. The user's Desktop checkout file contents and active Desktop `PackLab.exe` / OWNER DEV runtime were not accessed or altered.
- Limitations: no generated-source equivalence, native compiler compatibility, ABI, runtime import/CAD, fresh install, or redistribution/legal conclusion is established. VTK removal and the module-count mismatch need owner/criteria resolution before a native build can be authorized.

## Publication boundary and handoff

- Report/log evidence publication commit: [`fa6beeaa57ca8cf43fd5de23c51e6efe618c7247`](https://github.com/Sekiph82/PackLab/commit/fa6beeaa57ca8cf43fd5de23c51e6efe618c7247). It contains only this report and the initial matching log. GitHub `main` visibility and `0 0` local/remote parity were verified after that publication.
- This log does not claim independent audit acceptance or self-close PL-0350. The final log update is separately visible in its GitHub file history.
- Matching [prompt](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_PROMPT.md), [criteria](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_AUDIT_CRITERIA.md), [report](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_REPORT.md), [upstream release](https://github.com/CadQuery/OCP/releases/tag/7.9.3.1.1), and [upstream recipe run](https://github.com/CadQuery/ocp-build-system/actions/runs/26501389469) are the review references.

**AWAITING_INDEPENDENT_AUDIT / OWNER_BUILD_APPROVAL_REQUIRED**
