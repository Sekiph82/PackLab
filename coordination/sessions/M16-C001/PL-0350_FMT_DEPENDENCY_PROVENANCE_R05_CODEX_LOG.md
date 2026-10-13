# PL-0350 R05 Codex Implementation Log

Date: 2026-10-13  
Executor: Codex  
Task: PL-0350 only  
Final status: **BATCH_STOPPED_AT_PL-0350 / FMT_PROVENANCE_REQUIRED / AWAITING_INDEPENDENT_AUDIT**

## Starting state and authority

- Starting canonical repository state for this R05 sequence: `a2805616c9c0dd665e48b1de82c8436ea64b0805` (R04).
- R05 execution continued in the managed worktree `C:\Users\sekip\.codex\worktrees\pl0350-hosted-315-novtk\PackLab` on branch `codex/pl0350-opengl-sdk-contract-r03`; it did not operate in or modify the owner Desktop checkout.
- Before implementation, live `TASKS.md` named PL-0350 open, R05 provenance/checkpoint rescue as next action, and Codex as required actor. The R05 prompt and matching audit criteria were read. Both place a noncompiling SDK rescue and dependency-ownership gate before any native build.
- The active R05 prompt explicitly authorized the short recovery/probe workflows, bounded implementation, tests, and commit/push to `main`. No root tracker, independent audit, owner decision, or adjacent PL task was edited.
- Initial execution also included the R05 recovery and first probe commits `cfcbaa99621868e1238a3210e7113fe77a896d4d` and `bd1b2e25dacbbed991f843e9b7c040e9dd055a0e`. Later diagnostic/fix commits are listed below.

## Synchronization and changes

`git fetch origin main` was used before later implementation pushes; ahead/behind was `0/0` before each bounded push. Each implementation commit was pushed to `origin/main`; the final evidence push is separately recorded. Final source commit before evidence authoring was `5ff482278fae05bbae029b5185fa2838d1cb70b9`, equal to fetched `origin/main`. Final source lock SHA-256: `0fc50a9e092e4c712627518cb87ad0c841fc4a69f7272a2ba02cf5195f836acb`.

R05 implementation changes:

- Added manual-only hosted recovery that verified the original R04 source evidence and SDK artifact outer/inner hashes and re-sealed the exact bytes with origin lineage; no OCCT/OCP build occurred.
- Adjusted the SDK stage cache identity to hash producing inputs rather than the whole Studio workflow and added a validator binding cache identity to SDK build options.
- Added the exact fmt source/package contract and pinned fmt provenance in the canonical native source lock.
- Added a manual-only, guarded Windows dependency probe. It installs the explicit lock, prepares verified generated OCP source without compiling, checks `fmt::fmt`, validates source/recipe/package metadata and hashes, inspects the AMD64 `fmt.dll` PE imports, and fails closed on unresolved owners.
- The first hosted probe found a `repository` versus `repo` key mismatch in recipe URL formatting. Commit `858c8ac2206a8a80a5c9be5834ee2c1c0061ea42` fixed it and added a regression assertion.
- The next probe showed that conda's installed record omits its package SHA. Commit `3450afd83e369d84f67d51c717521f563bf9adc4` made mismatch details explicit. Commit `5ff482278fae05bbae029b5185fa2838d1cb70b9` accepted a missing installed-record hash only when version/build/URL match the exact lock, separately downloaded and verified the package archive SHA/size, retained any present-hash mismatch as a hard error, and tested both cases.
- No fmt linker mode, source lock authority, licensing gate, or unknown runtime dependency was bypassed. No OCP producer/manifest/bundle redistribution path was changed after the hosted ownership gate stopped on unresolved runtime sources/licenses.

## SDK rescue evidence

- Original R04 run: [38346317865](https://github.com/Sekiph82/PackLab/actions/runs/38346317865).
- Original SDK artifact `11790440856`: 57,520,243 bytes; SHA-256 `467b44ab0fb747343cb55e55e71a0dd4ecadb989fd7eed22d1e49fff3153ddf8`.
- Original source evidence artifact `11790585684`: 1,398 bytes; SHA-256 `091c391b8d6ccda19823f57eae891b1dd45383b164c117ca05928df6bafd2018`.
- Manual noncompiling recovery run: [38366186522](https://github.com/Sekiph82/PackLab/actions/runs/38366186522).
- Resealed artifact `11796717315`, 114,366,551 bytes; SHA-256 `3339c28cd99605c3c928f9c4f145245b39efb1f7ed99a19a17c1547d8e101c4e`; expiry 2026-10-27 07:59:40 UTC.
- Recovery validated 7,991 files / 173,975,159 bytes and SDK payload SHA-256 `7ad1c8b0b2634d32eeada2e6d8fa4fb6e85f7f3c1e6989e8beab7ebdbc2c9031`, including OpenGL enabled, VTK disabled, OCCT 7.9.3, native Python 3.12.15 and `win64/vc14` layout. It preserved original metadata and the original R04 source-lock digest. The recovered SDK was not consumed in a new OCP build.

## Hosted dependency probe and first blocker

Final noncompiling probe: [38370004545](https://github.com/Sekiph82/PackLab/actions/runs/38370004545), exact source SHA `5ff482278fae05bbae029b5185fa2838d1cb70b9`. It uploaded artifact `11799090609`, 1,983 bytes, SHA-256 `293017b77e9bc8d4cb44563d18c150d944b47eecdedef5d8a9c3bdc77b30010b`, expiry 2026-10-27 08:36:48 UTC.

Verified fmt evidence:

- Locked/downloaded conda archive `fmt-12.1.0-h1ced75a_1.conda`: 187,511 bytes, SHA-256 `1d6d6f1bf284e50cf617ce9a6250e0bf70bd0d30b068568364d6b1852aad9466`.
- Installed DLL `Library/bin/fmt.dll`: SHA-256 `0d4edfe1411f4a7c5f57758239f0f1e6e1cff7f2d0ae5f9511a1dfacc08b388d`; AMD64 PE.
- Upstream fmt source archive: 711,419 bytes, SHA-256 `ea7de4299689e12b6dddd392f9896f08fb0777ac7168897a244a6d6085043fea`.
- MIT `LICENSE`: 1,431 bytes, SHA-256 `07580f2a3b35709ce703d523f447b242f6dfec7582a8c0df102c7fa2849375f8`.
- Pinned conda-forge feedstock recipe SHA-256 `e122a830860163ff276b40a6ffcc42d79bc115bc73bdbdff78ccfbef5c13d436`; exact CMake target `fmt::fmt` was present.
- Windows 2022 probe report: `fmt.dll` source owner PASS; `kernel32.dll` resolved under System32. PE closure also imports six `api-ms-win-crt-*` DLLs plus `msvcp140.dll`, `vcruntime140.dll`, and `vcruntime140_1.dll` from conda `Library/bin`.

First unresolved ownership set:

- `ucrt 10.0.26100.0`, build `h57928b3_0`, locked archive SHA-256 `3005729dce6f3d3f5ec91dfc49fc75a0095f9cd23bab49efb899657297ac91a5`, owns the six imported API-set DLLs.
- `vc14_runtime 14.51.36247`, build `habf1de7_41`, locked archive SHA-256 `4e4cb599cdc41bf2109d1464c127b5bcbddf548ce3e322e612afb691338b48f8`, owns `msvcp140.dll`, `vcruntime140.dll`, and `vcruntime140_1.dll`.
- No exact source/license/redistribution record for either package exists in the PackLab source lock/component registry. The probe marks all nine files `SOURCE_OR_LICENSE_UNRESOLVED`; the workflow fails at `Fail closed when any native owner is unresolved` with `FMT_PROVENANCE_REQUIRED`.
- R05 therefore stopped before OCP/OCCT compilation. No Pyd, quarantine artifact, OCP manifest or runtime bundle, CAD smoke, Studio package, installer, warm-cache run, or release exists. This precompile probe does not prove the final Pyd's imports.
- The prior two probe runs only exposed implementation defects (recipe URL key mismatch; SHA absent from conda-meta). They were corrected and their same manual-only preflight was rerun. The final attempt reached the native import ownership gate and is the governing result.

## Commands, checks, and expected outcomes

For the final hosted Windows dependency probe, expected outcome was `PASS` only if every imported non-system DLL had a locked package owner plus exact source/license/notice evidence; otherwise it must upload the report and fail closed. Actual result: report `BLOCKED / UNKNOWN_NATIVE_IMPORT_OWNERS`; workflow failed at the explicit gate. No native build step exists in this manual workflow.

Local checks on final source commit `5ff482278fae05bbae029b5185fa2838d1cb70b9`:

- `uv run ruff check tools/packaging/probe_fmt_dependency.py tests/ci/test_fmt_dependency_probe.py` — pass.
- `uv run ruff format --check tools/packaging/probe_fmt_dependency.py tests/ci/test_fmt_dependency_probe.py` — pass.
- `uv run mypy tools/packaging/probe_fmt_dependency.py tests/ci/test_fmt_dependency_probe.py` — pass.
- `uv run pytest tests/ci/test_fmt_dependency_probe.py tests/ci/test_pl0350_sdk_recovery.py tests/ci/test_windows_native_source_lock.py tests/ci/test_windows_studio_build_workflow.py -q` — 36 passed.
- `uv run python -m compileall -q tools/packaging/probe_fmt_dependency.py tests/ci/test_fmt_dependency_probe.py` — pass.
- `python -S -m tools.packaging.verify_windows_workflow_python_imports` — `WORKFLOW_PYTHON_IMPORT_SMOKE_PASS count=19`; the script's own expected isolated-path negative check logged `SCRIPT_PATH_REPRODUCER_PASS exit=1 missing=tools`.
- `uv run --with PyYAML==6.0.3 python -c "from pathlib import Path; import yaml; [yaml.safe_load(Path(p).read_text(encoding='utf-8')) for p in ['.github/workflows/windows-studio-build.yml', '.github/workflows/pl0350-fmt-dependency-probe.yml']]; print('workflow YAML parsed')"` — pass. Plain `uv run python -c "import yaml"` initially failed because PyYAML is not a project dependency; the ephemeral pinned parser command above passed without changing project dependencies.
- `uv run python -m tools.packaging.validate_windows_native_source_lock --verify-build-lock --verify-conda-lock` — pass, 14 records, SHA above.
- `uv run python -m tools.packaging.validate_windows_occt_sdk_build_contract` — pass, SHA `11a684318c85be11056501ccee793500cedd17d5ca15c671669ecd92f2eab071`.
- `git diff --check` — pass before each implementation commit; the evidence commit receives the same check below.
- Hosted Python quality [38369998989](https://github.com/Sekiph82/PackLab/actions/runs/38369998989) — pass, including locked unit/repository tests.

No additional local or hosted native compilation was attempted. No source/license record was inferred from a binary filename or package presence.

## Secrets, privacy, and handoff

No secrets or private owner files were added to the repository. The workflow has contents-read permission, manual dispatch only, exact `main` guard plus explicit `YES`, and uploads only its generated dependency report. Root `TASKS.md`, ChatGPT audit/criteria files, the owner Desktop checkout and known-good PackLab EXE were not edited by Codex.

Final source push was `5ff482278fae05bbae029b5185fa2838d1cb70b9`. This log/report/master handoff are a separate evidence commit. After the push, fetch `origin/main`, verify exact SHA parity and a clean managed worktree, then stop here for ChatGPT's independent audit.

**AWAITING_AUDIT — BATCH_STOPPED_AT_PL-0350 / FMT_PROVENANCE_REQUIRED (UCRT + VC14_RUNTIME SOURCE/LICENSE AND REDISTRIBUTION EVIDENCE).**
