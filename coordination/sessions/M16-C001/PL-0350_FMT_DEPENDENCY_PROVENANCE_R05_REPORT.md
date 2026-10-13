# PL-0350 R05 — fmt Dependency Provenance and Checkpoint Rescue Report

Date: 2026-10-13
Status: **BATCH_STOPPED_AT_PL-0350 / FMT_PROVENANCE_REQUIRED / AWAITING_INDEPENDENT_AUDIT**

## Result

The urgent R04 OpenGL-enabled OCCT SDK and its source evidence were recovered and resealed by a manual Windows-hosted job without compilation. The later noncompiling dependency probe verified the locked `fmt` package, its exact Windows DLL, source, MIT license notice, feedstock recipe, CMake link target, and PE architecture. The probe did not pass the complete import-ownership gate: imports resolved to conda `ucrt` and `vc14_runtime` files for which PackLab has no exact source/license/redistribution records. The controlled native build was not dispatched.

## Preserved SDK checkpoint

Original R04 cold run: [38346317865](https://github.com/Sekiph82/PackLab/actions/runs/38346317865).

| Item | Identity |
|---|---|
| Original SDK artifact | `11790440856`, 57,520,243 bytes, SHA-256 `467b44ab0fb747343cb55e55e71a0dd4ecadb989fd7eed22d1e49fff3153ddf8` |
| Original source evidence artifact | `11790585684`, 1,398 bytes, SHA-256 `091c391b8d6ccda19823f57eae891b1dd45383b164c117ca05928df6bafd2018` |
| Recovery run | [38366186522](https://github.com/Sekiph82/PackLab/actions/runs/38366186522), Windows 2022, noncompiling |
| Resealed checkpoint artifact | `11796717315`, `packlab-pl0350-r04-sdk-recovery-38366186522-1`, 114,366,551 bytes, SHA-256 `3339c28cd99605c3c928f9c4f145245b39efb1f7ed99a19a17c1547d8e101c4e` |
| Resealed artifact expiry | 2026-10-27 07:59:40 UTC |
| Recovery verification | `PL0350_R04_CHECKPOINT_RECOVERY_PASS`; 7,991 SDK files / 173,975,159 bytes; SDK payload SHA-256 `7ad1c8b0b2634d32eeada2e6d8fa4fb6e85f7f3c1e6989e8beab7ebdbc2c9031`; nine source records |

The recovery preserved the original SDK and source evidence ZIP bytes and recorded their run/artifact identity. It verified the sealed inner file hashes and the OCCT 7.9.3, MSVC, native Python 3.12.15, OpenGL enabled, VTK disabled, and `win64/vc14` layout facts. The checkpoint's source-lock identity is the original R04 lock digest `c6a32326c1463dce53a70366200e9739d853893030f0553739188d878b1bf277`. The R05 source lock later gained the fmt source record; no OCP consumer was modified to pretend that the old SDK metadata used that newer lock digest.

## fmt package and DLL evidence

The noncompiling Windows 2022 probe completed at [38370004545](https://github.com/Sekiph82/PackLab/actions/runs/38370004545), head `5ff482278fae05bbae029b5185fa2838d1cb70b9`. It uploaded report artifact `11799090609`, `packlab-pl0350-fmt-dependency-probe-38370004545-1`, 1,983 bytes, SHA-256 `293017b77e9bc8d4cb44563d18c150d944b47eecdedef5d8a9c3bdc77b30010b`, expiry 2026-10-27 08:36:48 UTC.

| Evidence | Observed result |
|---|---|
| Exact conda lock | `fmt 12.1.0 h1ced75a_1`, win-64, archive SHA-256 `1d6d6f1bf284e50cf617ce9a6250e0bf70bd0d30b068568364d6b1852aad9466`, 187,511 bytes |
| Downloaded package archive | SHA-256 and size exactly matched the lock and Anaconda package metadata |
| Installed package record | Exact version/build/URL; its `conda-meta` record omits a SHA field. The explicit lock, independently downloaded archive digest, and installed file manifest were checked separately. |
| `fmt.dll` | `Library/bin/fmt.dll`, SHA-256 `0d4edfe1411f4a7c5f57758239f0f1e6e1cff7f2d0ae5f9511a1dfacc08b388d`, AMD64 PE |
| Link target | Generated OCP CMake links `fmt::fmt`; installed CMake config/targets point to the DLL |
| Upstream source | fmt 12.1.0 archive SHA-256 `ea7de4299689e12b6dddd392f9896f08fb0777ac7168897a244a6d6085043fea`, 711,419 bytes |
| MIT notice | `LICENSE` SHA-256 `07580f2a3b35709ce703d523f447b242f6dfec7582a8c0df102c7fa2849375f8`, 1,431 bytes |
| Pinned conda-forge recipe | Commit `437ad8fba6cc830bd16eef7f98aeb2d76c9ff060`, `recipe/meta.yaml` SHA-256 `e122a830860163ff276b40a6ffcc42d79bc115bc73bdbdff78ccfbef5c13d436` |
| Upstream fmt revision | Tag `12.1.0`, commit `407c905e45ad75fc29bf0f9bb7c5c2fd3475976f` |

The exact report contains the DLL hashes, imported names and package ownership details. The PE imports were `api-ms-win-crt-heap-l1-1-0.dll`, `api-ms-win-crt-locale-l1-1-0.dll`, `api-ms-win-crt-math-l1-1-0.dll`, `api-ms-win-crt-runtime-l1-1-0.dll`, `api-ms-win-crt-stdio-l1-1-0.dll`, `api-ms-win-crt-string-l1-1-0.dll`, `kernel32.dll`, `msvcp140.dll`, `vcruntime140.dll`, and `vcruntime140_1.dll` (ten imported names; `kernel32.dll` was resolved under System32).

## First blocker

The actual imported DLLs under `Library/bin` were attributed to these exact packages, but their source/license records are absent from the PackLab native source lock and component license registry:

| Package | Locked installed identity | Imported files blocked, actual DLL SHA-256 |
|---|---|---|
| `ucrt` | `10.0.26100.0`, build `h57928b3_0`, archive SHA-256 `3005729dce6f3d3f5ec91dfc49fc75a0095f9cd23bab49efb899657297ac91a5` | `api-ms-win-crt-heap-l1-1-0.dll`: `c71080cbcb43bf1f8f3e391deb12a582eb0abefc80946f340675a2c616e4feb4`; `api-ms-win-crt-locale-l1-1-0.dll`: `6c68648e524187e03c4ad9aaa4a99113c6ee9f29fb39cc0ed93f951975138e63`; `api-ms-win-crt-math-l1-1-0.dll`: `d4fbcccbe29371cbce431e43b2eb4f7ba9a6f04a3d740a071f02457a505e9dc8`; `api-ms-win-crt-runtime-l1-1-0.dll`: `72adc1b3677e0814d9c4ebf0964000e84bb2acf67336c8963061665e44f78029`; `api-ms-win-crt-stdio-l1-1-0.dll`: `900afc3989673c9bb1a687ed38c192f46db9e6ba6d11a668898a539e7fc23798`; `api-ms-win-crt-string-l1-1-0.dll`: `fcf12466cc12fd3b73611fc0763a5a1f9d44e90349513c34a0c83b0f36421793` |
| `vc14_runtime` | `14.51.36247`, build `habf1de7_41`, archive SHA-256 `4e4cb599cdc41bf2109d1464c127b5bcbddf548ce3e322e612afb691338b48f8` | `msvcp140.dll`: `7c26614e1d733892c2deac7e245ce115504b1d80592dd0a01b08e3e5a55f89ca`; `vcruntime140.dll`: `d1f4225df2cd877dbf130d5668a021dce3f94118455ff5ec952061c30afc9ce7`; `vcruntime140_1.dll`: `a7146c08f89fe5b04541ab507cdb59ff7b44534d4ba3c668a426c6450a03434e` |

The hosted report marks all nine package-provided runtime DLLs `SOURCE_OR_LICENSE_UNRESOLVED`; the step `Fail closed when any native owner is unresolved` therefore failed with `FMT_PROVENANCE_REQUIRED`. Existing PackLab registry entries classify Microsoft Windows and VC runtime components as unresolved when staged until exact source/build and redistribution evidence is reviewed. The files were found inside the conda prefix, so they were not relabeled as System32 or silently removed from the dependency closure.

The report proves the current fmt DLL import closure only. It does not prove which dependencies the eventual compiled OCP Pyd will import, because no OCP compilation occurred. It also does not prove redistributable clearance, an OCP manifest/bundle integration, a real Pyd quarantine artifact, runtime CAD smoke, Studio packaging, or Installer readiness.

## Runs and validation

- First probe attempt [38367878571](https://github.com/Sekiph82/PackLab/actions/runs/38367878571) failed because the recipe URL template expected the wrong contract key; its uploaded report contains only that probe error and no DLL evidence.
- Corrected probe [38368574153](https://github.com/Sekiph82/PackLab/actions/runs/38368574153) identified that conda's installed record omits the SHA field. A second fix verified the downloaded exact archive digest while retaining strict checks for any present record hash.
- Final probe [38370004545](https://github.com/Sekiph82/PackLab/actions/runs/38370004545) reached full PE ownership analysis and failed closed on the UCRT/VC runtime records above.
- Hosted Python quality [38369998989](https://github.com/Sekiph82/PackLab/actions/runs/38369998989) passed Ruff lint, Ruff format, mypy, and unit/repository tests.
- Local focused CI tests: 36 passed. Ruff lint/format and mypy passed. Compileall passed. The workflow Python import probe passed for 19 modules. Both relevant workflow files parsed with PyYAML. Native source-lock validation passed with 14 records and SHA-256 `0fc50a9e092e4c712627518cb87ad0c841fc4a69f7272a2ba02cf5195f836acb`; SDK build-contract validation passed with SHA-256 `11a684318c85be11056501ccee793500cedd17d5ca15c671669ecd92f2eab071`.
- Implementation commits: `cfcbaa99621868e1238a3210e7113fe77a896d4d` (SDK checkpoint recovery), `bd1b2e25dacbbed991f843e9b7c040e9dd055a0e` (fmt preflight), `858c8ac2206a8a80a5c9be5834ee2c1c0061ea42` (recipe URL fix), `3450afd83e369d84f67d51c717521f563bf9adc4` (record mismatch diagnostics), and `5ff482278fae05bbae029b5185fa2838d1cb70b9` (verify fmt archive when conda metadata omits SHA).

## Stop and handoff

No OCP or OCCT native compiler was run in R05. No native build was dispatched after the failed ownership gate. The SDK checkpoint remains available through its reported expiry. Root `TASKS.md`, ChatGPT audit files, owner Desktop files and the known-good PackLab EXE were not changed by this R05 worktree.

**BATCH_STOPPED_AT_PL-0350 / FMT_PROVENANCE_REQUIRED (UCRT + VC14_RUNTIME SOURCE/LICENSE AND REDISTRIBUTION EVIDENCE) / AWAITING_INDEPENDENT_AUDIT**
