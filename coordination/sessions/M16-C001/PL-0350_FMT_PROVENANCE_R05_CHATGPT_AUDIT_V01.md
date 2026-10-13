# PL-0350 R05 | ChatGPT Independent Audit V01

Date: 2026-10-13
**Verdict: AUDITED_PARTIAL_CHANGES_REQUIRED**
Actual status: **BATCH_STOPPED_AT_PL-0350 / NATIVE_CRT_REDISTRIBUTION_PROVENANCE_REQUIRED**
Builder's alias: `FMT_PROVENANCE_REQUIRED` remains in the historical logs; **fmt itself PASSED**, and the unresolved components are `ucrt` and `vc14_runtime`.
PL-0350 **OPEN**. No OCP native binary artifact, CAD/STEP smoke, installer, warm HIT or acceptance.

## Independently examined evidence

- Codex report: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_FMT_DEPENDENCY_PROVENANCE_R05_REPORT.md
- Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_FMT_DEPENDENCY_PROVENANCE_R05_CODEX_LOG.md
- Master handoff: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md
- Final R05 source SHA: https://github.com/Sekiph82/PackLab/commit/5ff482278fae05bbae029b5185fa2838d1cb70b9
- Builder evidence commit: https://github.com/Sekiph82/PackLab/commit/fc39d7d1355541b2434bcefacadc8687d18ccbd3
- Noncompiling OCCT SDK recovery: https://github.com/Sekiph82/PackLab/actions/runs/38366186522
- Noncompiling final fmt native dependency probe: https://github.com/Sekiph82/PackLab/actions/runs/38370004545
- Windows Python quality: https://github.com/Sekiph82/PackLab/actions/runs/38369998989
- Probe source: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/probe_fmt_dependency.py
- Probe manual-only workflow: https://github.com/Sekiph82/PackLab/blob/main/.github/workflows/pl0350-fmt-dependency-probe.yml
- Native source lock: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/windows_native_source_lock.json
- Exact conda lock: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/packlab-ocp-bindings-win.lock
- Native OCP builder: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/build_controlled_ocp_from_generated_sources.py
- OCP manifest validator: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/validate_controlled_ocp_manifest.py
- Distribution inventory: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/windows_redistribution_inventory.py

Independently fetched current GitHub report/log/master, production files and manifests, final probe/recovery GitHub job tables AND live job logs, artifact-listing API with exact sizes/digests/expiry, code diffs and exact committed conda-lock records. Local tests, hash verification inside the recovery job, and owner Desktop preservation are builder-recorded claims corroborated by hosted results but not personally replayed on the owner's computer.

## Narrow findings

**R05-01 PASS: urgent SDK rescue without recompilation.** Real `recover` hosted job **SUCCESS**, log `PL0350_R04_CHECKPOINT_RECOVERY_PASS sdk_files=7991 sdk_bytes=173975159 sdk_payload_sha256=7ad1c8b0b2634d32eeada2e6d8fa4fb6e85f7f3c1e6989e8beab7ebdbc2c9031`. GitHub artifact API shows **11796717315**, 114,366,551 bytes, SHA256 **3339c28cd99605c3c928f9c4f145245b39efb1f7ed99a19a17c1547d8e101c4e**, unexpired, expiry **2026-10-27 07:59:40 UTC**. Builder's lineage ties it to R04 original 11790440856+11790585684. This is a recovered *SDK*, NOT a cached OCP binary and not proof the current fmt-augmented source-lock accepts the old SDK metadata automatically. The R04 source-lock digest changed in R05; cross-run acceptance must prove old SDK component inputs immutable and its manifest remains valid, rather than overwrite origin provenance.

**R05-02 PASS: exact fmt source/binary probe.** Last hosted noncompiling `dependency-probe` job ran to its intended fail-closed policy step; artifact **11799090609** exists, 1,983 bytes, SHA256 **293017b77e9bc8d4cb44563d18c150d944b47eecdedef5d8a9c3bdc77b30010b**, expiry **2026-10-27 08:36:48 UTC**. The locked `fmt 12.1.0 h1ced75a_1` conda archive SHA256 **1d6d6f1bf284e50cf617ce9a6250e0bf70bd0d30b068568364d6b1852aad9466** matched; 64-bit `Library/bin/fmt.dll` SHA256 **0d4edfe1411f4a7c5f57758239f0f1e6e1cff7f2d0ae5f9511a1dfacc08b388d**, upstream source SHA256 **ea7de4299689e12b6dddd392f9896f08fb0777ac7168897a244a6d6085043fea** and MIT notice SHA256 **07580f2a3b35709ce703d523f447b242f6dfec7582a8c0df102c7fa2849375f8**. fmt source/recipe identity proven in reported job. This resolves the *named fmt ownership* blocker at the probe stage, but **does not close final OCP Pyd's dynamic import closure**, because no new OCP compilation was run.

**R05-03 CHANGES REQUIRED: conda environment-owned Microsoft runtimes.** `fmt.dll` imports six `api-ms-win-crt-*` API sets and three MSVC DLLs. Probe resolved six copies to conda `ucrt 10.0.26100.0 h57928b3_0` (locked package archive SHA256 `3005729dce6f3d3f5ec91dfc49fc75a0095f9cd23bab49efb899657297ac91a5`) and `msvcp140.dll`, `vcruntime140.dll`, `vcruntime140_1.dll` to `vc14_runtime 14.51.36247 habf1de7_41` (archive SHA256 `4e4cb599cdc41bf2109d1464c127b5bcbddf548ce3e322e612afb691338b48f8`). PackLab's current `probe_fmt_dependency.py` resolves search dirs in order `fmt parent (= CONDA_PREFIX/Library/bin)`, then conda paths, THEN Windows `System32`, and enforces source-lock matching for any DLL found in conda. Thus these nine blocked file records reflect **which copies the probe chose**, not necessarily nine files that must be bundled with an Installer. No evidence exists yet that locally-shipping all nine files is needed, permitted or safe.

**R05-04 architectural clarification to prevent artificial license block.** Microsoft documents UCRT as an **OS-provided component in Windows 10/11**; standard deployment prefers OS servicing. VC++ v14 runtime deployment is supported through the official, appropriately versioned **Microsoft Visual C++ Redistributable** subject to license terms and architecture requirements, generally preferred over app-local DLL copying. Specific guidance:
- https://learn.microsoft.com/en-us/cpp/windows/universal-crt-deployment
- https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute
- https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist/
- https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files

Source-availability requirements for open-source fmt/OCCT must **NOT mechanically be applied to proprietary Microsoft OS/runtime binaries**. Instead distinguish `SYSTEM_OS_API_SET`, `MICROSOFT_RUNTIME_PREREQUISITE`, and `APP_LOCAL_DISTRIBUTED_FILE` with recorded Microsoft official documentation/license/REDIST applicability. Do not relabel a conda DLL found inside a conda prefix as Windows `System32`, or silently ship Microsoft/con-da copies. Runtime resolution on target **fresh** Windows 11 and minimum supported Windows must be demonstrated, and official VC redist version must be no older than required compiler version. Actual distribution/prerequisite choice and license/redistribution proof remains OPEN; this is not legal approval.

**R05-05 PASS: implementation safeguards and stop.** Windows-hosted lock probe failed CLOSED on unknown deployment/notice owners, without OCCT/OCP compile or installer. GitHub quality job SUCCESS at R05 source SHA; builder reports 36 tests PASS, mypy, Ruff, formatting, compileall, 19 imports and YAML checks. No secret exposure or owner Desktop modification reported. Parent source-built 315 No-VTK contract, 4 workers, Python 3.12.15, manual-only native workflow and incomplete PL-0350 preserved.

## Required R06, before any >hour build

1. Resolve *deployment class* for each of nine conda-owned imports by a noncompiling Windows-hosted OS-vs-prefix PE resolution test, considering Win10/Win11 baseline, API-set forwarding and system UCRT. Never mark a conda DLL as OS if the planned staged package still includes it. Explicitly exclude conda UCRT app-local copies from final payload if OS-mode is chosen; prove loader resolves on clean target system.
2. For VC++ v14 runtime, decide via official Microsoft license/REDIST documentation whether the installer should verify/install official x64 `vc_redist` prerequisite, or ship enumerated licensed files locally; pin provider/version/architecture, minimum toolset compatibility, SHA of any redistributed *installer package*, terms and exact installed/not-bundled file disposition. Avoid downloading/unverifiably uploading a mutable `latest` package as a pinned asset.
3. Align dependency probe, source/redistribution classification, OCP builder/manifest validator/bundle/Studio installer with distinct `BUILD_ENV_CONDA_FILE`, `SYSTEM_PREREQUISITE`, `APP_SHIPPED_THIRD_PARTY_FILE` roles. Fail closed on unresolved imports, inappropriate license/source claims, actual unowned shipped files and missing installer prerequisites. fmt itself remains a pinned MIT owner. Test negative matrices including absent VC runtime, conda/System32 name collision, tampering, wrong MSVC versions and runtime absent from fresh target.
4. **Do not rerun OCCT or two-hour OCP until the entire precompile native dependency plan, SDK cross-run provenance and production manifest schema pass**. Preserve rescued SDK, use a short R06 manual-only hosted probe; only if COMPLETE green, enable one narrowly authorized native continuation. Immediately quarantine any newly compiled Pyd before post-link/compliance gate to avoid another lost two hours. Stop at first new blocker.
5. Owner Desktop/known-good EXE, ChatGPT-only root TASKS.md, unrelated PackLab tasks, no pywrap, no opaque wheel, provenance and installer smoke gates remain unchanged.

## Disposition

**AUDITED_PARTIAL_CHANGES_REQUIRED** for PL-0350; successfully retained OCCT SDK and verified fmt, but Microsoft runtime deployment/provenance is unresolved. No Installer and NO native OCP link during R05. Start R06 *only* from this focused task, not a new milestone.

R06 Codex:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_WINDOWS_CRT_DEPLOYMENT_R06_CODEX_PROMPT.md

R06 matching criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_WINDOWS_CRT_DEPLOYMENT_R06_CHATGPT_AUDIT_CRITERIA.md
