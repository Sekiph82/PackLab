# PL-0350 — ONE-SHOT MASTER | FINISH ALL REMAINING WORK, DELIVER ACTUAL WINDOWS INSTALLER

**Executor: Codex. Repository: `Sekiph82/PackLab`. Current task: PL-0350 ONLY.**
**This single master replaces R06 AND all subsequent piecemeal PL-0350 implementation/remediation prompts.**
**OWNER PRIORITY: TOTAL ELAPSED TIME. Work autonomously from current main to the final PL-0350 deliverables. Do not stop to request another task number, R07 prompt, or owner approval for each routine defect.**

Authoritative root `TASKS.md` remains **ChatGPT-only**; Codex owns code, tests, workflows, builder logs and evidence. Final independent PL-0350 audit remains **ChatGPT-only**; Codex must never mark PL-0350 PASS itself.

Required reading ONCE at start: live `origin/main:TASKS.md`, this prompt, matching ChatGPT audit criteria, owner's hosted build approval, latest R05 audit, source/conda locks, current source manifests and Windows workflow:
- Master audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_ALL_REMAINING_WORK_ONE_SHOT_CHATGPT_AUDIT_CRITERIA.md
- Owner native build authority: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OWNER_APPROVAL_HOSTED_BUILD_315_NOVTK.md
- Latest accepted R05 evidence: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_FMT_PROVENANCE_R05_CHATGPT_AUDIT_V01.md
- Historical R01–R05 reports/implementation, R06 master, `tools/packaging/windows_native_source_lock.json`, `tools/packaging/packlab-ocp-bindings-win.lock`, `tools/packaging/controlled_ocp_runtime_contract.json`, `.github/workflows/windows-studio-build.yml`.

## ONE TASK, ALL REMAINING WORKPACKAGES

Execute **W01–W12 within this ONE assignment**. Work on *independent* W02/W03/W05/W07 readiness items in parallel/separate logical passes where useful; respect actual dependencies when compiling, sealing and packaging. Each workpackage gets a concise builder log subsection and local acceptance tests, **not a new ChatGPT prompt**. Automatically correct narrow issues found during implementation/test and continue to next workpackage. Codex may create its own brief code-level todo notes only within its required log, never new tracking dashboards, new milestones or extra owner prompts. Do not move to PL-0351, M17 or PL-0368.

### W01 — Non-destructive source sync and native cost/trust gates

Fetch `origin/main`, read root tracker, and fast-forward managed Codex worktree non-destructively. Preserve every owner Desktop untracked/dirty file, both current+previous-good PackLab.exe/OwnerDev, other repos and shared caches. No reset --hard, broad cleanup, local native OCCT/OCP compilation, giant Python tests or owner's local installer overwrite. Keep C: >=40GiB, pytest/temp/fixture quotas at 4/2/8GiB. All long compiles occur **only on GitHub-hosted Windows 2022**. Workflow must stay `workflow_dispatch` ONLY, explicit affirmative user authorization input, exact SHA, and preflight-only option that skips all heavy jobs. No signing, public release/tag, network secrets or untrusted prebuilt OCP wheel.

### W02 — Restore reusable OCCT SDK and bridge source-lock identity

**Already built, do NOT rebuild casually**: R05 recovery https://github.com/Sekiph82/PackLab/actions/runs/38366186522 uploaded GitHub artifact ID **11796717315**, size **114,366,551**, SHA-256 **3339c28cd99605c3c928f9c4f145245b39efb1f7ed99a19a17c1547d8e101c4e**, expiry **2026-10-27 07:59:40 UTC**. Inner SDK **7,991 files / 173,975,159 bytes**, payload SHA-256 `7ad1c8b0b2634d32eeada2e6d8fa4fb6e85f7f3c1e6989e8beab7ebdbc2c9031`. Source-pinned OCCT 7.9.3, `USE_OPENGL=ON`, `USE_VTK=OFF`, win64/vc14 installed layout, real native CPython 3.12.15. The **original R04 source-lock SHA is historical**; R05 appended fmt. Verify **immutable SDK-relevant source/toolchain inputs** for cross-lock compatibility and record exact origin artifact chain without rewriting original source-lock digest, copying wrong R02 OpenGL-OFF SDK or fabricating cache-HIT. Run short hosted restore/validate/republish if needed before expiry; do not download 114MB to owner C: unnecessarily. SDK stage cache key must be based on SDK inputs, not unrelated workflow text. No OCCT compile if a verified reusable SDK exists.

### W03 — Finish fmt DLL and Microsoft CRT deployment model, END TO END

Current R05 nonbuild probe https://github.com/Sekiph82/PackLab/actions/runs/38370004545 established:
- `fmt 12.1.0 h1ced75a_1` conda archive SHA256 `1d6d6f1bf284e50cf617ce9a6250e0bf70bd0d30b068568364d6b1852aad9466`, MIT upstream+recipe/source evidence, AMD64 `Library/bin/fmt.dll` SHA256 `0d4edfe1411f4a7c5f57758239f0f1e6e1cff7f2d0ae5f9511a1dfacc08b388d`. fmt upstream MIT source proof is COMPLETE at probe level. Do not re-research it or mark it an OS DLL.
- Six `api-ms-win-crt-*` imports resolved *in conda-prefix build probe* to locked `ucrt 10.0.26100.0 h57928b3_0` archive SHA256 `3005729dce6f3d3f5ec91dfc49fc75a0095f9cd23bab49efb899657297ac91a5`. Three `msvcp140.dll`, `vcruntime140.dll`, `vcruntime140_1.dll` resolved to locked `vc14_runtime 14.51.36247 habf1de7_41` SHA256 `4e4cb599cdc41bf2109d1464c127b5bcbddf548ce3e322e612afb691338b48f8`. These NINE conda binaries are *not automatically required in our Installer*.
- **Default least-risk Windows deployment path:** Supported Windows 10/11 provides serviced UCRT/API sets as Windows system component; DO NOT package copied conda `ucrt` forwarders in OS mode. For MSVC v14 runtime, use exact documented Microsoft-signed x64 Visual C++ Redistributable **prerequisite** of version >= required linked toolset; detect missing/wrong architecture/version and fail installer safely or install official signed pinned redistributable when authoritative license and checksum are available. Do not claim conda `vc14_runtime` DLLs are magically System32 or permitted to redistribute. Choose app-local MSVC DLLs only with exact REDIST-list/entitlement evidence. Check Windows minimum and offline installer requirements explicitly.
- Consult actual Microsoft UCRT, MSVC redist and REDIST-list docs; record verifiable release/version, provider, Authenticode/sha256 if a redistributable executable is shipped; document legal_review_required=true/public_release_authorized=false. No invented source SHA for closed-source Microsoft runtime. If an official signed-prerequisite license can't be proven for bundling, **ship none and implement a versioned prerequisite gate**, documenting installer behavior. Do not weaken any SOURCE/NOTICE gate for actual bundled libraries.

### W04 — Cohesive ownership, PE closure and redistribution implementation

Implement the decided CRT policy and pinned fmt across the **entire** production chain: `probe_fmt_dependency.py`, `build_controlled_ocp_from_generated_sources.py`, native source/third-party build contract, `validate_controlled_ocp_manifest.py`, `controlled_ocp_runtime_bundle.py`, `windows_redistribution_inventory.py`, packaging UI/installer config+notices and corresponding tests. Separate **BUILD_ENV_CONDA_ONLY**, **WINDOWS_OS_COMPONENT**, **MICROSOFT_SIGNED_PREREQUISITE**, **APP_SHIPPED_THIRD_PARTY**, **OCCT_OWNED**, **OCP_SOURCE_BUILT**. Actual PE graph must be fully resolved against hashed installed payload, true supported Windows OS runtime and prevalidated required official VC redist; do not just add `fmt.dll` to `is_external_runtime()` or fake it as OCCT-owned.

File-level fmt binary hash, MIT notice/source+recipe, exact conda package hash and import closure must carry into signed-off engineering manifest; every file actually shipped gets a genuine owner/version/license/source/notice. Unknown, absent, ambiguous, spoofed, duplicate, or extra shipped DLL blocks engineering packaging. Don't mistake OS API-set forwarding for a redistributable app DLL. Validate real final Pyd's imports after compilation, not just conda probe.

### W05 — Preflight / diagnostic cheaply prove ALL known failure classes first

Combine required small tests for: Python bootstrap 3.12.10 vs conda native Python 3.12.15; repo `python -m tools.packaging.*` import resolution; No-VTK exactly 319 source triplets→315 binding modules with four IVtk-only exclusions; `USE_OPENGL=ON`, `USE_VTK=OFF`; nested `win64/vc14` SDK SDK artifact layout, source/SDK metadata and CMake exports; noncompiling 315-generated includes and link dependencies; fmt file/source/notice identity; OS API set resolution; minimum MSVC redist/authoritative source+version; all PE direct/transitive owners; tamper/missing/extra/wrong-arch tests; actual installer prereq behavior in simulation; SDK cross-lock lineage compatibility; workflow auto-trigger safety and post-link quarantine. Make diagnostic a guarded **manual-only Windows-hosted <=30min job** with actual PASS/BLOCKED report/artifact. Do NOT compile heavy native OCP when this noncompile preflight is red. Continuously repair cheap code/fixtures as needed **within this one prompt**, without needing another R07 instruction.

### W06 — Native builds; mandatory checkpointing before audits

After complete W01–W05 PASS, use recovered valid source-built SDK, no redundant OCCT compilation. Real binding remains: CadQuery OCP 7.9.3.1.1 official generated ZIP **6,481,047 bytes**, SHA256 **290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b**; 315 modules (319 minus IVtk/IVtkOCC/IVtkTools/IVtkVTK), native OCCT 7.9.3, Python conda 3.12.15, pinned Windows/MSVC/CMake SDK and <=4 workers; no VTK, no pywrap generation, no opaque prebuilt OCP wheel.

Launch a **manual** exact-SHA hosted cold native build only after all short checks green. Real OCCT SDK must be verified and uploaded/available across job boundary before OCP starts. Native OCP C++ build already succeeded once in R04, then fmt policy rejected it; **after linking OCP*.pyd, immediately SHA256/bytes attest and upload a QUARANTINED NON-DISTRIBUTABLE Pyd artifact** with exact SDK/source/toolchain/module identities *BEFORE* PE/provenance/runtime checks. This artifact does not confer runtime clearance and must not be included in shipped Installer until clean. If later compliance/smoke fails, retain Pyd+SDK and fix code/provenance without spending 2h recompiling unless actual source/ABI changed. Validate genuine native import and CAD/STEP after full dependency ownership. Upload sealed controlled OCP bundle with verified per-file hashes and source inventory.

### W07 — Engineering Studio packaging / Installer creation

In parallel with prior build phases, prepare installer scripts, distribution inventory, notices, minimum Windows OS / VC prerequisite behavior and actual packaging tests. After W06 valid runtime, run real PackLab Studio package (Qt GUI, QtPdf/PDFium, Open3D, CAD/BREP, STEP import/export, DXF, measurements) and **offline/no-network** smoke on hosted Windows environment. No forbidden Qt modules, no unowned DLL or missing corresponding source/NOTICE. Require engineering clearance state `CLEARED_FOR_PL0350_ENGINEERING_PACKAGING` and `unresolved_count=0`, independent `legal_review_required=true`, `public_release_authorized=false`. Build **real unsigned Inno Setup Windows Installer (.exe)**; upload Actions artifact plus SHA256, bytes, immutable revision, native manifests, source/notice report and smoke logs. No signing or GitHub Release. PL-0351 clean-machine acceptance remains separate and NOT to be executed here; lightweight package/installer smoke belonging to PL0350 IS authorized.

### W08 — One measured warm-cache proof

Only after successful cold Installer, execute one independent warm cache HIT workflow on exact inputs. Verify source-built OCCT and OCP heavy compilation actually SKIPPED, exact validated source/runtime cache manifests and packaged smoke still RUN. Record distinct run URLs and artifact SHA, no invented HIT. If warm reuse breaks, **auto-remediate cache identity/restore** with quick tests and one verified proof; do not redo two-hour compile just because job metadata changed. Stop safely on irreconcilable artifact/source mismatch.

### W09 — Quality / bounded regressions

Throughout W01–W08, run focused changed-code pytest (negative cases), Ruff+format, mypy, compileall, true workflow YAML parser, import smoke and GitHub Windows Quality, plus relevant existing locked suite once at an appropriate stage. Respect owner C: quotas. R05 36/36 checks and earlier 2,061/11 checks are historical, not new evidence; log current counts honestly. Every source+build manifest, security boundary and recorded owner metadata must survive tamper tests.

### W10 — Efficient autonomous remediation INSIDE THIS SINGLE MASTER

When an implementation/test/hosted stage fails, do **NOT** stop simply to ask ChatGPT for R07, R08, another prompt, or another task number. **In the same Codex run**, extract exact GitHub job logs, classify first error, amend only affected code+tests, execute fast preflight, sync commit+quality, then resume from last verified immutable SDK/Pyd/source checkpoint. Technical import, path, CMake, manifest, source-identity, known dependency mapping and test failures are expected in-scope for Codex to self-repair. Save evidence per checkpoint and continue towards Installer.

**Strict bounded cost/owner safety:** No blind repeat of a six-hour monolithic Actions run. No parallel duplicate cold native jobs. Before repeating ANY >30min native compile, show (in builder log) why existing checkpoint cannot be used, exact changed compiled inputs and a successful short failing-case reproduction. At most ONE new OCP native cold compile plus TWO genuinely distinct, preflight-proven repair compiles within this master; one OCCT recompile only if the SDK is cryptographically invalid/unrecoverable and owner has separately approved that distinct rebuild. If repair budget/expenditure exceeds this scope, or genuinely new source/legal/signing/permission decisions cannot be resolved from authoritative evidence, STOP with one actionable owner decision rather than fabricating clearance. Unlimited small tests/cheap static fixes within safe budgets; no one-hour polling loops or recurring workflows.

If OCP source unchanged and only post-link runtime/manifests/compliance changed, **must prefer reuse of quarantined Pyd** rather than recompiling. Never downgrade source/redistribution checks for convenience.

### W11 — Evidence + all-in-one final Codex handoff

Codex keeps ONE **append-only** master build log for this single PL0350 assignment, even across its own commits/technical sub-phases:
`coordination/sessions/M16-C001/PL-0350_ALL_REMAINING_WORK_ONE_SHOT_CODEX_LOG.md`
And one authoritative **builder result**:
`coordination/sessions/M16-C001/PL-0350_ALL_REMAINING_WORK_ONE_SHOT_REPORT.md`

Also update existing builder-only `MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md` to refer to the new ONE-SHOT result and preserve all old R01–R05 history. DO NOT generate 12 separate cycle/master prompts, new milestone trackers, or new R07/R08 task state. Link real source/implementation SHA, evidence SHA and exact run/job URLs, test counts, SDK and quarantined+approved OCP artifact IDs/hash/expiry, fmt/MSVC API-set policy and binary/notice source evidence, cold+HIT, packaged smoke, unsigned Installer artifact SHA/size and git main parity. Distinguish `COMPLETE_AWAITING_INDEPENDENT_AUDIT` from safe blocking condition; Codex cannot self-award auditor PASS.

### W12 — Finish/stop criteria

Goal is **actual working unsigned Windows Installer** plus source-built 315 No-VTK OCP, full package tests, zero unresolved shipped files, owner-protected Desktop, and verified cold+warm hosted evidence. **Do not conclude after W03 fmt or W05 preflight PASS.** Continue autonomously with all remaining PL0350 work to completion.

Only legitimate early stop: security/provenance/legal source actually impossible to evidence, required owner decision outside original authority, irrecoverable SDK Pyd checkpoint with further expensive work not authorized, or an actual exhausted hard compute quota. Report first unresolvable decision exactly; not a generic 'need next prompt'. PL-0351, M17, PL-0368 remain untouched. Root `TASKS.md` and independent ChatGPT audit files remain unchanged by Codex. Final handoff for ChatGPT independent audit **only once** at completion (or unavoidable substantive blocker).

**DO THE WHOLE PL-0350 NOW. ONE PROMPT. NO PIECEMEAL TASK HANDOFF.**
