# PL-0350 315-Module No-VTK Prebuild — ChatGPT Independent Audit V01

Date: 2026-10-12
Scoped verdict: **AUDITED_PASS_STATIC_PREFLIGHT_ONLY**
Parent PL-0350: **INCOMPLETE / NATIVE_BUILD_OWNER_APPROVAL_REQUIRED**
No PL-0351 authorization. No native compiler or installer PASS.

## Independent source review

- Owner's 315-module ruling: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OWNER_DECISION_NOVTK_315_MODULES.md
- Implementer report: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_PREFLIGHT_REPORT.md
- Implementer log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_PREFLIGHT_CODEX_LOG.md
- Published final commit: https://github.com/Sekiph82/PackLab/commit/2dd85398373cc6bddbad2d722a51e9ef2941db44
- Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_PREFLIGHT_CHATGPT_AUDIT_CRITERIA.md
- Upstream ZIP independent read-only audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_CHATGPT_AUDIT_V01.md
- Existing source-built Windows workflow: https://github.com/Sekiph82/PackLab/blob/main/.github/workflows/windows-studio-build.yml

Independently fetched the two published reports, authoritative owner decision, matching criteria, all four GitHub workflow definitions and every implementation/publication commit (0b479b1, 923d204, b288c32, 2dd8539). All four commits touched only the two expected `coordination/sessions/M16-C001/` report/log files. Neither the expensive `windows-studio-build.yml` nor other workflow's push filter matches those paths. **No full hosted/job-status or owner-PC runtime was independently executed during this audit**; no output should imply a native build was performed. Published fixture results and the in-memory ZIP checks are builder-reported; independently cross-checked report contents, source lock/official upstream recipe in the prior inspection audit.

## Evidence-backed acceptance

**S01 PASS:** git fetch, clean managed-worktree fast-forward, owner checkout preservation and read-only source-analysis boundaries described. `TASKS.md`, decision, package/build/CI files and owner Desktop binary were untouched by Codex.

**S02 PASS:** 6,481,047-byte official Windows 7.9.3.1.1 ZIP, expected SHA256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`; report verifies 319 generated module IDs with `.cpp`, `_pre.cpp`, `_tmpl.hxx` and matching 638 forward declarations/638 registrations (one enum/one module per ID). Removing exactly `IVtk`, `IVtkOCC`, `IVtkTools`, `IVtkVTK` leaves 315 IDs. Small actual-inventory/missing/extra/duplicate-ID in-memory fixtures are reported green. Canonical static patch-plan digest `8263b11294f99be6052272273fb84b518abe328d43dc3d7ce668f86962584248` is an INPUT/PLAN digest, not a patched-file byte attestation.

**S03 PASS, STATIC ONLY:** PackLab `core/src` and `apps/windows-studio/src` scan reports 27 literal OCP submodules, including STEP import/export module surfaces. All 27 are among retained 315; no string reference to the removed IVtk IDs, and a literal root `importlib.import_module('OCP')` was recorded. DXF R2000 output is a Python-owned route without an OCP submodule. Dynamic nonliteral imports, plugins, compiled ABI, actual CAD/STEP behavior cannot be certified from static text.

**S04 PASS:** plan identifies actual `USE_VTK=OFF`, upstream `PYWRAP=false`, version identity issue (`OCP.__version__='7.9.3.1'` versus package `7.9.3.1.1`), separate source-provenance obligations, artifact bytes/hashes and disallowed stale CMake absolute paths. The historic ~42m41s OCCT and ~5h04m pywrap durations are correctly not claimed as new runs. Pywrap can be bypassed on this *proposed* path, but native OCP compile time/SDK size remain unknown.

**S05 PASS:** reported C: free 173.60 GiB before and 173.61 GiB after, ZIP memory stream without scratch, no native build, installer, long hosted run, tests outside tiny fixtures, OwnerDev refresh, wheel substitution, cache cleanup or broad temp operations. This is builder-local evidence, not directly remeasured by auditor.

**S06 PASS:** the historic opaque OCP wheel 79-row native source/third-party provenance blocker is not falsely cleared. Qt/PySide/QtPdf/PDFium/Open3D source/notices and actual unsigned installer gates remain open. No PL-0351 or M17 advancement is claimed.

## Remaining hard gates before any real native run

- **B01 CODE NOT IMPLEMENTED:** only a static patch plan exists; it has NOT been applied to a real generated C++ tree or production pipeline, nor checked against native CMake configuration. A future implementation must deterministic-patch VTK references and exactly four generated module triplets, validate 315 registrations, reject missing/unexpected files and attest actual post-patch hashes.
- **B02 CI AUTO-TRIGGER:** the existing `windows-studio-build.yml` automatically starts its previous six-hour producer on main pushes touching `tools/packaging/**` or `tests/ci/**`. A future implementation must FIRST isolate the old expensive job from unintended push triggers and make real native compilation **explicit opt-in** under separate owner authorization; do not attempt to rely on commit skip markers to suppress a 6h run.
- **B03 NATIVE EVIDENCE:** future hosted Windows 2022 source-built OCCT and generated-315 OCP C++ jobs require measured actual success, durable validated transfer/cache artifacts, correct Python/SDK/ABI, CAD and STEP smoke, wheel/private DLL exclusion, and zero unresolved redistribution and appropriate notice/source evidence. Current no-VTK preflight does NOT satisfy these.
- **B04 OWNER BUILD DECISION:** user's explicit `evet` accepted 315 modules but earlier instruction explicitly reserved a **separate approval** before hours-long native compilation. No native build approval is implied by submitting preflight for audit. This audit therefore stops here and requests owner ruling before writing/executing any production native-build prompt.

## Verdict

`AUDITED_PASS_STATIC_PREFLIGHT_ONLY / PL0350_NATIVE_BUILD_OWNER_APPROVAL_REQUIRED`.

The passed work is the small, safe, static preflight, **not** PL-0350 task completion. Do not mark PL-0350 checked, and do not begin PL-0351. Preserve Desktop OwnerDev and other projects, no 6h blind monolithic rebuild, no unverified prebuilt wheel. PL-0368 remains DEFERRED_POST_M17.
