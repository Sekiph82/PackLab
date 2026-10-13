# Master Handoff — PL-0350 Hosted 315-Module No-VTK Build

Date: 2026-10-13
Latest implementation: `5ff482278fae05bbae029b5185fa2838d1cb70b9` (R05 hosted dependency preflight)
Status: **BATCH_STOPPED_AT_PL-0350 / FMT_PROVENANCE_REQUIRED (UCRT + VC14_RUNTIME) / AWAITING_INDEPENDENT_AUDIT**

## R05 current state

R05 preserved the original OpenGL-enabled R04 SDK and source evidence in a noncompiling Windows-hosted recovery. The new artifact `11796717315` contains the exact original checkpoint bytes plus lineage; the recovery verified 7,991 SDK files / 173,975,159 bytes and payload SHA-256 `7ad1c8b0b2634d32eeada2e6d8fa4fb6e85f7f3c1e6989e8beab7ebdbc2c9031`.

The manual Windows 2022 fmt preflight [38370004545](https://github.com/Sekiph82/PackLab/actions/runs/38370004545) verified the exact locked `fmt` package archive (SHA-256 `1d6d6f1bf284e50cf617ce9a6250e0bf70bd0d30b068568364d6b1852aad9466`), installed AMD64 `fmt.dll` (SHA-256 `0d4edfe1411f4a7c5f57758239f0f1e6e1cff7f2d0ae5f9511a1dfacc08b388d`), upstream source/MIT notice hashes, pinned feedstock recipe, CMake target and PE imports. The probe stopped before any native build because six imported API-set DLLs were owned by locked `ucrt 10.0.26100.0` and three VC DLLs by locked `vc14_runtime 14.51.36247`; no exact PackLab source/license/redistribution entries exist for these current conda runtime files. The workflow uploaded report artifact `11799090609` and failed closed with `FMT_PROVENANCE_REQUIRED`.

Hosted Python quality [38369998989](https://github.com/Sekiph82/PackLab/actions/runs/38369998989) passed. No OCP/OCCT compile, Pyd quarantine, runtime CAD smoke, Studio package, Installer, or warm-cache run occurred. Root `TASKS.md`, independent audit files, owner Desktop and known-good EXE remain untouched.

R05 implementation commits: `cfcbaa99621868e1238a3210e7113fe77a896d4d`, `bd1b2e25dacbbed991f843e9b7c040e9dd055a0e`, `858c8ac2206a8a80a5c9be5834ee2c1c0061ea42`, `3450afd83e369d84f67d51c717521f563bf9adc4`, `5ff482278fae05bbae029b5185fa2838d1cb70b9`. Detailed records: `PL-0350_FMT_DEPENDENCY_PROVENANCE_R05_CODEX_LOG.md` and `PL-0350_FMT_DEPENDENCY_PROVENANCE_R05_REPORT.md`.

**Awaiting ChatGPT's independent audit. Stop at the unresolved UCRT/VC runtime source/license and redistribution gate; do not retry OCP compilation or advance to PL-0351.**

## R04 current state

R04 introduced one shared strict Windows OCCT SDK layout contract for `inc/OpenGl_Context.hxx`, `win64/vc14/lib/TKOpenGl.lib`, and `win64/vc14/bin/TKOpenGl.dll`. Producer, consumer, downstream dependency audit, generated OCP builder, and runtime metadata use this contract. Cache namespaces were bumped to v4. A synthetic hosted preflight verified producer, consumer, and downstream scanner behavior without native builds.

Implementation commit `a2805616c9c0dd665e48b1de82c8436ea64b0805` was pushed to `main`. Focused checks passed (37 passed, 1 skipped), as did Ruff, format, mypy, compileall, 16 workflow Python imports, YAML parse, preflight fixture, and diff hygiene.

The valid exact-SHA hosted preflight [38346246435](https://github.com/Sekiph82/PackLab/actions/runs/38346246435) passed and independently skipped native SDK/OCP/Studio jobs. The single authorized cold run [38346317865](https://github.com/Sekiph82/PackLab/actions/runs/38346317865) compiled, validated, sealed, and uploaded the canonical OpenGL-enabled SDK before starting OCP. Preserved artifacts:

- SDK: ID `11790440856`, `packlab-occt-sdk-38346317865-1`, 57,520,243 bytes, SHA-256 `467b44ab0fb747343cb55e55e71a0dd4ecadb989fd7eed22d1e49fff3153ddf8`.
- Corresponding-source evidence: ID `11790585684`, `packlab-native-source-evidence-38346317865-1`, 1,398 bytes, SHA-256 `091c391b8d6ccda19823f57eae891b1dd45383b164c117ca05928df6bafd2018`.

The official OCP extension compiled, but its post-build dependency ownership check stopped on `ValueError: compiled OCP references an unowned DLL dependency: fmt.dll`. OCP smoke/runtime artifact steps and Studio packaging were skipped. No Installer, compliance clearance, warm-cache run, signing, or release exists. No retry was dispatched. Parent PL-0350 remains unaudited and open.

Detailed R04 records:

- `PL-0350_SDK_WINDOWS_LAYOUT_R04_CODEX_LOG.md`
- `PL-0350_SDK_WINDOWS_LAYOUT_R04_REPORT.md`

**Awaiting ChatGPT's independent audit and separately issued follow-up prompt. Do not retry the native build, claim acceptance, or proceed to PL-0351.**

## R03 current state

R03 verified the retained OpenGL-disabled SDK read-only, audited all 315 generated consumers, and proved that the old SDK omitted 97 OpenGl headers plus `TKOpenGl.lib` and `TKOpenGl.dll`. The builder was updated to use `USE_OPENGL=ON` while retaining `USE_VTK=OFF`, with versioned SDK metadata/cache keys and fail-fast dependency checks.

The first exact-SHA native dispatch, [38304697335](https://github.com/Sekiph82/PackLab/actions/runs/38304697335), failed at capacity preflight before native work because the fixed two-run ceiling arithmetic could not account for the retained R02 artifacts. The preflight was corrected to split remaining space under the unchanged 8 GiB ceiling, and upload steps now check cumulative current-run artifact usage. This change is commit `038d3c462ef176293cb37d778fc79676f3bbf0be`.

The corrected single authorized native dispatch [38305407910](https://github.com/Sekiph82/PackLab/actions/runs/38305407910) passed capacity preflight and ran the source-pinned OCCT build. CMake built and installed `OpenGl_Context.hxx`, `TKOpenGl.lib`, and `TKOpenGl.dll`; the latter two were installed under `win64/vc14/lib/` and `win64/vc14/bin/`. The post-install validator incorrectly expected flattened `lib/` and `bin/` paths and stopped with `OCCT install lacks the required OpenGL header, import library, or runtime DLL`.

No SDK manifest/seal/upload/v3 cache was produced. OCP runtime and Studio package jobs were skipped. The old immutable SDK artifact `11755977987` and matching source-evidence artifact `11755908172` remain unchanged. No new SDK artifact SHA exists. There is no OCP binary, native smoke, compliance clearance, installer, warm cache-hit proof, or acceptance. R03 stops at this first manifest/layout blocker; no second build/retry was attempted.

R03 local validation: 34 focused tests passed; Ruff, Ruff format, targeted mypy, compileall, 15 workflow Python imports, and diff checks passed. No local YAML parser was available; the exact workflow was accepted and executed by GitHub. No owner Desktop/native files or root `TASKS.md`/ChatGPT audits were edited. No adjacent PL task was started.

Detailed records:

- `PL-0350_OPENGL_SDK_CONTRACT_R03_CODEX_LOG.md`
- `PL-0350_OPENGL_SDK_CONTRACT_R03_REPORT.md`
- Retained-SDK diagnostic: [38304468474](https://github.com/Sekiph82/PackLab/actions/runs/38304468474)

**Awaiting ChatGPT's independent audit and a separately issued follow-up prompt. Do not retry the native build, claim acceptance, or proceed to PL-0351.**

## Historical R01 record

R01 corrected setup-python bootstrap pins to 3.12.10 while preserving native conda Python 3.12.15, added native interpreter assertions, and introduced a guarded preflight-only dispatch. R01's exact-SHA quality and diagnostic preflight passed. The single R01 cold continuation stopped before source download because `fetch_verify_windows_native_sources.py` raised `ModuleNotFoundError: No module named 'tools'`; no native artifact, installer, or warm-cache proof was produced.

- R01 implementation log: `PL-0350_SETUP_PYTHON_BOOTSTRAP_R01_CODEX_LOG.md`
- R01 blocker report: `PL-0350_SETUP_PYTHON_BOOTSTRAP_R01_REPORT.md`
- R01 cold dispatch: [38257727675](https://github.com/Sekiph82/PackLab/actions/runs/38257727675)
- R01 failed source-fetch job: [114840209934](https://github.com/Sekiph82/PackLab/actions/runs/38257727675/job/114840209934)
