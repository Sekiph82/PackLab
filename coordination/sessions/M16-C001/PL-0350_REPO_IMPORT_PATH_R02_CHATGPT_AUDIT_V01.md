# PL-0350 R02 | ChatGPT Independent Audit V01

Date: 2026-10-12
Verdict: **AUDITED_PARTIAL_CHANGES_REQUIRED**
Blocking stage: **OCP_COMPILE_FAILED_OPENGL_CONTEXT_HEADER_MISSING**
Parent PL-0350 remains OPEN. No OCP native runtime, Studio Installer, source/notice clearance or warm HIT.

## Evidence independently checked

- Implementation: https://github.com/Sekiph82/PackLab/commit/4f064e2f44359a40298d13baece02dcb18fb01f7
- Codex report: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_REPO_IMPORT_PATH_R02_REPORT.md
- Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_REPO_IMPORT_PATH_R02_CODEX_LOG.md
- Quality https://github.com/Sekiph82/PackLab/actions/runs/38262833083
- Quick preflight https://github.com/Sekiph82/PackLab/actions/runs/38262855024
- Cold run https://github.com/Sekiph82/PackLab/actions/runs/38263302823 ; OCCT job 114859244116, failed OCP job 114879875867
- Exact source-built OCCT code: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/build_controlled_occt_sdk.py
- OCP producer: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/build_controlled_ocp_from_generated_sources.py
- Exact upstream OCCT source CMake: https://github.com/Open-Cascade-SAS/OCCT/blob/a016080bf6738d6aeae020badee4e888ad1540a5/CMakeLists.txt
- Upstream missing header source: https://github.com/Open-Cascade-SAS/OCCT/blob/a016080bf6738d6aeae020badee4e888ad1540a5/src/OpenGl/OpenGl_Context.hxx

Directly read actual GitHub Actions job outcomes, failed OCP job log, current SDK/OCP producer and validator code, original source CMake at pinned revision, and uploaded artifact metadata. This confirms the independent conclusions; builder-local tests/owner machine state were not rerun.

## Findings

**F01 PASS, import repair:** 21 workflow CLI calls converted to repository module execution. Actual Windows quick diagnostic and full cold capacity preflight succeeded; 12 import probes, official 319→315 source patch, Python bootstrap 3.12.10 and native conda 3.12.15 pass. Exact-SHA quality job SUCCESS. Builder reports six focused tests PASS, Ruff, formatting, mypy, compileall PASS. No new full-suite run; no owner-local native build.

**F02 PASS, first truly reusable native intermediate:** Cold OCCT source build/install/seal job completed successfully (~50m). Exact run 38263302823 contains TWO live GitHub Actions artifacts:
- OCCT SDK: ID 11755977987, name `packlab-occt-sdk-38263302823-1`, 56,405,631 bytes, GitHub artifact SHA256 `1ad03b366958f0a81d98813fac313d85d0133e79db9e85f4844d783b0306d0ae`.
- Source evidence: ID 11755908172, 1,398 bytes, artifact SHA256 `4b596da7de0616b58bcf21194dc0bc832e6f53464282b87c1199bc325bd35e9d`.
Both were unexpired when checked. These archive digests are outer artifact digests; independently verify inner SDK file hashes using its sealed SDK metadata before any reuse. No OCP artifact.

**F03 HARD BLOCK, specific native contract error:** Actual OCP C++ build failed with MSVC C1083 in `OpenGl.cpp:41` and `OpenGl_pre.cpp:40`, both including missing `OpenGl_Context.hxx`; first errors appeared 16:33Z, compile finally stopped 17:25Z. This was not a time-budget failure. Studio job skipped. No OCP compiled binary.

**F04 ROOT CAUSE strongly evidenced:** PackLab OCCT SDK builder explicitly sets **`-DUSE_OPENGL=OFF` AND `-DUSE_VTK=OFF`**. The pinned upstream OCCT 7.9.3 CMake removes `TKOpenGl` and `TKOpenGlTest` when `USE_OPENGL=OFF`; upstream source contains `src/OpenGl/OpenGl_Context.hxx`. Yet PackLab's owner-approved 315-module No-VTK OCP source *retains its non-VTK `OpenGl` module*, which imports this header. **No-VTK does not mean No-OpenGL.** The SDK and OCP module-surface contracts are inconsistent. Confirm SDK artifact lacks exact header/import lib in bounded read-only inventory before the build-route correction. The SDK validator only checks for *any* DLL, any LIB and CMake config, not for 315-module OCP-required graphics headers/toolkits. This allowed an incomplete-for-OCP SDK to pass sealing.

**F05 SECONDARY ISSUE:** The builder's `MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md` on main still describes R01's import failure and old implementation, rather than R02's new achieved SDK / OpenGL failure. Update builder-owned master handoff as part of R03; keep only root TASKS.md as authoritative tracker.

## Remediation constraints and reuse

1. First **inspect the existing sealed OCCT artifact** without compiling. Verify source lock/manifest, actual OpenGl headers and `TKOpenGl` import/runtime libraries; compare against generated source `#include` requirements and CMake link targets for all retained modules.
2. Preserve exactly **315 No-VTK OCP modules**. Do not silently cut `OpenGl` or another required module, copy a lone header into an incomplete SDK, disable CAD, or substitute a prebuilt opaque OCP wheel.
3. If artifact is missing OpenGL toolkit (high-confidence from pinned OCCT build flags), corrected SDK must enable **`USE_OPENGL=ON` while preserving `USE_VTK=OFF`**. Require a new hash-identified SDK configuration/cache key and updated SDK manifest, negative tests, and an import-header/link-library dependency closure check **BEFORE starting long OCP compile**. Do not claim the existing OFF SDK is reusable for an ON contract. Preserve the old artifact untouched. Generate a complete verified replacement OCCT SDK as necessary; this means a single additional ~50-minute hosted SDK build, not a 5-hour pywrap rerun.
4. Add lightweight precompiled header/toolkit dependency checks for generated 315 sources and OCCT SDK to fail within minutes on missing includes/libs. Test via small fixtures, and read-only validate regenerated SDK before launching OCP. Check package shipping source/notices for newly included graphics DLLs.
5. Manual-only hosted workflow with existing job gates and native Python 3.12.15; staged, sealed OCCT→OCP→Installer; no heavy owner-local operations, no blind six-hour reruns. One controlled new cold attempt only when fail-fast checks and hosted source/SDK handoff pass, and one warm hit after fully green.
6. Continue reporting precise first native compiler failures; retain validated artifacts across failures. Owner Desktop untouched. No PL-0351/M17/PL-0368 until actual independently audited Installer.

Focused same-task R03 prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OPENGL_SDK_CONTRACT_R03_CODEX_PROMPT.md
Corresponding criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OPENGL_SDK_CONTRACT_R03_CHATGPT_AUDIT_CRITERIA.md

**Result:** `AUDITED_PARTIAL_CHANGES_REQUIRED / OCP_COMPILE_FAILED_OPENGL_CONTEXT_HEADER_MISSING`. OCCT SDK *build* and *artifact creation* accepted as achieved milestones, but current SDK is not proven compatible with complete 315-module OCP and may require regeneration under corrected OpenGL configuration. No installer PASS.
