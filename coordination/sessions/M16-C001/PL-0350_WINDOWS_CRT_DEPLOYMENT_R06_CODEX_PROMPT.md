# PL-0350 R06 — Resolve Windows UCRT / VC++ Runtime Deployment Before Another OCP Compile

**CODEX MASTER IMPLEMENTATION PROMPT. SAME PL-0350, NO NEW MILESTONE.**
Owner approval applies to the official source-built 315-module No-VTK GitHub-hosted route; no uncontrolled repeated cold build, any unrelated workflow, opaque wheel substitution or public release.

**Independent R05 audit:**
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_FMT_PROVENANCE_R05_CHATGPT_AUDIT_V01.md

**Matching R06 audit criteria:**
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_WINDOWS_CRT_DEPLOYMENT_R06_CHATGPT_AUDIT_CRITERIA.md

**Existing source-built build authority:**
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OWNER_APPROVAL_HOSTED_BUILD_315_NOVTK.md

## Current verified state

- R05 rescued OCCT SDK **without compiling**: https://github.com/Sekiph82/PackLab/actions/runs/38366186522 ; artifact **11796717315**; SHA-256 `3339c28cd99605c3c928f9c4f145245b39efb1f7ed99a19a17c1547d8e101c4e`, 114,366,551 bytes, **expires 2026-10-27 07:59:40 UTC**. Sealed SDK interior 7,991 files / 173,975,159 bytes SHA-256 `7ad1c8b0b2634d32eeada2e6d8fa4fb6e85f7f3c1e6989e8beab7ebdbc2c9031`. Rescued SDK contains original `OCCT=7.9.3` build with `USE_OPENGL=ON, USE_VTK=OFF`, exact 3.12.15 Python, real win64/vc14 layout; provenance is the **R04 source-lock hash** `c6a32326...`, not the R05 source lock augmented with fmt. Do NOT rewrite the older source-lock digest inside its sealed manifest to fake identity.
- Hosted fmt probe https://github.com/Sekiph82/PackLab/actions/runs/38370004545 conclusively resolves `fmt==12.1.0` conda package SHA `1d6d6f1bf284e50cf617ce9a6250e0bf70bd0d30b068568364d6b1852aad9466`, DLL SHA `0d4edfe1411f4a7c5f57758239f0f1e6e1cff7f2d0ae5f9511a1dfacc08b388d`, pinned upstream MIT source/license/recipe. **fmt itself passed.** Blocker is six `api-ms-win-crt-*` names resolved by current probe to conda `ucrt 10.0.26100.0` and three MSVC DLLs from `vc14_runtime 14.51.36247`, with no official deployment classification/notice.
- R04 OCP actually C++ linked `OCP.cp312-win_amd64.pyd`, then post-link ownership scanner failed `fmt.dll`. No OCP artifact survived. OCP **must not** recompile while known runtime provenance unresolved. No Installer exists.

## R06.0 Non-destructive sync / preparation

1. Fetch main in existing managed worktree without destructive reset, read root `TASKS.md`, audit and owning approval, preserve user's Desktop modified/untracked files, current/previous known-good PackLab.exe, shared cache, other repos and unrelated worktrees. No native compiler or giant test locally, no broad cache deletion. Codex NEVER writes root TASKS.md or independent ChatGPT audit/decision files.
2. Preserve SDK recovery artifact by exact full hash + verified inner file/manifest + sealed origin lineage. SDK source-lock digest predates fmt record; compare **SDK-relevant OCCT/OCP build inputs** precisely between old/new locks and record a separate compatibility attestation only if frozen OCCT SDK dependency bytes/toolchain unchanged. Never rewrite original source record, blindly republish a provenance-free cache, or claim source-lock versions equivalent because their filenames match. R06 may use a SHORT no-compile hosted SDK recovery/checkpoint validation; stop if artifacts expired or evidence cannot be validated.
3. Enumerate all runtime PE imports of conda `Library/bin/fmt.dll` and probe resolution paths in exact Windows-2022 runner: OS System32/Windows API-set loader contracts versus copied `ucrt`/VC runtime files in conda prefix. For each of six `api-ms-win-crt-*` plus `msvcp140.dll`, `vcruntime140.dll`, `vcruntime140_1.dll`, record: locked package owner/build/SHA, exact prefix binary path + hash, OS resolver alternative, selected deployment policy, whether shipped into Studio, provider, required license/notice, proof and unresolved state. **Do not claim a conda file is an OS system file.**
4. Read official Microsoft deployment/licensing sources (not community guesswork):
   - https://learn.microsoft.com/en-us/cpp/windows/universal-crt-deployment
   - https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute
   - https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist/
   - https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files

   For Windows 10/11 baseline, UCRT is OS-serviced and generally should NOT be app-local shipped. VC++ v14 depends on official x64 Microsoft VC Redistributable of version >= MSVC toolchain and appropriate licensing; official redist central deployment preferred. Check if clean Windows runner already has it, but **presence on runner ≠ proof end user's clean machine does**.
5. Choose ONE explicit, evidence-backed production deployment contract for each:
   - `WINDOWS_OS_COMPONENT`: named API-set/UCRT resolved by supported Windows OS, no conda copy in Studio output, platform minimum enforced.
   - `MICROSOFT_SIGNED_PREREQUISITE`: official x64 Microsoft VC++ Redistributable, authenticated publisher/Authenticode, exact pinned artifact bytes/SHA/version/provider and actual license terms + redistributable eligibility; installer must verify/install or clearly enforce versioned prerequisite on a fresh machine, with offline installer/network policy made explicit and clear failure path.
   - `APP_LOCAL_REDISTRIBUTABLE`: allowed only when exact Microsoft REDIST list/licensing permits EACH app-local DLL and end-to-end source/notice chain is separately audited. Not default.
   - For open-source fmt, retain `PINNED_CONDA_THIRD_PARTY` with exact MIT upstream source, actual `fmt.dll` package SHA/file hash and notice. fmt.dll IS actually part of Stage OCP if required, and must be file-level owned.
   No fake "MIT license" or source archiving requirement for closed-source Microsoft OS and VC redist components. Instead exact official terms/REDIST evidence and actual deployed disposition. Unknown state must remain `BLOCKED`.
6. **Do not yet mutate source/provenance gates to PASS.** First issue a bounded, noncompiling **R06 Windows runtime deployment report** and executable tests that prove the classification is internally consistent. If official Microsoft terms or exact acceptable package version cannot be verified, STOP `MS_RUNTIME_DISTRIBUTION_OWNER_REQUIRED` and publish evidence, no native compilers.

## R06.1 Repair complete ownership and packaging system, NOT just the probe

7. Once supported by evidence, extend `probe_fmt_dependency.py`, native source/build component contract, `build_controlled_ocp_from_generated_sources.py`, `validate_controlled_ocp_manifest.py`, `controlled_ocp_runtime_bundle.py`, `windows_redistribution_inventory.py`, Studio packaging/prerequisite documentation/workflow so all **ACTUALLY SHIPPED** files have precise owner/source/terms and all **unshipped** Windows CRT DLLs are validated external requirements. Keep old valid fmt source lock and exact conda lock; do not mark OS/prerequisite files as PackLab-supplied source-built third parties. Treat runtime external dependencies as a separate validated manifest with min-OS/prerequisite proof and fail-on-target-missing.
8. Fix the **existing bug by design, not whitelist**: prior OCP PE dependency scan accepted only `is_external_runtime` or OCCT toolkit DLLs; now `fmt.dll` must be recognized as an exact locked conda-third-party file with real SHA and source/notice/pe graph. Conda-provided UCRT / VC14 files may appear on the **build** runner; they must not auto-enter the final shipped runtime. Ensure deterministic PE dependency ownership across direct+transitive imports and Windows API-set resolution (native `LoadLibrary`/delay imports where discoverable). Unknown/duplicate/tampered DLL → fail-closed. The final compiled Pyd's import table cannot be proven until actual link and must be scanned post-link.
9. Run representative small negative tests of absent/wrong MS VC redist, missing Windows API-set contract, conda-prefix DLL shadowing an OS DLL, bogus signed publisher, wrong redist architecture/toolset version, license/REDIST evidence absent, fmt DLL hash corruption or wrong package, missing native transitive, duplicate/unknown PE dependency, path collisions, injected unowned file and manifest source schema misclassification.
10. Give preflight-only/manual `.github/workflows/pl0350-fmt-dependency-probe.yml` a bounded noncompiling **runtime ownership + installed MSVC prerequisites** mode that exercises *real Windows runner* probe and produces an artifact/report, with explicit PASS/BLOCKED. Ensure `.github/workflows/windows-studio-build.yml` remains manual-only, exact source SHA and affirmative `run_native_build`, and its `preflight_only` skips SDK/OCP/Studio. No auto 6h producer on push. Run short/targeted checks, Ruff/format/mypy/compileall, true YAML parsing, import smoke, full relevant tests within owner local 40GiB C-free and 4/2/8GiB disposable quotas. No local native compile.

## R06.2 First native continuation only after all noncompiling gates PASS

11. Make source-locked recovered SDK *reusable* across runs with defensible original manifest origin/source-lock chain and full hash compatibility. **Don't trigger another 40–50m OCCT build** if rescued SDK matches; if reuse needs a safe isolated hosted bridge stage, implement bounded noncompiling republish/identity proof first. Stop if unavailable instead of silently rebuilding.
12. When and only when **actual hosted precompile dependency policy PASS**, source/license/redistribution schema validators PASS, fast target prerequisites PASS and SDK reuse verified, dispatch ONE owner-approved **manual cold native continuation** with official ZIP 319→315, Python 3.12.15, 4 workers, no VTK, no pywrap or opaque prebuilt OCP wheel. Prohibit uncontrolled retries.
13. **Immediately after actual OCP C++ links**, hash and upload a bounded **QUARANTINED NON-DISTRIBUTABLE** Pyd+source/module/build/SDK identity **BEFORE any PE or license check that could fail**. Fail closed if quarantine save fails, retain stage logs/checkpoint; do not allow quarantined Pyd to satisfy runtime or release gates. A failed audit must preserve this first new 2h binary for future investigation without having to rebuild it. No attempt to recover last R04 Pyd: it wasn't uploaded.
14. Complete actual post-link PE import closure incl fmt and system/VC prerequisites, validate native OCP CAD/STEP; only then seal controlled runtime and build PackLab Studio. Real packaged no-network QtPdf/PDFium/Open3D/STEP/DXF/CAD smoke, no unowned shipped DLL/unknown prohibited Qt, source/NOTICE/REDIST evidence and clean engineering inventory before real unsigned Installer. `legal_review_required=true`, `public_release_authorized=false`. If any stage fails STOP with first exact error and preserve **SDK + quarantine**. Warm cache-HIT workflow only after full installer cold PASS. No PL-0351, M17, PL-0368, signing or public release.

## Builder handoff

Publish to GitHub main:
- `coordination/sessions/M16-C001/PL-0350_WINDOWS_CRT_DEPLOYMENT_R06_CODEX_LOG.md`
- `coordination/sessions/M16-C001/PL-0350_WINDOWS_CRT_DEPLOYMENT_R06_REPORT.md`
- Refresh builder-owned `MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md` (preserve R05 and earlier history).

List exact implementation/evidence commits, saved SDK provenance and expiry, official Microsoft prerequisite terms/version/SHA if applicable, lock owners and each DLL disposition, test outputs, guarded hosted preflight/cold/warm URLs or explicit absence, quarantine artifact IDs/size/hash if produced, OCP/Studio/Installer results and source notice/license boundaries. Preserve origin/main parity and owner Desktop dirty files. **Do NOT write root TASKS.md or independent audit criteria.**

End `READY_FOR_INDEPENDENT_PL0350_AUDIT` ONLY if real fully cleared Installer + cold/warm provenance exists; otherwise `BATCH_STOPPED_AT_PL-0350 / <FIRST_HARD_GATE> / AWAITING_INDEPENDENT_AUDIT`. No silent authorization escalation.
