# PL-0350 R03 | ChatGPT Independent Audit V01

Date: 2026-10-13
**Verdict: AUDITED_PARTIAL_CHANGES_REQUIRED**
Stop: `BATCH_STOPPED_AT_PL-0350 / OCCT_SDK_INSTALL_LAYOUT_VALIDATION_MISMATCH`
PL-0350: **OPEN**. No sealed replacement OpenGL-enabled OCCT SDK, no OCP runtime, no packaged installer or cache-HIT.

## Sources actually inspected

- R03 builder log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OPENGL_SDK_CONTRACT_R03_CODEX_LOG.md
- R03 blocker report: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OPENGL_SDK_CONTRACT_R03_REPORT.md
- Current builder master handoff: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md
- Implementation commit: https://github.com/Sekiph82/PackLab/commit/038d3c462ef176293cb37d778fc79676f3bbf0be
- Hosted retained-SDK analysis: https://github.com/Sekiph82/PackLab/actions/runs/38304468474
- First capacity blocked run: https://github.com/Sekiph82/PackLab/actions/runs/38304697335
- Corrected cold run: https://github.com/Sekiph82/PackLab/actions/runs/38305407910
- SDK job **114998244496**: https://github.com/Sekiph82/PackLab/actions/runs/38305407910/job/114998244496
- Pinned native SDK producer code: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/build_controlled_occt_sdk.py
- SDK validator: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/validate_controlled_occt_sdk.py
- Actual downstream generated OCP builder: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/build_controlled_ocp_from_generated_sources.py

Auditor independently fetched the actual R03 job table, failed SDK job logs, four current producer/validation/dependency-source files and live GitHub artifact inventory for runs 38304468474, 38304697335, 38305407910, 38263302823. Local test results and Desktop preservation are builder-reported and not reproduced independently from the user's computer.

## Directly verified

1. **R03 architecture correction works through OCCT native install.** The hosted logs independently show `TKOpenGl.vcxproj` output, installed `install/inc/OpenGl_Context.hxx` at 21:20:45Z, `install/win64/vc14/lib/TKOpenGl.lib` and `install/win64/vc14/bin/TKOpenGl.dll` at 21:20:46Z. This confirms the CMake `USE_OPENGL=ON`, `USE_VTK=OFF` pathway produced the needed graphics toolkit. Do **not** conflate with finished SDK: sealing/upload never happened.
2. **Precise failure is a false-negative path check after install.** `build_controlled_occt_sdk.py` copies the actual installed tree to the output and then unconditionally demands case-folded relative paths `inc/opengl_context.hxx`, `lib/tkopengl.lib`, `bin/tkopengl.dll`. The first is correct, but OCCT Windows installs the latter two under `win64/vc14/lib/` and `win64/vc14/bin/`. At 21:20:54Z `ValueError: OCCT install lacks the required OpenGL header, import library, or runtime DLL` stops before schema-v2 manifest write. `validate_controlled_occt_sdk.py` independently repeats the same wrong flattened relative-path requirements. These must both change, including tests and consumers.
3. **Hosted outcomes verified:** run 38304697335 failed at the corrected-but-earlier capacity budget gate with all native jobs skipped; corrected cold run 38305407910 capacity SUCCESS, SDK job FAILURE, OCP and Studio SKIPPED. SDK job build/install/validator step lasted approximately 38m52s; no usable new SDK was sealed. The later micromamba post-cleanup warning was not the stop cause.
4. **Artifact absence verified:** runs 38304468474, 38304697335 and 38305407910 currently return **zero** Actions run artifacts. Previously sealed R02 OCCT artifact **11755977987** (56,405,631 bytes; SHA-256 `1ad03b366958f0a81d98813fac313d85d0133e79db9e85f4844d783b0306d0ae`) and source evidence **11755908172** still exist on run 38263302823 and are unexpired. That OLD SDK was built with `USE_OPENGL=OFF`, so it is NOT a substitute for the new `USE_OPENGL=ON` SDK. Installed output from failed R03 runner is gone; cannot be resumed on a new runner without an appropriate checkpoint.
5. **Builder reported tests:** 34 focused Python tests, Ruff, formatting, targeted mypy, compileall, 15 workflow module probes, git diff checks PASS. GitHub accepted and executed the workflow. No installer/native OCP smoke or clean Windows test was performed.
6. **R03 owner/scope handling:** no second cold retry, no warm run, no native work on the user's Desktop, root `TASKS.md` and independent auditor docs unchanged by Codex. Builder master handoff is updated to R03, fixing the stale R01 handoff concern.

## Extra independent engineering findings for R04

- Current producer path assertion (in `tools/packaging/build_controlled_occt_sdk.py`) and current consumer SDK validator (in `tools/packaging/validate_controlled_occt_sdk.py`) are **both wrong**. Correct in one shared, exact, case-insensitive **canonical layout contract**: `inc/OpenGl_Context.hxx`, `win64/vc14/lib/TKOpenGl.lib`, `win64/vc14/bin/TKOpenGl.dll`. Do not use basename-only or unrestricted `rglob` acceptance of DLLs outside the sealed SDK tree. Ensure real CMake package paths and downstream OCP include and LIB/DLL search paths still agree; this project's OCP builder already discovers OCCT DLL and exported config via bounded `rglob`, so do not rewrite functioning logic without evidence.
- Replace test fixtures' flattened `bin/TKernel.dll`/`lib/TKernel.lib` assumptions with the actual installed `win64/vc14` layout (include proper CMake/config root). Add explicit regressions for valid canonical layout and missing header/lib/dll, wrong duplicate paths, case collisions, nonsealed extras, source/manifest tampering, traversal, CMake export mismatch.
- **Cost and reliability:** future hosted OCCT build again takes tens of minutes because R03 OPENGL=ON results were never sealed. No blind repeat: first complete all path/contract checks using tiny fixtures and, if useful, an imported read-only sample of actual R03 job log paths; then make a controlled manual single cold run and ensure the validated SDK is sealed and uploaded *before* attempting the OCP ~2h compile. Do not modify existing immutable R02 artifacts.
- Native source, exact 315 No-VTK modules, Python 3.12.15, four workers, manual-only workflow, hash manifests, ABI, notices and packaged Installer gate remain unchanged. No 5-hour pywrap or opaque wheel substitution.

## Final disposition

`AUDITED_PARTIAL_CHANGES_REQUIRED / OCCT_SDK_INSTALL_LAYOUT_VALIDATION_MISMATCH`.
Next same-task `R04` is a narrowly scoped **Windows OCCT SDK layout contract correction** and guarded existing 315 OCP/Installer continuation. Parent PL-0350 remains unchecked; PL-0351, PL-0368 and M17 remain blocked.

R04 Codex:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_SDK_WINDOWS_LAYOUT_R04_CODEX_PROMPT.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_SDK_WINDOWS_LAYOUT_R04_CHATGPT_AUDIT_CRITERIA.md
