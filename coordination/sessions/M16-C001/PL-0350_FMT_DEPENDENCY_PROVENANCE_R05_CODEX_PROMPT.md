# PL-0350 R05 | Preserve Proven OCCT SDK, Resolve Real fmt.dll Ownership, Then Controlled OCP/Installer Continuation

Executor: **CODEX**. Same PL-0350 only; no new milestone or unrelated change. Existing owner approval covers the exact source-built Windows 2022 315-module no-VTK route, but NOT uncontrolled rebuild/retries or unknown third-party binary distribution.

R04 independent audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_SDK_WINDOWS_LAYOUT_R04_CHATGPT_AUDIT_V01.md
Matching criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_FMT_DEPENDENCY_PROVENANCE_R05_CHATGPT_AUDIT_CRITERIA.md

## Exact observed state

At cold run https://github.com/Sekiph82/PackLab/actions/runs/38346317865 :
- **OCCT source-built SDK PASSED, SEALED, stored.** Artifact ID **11790440856**; ZIP SHA256 `467b44ab0fb747343cb55e55e71a0dd4ecadb989fd7eed22d1e49fff3153ddf8`; 57,520,243 bytes; corresponding source evidence ID **11790585684** digest `091c391b8d6ccda19823f57eae891b1dd45383b164c117ca05928df6bafd2018`. Artifacts currently expire **2026-10-14 05:03 UTC**. SAVE verified SDK durable checkpoint **FIRST**, without native compilation.
- OCP compiled: GitHub logs show `OCP.cp312-win_amd64.pyd` from real `cmake --build`. Post-link PE dependency scan then failed `compiled OCP references an unowned DLL dependency: fmt.dll`. No OCP artifact was sealed or uploaded; hosted runner's resulting pyd is not accessible from a new run.
- Exact conda lock already has `fmt==12.1.0` Windows package `fmt-12.1.0-h1ced75a_1.conda` SHA256 `1d6d6f1bf284e50cf617ce9a6250e0bf70bd0d30b068568364d6b1852aad9466`. The existing OCP ownership code only knows OCCT-owned DLLs and Windows OS/system DLLs. **A locked conda package is NOT itself proof of its exact compiled DLL identity or redistribution/source/notice clearance.**
- No installer/native CAD smoke/PL0350 PASS. DO NOT report this as C++ compilation failure.

## R05.0 immediate NON-BUILD checkpoint rescue

1. Non-destructively read live origin/main TASKS.md, this audit, exact artifact metadata and producer/consumer schema; sync controlled worktree without touching user's Desktop, known-good PackLab EXE, active worktrees, shared caches or root TASKS.md/ChatGPT audits.
2. **Time-critical:** before artifact expiry, use a *short manual GitHub-hosted read-only recovery/reseal operation*, without OCCT/OCP compilation, to retrieve exact original R04 SDK **and source evidence**, verify GitHub outer artifact SHA+size and EVERY sealed inner file SHA/byte identity, source lock `OCCT=7.9.3`, compiler/MSVC, SDK, native Python 3.12.15, `USE_OPENGL=ON`, `USE_VTK=OFF`, `win64/vc14` layout. Preserve original bytes and origin run/artifact/manifest identity in a lineage record. Re-publish to verifiable durable cache or new Actions artifact under current run with retained provenance; no metadata laundering, guessing cache HIT or deleting previous checkpoint. Respect existing artifact budget and limits. If artifact inaccessible, say so immediately and STOP before any requested native source rebuild.
3. Prevent needless future 40-50min SDK rebuild from a workflow-only hash change: revise **stage-specific source/config/toolchain/SDK-producing-file cache identity** instead of whole workflow YAML hash, but only if security/provenance remains fail-closed. Validate origin and current source/SDK build options, exact validated payload lineage and current toolchain. If cache incompatible, REUSE only the independently verified payload with explicit origin-run attestation; never treat old `USE_OPENGL=OFF` R02 SDK as valid. This SDK rescue is a separate documented noncompiling gate.

## R05.1 complete third-party native ownership BEFORE long OCP build

4. Inspect exact locked conda-forge `fmt==12.1.0` package provenance, including conda manifest/recipe/source reference, license+notice and Windows `fmt.dll` path/PE SHA256/architecture/imports on a **hosted Windows 2022** runner. Verify which linked native binary is actually imported by built OCP, not by assuming name match. If unproven, stop `FMT_PROVENANCE_REQUIRED`; do NOT whitelist as Windows System32, OCCT-owned, or copy unknown binary into package.
5. Inspect full link closure of the 315-generated OCP CMake and all OCCT SDK toolkit dependencies, exact conda native package binaries, built/link dependency graph and all transitives against Windows system trusted imports. Identify ALL third-party DLL dependencies upfront, not just fmt. Add a bounded host-only **precompile import/ownership preflight**: verify the DLL exists in the exact locked conda env, full PE import closure and required corresponding sources/licenses/notice records. Static CMake link + representative tiny PE link fixture acceptable for preflight; do not imply it proves final extension byte imports. Fail BEFORE spending another 2h if any required owner remains unknown. Mark dynamic late dependencies unresolved until checked on real Pyd.
6. Extend **all ownership authorities consistently**, not just the first exception: source lock with pinned/attested fmt exact upstream source+license/notice (and any other required native libraries), file-level OCP manifest producer and validator, bundle sealing/validation/install, package dependency tree, Windows redistribution inventory/source/NOTICE evidence, runtime smoke. Source archives must be immutable by verified SHA, not invented. Every staged fmt DLL must have exact conda binary package identity, DLL SHA, owner, source, license, and expected transitive PE DLLs; reject tampered/missing/extra binaries. Preserve source-built OCP/OCCT, 315 modules, No-VTK, Python 3.12.15 and 4-worker cap. **Do NOT change fmt linker mode to static/header-only merely to hide provenance**, and do not bypass license gates.
7. Add small negative/positive fixture tests for fmt binary ownership, source evidence, PE dependency graph, nested redistributable DLLs, unknown additional transitive, copy integrity, OS fake whitelist, package manifest mismatch and runtime tree tampering. Add a noncompiling hosted `dependency_probe_only` or fully guarded preflight-only mode covering actual locked conda fmt metadata, Windows DLL existence and dependency ownership. No native OCP build until those checks truly PASS; no secret upload.

## R05.2 controlled build, preserve expensive output

8. Run focused tests + Ruff/format/mypy/compileall/actual workflow import probes/real YAML parser and quality CI, bounded local disk; preserve manual-only workflow_dispatch exact-SHA/input and skip guarantees, avoid local OCCT/C++ or giant tests. Keep legal_review_required=true/public_release_authorized=false. Commit/push tested changes to main and verify no accidental native auto-trigger.
9. Only after SDK rescue and full precompile ownership gate PASS, run **ONE corrected cold GitHub-hosted** native continuation. **Use recovered authenticated SDK; do not rebuild OCCT** if its source/toolchain and layout are fully compatible. Same-run SDK republish/checkpoint MUST be validated before OCP expensive stage. No pywrap regeneration or opaque prebuilt OCP wheel. If Stage A reuse cannot be proven, STOP with `SDK_RECOVERY_BLOCKED` rather than silently spending 50 more minutes.
10. For OCP stage, deliberately **preserve the newly compiled Pyd immediately after linker succeeds**, with immutable generated-source/315-module/SDK/config/compiler/ABI/hash manifest in a **quarantined non-distributable artifact** BEFORE executing potentially failing ownership/compliance scans. Require that a quarantine artifact cannot be installed, declared cleared or bypass source/ownership gates, and can only be resumed if separately verified byte-for-byte/source-locked. This prevents a second loss of 2h of completed C++ compilation. Quarantine storage must respect size/time/security budgets.
11. Then complete exact dynamic PE closure and source/NOTICE ownership, emit sealed native bundle only if ALL dependencies including fmt are accounted for and actual `import OCP` CAD/STEP smoke passes. Stop at any missing dependency; save quarantine/previous successful SDK. Only then run Studio packed GUI/QtPdf/PDFium/Open3D/STEP/DXF/CAD offline smoke and zero unresolved source/license/notice/forbidden Qt gate, produce real unsigned Installer artifact and hash. ONE genuine warm cache HIT only after full cold installer success. No signing/public release, PL-0351, M17 or PL-0368.
12. If any first blocker, STOP; no automatic repeated 2-hour OCP recompile. No change of owner data/files. Capture actual artifact IDs, expiry, sizes, digests, real cold/probe/HIT run URLs and status, not speculative PASS.

## Handoff

Publish and commit builder-owned:
- `coordination/sessions/M16-C001/PL-0350_FMT_DEPENDENCY_PROVENANCE_R05_CODEX_LOG.md`
- `coordination/sessions/M16-C001/PL-0350_FMT_DEPENDENCY_PROVENANCE_R05_REPORT.md`
- Update `MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md` to latest state.

Report source-lock SHA, fmt conda package SHA and actual DLL SHA, full native DLL owners, SDK recovery lineage, 315 generated modules and compiled extension SHA if available, actual tests/runs/artifact identities, first failure and owner Desktop/git parity. Do not edit root TASKS.md, independent audits or owner decisions.

Final only `READY_FOR_INDEPENDENT_PL0350_AUDIT` if real installer + clearance + cold/warm proof exist, otherwise `BATCH_STOPPED_AT_PL-0350 / <FIRST_BLOCKER> / AWAITING_INDEPENDENT_AUDIT`. 
