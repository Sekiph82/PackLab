# Master Handoff — PL-0350 Hosted 315-Module No-VTK Build

Date: 2026-10-13
Latest implementation: `038d3c462ef176293cb37d778fc79676f3bbf0be` (R03)
Status: **BATCH_STOPPED_AT_PL-0350 / OCCT_SDK_INSTALL_LAYOUT_VALIDATION_MISMATCH**

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
