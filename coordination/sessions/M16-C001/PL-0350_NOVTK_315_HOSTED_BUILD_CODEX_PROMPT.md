# PL-0350 — Host-Gated 315-Module OCP / OCCT Native Build + Unsigned PackLab Installer

**Executor: CODEX. Repo: Sekiph82/PackLab. Branch: main.**
**Status: OWNER_APPROVED_TO_IMPLEMENT_AND_DISPATCH_ONE_CONTROLLED_HOSTED_COLD_BUILD.**
**NO MORE OWNER CONFIRMATION NEEDED FOR THIS EXACT FIRST HOSTED ROUTE.**
Owner authorization:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OWNER_APPROVAL_HOSTED_BUILD_315_NOVTK.md

Corresponding independent criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_HOSTED_BUILD_CHATGPT_AUDIT_CRITERIA.md

Mandatory source references:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_PREFLIGHT_CHATGPT_AUDIT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_PREFLIGHT_REPORT.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OWNER_DECISION_NOVTK_315_MODULES.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V07.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V05.md
- `tools/packaging/windows_native_source_lock.json`
- `tools/packaging/packlab-ocp-bindings-win.lock`
- `tools/packaging/controlled_ocp_runtime_contract.json`
- `tools/packaging/build_controlled_ocp_runtime.py`
- `tools/packaging/controlled_ocp_runtime_bundle.py`
- `tools/packaging/windows_redistribution_inventory.py`
- `.github/workflows/windows-studio-build.yml`
- Root canonical `TASKS.md`.

**Goal:** Produce verifiably source-built, VTK-free controlled 315-module OCP/OCCT runtime, packaged native-CAD-capable PackLab Studio, and a real unsigned Installer **without rerunning five-hour pywrap**. Prevent lost 42-minute OCCT work if later phases fail. Do not treat a launch or partial job as a PASS.

## Non-negotiable safety

- Start by `git fetch origin` and `git show origin/main:TASKS.md`, check owner decision/criteria are live; preserve owner Desktop dirty/untracked files and current/previous OwnerDev, all active worktrees. Use a clean managed worktree; no force reset, destructive sync or broad cleanup. Never edit root TASKS.md or `*CHATGPT_AUDIT*`/owner decision documents.
- **ALL expensive native builds run ONLY in GitHub-hosted Windows 2022**, no local OCCT or generated OCP compile on owner's Acer laptop. Respect local >=40GiB free C:, pytest/temp 4/2/8GiB quota policy, avoid large copies/checkouts/tests, don't prune shared uv or ambiguous AppData; protect other programs. No need to force owner runtime refresh until verified product code releases can be safely promoted, then retain known-good fallback and follow existing owner refresh contract.
- **FIRST remove accidental CI trigger:** `.github/workflows/windows-studio-build.yml` currently has `on: push` and `on: pull_request` path filters. Any changes to `tools/packaging/**`, `tests/ci/**` etc will otherwise launch old 6h production automatically. First make that heavy workflow **manual-only, `workflow_dispatch` with affirmative `run_native_build` input**, and add a job-level fail-closed input gate; use a dedicated small change before production scripts. Confirm actual post-push CI run list that no expensive old producer began. GitHub Actions workflow definition for push/PR must no longer auto-run native producer. The initial workflow edit may itself be a path match under old rules, so do not assume it is safe: read GitHub event behavior/current workflow at commit, publish minimal opt-in change, immediately inspect runs; if unintended old producer starts, cancel immediately (if authorized tool permits), do not start further work until stopped. Expect ordinary `windows-python-quality.yml` to run on `.github/workflows/**`; do not disable quality checks. **Never rely on `[skip ci]` to protect against the old native trigger.**
- Gate manual dispatch by exact source revision/inputs, one explicit attempt only (unless pass and one warm-cache proof). Do not schedule hourly/repeated build, use no automatic retries, do not rerun an old 6h workflow. No signing, public release, GitHub Release, tag, production deployment, secrets/credentials/external data upload. Keep legal-review flag / public-release=false.
- Scope is ONLY PL-0350; do not start PL-0351, PL-0352..0367, PL-0368, or M17.

## P0: preserve source and update schema before heavy runs

- Existing pinned native source: OCP 7.9.3.1.1 revision `d69b064a3a604ebf245b1f3b14fb54c835a3a571`, OCCT 7.9.3 revision `a016080bf6738d6aeae020badee4e888ad1540a5`; use current exact locked conda/native dependencies. Windows 2022 x64, CPython 3.12.15, MSVC 19.44.35229.0, Windows SDK 10.0.26100.0, CMake 3.31.8; 4 workers/parallel compile limit.
- Add separate frozen **official OCP pre-generated Windows source asset** input: `OCP_src_stubs_Windows.zip`, size **6,481,047**, SHA256 **`290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`**, exact official CadQuery release `7.9.3.1.1`. Verify downloaded archive byte count, full digest and safe paths/ZIP expansion before any patch/build. Fail closed on drift. The code-prep stage MUST NOT invoke pywrap or download an opaque wheel to substitute.
- Official archive must have 319 unique module triplets `M.cpp`, `M_pre.cpp`, `M_tmpl.hxx`, 638 corresponding register declaration/call pairs, `OCP.cpp`, matching module ID set. Apply a deterministic **upstream-equivalent No-VTK patch** removing exactly `IVtk`, `IVtkOCC`, `IVtkTools`, `IVtkVTK` triplets and `OCP.cpp` registrations/declarations; remove VTK CMake discovery and link targets/references. Test *actual patched file contents*, not merely 315-set arithmetic. Assert 315 complete retained triples, complete enum/module declarations+calls, no residual IVtk or VTK references in compiled CMake inputs, no duplicate/missing/extra. Preserve all non-VTK source bytes except intentional necessary integration edits, hash pre/post actual files, capture exact patch revision/digest.
- Preserve generated `OCP.__version__=7.9.3.1` separately from upstream release/package identity `7.9.3.1.1` in manifests; never silently rewrite version.
- Verify all 27 literal PackLab-imported OCP modules in generated 315 IDs (from prior preflight), and complete runtime dynamic import/CAD/STEP coverage. No change to CAD, STEP, DXF, BREP/geometry/measurements or Open3D logic; only packaging integration.
- Native OCP C++ build config must use the generated C++ source folder, not pywrap-generated original CMake path, and link OCCT with `USE_VTK=OFF` and pinned Python/pybind11/fmt. Re-create CMake build dirs in every fresh runner, no stale absolute CMake paths.

## P1: staged hosted pipeline, durable checkpoints, budget preflight

Implement a **true multi-job, same-run DAG** with an explicitly gated dispatch in existing workflow or a safe new workflow. Prefer separation:
- **Job A — OCCT SDK build and seal:** verify source lock, controlled OCCT Windows build/install (historically 2,560.860s), runtime/header/import libraries and required CMake config. Seal *minimal sufficient relocated SDK* in a validated artifact with versioned schema, SHA256+byte count for EVERY file, source/SDK/compiler identities and exact producer run/job ID. Retain source and license evidence. Upload checkpoint **before downstream work**; restore from exact cache only after full manifest check. Never include compiler temp trees/private cache/full repository.
- **Job B — source ZIP verify + No-VTK patch + native 315 OCP C++ compile:** fresh hosted runner, download **same-run Job A OCCT SDK artifact** (or exact authenticated re-publish from a content-validated cache), validate manifest and compatible toolchain. Fetch/re-verify official ZIP. Apply audited patch and 315 registration/module checks, configure native build with fresh paths, compile/link only generated extension (no OCCT rebuild, no pywrap). Confirm exactly one `OCP*.pyd`; stage only required OCCT `TK*.dll` and proven dependencies. Perform actual native `import OCP`, BRep box/check, shape/STEP IO smoke and dependency graph; log Python/OCCT identities. Seal runtime bundle with file hashes and full provenance mapping. Generated C++ compile time is **unknown**; constrain job to **<360 minutes including setup, validation and upload**. If timing threatens limit, stop before cancellation, export already validated stage evidence; do not increase workers or repeat blindly. Any proposed compilation sharding must be independently proven safe within this source lock.
- **Job C — production packaging/redistribution/unsigned installer:** separate fresh Windows runner consumes only validated **same-workflow-run** OCP runtime artifact, overlays controlled native OCP while removing `cadquery_ocp_novtk.libs`/opaque private DLLs. Run actual packaged **no-network Qt GUI, QtPdf/PDFium, OCP/CAD, STEP/DXF and Open3D** smoke. Fail closed on missing native DLL, import failure, VC runtime incompatibility, overbroad Qt/VirtualKeyboard, altered SDK/provenance or any unresolved source/notice/license row. Run existing exact production redistribution inventory and component mapping; reconcile actual binary tree file-by-file to pinned corresponding source/third-party licenses (do not fake zero). Build unsigned Inno installer ONLY if `CLEARED_FOR_PL0350_ENGINEERING_PACKAGING` and `unresolved_count=0`, missing sources/notices=0, forbidden Qt=0. Engineering status does not assert legal approval; `legal_review_required=true`, `public_release_authorized=false`. Upload versioned real installer plus technical compliance report/notice/source evidence and SHA256/bytes.

Each job <= GitHub six-hour hard hosted cap, use <=330-minute job timeout or demonstrably safe margin; cache keys include source SHA, official ZIP SHA, post-patch rule/hash, builder+validator digest, Python/MSVC/SDK/CMake and schema. No broad `restore-keys`; handle cache misses by rebuilding ONLY the affected phase from a valid prior checkpoint. Artifact immutability and two-way hash verification across jobs are required. Do not confuse the prebuilt OCP PyPI wheel and past six-hour logs with source attestations. Failure must retain earlier successful checkpoint and stop without recreating unrelated jobs.

**Before dispatching**, publish measured dry-run manifest/estimated sizes/runner free disk, projected job time headroom, release-license source paths and artifact quota/retention against real GitHub Actions constraints. If any one job is predicted infeasible, do NOT dispatch; stop and hand off measured blocker. Do not upload owner-specific data or local cache.

## P2: preflight test and controlled execution

1. First settle auto-trigger safety, independently inspect actual run list, all `.github/workflows` push/PR filters and appropriate permissions. If a dangerous automatic native job appears, STOP/cancel and report. Use good Actions best practice: actions pinned to exact full SHA, read-only token scope and no secrets.
2. Implement small deterministic pure/static patcher and validators, with tests for: exact ZIP sha/size; 319 input/315 output, four removal IDs, 638 registration mapping, missing/extra/duplicate source modules, stale VTK links, wrong cache key, tampered SDK/output file, path traversal, case-colliding paths, absent linked DLLs, wrong version identity. Test actual file rewrite on tiny in-memory/source fixtures, not merely presence of code tokens. Avoid large pytest duplications and local native builds.
3. Run changed-code Ruff/type/compileall, relevant locked unit/CI suites under monitored basetemp local quota, Windows Python-quality workflow. Existing full suite 2,055 PASS from previous iteration is context, NOT proof of current change; if full suite feasible under live 4/2/8 GiB boundaries rerun it, otherwise disclose what was not rerun. Do not make a 65GB owner laptop test tree.
4. Commit/push reviewed implementation only when safe automatic-trigger gate is active and tests green; verify parity and job trigger list after each push. Follow project non-destructive OwnerDev refresh rule **only when safe**, preserving known-good runtime. Do not deploy a half-built OCP runtime onto owner's current machine.
5. **Owner already authorized ONE real first cold native build.** Explicitly `gh workflow run` on `main` (or supported Actions dispatch) with required affirmative gated input and immutable run identity after ALL gates green. Record actual run link/job IDs, stages/time/exit codes. No simultaneous second cold run.
6. If fully green, do ONE real exact-input warm cache-hit workflow run that independently validates hashes and no repeated OCCT/OCP expensive compilation. Cache HIT must still run native CAD and packaging smoke. Capture distinct URLs.
7. If blocked at any phase: **STOP**, do not rerun blindly. Keep completed A/B artifacts, report exact blocked stage, errors, digests and next narrowly scoped remediation. Do not claim source/legal clearance, module validity or installer until actually evidenced.

## Required reports & termination

Codex implementation log:
`coordination/sessions/M16-C001/PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md`
Mandatory status/evidence report:
`coordination/sessions/M16-C001/PL-0350_NOVTK_315_HOSTED_BUILD_REPORT.md`
Master handoff:
`coordination/sessions/M16-C001/MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md`

Include: exact implementation SHA and log SHA; source lock/official ZIP/patch actual SHA; four excluded IDs and module inventories; relevant tests + exact skips/failures; C: free before/after and disposable peak; CI safety setup result; all run URLs (cold/hit), job timings, successful and failed checkpoint artifact keys/byte counts/hashes; runtime binary SHA; packaged smoke; source/notices/redistribution per component; actual unsigned installer SHA/size/link if produced; clean source git parity; owner Desktop/OwnerDev unchanged or safe refreshed with fallback; clear legal/public release boundary.

If installer + cache-hit + redistribution engineering gates all PASS, end `READY_FOR_INDEPENDENT_PL0350_AUDIT`. **Do not check off task or start PL-0351**. If any hard blocker, end `BATCH_STOPPED_AT_PL-0350 / AWAITING_INDEPENDENT_AUDIT` with exact code `<phase>_<reason>`. Root TASKS and independent audit documents are ChatGPT-only. No more broad V08/V17 iteration cycles. Focus on producing the one real installer.
