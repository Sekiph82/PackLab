# PL-0350 R03 Codex Implementation Log

Date: 2026-10-13 (Europe/Istanbul; hosted events occurred 2026-10-12 UTC)
Task: PL-0350 only
Status: `BATCH_STOPPED_AT_PL-0350 / OCCT_SDK_INSTALL_LAYOUT_VALIDATION_MISMATCH`

## Starting authority and synchronization

- Active prompt: `PL-0350_OPENGL_SDK_CONTRACT_R03_CODEX_PROMPT.md`.
- Matching criteria: `PL-0350_OPENGL_SDK_CONTRACT_R03_CHATGPT_AUDIT_CRITERIA.md`.
- Root `TASKS.md` identified PL-0350 R03 as the active Codex task and was not edited.
- Managed worktree: `C:\Users\sekip\.codex\worktrees\pl0350-hosted-315-novtk\PackLab`.
- Starting HEAD and `origin/main`: `2a4901b0abb472c54c1c6e4dbb9c494120a92983`; fetch reported `0 0` divergence before implementation.
- Desktop checkout and owner files were not touched; no local native compilation was run.

## Prior immutable SDK inspection and dependency evidence

- Read-only retained-SDK hosted audit: [run 38304468474](https://github.com/Sekiph82/PackLab/actions/runs/38304468474), successful with `EXPECTED_INCOMPATIBLE`; native jobs were skipped.
- Retained SDK artifact `11755977987`, run `38263302823`, remains unchanged: 56,405,631 bytes; outer archive SHA-256 `1ad03b366958f0a81d98813fac313d85d0133e79db9e85f4844d783b0306d0ae`. Matching source evidence artifact `11755908172` remains retained.
- The SDK's inner sealed manifest recorded 7,886 files / 170,172,521 bytes and payload SHA-256 `45c313833beaa6f07f87397d15b4cee2196c112a465f198162b131612026cec2`; source-lock SHA-256 `c6a32326c1463dce53a70366200e9739d853893030f0553739188d878b1bf277`; OCCT revision `a016080bf6738d6aeae020badee4e888ad1540a5`; Python 3.12.15, MSVC 19.44.35229.0, Windows SDK 10.0.26100.0, four workers, prior cache key `Windows-x64-occt-sdk-v2-2b0408d1b78a38261d6775f4a5d6dcd1b65de864539844da96b2ab28b34fbb66`.
- The hosted source/consumer audit scanned 315 generated modules, 631 C++ translation units including OCP.cpp, 72,414 include directives, 7,184 OCCT source headers, and 7,056 installed headers. It found 97 missing OpenGl-family headers plus `TKOpenGl.lib` and `TKOpenGl.dll`; the other 65 exported toolkits and Windows system GL prerequisites were present.
- Pinned upstream OCCT CMake confirms Windows desktop OpenGL is enabled by default and `USE_OPENGL=OFF` removes `TKOpenGl`: [pinned CMakeLists.txt](https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/a016080bf6738d6aeae020badee4e888ad1540a5/CMakeLists.txt), [pinned OpenGl_Context.hxx](https://github.com/Open-Cascade-SAS/OCCT/blob/a016080bf6738d6aeae020badee4e888ad1540a5/src/OpenGl/OpenGl_Context.hxx).

## Implementation and local validation

- The R03 implementation commits already on `main` configure the OCCT SDK with `USE_OPENGL=ON` and `USE_VTK=OFF`, record schema-v2 CMake options, require OpenGL header/import library/runtime DLL, and use versioned SDK/OCP cache identities. The SDK validator, source/link closure audit, and OCP gate fail before the expensive OCP compile when SDK dependencies are incomplete.
- The R03 implementation includes bounded archive inspection, full generated-source dependency auditing, and tests for missing OpenGL headers/library/DLL, other missing toolkit/header dependencies, lock/manifest tampering, case-fold duplicates, and partial SDKs.
- R03 product files changed: `.github/workflows/windows-studio-build.yml`; `tools/packaging/audit_controlled_occt_sdk_dependencies.py`; `tools/packaging/build_controlled_occt_sdk.py`; `tools/packaging/build_controlled_ocp_from_generated_sources.py`; `tools/packaging/inspect_retained_occt_sdk.py`; `tools/packaging/validate_controlled_occt_sdk.py`; `tests/ci/test_controlled_occt_sdk.py`; `tests/ci/test_inspect_retained_occt_sdk.py`; `tests/ci/test_windows_studio_build_workflow.py`. The capacity correction additionally adds `tools/packaging/assert_actions_run_artifact_budget.py` and `tests/ci/test_actions_run_artifact_budget.py`.
- An initial authorized native dispatch at SHA `2a4901b0abb472c54c1c6e4dbb9c494120a92983`, [run 38304697335](https://github.com/Sekiph82/PackLab/actions/runs/38304697335), failed capacity preflight before any SDK/native job. Cause: fixed per-run 4 GiB caps rejected the immutable retained 56,407,029 artifact bytes against an 8 GiB two-run ceiling.
- Corrected that arithmetic without deleting artifacts or increasing the ceiling: preflight now assigns each of two runs `min(4 GiB, floor((8 GiB - retained artifact bytes)/2))`; this run's measured ceiling was 4,266,763,781 bytes. A helper queries the bounded GitHub artifact inventory and checks cumulative current-run bytes before every SDK, source-evidence, runtime, compliance, and installer artifact upload. Added helper unit tests and workflow assertions.
- Product commit: `038d3c462ef176293cb37d778fc79676f3bbf0be` (`Fix retained artifact budget preflight`), pushed to `origin/main`; post-push fetch showed exact parity (`0 0`). This is the final implementation SHA.
- Local validation passed:
  - `uv run --locked pytest -q tests/ci/test_actions_run_artifact_budget.py tests/ci/test_windows_studio_build_workflow.py tests/ci/test_controlled_occt_sdk.py tests/ci/test_inspect_retained_occt_sdk.py tests/ci/test_controlled_ocp_runtime_builder.py tests/ci/test_controlled_ocp_runtime_bundle.py` — 34 passed.
  - `uv run --locked ruff check ...` — passed.
  - `uv run --locked ruff format --check ...` — passed.
  - `uv run --locked mypy tools/packaging/assert_actions_run_artifact_budget.py tests/ci/test_actions_run_artifact_budget.py` — passed.
  - `uv run --locked python -m compileall -q ...` — passed.
  - `uv run --locked python -S -m tools.packaging.verify_windows_workflow_python_imports` — 15 workflow modules passed, including the new upload-budget helper.
  - `git diff --check` and staged diff check — passed.
- No standalone YAML parser/actionlint was installed locally. GitHub accepted and executed the exact-SHA workflow dispatch, confirming workflow syntax/trigger validity.

## Hosted cold run and first stop

- Corrected exact-SHA authorized dispatch: [run 38305407910](https://github.com/Sekiph82/PackLab/actions/runs/38305407910), head `038d3c462ef176293cb37d778fc79676f3bbf0be`, inputs `run_native_build=true`, `preflight_only=false`, `inspect_retained_sdk=false`.
- Capacity preflight passed (job `114998130524`): Windows 2022, Python bootstrap 3.12.10, 15 workflow imports passed, exact 319-to-315 generated-source patch passed; both old artifacts remained the only live artifacts. The new v3 cache key was `Windows-x64-occt-sdk-v3-71da32c6cbd11d5226fc6a60d159a39703117ce700a2428bc6cf2b67d1a5ae44`; exact cache restore missed. Nine source-lock entries passed with lock SHA-256 `c6a32326c1463dce53a70366200e9739d853893030f0553739188d878b1bf277`.
- SDK job `114998244496` ran from 20:37:43Z to 21:21:02Z. Its build/validation step ran 20:42:02Z–21:20:54Z (38m52s). No OCP compiler started.
- CMake built `TKOpenGl` and installed all three expected OpenGL payload files:
  - `install/inc/OpenGl_Context.hxx` at 21:20:45Z;
  - `install/win64/vc14/lib/TKOpenGl.lib` at 21:20:46Z;
  - `install/win64/vc14/bin/TKOpenGl.dll` at 21:20:46Z.
- The first hard stop was the builder's post-install required-path check in `tools/packaging/build_controlled_occt_sdk.py`: it required `inc/OpenGl_Context.hxx`, `lib/TKOpenGl.lib`, and `bin/TKOpenGl.dll`, but the Windows install layout nests the library and DLL beneath `win64/vc14`. The build step raised `ValueError: OCCT install lacks the required OpenGL header, import library, or runtime DLL` at 21:20:54Z despite the three install records above. This is a validator/install-layout mismatch, not evidence that the OpenGL build products were absent.
- SDK metadata/sealing and SDK upload steps were skipped after the error. The candidate SDK was not sealed, uploaded, or saved to the v3 cache; the hosted runner was disposed. Only the prior two immutable R02 artifacts remain live (artifact inventory after the run: IDs `11755977987` and `11755908172`). No new SDK artifact/digest exists to claim or reuse.
- OCP runtime job `115013352797` and Studio package job `115013353231` were skipped. No OCP extension, native CAD/STEP/DXF smoke, packaged Studio smoke, compliance inventory, installer, warm cache-hit proof, redistribution clearance, or public release was produced.
- The run emitted a later micromamba cleanup warning `powershell is not supported`; it followed the already-failed build step and was not the blocker.

## Safety, privacy, and handoff

- Local C: free space observed: 123,487,326,208 bytes. No local native compile, owner Desktop/EXE access, cache deletion, bulk artifact download, or owner-file modification occurred.
- No secrets, tokens, private scans, supplier files, or owner runtime files were committed or uploaded. No signing, public release, tag, or deployment occurred.
- Root `TASKS.md`, all ChatGPT audit files, and owner approval files were not edited. No adjacent PL task began. The original retained artifacts were not modified or deleted.
- First-stop result: `BATCH_STOPPED_AT_PL-0350 / OCCT_SDK_INSTALL_LAYOUT_VALIDATION_MISMATCH`. Stop here; do not retry or rebuild under R03. A follow-up prompt must authorize any validator/layout correction and any further native run.
- Final `origin/main` parity before evidence docs: HEAD `038d3c462ef176293cb37d778fc79676f3bbf0be`; report/log evidence commits follow separately. Await independent ChatGPT audit; no acceptance is claimed.
