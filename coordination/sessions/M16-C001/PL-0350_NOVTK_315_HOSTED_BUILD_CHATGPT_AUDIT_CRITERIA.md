# PL-0350 — ChatGPT Independent Audit Criteria: Host-Gated 315-Module No-VTK OCP Native Pipeline

Date: 2026-10-12
Owner-approved build route:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OWNER_APPROVAL_HOSTED_BUILD_315_NOVTK.md
Implementation authority:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_PROMPT.md
Preflight independent PASS:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_NOVTK_315_PREFLIGHT_CHATGPT_AUDIT_V01.md

**Decision conditions:** Only an actual, independently auditable Windows unsigned installer and source-controlled proof meet PL-0350 PASS; static plan, stage launch, canceled workflow, or simulated smoke never qualifies.

### A. Trigger containment and owner safety

1. Before *any* source/test/package path push, the old `windows-studio-build.yml` automatic `push`/`pull_request` 6h producer is deactivated or genuinely gated against expensive work. Inspect pre/post workflow YAML, actions/run evidence and changed-file history; no accidental native producer triggered. Manual `workflow_dispatch` with explicit affirmative native-build input, immutable ref and fail-closed job gate exists. Quality workflow remains available. If legacy job unintentionally launched, stop/cancel; do not proceed until resolved.
2. Exact owner-approved 315 only and real hosted build approval recorded. Does not authorize opaque prebuilt OCP binary substitution, signing/public release, other milestones, mass local build or repeated cold runs.
3. Native compiles run exclusively on GitHub-hosted Windows 2022; no local owner OCCT/pywrap/OCP compile, 65GB copy/temp tree, owner personal file deletion, active uv-cache purge or dirty checkout overwrite. OwnerDev current and previous-good preserved. If safe owner refresh after published implementation is claimed, verify non-destructive success and previous-good retention.
4. Git main parity, implementation/log separation, audit-only authority of root TASKS. Codex never writes root tracker or independent audit documents.

### B. Verified no-VTK source preparation

5. GitHub official asset `OCP_src_stubs_Windows.zip`: exactly 6,481,047 bytes, SHA256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`, tag 7.9.3.1.1 and source revision `d69b064a3a604ebf245b1f3b14fb54c835a3a571`; reject path traversal, duplicate/case-collision and unbounded decompression; no silent alternative artifact.
6. Deterministic real input check: 319 unique binding module IDs, 319 `.cpp`, 319 `_pre.cpp`, 319 `_tmpl.hxx`, exact 638 enum/module register declarations/calls; actual patch modifies only four names `IVtk`, `IVtkOCC`, `IVtkTools`, `IVtkVTK` and upstream-proven VTK CMake linkage/discovery; final 315 complete modules/registrations, no stray VTK symbols in build inputs, no removed extra module. Check real patched C++/CMake file hashes, not only plan digest.
7. All 27 literal PackLab source OCP imported modules from static preflight retained. Dynamic OCP root/version and CAD/STEP/measure/geometry imports handled; generated internal `OCP.__version__=7.9.3.1` vs release `7.9.3.1.1` recorded independently, not concealed.
8. **Zero invocation of pywrap generator** in actual native build and **no prebuilt opaque OCP wheel** as shipped OCP/OCCT runtime. The 5h generation phase is genuinely bypassed, not skipped with missing OCP extension.

### C. Native stage and cache evidence

9. A: actual locked OCCT 7.9.3 source build with `USE_VTK=OFF`, locked Win2022/CPython 3.12.15/SDK/MSVC/CMake and <=4 workers. Retained minimal OCCT SDK with complete manifest, file hashes, byte counts, immutable job/source IDs and exact source/license evidence.
10. B: separate fresh hosted runner consumes validated same-workflow OCCT checkpoint and produces genuine 315-source `OCP*.pyd` via C++ compile/link without recreating OCCT or pywrap; real native BREP/CAD/STEP tests import and use it. No stale CMake absolute paths, unbound native DLLs or missing generated dependencies.
11. Each stage fits hosted six-hour job limit with bounded job budgets **including** source/env setup and upload. Pre-dispatch feasibility includes actual storage/artifact constraints. GitHub run logs contain start/end and stage timings; no six-hour monolithic reset or unbounded retry.
12. Stage checkpoints survive a downstream failed job, are hash/size verified with versioned schemas and stage identities; exact source/patch/toolchain/validator cache keys, no broad restore fallback; induced tampering, missing/extra and provenance mismatches fail closed. Artifacts transferred in same run, not pretending generic uv cache is controlled runtime cache.
13. Exactly one authorized initial cold controlled workflow dispatch after tests/gates. If green, **one distinct real warm-cache HIT workflow** where OCCT/pywrap/OCP expensive regeneration does NOT occur and cache manifest validation + runtime smoke actually execute. If first job blocks, no blind repeat and no fabricated HIT; report accurate blocked phase instead.

### D. Product, redistribution and delivery

14. Packaged **no-network** Qt GUI/QtPdf, OCP BREP/CAD, STEP import/export, PackLab DXF, Open3D and real locked feature/runtime smoke all green on completed PyInstaller staging tree. The current-vs-previous-good launcher smoke alone is not standalone distribution acceptance.
15. Exact final staged source/license/NOTICE ownership for every redistributed native component, including OCP controlled OCCT DLLs, Qt/PySide/Shiboken/QtPdf/PDFium/Open3D and third-party DLLs; reject GPL-only VirtualKeyboard. V05 historic 79 opaque-wheel file rows do not magically disappear unless opaque wheel really excluded and actual replacement contents have their own verified mappings. No fabricated versions/clearance rows.
16. Engineering gate requires zero unresolved shipped files/components, missing source packages/notices and forbidden Qt; exact `CLEARED_FOR_PL0350_ENGINEERING_PACKAGING`. Explicitly retain `legal_review_required=true` and `public_release_authorized=false`. Engineering pass is NOT external legal signoff.
17. A **real unsigned installer** exists and is uploaded as a GitHub Actions artifact with exact SHA256, size, build revision, source manifest, notices and smoke logs. No public tag/release/signature claim; signed release remains future authorized work. If no installer, PL-0350 is not PASS.
18. Full relevant regression/quality/negative fixtures and disk-wrapper evidence, with honest test counts and skips. All actual GitHub runs/commit/artifact links in Codex report and final git main parity.
19. STOP on earliest unremediable compile, source, stage, license, artifact, compatibility, time or capacity blocker; publish partial validated checkpoints and exact observed error. Independent audit returns `AUDITED_CHANGES_REQUIRED / BATCH_STOPPED_AT_PL-0350`, not a pass or authorization for further repetitive rebuild.
20. PL-0350 checkbox is changed **only by ChatGPT** after its independent PASS. PL-0351 not run as part of this execution; owner can separately authorize clean Windows install test after installer available and audited. No M17, PL-0368 remains deferred.

**Verdicts:**
- `AUDITED_PASS`: real cold+HIT native source-built and all product/redistribution/installer gates independently evidenced.
- `AUDITED_PARTIAL_CHANGES_REQUIRED`: safety architecture or successful partial stages evidenced but full installer/cold-HIT gate blocked.
- `AUDITED_FAIL`: violated no-build-on-owner, automatic workflow trigger bypass, abandoned provenance/VTK constraints, package substitution, false/unsupported test claims, or unsafe destructive operation.

Required handoff files:
`coordination/sessions/M16-C001/PL-0350_NOVTK_315_HOSTED_BUILD_REPORT.md`
`coordination/sessions/M16-C001/PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md`
`coordination/sessions/M16-C001/MASTER_PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_LOG.md`
