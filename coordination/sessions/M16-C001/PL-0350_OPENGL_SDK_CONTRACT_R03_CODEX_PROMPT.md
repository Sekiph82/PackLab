# PL-0350 R03 | Correct OCCT OpenGL SDK Contract BEFORE 315-Module OCP Compile

Executor: CODEX. SAME PL-0350. Owner-approved GitHub-hosted source-built 315-module No-VTK OCP route only. This is an SDK configuration correction, NOT permission for unbounded repeated builds or new product scope.

Independent audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_REPO_IMPORT_PATH_R02_CHATGPT_AUDIT_V01.md
R03 acceptance:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OPENGL_SDK_CONTRACT_R03_CHATGPT_AUDIT_CRITERIA.md
Owner authority:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OWNER_APPROVAL_HOSTED_BUILD_315_NOVTK.md
Last cold build:
https://github.com/Sekiph82/PackLab/actions/runs/38263302823

## Reality and requirement

- Source-built OCCT SDK job PASSED (~50m) and GitHub artifact ID **11755977987** is live: `packlab-occt-sdk-38263302823-1` / 56,405,631 bytes / archive SHA256 `1ad03b366958f0a81d98813fac313d85d0133e79db9e85f4844d783b0306d0ae`; matching source-evidence artifact ID 11755908172. Preserve both without modification. Verify inner manifest separately; outer ZIP hash is not inner content attestation.
- OCP source-generated C++ compile failed after ~2h (first missing header after ~1h): `OpenGl.cpp` and `OpenGl_pre.cpp` require `OpenGl_Context.hxx`, MSVC C1083.
- Current `tools/packaging/build_controlled_occt_sdk.py` sets **`-DUSE_OPENGL=OFF`** along with `-DUSE_VTK=OFF`. At the pinned OCCT commit, CMake removes `TKOpenGl` when USE_OPENGL=OFF. Source `src/OpenGl/OpenGl_Context.hxx` exists. Exactly 315 owner-approved No-VTK generated bindings **include** a non-VTK OpenGl binding. **No-VTK must NOT be conflated with No-OpenGL.**

## R03 gates, in this exact order

**R03.A — read-only inventory and cheap tests FIRST.**
1. Fetch/sync origin/main non-destructively in clean managed worktree. Read latest root TASKS.md and audit. Owner dirty Desktop/previous-good EXE/active worktrees protected; no local native compile, bulk copy, shared cache deletion or audit/TASKS edit by Codex.
2. Obtain retained OCCT SDK artifact *read-only* using GitHub-hosted quick/manual diagnostic or bounded safe download, verify actual GitHub artifact SHA, extract safely within bounded scratch on hosted runner, validate sealed per-file SDK manifest+lock. Print evidence for `OpenGl_Context.hxx`, `TKOpenGl.lib`, `TKOpenGl.dll`, all OCCT installed include directories and CMake exported target references, SDK OCI source/toolchain/provenance. Do not infer missing headers solely from log text.
3. Independently examine pinned upstream OCCT CMake and `src/OpenGl`/TKOpenGl toolkit membership; compare required generated-315 `#include` directives and linked toolkit/dependencies to actual OCCT SDK headers/libs. Log FULL deficiency set, not just first file. Distinguish SDK content omissions from include-path-only problems. **If SDK actually contains correct header and libs, FIX ONLY OCP CMake include path and keep the valid SDK without rebuild.** Rebuild SDK ONLY when proven incompatible/missing.
4. If old SDK truly lacks TKOpenGl, explicitly **enable USE_OPENGL=ON and keep USE_VTK=OFF** in OCCT builder. Keep exactly four VTK bindings omitted, 315 retained; do not remove the OpenGl generated module, disable CAD, copy lone header as workaround or use opaque prebuilt wheel. Pin the new OCCT compile-option contract in SDK metadata and checker, tests and stage cache identity. A changed SDK configuration must produce a NEW exact key; old OFF SDK cannot be accepted for ON without a full conforming SDK. Preserve source SHA, native Python 3.12.15, compiler/SDK versions and four workers. Confirm OpenGL system import/link libraries are available for Windows 2022 using standard official SDK. Account for any additional graphics runtime DLLs in redistribution/source/notice inventory.
5. Implement **fail-fast full include/link audit**: for all 315 generated C++/pre C++ units (not only module names), parse or compile-probe relevant OCCT header includes and explicit library/target closure against the SDK to detect missing `OpenGl_Context.hxx`, related OpenGl and other headers, TKOpenGl import LIB and runtime DLL before native OCP compilation. Distinguish quoted local headers vs OCCT headers. If unresolved dependencies remain, STOP BEFORE expensive OCP C++ build. Unit tests MUST deliberately omit a required OpenGl header/lib and prove rejection, validate source-lock and manifest tampering, casefold duplicates, and partial SDK. Existing validator's 'some .dll + some .lib' checks are inadequate for a 315-module target.
6. Before new hosted cold run, use quick diagnostics in separate guarded workflow mode to execute actual real SDK/consumer compatibility checks. If running against the existing OFF SDK, it must FAIL **as expected** to validate the detection; a predicted mismatch is not a green preflight. Do not accidentally launch OCCT/OCP compilers during cheap diagnostic.

**R03.B — controlled hosted build once evidence passes.**
7. Keep workflow `workflow_dispatch` only with exact main commit, affirmative native input and import/provenance preflight gate. Test all steps against accidental auto-trigger. Run focused/YAML/subprocess/synthetic dependency tests, Ruff, format, mypy, compileall, and appropriate safe regression under 40 GiB C-free and 4/2/8 GiB disposable. No native build on owner's machine.
8. If new SDK needed, do ONE source-pinned hosted OCCT `USE_OPENGL=ON`, `USE_VTK=OFF` build and seal validated SDK artifact with complete header, TKOpenGl LIB/DLL, configured native options, per-file SHA and versioned cache key. Upload/retain BEFORE starting any OCP compilation. Do not reuse incompatible OFF SDK. If old SDK is actually complete, explicitly reuse its verified immutable artifact and skip the OCCT rebuild.
9. Add hosted source-consumer compatibility gate immediately AFTER SDK is verified and BEFORE heavy OCP build; this must exercise real `OpenGl_Context.hxx` and all 315 include/link dependencies, not merely string-check flags. A failing SDK gate must SKIP OCP C++ build. Log SDK artifact names/digests/budget.
10. Only after genuine SDK compatibility PASS, launch the approved staged 315 No-VTK OCP C++ compile, source-locked Python 3.12.15, no pywrap. Stop at the FIRST new compile/manifest issue, retain fully validated checkpoint. If native 315 OCP real CAD/STEP smoke passes, proceed Studio QtPdf/Open3D/DXF packaged smoke and exact notice/source/redistribution clearance; produce unsigned Installer ONLY when zero blockers. Only after cold full PASS run a SINGLE real warm cache-HIT proof.
11. No false Installer/PASS, no PL-0351, PL-0368, M17, signing or public release. End on first hard blocker with facts, avoid unbounded reruns. Owner desktop executable remains intact; builder does not edit root TASKS or ChatGPT audits.

## Logs

Publish:
- `coordination/sessions/M16-C001/PL-0350_OPENGL_SDK_CONTRACT_R03_CODEX_LOG.md`
- `coordination/sessions/M16-C001/PL-0350_OPENGL_SDK_CONTRACT_R03_REPORT.md`
- Refresh builder-owned `MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md` (currently stale at R01) to R03's actual latest first stop or real installer state. Preserve historical logs.

Record exact hosted job/run URLs and HEAD SHA, old vs new SDK contents/config/cache identity, real dependency closure results, tests, artifact bytes/SHA and source-lock evidence, compile time, actual packaged smoke and Installer digest if available, license/notices, local disk safety and GitHub origin/main parity. State `BATCH_STOPPED_AT_PL-0350 / <FIRST_FAIL>` or `READY_FOR_INDEPENDENT_PL0350_AUDIT` only if actual full Installer+HIT gates pass.
