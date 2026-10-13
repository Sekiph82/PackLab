# PL-0350 — ONE-SHOT MASTER | ChatGPT Independent Acceptance Criteria

Owner explicitly directed that **ALL remaining PL-0350 work be assigned together in ONE master**, without a new independent prompt after each normal implementation blocker. This is one task, PL-0350; no task/milestone sprawl.

Implementation:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_ALL_REMAINING_WORK_ONE_SHOT_MASTER_CODEX_PROMPT.md
Historical independent audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_FMT_PROVENANCE_R05_CHATGPT_AUDIT_V01.md
Native build owner approval:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_OWNER_APPROVAL_HOSTED_BUILD_315_NOVTK.md

## Scope of ONE end-to-end audit

**Acceptance requires actual Installer**; completion of fmt/CRT research, OCP compilation, static tests, successful SDK build, empty cached folders or a green workflow without real runtime evidence is insufficient. Audit independent from Codex log against live GitHub commits, workflow job logs, artifacts/manifest digests and true report bytes. Only ChatGPT may update/check off root `TASKS.md`.

### A. Automation and time economy

1. Codex executed W01–W12 within this single master and automatically corrected cheap deterministic code/CI errors without waiting for more R07/R08 prompts. Workpackage evidence is within one append-only builder log and one report; no duplicate root progress tracker/new milestone. Sequential native dependencies respected; independent code/license/packaging readiness explored without repeated owner interruptions.
2. Existing owner checkout, active/previous PackLab.exe, untracked files and other repos were not touched. No local massive native builds, 65GiB test trees, shared-cache deletion or uncontrolled repeated six-hour hosted attempts. C: free and 4/2/8GiB quotas adhered to. Single controlled job at a time; different native reruns only if proven changed inputs + preflight success + owner cost gates.
3. `.github/workflows/windows-studio-build.yml` remains MANUAL-ONLY with exact main SHA and affirmative authorization, all native jobs skipped in short preflight-only mode; GitHub quality remains active. No tags, releases, signatures, secrets or public package claims.
4. All commits/evidence attached to actual SHA and run URLs; no unbacked “PASS”, “cache-hit”, “Installer” or “owner Desktop verified” assertions.

### B. OCCT/OCP checkpoint and correctness

5. Verify retained SDK origin: recovered OCCT artifact **11796717315** SHA256 `3339c28cd99605c3c928f9c4f145245b39efb1f7ed99a19a17c1547d8e101c4e`, 114,366,551 bytes, expires 2026-10-27 07:59:40 UTC; inner SDK 7,991 files/173,975,159 bytes SHA `7ad1c8b0b2634d32eeada2e6d8fa4fb6e85f7f3c1e6989e8beab7ebdbc2c9031`. SDK is source-built OCCT 7.9.3, OpenGL=ON/VTK=OFF, Windows `win64/vc14` layout, native CPython 3.12.15. Original R04 source-lock hash differs from fmt-augmented R05: independently verify old-vs-new SDK-relevant inputs and retain original manifest identity. No metadata laundering, no false cache HIT, no automatic OCCT recompilation.
6. Exact OCP 7.9.3.1.1 official pre-generated ZIP byte length **6,481,047**, SHA256 **290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b**. Input 319 generated modules/triplets, exact removal only IVtk, IVtkOCC, IVtkTools, IVtkVTK -> 315 complete non-VTK modules/registrations and working OpenGl bindings. Locked MSVC/Windows SDK, CPython native 3.12.15 vs bootstrap 3.12.10, <=4 C++ workers; NO pywrap regeneration and NO opaque prebuilt OCP wheel.
7. Before native OCP compile, real short hosted SDK include/link/module and full known PE dependency + source/notice policy preflight PASS. After OCP native link, upload an **immutable QUARANTINE .pyd artifact BEFORE ANY potential provenance/runtime failure**, with bytes/SHA/SDK/source/ABI and raw data preservation; it is not an approved or distributable runtime. No repeated two-hour recompilation for mere compliance logic change if fully compatible quarantined object exists.
8. Actual final OCP `*.pyd` can import in locked Windows runtime and pass CAD/BREP/STEP smoke, dependency PE transitive graph and all package tree hash checks; no extra OCP modules removed. Sealed approved OCP runtime artifact with exact per-file identity and runtime manifests is a separate stage from quarantine.

### C. fmt, Microsoft runtime, third-party distribution policy

9. `fmt 12.1.0` exact conda package SHA `1d6d6f1bf284e50cf617ce9a6250e0bf70bd0d30b068568364d6b1852aad9466`; actual AMD64 `fmt.dll` SHA `0d4edfe1411f4a7c5f57758239f0f1e6e1cff7f2d0ae5f9511a1dfacc08b388d`; upstream MIT license/source/notice and pinned feedstock; actual shipped fmt file must be that provable component, not OCCT-owned/OS-whitelisted.
10. Six UCRT API-set imports from conda `ucrt 10.0.26100.0` and three conda `vc14_runtime 14.51.36247` DLLs from R05 are correctly **classified by chosen deployment method**, not mechanically assumed all shipped or wrongly declared Windows System32. Supported Windows UCRT OS-serviced API-set policy validated; no app-local conda UCRT files accidentally shipped. VC++ v14 is official compatible x64 Microsoft Redistributable *prerequisite* with actual documented provider/version/signature/license/REDIST rights and Installer behavior, or individually verifiably licensed app-local shipped files. Lack of required source for proprietary MS Windows runtime is not falsely labeled an open-source license violation, but actual redistribution eligibility must be proven. No invented immutable checksums for mutable 'latest' download.
11. All native direct/transitive imports classified separately as OCCT-built, OCP-built, pinned MIT third party (fmt), OS component, verified official prerequisite or actually shipped licensed vendor binary; no blanket `is_external_runtime()` fmt exemption. All actually packaged binaries are file-hashed/owned/NOTICE/source traced; unshipped OS/prereq files represented in reproducible external prerequisite manifest. Unsupported, missing, tampered, ambiguous, extra or wrong-arch/native DLLs fail closed.
12. Fmt probe, native builder, OCP manifest validator, sealed runtime bundle, redistribution inventory, Studio installer and **fresh-target prerequisite checks** share the same policy and verifiable versions. Negative fixtures cover UCRT conda prefix shadowing OS forwarders, missing/wrong MSVC redist, wrong DLL SHA, missing notice/source/REDIST rights, duplicate/unknown PE imports, invalid issuer/signature, runtime without prereq and manifest tampering.

### D. Production packaged acceptance and tests

13. Real packaged no-network Windows Studio smoke PASS: QtCore GUI, QtPdf/PDFium, CAD/geometry, STEP I/O, PackLab DXF, Open3D, version/identity, no forbidden Qt virtual keyboard or opaque wheel native binaries. No demo-only trace or Python import in development env counted as production acceptance.
14. Source/license/NOTICE/redistribution engineering gate `CLEARED_FOR_PL0350_ENGINEERING_PACKAGING`, **zero unresolved included files/components**, zero forbidden Qt, correct Windows prerequisite policy, `legal_review_required=true`, `public_release_authorized=false`. Engineering PASS is not external legal signoff; if genuine legal owner decision required and not inferable, Codex must stop rather than forge approval.
15. A real **unsigned Inno Setup Installer** exists, uploaded as GitHub Actions artifact with exact SHA256, bytes, immutable commit SHA, true native manifests, package smoke results and notices/source/prerequisite details. PL-0351 clean Windows install acceptance remains separately blocked, but bounded PL0350 Installer/packaging smoke is required.
16. One separate verified cold-to-warm exact cache-HIT workflow only after first full cold/Installer success, with OCCT/OCP heavy compilation verifiably skipped and actual package/native smoke rerun; not an empty cache lookup or unverified second Installer.
17. Real current focused tests, Ruff/format/mypy/compileall/quality/YAML/module import and source/manifest negative tests recorded, not recycled R05 results. Actual skip and test counts, compile duration and artifact sizes credible and reproducible. Source-controlled evidence and GitHub main parity verified.

### E. Review/disposition

18. Codex outputs ONE `PL-0350_ALL_REMAINING_WORK_ONE_SHOT_CODEX_LOG.md` and ONE `PL-0350_ALL_REMAINING_WORK_ONE_SHOT_REPORT.md`, plus updates its existing builder master history. It must not write `TASKS.md` or independent audit files, advance PL-0351/M17/PL-0368, or create unrequested independent milestone/task prompts. Cheap/in-scope fixes are handled autonomously inside this single work assignment.
19. The auditor checks **all W01–W12** together and records one final `PL-0350_ALL_REMAINING_WORK_ONE_SHOT_CHATGPT_AUDIT_V01.md` after Codex handoff, with any incomplete evidence flagged. No automatic task closure before real Installer proof.
20. Valid early stop only for a genuine new owner-only legal/security/source decision, irrecoverable native checkpoint requiring an unapproved expensive rebuild, or reached hard build cost cap. A routine Python import, Windows install path, CMake typo, report error or failed negative unit test is NOT an adequate reason to ask ChatGPT for a new R-number prompt.

**Audit PASS:** All native/installer/compliance/cold+HIT gates plus owner safety proven. ChatGPT alone marks PL-0350 completed. 
**Audit PARTIAL:** Safe true blocker with artifacts preserved and exact owner decision needed, not a hidden endless retry. 
**Audit FAIL:** Misreported source/ownership/installer, unauthorized local build, falsely waived license gate, unsafe duplicate heavy CI or changed frozen architecture.
