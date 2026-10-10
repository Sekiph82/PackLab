# PL-0350 V07-R01 — R0 Recovery Inventory

Date: 2026-10-10
Authority: [R01 prompt](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_V07_R01_PHASE_SPLIT_CODEX_PROMPT.md) · [R01 audit criteria](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_V07_R01_PHASE_SPLIT_CHATGPT_AUDIT_CRITERIA.md)
Result: **No exact-current, source-verified OCCT SDK or generated pywrap checkpoint was found in bounded inspected sources. `OWNER_APPROVAL_REQUIRED_FOR_NATIVE_REBUILD`.**

## Authority and scope

- Live `origin/main:TASKS.md` names PL-0350 V07-R01 and `R0_RECOVERY_INVENTORY_FIRST / COLD_NATIVE_REBUILD_NOT_AUTHORIZED / OWNER_APPROVAL_REQUIRED_IF_UNRECOVERABLE`.
- Started from `ba7d258252d9172707c1c5ced8445f9a5058af90`; fetched `origin/main`, fast-forwarded a clean worktree to `e6a7ce862e9a905980b70e0e0aade5989ffaf665`, and verified `HEAD...origin/main = 0 0`.
- Read the live R01 prompt, matching criteria, parent [V07 source prompt](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V07.md), and [V07 audit](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V07.md).
- R01’s owner hold controls: no OCCT compilation, pywrap generation, generated C++ compilation, long cold-cache Actions run, or large local build was started. No cache was restored, changed, or pruned. OwnerDev was read-only inspected; no files were copied or modified.

## Prior hosted run artifacts

GitHub Actions artifact API was queried for each specified run:

| Run | Result | Classification |
| --- | --- | --- |
| [37967978530](https://github.com/Sekiph82/PackLab/actions/runs/37967978530) | 0 workflow artifacts | Logs establish OCCT and pywrap completed and generated C++ compilation began, but no checkpoint survived as a run artifact. |
| [37951025064](https://github.com/Sekiph82/PackLab/actions/runs/37951025064) | 0 workflow artifacts | Earlier builder failed after pywrap; historical log/progress only. |
| [37860820132](https://github.com/Sekiph82/PackLab/actions/runs/37860820132) | 0 workflow artifacts | Earlier hosted run canceled during pywrap; historical log/progress only. |

The repository-wide Actions artifact listing returned exactly two unexpired items, both unrelated `PackLabStudioPreview-Windows` artifacts: run [36326581390](https://github.com/Sekiph82/PackLab/actions/runs/36326581390), 23,675,307 bytes; and run [36326578790](https://github.com/Sekiph82/PackLab/actions/runs/36326578790), 23,672,862 bytes. Neither is a native build checkpoint. The only successful `PackLab Studio Windows Build` in the bounded 100-run success listing, [37424680100](https://github.com/Sekiph82/PackLab/actions/runs/37424680100), also has 0 artifacts.

## GitHub Actions cache inventory

The workflow’s controlled-runtime key schema is `Windows-X64-controlled-ocp-py3.12-v1-${hashFiles(...)}`; the input set is in [windows-studio-build.yml](https://github.com/Sekiph82/PackLab/blob/main/.github/workflows/windows-studio-build.yml#L120). A read-only listing of all repository Actions caches returned only these three keys, all generic `uv` package caches on `refs/heads/main`:

| Exact cache key | Bytes | Created (UTC) | Last accessed (UTC) | Classification |
| --- | ---: | --- | --- | --- |
| `Windows-X64-python-3.12-uv-0.11.26-8c0977e9936dd8f85ad476083fbbf1a0a0732f60d49e6e6d603e8477752b5000` | 404,487,128 | 2026-10-06 11:19:22 | 2026-10-09 21:15:24 | Generic package cache; API exposes metadata, not contents or a native-stage manifest. |
| `Windows-X64-python-3.12-uv-0.11.26-34e5b3fd9cbcead450ac4bdabdc960aa09d49ddb2b59fbafc50f3a5764b9ab35` | 404,937,724 | 2026-10-06 06:28:24 | 2026-10-06 07:45:43 | Generic package cache; not a controlled-runtime key. |
| `Windows-X64-python-3.12-uv-0.11.26-c8f8525a8b54b756d64b1de94e58d607af19c73345b419a0c32b2b45f39f5950` | 403,887,016 | 2026-10-06 05:45:05 | 2026-10-06 05:45:57 | Generic package cache; not a controlled-runtime key. |

No cache with the controlled-runtime key schema exists in the complete repository cache listing. The generic `uv` cache API does not expose package contents, per-file hashes, or provenance. It is therefore **not** evidence of an OCCT SDK or generated-C++ checkpoint. Shared local package-cache contents were not traversed; the OwnerDev wheel evidence below was inspected directly, and no shared cache was modified.

## Bounded OwnerDev and prebuilt-wheel inspection

Read-only inspection of current and previous-known-good OwnerDev runtime manifests found:

| Manifest | Source commit | Runtime ID | Python | Manifest SHA-256 | Evidence |
| --- | --- | --- | --- | --- | --- |
| Current | `1f45e61f3743879301528157f047b6415cbac9bf` | `1f45e61f3743879301528157f047b6415cbac9bf-47b29e26d0294872bf0386e1a0dbfa26` | 3.12.10 | `824B07516B6DF27837482B877605D0C37BB3D30457D95D88996268241B994FB7` | Manifest says smoke `PASS`; `uv_lock_sha256=6fb1ebbab447a1796c41b1be66af11f425a0fd170246753245859e3374bd2846`. |
| Previous | `408dae870859268876693c182054bb48c3a24517` | `408dae870859268876693c182054bb48c3a24517-c59343780aa24bd8a5ba1014ee095861` | 3.12.10 | `D963D4573F049A921B7472780033765C21FCBAF2B3BA048715AC1EC6ABDBD5A8` | Manifest says smoke `PASS`; same `uv_lock_sha256`. |

Both environments contain the same `OCP/OCP.cp312-win_amd64.pyd`: 93,748,736 bytes, SHA-256 `9B103790E366DC33509F7EE8958DFA40334076EADDC40DABA275BF18E6A50B20`. The bounded `OCP` directory listing contains only `__init__.py` (398 bytes) and that `.pyd`; no generated `.cpp` files or standalone SDK headers/libraries were present there. These environments are protected current/previous OwnerDev runtimes and were not used as build inputs.

Their `uv.lock` identifies official PyPI `cadquery-ocp-novtk==7.9.3.1.1`, including the CPython 3.12 Windows x64 wheel URL, published-wheel SHA-256 `5d22339cdaac64c396f0658de8728915acfac9b868406f0078e52f50a3c25c65`, and compressed size 46,364,919 bytes; [PyPI release metadata](https://pypi.org/project/cadquery-ocp-novtk/7.9.3.1.1/) lists that Windows x64 CPython 3.12 wheel. This is an installed prebuilt-wheel candidate, **not** a source-built phase checkpoint: the OwnerDev manifest has no OCCT/OCP native source-lock digest, compiler/toolchain attestation, generated-source digest, per-file runtime manifest, or checkpoint schema; the recorded interpreter patch is 3.12.10 while the controlled build contract requires 3.12.15. The `.pyd` digest alone cannot establish provenance or a complete OCCT runtime. It is not authorized for substitution or copying.

## Frozen native inputs and hashes

At synchronized `origin/main` `e6a7ce862e9a905980b70e0e0aade5989ffaf665`:

| File | SHA-256 |
| --- | --- |
| `tools/packaging/windows_native_source_lock.json` | `C6A32326C1463DCE53A70366200E9739D853893030F0553739188D878B1BF277` |
| `tools/packaging/packlab-ocp-bindings-win.lock` | `38E8C0A4D4B8AD1284F5595EB33F9196D124271C63DA9C1395AFA083028D3867` |
| `tools/packaging/controlled_ocp_runtime_contract.json` | `29D92EEF8E7B1D125E3164BE65A02E8EEA7C119A23E661512EDAB67D6389F184` |
| `.github/workflows/windows-studio-build.yml` | `58132B6471731447A782E8CC6114041CAA4140E8DA6EE60B2A21BFB0BA59175A` |
| `tools/packaging/build_controlled_ocp_runtime.py` | `3A2607EEE4360274A2FFF8343BC88144F5E376E9D537BFD95061C4967FB9BA28` |
| `tools/packaging/controlled_ocp_runtime_bundle.py` | `6F3EEE165DFEBF06AD0053D3327DA90692B55CDC71F82C8C110630CDB16FB1FF` |

The frozen lock requires OCP source revision `d69b064a3a604ebf245b1f3b14fb54c835a3a571`, pywrap `92519409a57f9ec3f2c005b8057006fdb4752c23`, and OCCT `a016080bf6738d6aeae020badee4e888ad1540a5`. Its build contract is Windows 2022 x86_64, CPython 3.12.15, locked MSVC 19.44.35229.0, CMake 3.31.8, Windows SDK 10.0.26100.0, and four workers. No inspected candidate carries and validates these source/build identities together with the required full checkpoint file manifest.

## Candidate classification

| Candidate | Classification | Reuse decision |
| --- | --- | --- |
| Run `37967978530` OCCT completion and pywrap completion | **(c) Log/progress only**; no run artifact or cache checkpoint. | Cannot skip either phase. |
| Runs `37951025064`, `37860820132` | **(c) Log/progress only**; zero run artifacts; older run failed/canceled. | Cannot skip either phase. |
| Three GitHub `uv` caches above | **(b) Opaque generic package caches**; no controlled key, contents manifest, or stage identity exposed. | Not a checkpoint; no restore. |
| Current/previous OwnerDev `.pyd` | **(b) Historical prebuilt wheel output with incomplete native provenance**, protected inside known-good OwnerDev runtimes. | Not an exact source-built checkpoint; no copy or substitution. |
| Two remaining GitHub preview artifacts | Unrelated preview packages, not native producer outputs. | No use. |
| Exact-current OCCT SDK / generated pywrap C++ checkpoint | **(d) No verified surviving output found** in the inspected bounded sources. | Owner decision required before rerunning any unrecoverable native phase. |

## Feasibility, minimum work, and owner decision

The audited V07 run [37967978530](https://github.com/Sekiph82/PackLab/actions/runs/37967978530) measured OCCT at 2,560.860 seconds (42m 40.860s) and pywrap generation at 18,220.375 seconds (5h 03m 40.375s). Generated OCP C++ compilation had only begun about 8m30s before the six-hour job cancellation and had not completed; no reliable completion time or final package duration is available. The measured pywrap phase alone leaves at most 56m19.625s within a six-hour ceiling for setup, validation, checkpoint hashing, and upload, so its checkpointed Job B budget is **not yet demonstrated feasible**. These are historical measurements, not a new run estimate or authorization.

If the owner wants the exact source-built runtime and no separate provenance review accepts an alternative, the minimum unrecovered native sequence is: (A) rebuild and seal the locked OCCT SDK; (B) regenerate and seal all 319 pywrap modules from that SDK; (C) compile the generated OCP extension on a fresh runner and seal/import-smoke the runtime; then (D) run production packaging, feature smoke, and redistribution clearance. R01 does not authorize A, B, C, or a cold hosted workflow. Before any such approval, the phase plan must address Job B setup/upload headroom or safe partitioning while preserving all 319 modules, plus artifact sizes, expirations, hashes, and fresh-runner portability.

No native phase has been re-run. Handoff: **`OWNER_APPROVAL_REQUIRED_FOR_NATIVE_REBUILD` / `AWAITING_OWNER_DECISION`**. PL-0351 remains blocked until the actual unsigned installer is cleared.
