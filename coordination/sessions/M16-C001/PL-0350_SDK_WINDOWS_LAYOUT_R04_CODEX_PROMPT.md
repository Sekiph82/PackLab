# PL-0350 R04 | Fix OCCT Windows SDK Install Layout, Then Gated Hosted Continuation

**CODEX MASTER PROMPT. SAME PL-0350 task, not another milestone. Owner-approved 315 No-VTK source-built PackLab Installer route remains in force.**
R03 independent audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OPENGL_SDK_R03_CHATGPT_AUDIT_V01.md
R04 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_SDK_WINDOWS_LAYOUT_R04_CHATGPT_AUDIT_CRITERIA.md
Original owner authorization:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OWNER_APPROVAL_HOSTED_BUILD_315_NOVTK.md

## Proven failure, not a new CAD architecture problem

Hosted cold run https://github.com/Sekiph82/PackLab/actions/runs/38305407910 actually installed:
- `install/inc/OpenGl_Context.hxx`;
- `install/win64/vc14/lib/TKOpenGl.lib`;
- `install/win64/vc14/bin/TKOpenGl.dll`.

But both Python SDK producer and SDK consumer validator mistakenly demand flattened `lib/TKOpenGl.lib` and `bin/TKOpenGl.dll`. GitHub log shows the files were created, and only **after 38m52s of OCCT build/install** the Python assertion failed. R03 runner is gone and **no new sealed SDK cache/artifact** was produced. The old retained R02 SDK artifact ID 11755977987 was `USE_OPENGL=OFF`, NOT compatible with the new graphics-module SDK. Do NOT download/repack/forge it as an ON SDK.

## Step A: eliminate entire path mismatch using zero native rebuilds

1. Read LIVE `origin/main:TASKS.md`, R03 audit, current owner authority and source-locked OCCT/OCP contracts; sync managed worktree non-destructively. Preserve user Desktop dirty files, prior-good PackLab EXE/OwnerDev, other worktrees and caches. Codex does NOT touch root `TASKS.md`, owner decisions or ChatGPT audit files.
2. Audit **all** assumptions about OCCT installed include, LIB, DLL, CMake export and copy-tree paths in `tools/packaging/build_controlled_occt_sdk.py`, `validate_controlled_occt_sdk.py`, `audit_controlled_occt_sdk_dependencies.py`, `build_controlled_ocp_from_generated_sources.py`, `controlled_ocp_runtime_bundle.py`, Studio packaging/notice map and tests. Avoid repeating the same false path assumption after the SDK gets past the first check.
3. Implement ONE strict, shared canonical Windows OCCT layout definition/validator anchored to exact installed hierarchy:
   `inc/OpenGl_Context.hxx`,
   `win64/vc14/lib/TKOpenGl.lib`,
   `win64/vc14/bin/TKOpenGl.dll`.
   Require **all** files with correct case-insensitive Windows handling but no ambiguous duplicate or path traversal/symlink shortcuts; keep headers and other libraries in their actual installed directories; preserve source/toolchain hash, relative path, sizes and per-file digest in schema-v2 SDK metadata. No flatten/copy hack into parallel `lib/` or `bin/`; no basename-only success. Validate source exact revision, OCCT CMake exported include/link paths and each `USE_OPENGL=ON / USE_VTK=OFF` option.
4. Producer and consumer MUST apply the same shared layout contract, including `validate_controlled_occt_sdk.py` and any downstream OCP/header closure audits. Confirm `OpenCASCADEConfig.cmake` actual exports point to present files, and OCP CMake can find OpenGl includes/import libraries/DLLs; correct missing link/path wiring only if a real test reveals it. Keep 315 module identities, Python native 3.12.15, bootstrap 3.12.10, official generated ZIP hashes, exact source revisions, four C++ workers, no VTK, no pywrap, no prebuilt opaque OCP wheel. If changing SDK producer/validator invalidates cache contract, use new exact cache key/schema and fail-closed migration; never trust an older `USE_OPENGL=OFF` v2 cache.
5. Write ACTUAL cheap synthetic-fixture and subprocess tests reproducing R03 bug: nested `win64/vc14` tree should PASS with full manifest; flattened-only and missing header, lib or dll should FAIL; collisions/unsafe paths/extra files/altered hashes/wrong flags/source lock should FAIL. Exercise BOTH build producer's post-install assertion via a small test seam (without invoking native OCCT CMake) AND real consumer validator, plus downstream dependency scanner. A string search or test of only the validator is insufficient.
6. Include a prebuild **hosted cheap layout/SDK-closure smoke** in the `preflight_only` safe path, based on deterministic tiny fixtures matching the actual R03 layout and containing expected CMake export paths; ensure OCCT/OCP/Studio jobs SKIP, no long source download or native compilation. Add checks that every heavy source step occurs only after this smoke PASS.

## Step B: precisely one owner-approved controlled cold continuation

7. Execute bounded local checks (focused tests, affected regression, Ruff/format, mypy, compileall, real YAML parser if installed, Python workflow imports, diff hygiene), preserve 40GiB owner C: free rule, 4/2/8GiB disposable limits, no owner-local OCCT/OCP builds or broad cache cleanup. Confirm manual-only native workflow `workflow_dispatch` with exact SHA and affirmative input, no automatic 6h trigger on code push, all quality CI available.
8. Push changes to `main` only after checks; run ONE quick `preflight_only=true` hosted diagnostic at exact SHA and independently verify native jobs SKIPPED. If diagnostic fails, STOP without compiling.
9. If green, start ONE guarded `preflight_only=false` cold workflow on GitHub-hosted Windows 2022. SDK stage actually compiles source-locked OCCT `USE_OPENGL=ON`, `USE_VTK=OFF`; validates real flattened `inc/` plus `win64/vc14/lib`/`bin` Windows SDK layout, full headers/toolkits and CMake export closure, source/manifest hashes, complete payload and artifact size budget. **Seal and upload the OCCT SDK checkpoint FIRST**, and verify the new GitHub Actions artifact appears with ID, name, byte count and checksum BEFORE allowing costly 315-module OCP native compilation. Build cache must not be treated as saved without actual evidence.
10. Use this exact same-run checked SDK for official 319→315 generated no-VTK OCP compile under Python 3.12.15, with a fast actual SDK header/link/compile probe first. After OCP native import+CAD/STEP smoke, package real Windows PackLab Studio, QtPdf/Open3D/DXF/STEP/CAD smoke, prove all source/license/NOTICE/native ownership and unresolved=0, then emit unsigned Installer as an Actions artifact with SHA/size. Retain `legal_review_required=true` and `public_release_authorized=false`. If any stage fails, STOP at first issue, preserve all already-sealed artifacts; no blind repeat of OCCT or 2h OCP. Only if cold fully passes, run ONE genuine exact-cache warm HIT workflow for independent reproduction.
11. No unauthorized signing/public release, no PL-0351, PL-0368 or M17; no fake Installer or false tests. No background work. Every build must be explicit/manual hosted.

## Required handoff

Builder log `coordination/sessions/M16-C001/PL-0350_SDK_WINDOWS_LAYOUT_R04_CODEX_LOG.md`, report `PL-0350_SDK_WINDOWS_LAYOUT_R04_REPORT.md`, and update builder-owned `MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md` to actual latest state while keeping historical logs. Show test counts and exact GitHub preflight/cold/warm links or explicit absence, source/SDK config/path evidence, proven artifact digests and cache HIT/MISS, native/Installer hashes if truly produced, owner Desktop preservation, Git parity.

End `READY_FOR_INDEPENDENT_PL0350_AUDIT` only after all real installer, license, CAD and cold/warm gates; otherwise `BATCH_STOPPED_AT_PL-0350 / <FIRST_ERROR> / AWAITING_INDEPENDENT_AUDIT`. Root TASKS and audit docs stay ChatGPT-only.
