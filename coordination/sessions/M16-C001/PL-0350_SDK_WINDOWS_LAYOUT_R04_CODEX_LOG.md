# PL-0350 R04 Codex Implementation Log

Date: 2026-10-13
Cycle: M16-C001
Task: PL-0350 SDK Windows layout R04
Status: **BATCH_STOPPED_AT_PL-0350 / OCP_NATIVE_DEPENDENCY_UNOWNED_FMT_DLL / AWAITING_INDEPENDENT_AUDIT**

## Authorization and synchronization

- Read live `origin/main:TASKS.md`, the R04 implementation prompt and audit criteria, the R03 audit, and the owner authorization for the hosted 315 No-VTK build.
- R04 is the current PL-0350 task. No root `TASKS.md` or ChatGPT audit file was changed.
- Worktree: managed PackLab worktree on existing branch `codex/pl0350-opengl-sdk-contract-r03`.
- Starting worktree commit after safe fast-forward: `c6c5f4ab0fd0681afc95eb7a5c5c656362d95750`. It began four commits behind `origin/main`, was clean, and fast-forwarded without reset or stash.
- Implementation commit: `a2805616c9c0dd665e48b1de82c8436ea64b0805` (`Fix canonical Windows OCCT SDK layout contract`), pushed to `origin/main` before hosted validation.
- The hosted preflight and cold run both used exact SHA `a2805616c9c0dd665e48b1de82c8436ea64b0805`.

## Changes implemented

- Added shared strict canonical Windows OCCT SDK layout validation in `tools/packaging/windows_occt_sdk_layout.py` for `inc/OpenGl_Context.hxx`, `win64/vc14/lib/TKOpenGl.lib`, and `win64/vc14/bin/TKOpenGl.dll`.
- Wired the producer post-install check, consumer SDK validator, downstream dependency audit, generated OCP builder and runtime bundle metadata to the shared layout/toolchain contract. Preserved SDK metadata schema v2 and made its cache identity include the changed contract.
- Bumped SDK and OCP cache namespaces to v4 and added the SDK layout fixture to their contract hashes.
- Added a hosted `preflight_only` layout/SDK-closure fixture before archive download. The preflight exercises the producer seam, consumer validator, dependency scanner, and flat-only negative case without native compilation.
- Added nested-layout, absent-header/LIB/DLL, flat-only, bad-export, source-lock/manifest/hash/flags/path, downstream scanner, and symlink boundary tests. Symlink creation is skipped on this Windows environment because the required privilege is unavailable.
- No owner Desktop/EXE, caches, root tracker, or audit documents were modified. No local native build was run.

## Local validation

All commands ran against implementation commit `a2805616c9c0dd665e48b1de82c8436ea64b0805` before hosted runs.

| Check | Expected result / failure condition | Actual result |
|---|---|---|
| `python -m pytest -q tests/ci/test_controlled_occt_sdk.py tests/ci/test_inspect_retained_occt_sdk.py tests/ci/test_windows_studio_build_workflow.py tests/ci/test_controlled_ocp_runtime_builder.py tests/ci/test_controlled_ocp_runtime_bundle.py` | Focused tests green; any failed assertion exits nonzero | **37 passed, 1 skipped** (Windows symlink creation unavailable) |
| `python -S -m tools.packaging.verify_windows_workflow_python_imports` | All workflow Python modules import; missing module fails | **PASS, 16 modules** |
| `python -S -m tools.packaging.preflight_occt_sdk_layout` | Synthetic nested layout producer, consumer and scanner pass; flattened-only layout fails closed | **PASS** |
| Ruff check and `ruff format --check` on changed Python sources | No lint/format failures | **PASS** |
| mypy on 10 changed source files | No type errors | **PASS** |
| compileall on changed Python files | No syntax failures | **PASS** |
| PyYAML parse of `.github/workflows/windows-studio-build.yml` | Workflow parses | **PASS, YAML_PARSE_PASS jobs=5** |
| `git diff --check` | No whitespace errors | **PASS** |
| C: free-space check | At least 40 GiB; below threshold blocks native work | **121,687,945,216 bytes free** |

No standalone `actionlint` was installed. GitHub accepted and executed the exact workflow. No local heavy OCCT/OCP compile was performed.

## Hosted validation

### Preflight-only diagnostic

- One initial dispatch, run [38346211718](https://github.com/Sekiph82/PackLab/actions/runs/38346211718), used an invalid `build_revision` input; all jobs were skipped and it performed no preflight or native work. It produced no build evidence and is not counted as the valid diagnostic.
- Correct exact-SHA preflight run: [38346246435](https://github.com/Sekiph82/PackLab/actions/runs/38346246435), input SHA `a2805616c9c0dd665e48b1de82c8436ea64b0805`.
- Capacity/preflight job `115128246011` succeeded. Log output:
  `OCCT_SDK_LAYOUT_PREFLIGHT {"canonical_paths":{"inc/OpenGl_Context.hxx":"inc/OpenGl_Context.hxx","win64/vc14/bin/TKOpenGl.dll":"win64/vc14/bin/TKOpenGl.dll","win64/vc14/lib/TKOpenGl.lib":"win64/vc14/lib/TKOpenGl.lib"},"consumer_validator":"PASS","downstream_dependency_scanner":"PASS","native_build_invoked":false,"producer_post_install":"PASS","status":"PASS"}`
- SDK, OCP, and Studio jobs were each independently reported `skipped`.

### Single authorized cold run

- Run: [38346317865](https://github.com/Sekiph82/PackLab/actions/runs/38346317865); head SHA verified as `a2805616c9c0dd665e48b1de82c8436ea64b0805`.
- Capacity job `115128473129`: success. SDK job `115128573487`: success. SDK cache v4 exact-key restore was a miss; the job compiled and validated the source-locked `USE_OPENGL=ON`, `USE_VTK=OFF` SDK. Consumer output was `CONTROLLED_OCCT_SDK_VALID files=7991 bytes=173975159`; the build log showed `TKOpenGl.lib` at `win64/vc14/lib/` and `TKOpenGl.dll` at `win64/vc14/bin/`.
- SDK artifact `packlab-occt-sdk-38346317865-1`: ID `11790440856`, size `57,520,243` bytes, digest `sha256:467b44ab0fb747343cb55e55e71a0dd4ecadb989fd7eed22d1e49fff3153ddf8`.
- Corresponding-source evidence artifact `packlab-native-source-evidence-38346317865-1`: ID `11790585684`, size `1,398` bytes, digest `sha256:091c391b8d6ccda19823f57eae891b1dd45383b164c117ca05928df6bafd2018`.
- OCP job `115138281145` verified the SDK artifact manifest/hashes and source evidence, downloaded the official generated source ZIP, and fail-closed rejected the exact OCP cache key as a miss. Key: `Windows-x64-controlled-ocp315-v4-7ad1c8b0b2634d32eeada2e6d8fa4fb6e85f7f3c1e6989e8beab7ebdbc2c9031-cdf72c1ef30b51a48bbb60fbc8d14583dcb8c84d283ce6aee8cd4b5b8bc2942d-290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`.
- Generated OCP source compilation reached a built `OCP.cp312-win_amd64.pyd` at 07:07:31Z. At 07:07:34Z the builder’s post-build ownership check failed with the first blocking error: `ValueError: compiled OCP references an unowned DLL dependency: fmt.dll`. The workflow step failed with exit code 1. This is a post-build dependency-ownership failure, not a compiler failure.
- OCP runtime checkpoint validation, native CAD/STEP smoke, OCP artifact/cache save and upload steps were skipped. Production Studio job `115174068548` was skipped. No compliance clearance, Installer, or warm-cache hit was produced. No retry was dispatched.
- There is no six-hour job timeout: the terminal failure was the `fmt.dll` dependency check.

## Scope, privacy, and handoff

- The valid cold run is the one authorized R04 attempt. Stop at `fmt.dll`; no speculative fix, second cold run, or warm run was performed.
- No native runtime or Installer artifact exists. The SDK and corresponding-source artifacts above are preserved. The observed SDK artifact expiry was 2026-10-14 05:03 UTC; OCP fail log ended 2026-10-13 07:07 UTC.
- No owner Desktop files, private scans, credentials, or secrets were read into project evidence or committed. No production publish/signing action was taken.
- Parent PL-0350 remains unaccepted. No PL-0351, PL-0368, M17, or adjacent task was started.
- Final requested handoff: **BATCH_STOPPED_AT_PL-0350 / OCP_NATIVE_DEPENDENCY_UNOWNED_FMT_DLL / AWAITING_INDEPENDENT_AUDIT**.

The independent reviewer should inspect the source diff, the local check results above, the [preflight run](https://github.com/Sekiph82/PackLab/actions/runs/38346246435), the [cold run](https://github.com/Sekiph82/PackLab/actions/runs/38346317865), job `115138281145`, and the two artifact digests. This log is builder evidence only, not an audit verdict.
