# PL-0350 — 315-Module no-VTK PREBUILD PREFLIGHT (NO NATIVE BUILD)

Executor: CODEX. Repo: https://github.com/Sekiph82/PackLab
**Task: PL-0350 / Owner decision implementation-preflight, not a new milestone/version.**
Owner ruling: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OWNER_DECISION_NOVTK_315_MODULES.md
Prior accepted source inspection: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_CHATGPT_AUDIT_V01.md
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_PREFLIGHT_CHATGPT_AUDIT_CRITERIA.md

## Preflight contract and synchronization

Fetch origin/main and read `git show origin/main:TASKS.md`, current owner decision, pinned source lock and both previous audits. Preserve user Desktop dirty checkout, current and previous OwnerDev, all active worktrees, shared uv caches and unrelated apps. Work in a managed clean worktree. Root `TASKS.md` and ChatGPT audit/decision files are **ChatGPT-only**; Codex must not modify them. Do not auto-approve the owner build gate.

**IMPORTANT: NO actual build authorization.** No OCCT native build, pywrap, OCP C++ compile/link, cold/warm Windows packaged workflow, launcher refresh, installer, source lock replacement, prebuilt opaque wheel substitution, or mass cache cleanup. Static checks and tiny synthetic fixture tests only. No multi-GB test material; max 200 MiB disposable scratch with automatic cleanup, respect >=40 GiB C: safety gate and avoid an extra clone of entire repo. Zero private project data.

## P0: GitHub auto-run safety gate FIRST

Inspect ALL `.github/workflows/*.yml` / `*.yaml` and identify push-trigger paths. The existing `windows-studio-build.yml` triggers the expensive 6h controlled-native producer when changes to `tools/packaging/**`, `tests/ci/**`, `.github/workflows/windows-studio-build.yml`, `apps/windows-studio/**`, `core/**`, `schemas/**`, `pyproject.toml`, `uv.lock`, or `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md` are pushed to main.

**Do not edit or push ANY path that would start the long hosted workflow.** First deliver documentation-only preflight under `coordination/sessions/M16-C001/` (and optionally safe `docs/architecture/` paths EXCEPT dependency register). For tiny contract tests use in-memory code or safe non-trigger local scripts under `tools/dev/` ONLY if every workflow is confirmed safe for this path. Do not rely on workflow cancellation, skip-ci text, or delayed cleanup; if triggers cannot be proven safe, publish reports only and stop. No automatic GitHub Actions dispatch.

## P1: exact 315-module source contract

From previously verified official OCP Windows release ZIP `OCP_src_stubs_Windows.zip` (6,481,047 bytes SHA-256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`), inspect the prior detailed module/hashes report first; re-download only if necessary with strict size/digest bounds.

Define deterministic **pure/static patch plan**:
1. Input 319 distinct generated module IDs, 319 matching `.cpp`, `_pre.cpp`, `_tmpl.hxx` triplets and registration pairs in `OCP.cpp`, plus single extension entry point.
2. Remove **exactly** `IVtk`, `IVtkOCC`, `IVtkTools`, `IVtkVTK` and only their associated declarations/sources/registrations/VTK discovery/link flags, following pinned official upstream no-VTK instructions.
3. Output exactly 315 binding IDs, 315 module+enum registration pairs, no stray IVtk registration, no stale VTK CMake reference or missing input files; reject duplicate/missing/extra and inconsistent module coverage. Preserve all 315 other modules. Include hashes pre/post or deterministic patch digest. Explicitly account for the OCP.__version__ generated 7.9.3.1 vs tagged wheel 7.9.3.1.1 without quietly falsifying runtime identity.
4. Check that active PackLab CAD/STEP/DXF/measurement/geometry Python imports and dynamic imports do not use the removed four. Include textual/dynamic import inventory, unresolved dynamic cases, and tiny fixture tests for the patch behavior. No native compilation in this stage.

## P2: native/third-party provenance and CI phase blueprint (DESIGN ONLY)

- Identify exact pinned source archives/OCCT SDK and remaining required pybind11, fmt, Windows Python3.12.15, MSVC/SDK; generated-source ZIP is not a compiled runtime nor source-closure guarantee.
- Provide a feasible and secure future job plan: build/verify OCCT native SDK in a dedicated <=6h GitHub-hosted job; read/verify the small official ZIP + patch exactly four VTK modules; compile/link OCP generated 315-module sources in *separate* <=6h hosted job using source-verified OCCT; seal/checkpoint each stage with cryptographically verifiable file inventory, exact cache keys and schema, disallow stale absolute CMake paths; finally package and no-network-smoke QtPdf/OCP/CAD/Open3D and clear redistribution/notice/source before unsigned installer.
- The exact C++ native-compile time remains unknown; budget appropriately and stop for owner approval before long phases. Stage artifact/path size, cache retention, immutable source locks, single-run transfer and cold/hit proof requirements. Note previous 5-hour pywrap can be avoided only if this route actually compiles and passes product checks later.
- Retain existing blocked opaque wheel 79 OCP-file provenance; avoid guessing license versions or allowing unsafe binaries. Qt/PySide6/Open3D independent obligations remain.
- Do not amend runtime source/build contract files or Actions YAML here, since pushing them would start the expensive workflow before the owner authorizes it. Propose exact future changes in a *non-executing* patch plan/report instead.

## P3: local lightweight checks, handoff, stop

- Run only short text/module/import checks and tiny in-memory/synthetic artifact tests, bounded under 200MiB scratch. Any missing source/unsafe import means `PREFLIGHT_BLOCKED`. Record exact commands, pass/fail, runtime, free disk before/after, zero source-pipeline jobs launched and any uncertainty.
- Publish two files in `coordination/sessions/M16-C001/`: `PL-0350_NOVTK_315_PREFLIGHT_REPORT.md` and `PL-0350_NOVTK_315_PREFLIGHT_CODEX_LOG.md`. No source/product/workflow edit, no TASKS edit, no audit edit; only report/log (optional code in proven non-trigger path if explicitly necessary and harmless).
- Push docs only to main, verify post-push parity & readback. End `AWAITING_INDEPENDENT_AUDIT / NATIVE_BUILD_OWNER_APPROVAL_REQUIRED`. If original 315 CAD surface cannot be substantiated, stop `PREFLIGHT_BLOCKED` and explain exact deficits. **No workflow runs, no EXE modifications, no PL-0351.**

Owner has approved the **315-module contract**, NOT execution of long native build jobs.
