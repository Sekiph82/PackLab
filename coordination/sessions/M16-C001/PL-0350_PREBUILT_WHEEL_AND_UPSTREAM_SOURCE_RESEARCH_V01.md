# PL-0350 — Prebuilt OCP Wheel vs Official Generated Source: Independent Feasibility Assessment V01

Date: 2026-10-12
Owner request: read-only assessment of using the already-published OCP wheel to avoid repeating the 42-minute OCCT and 5-hour pywrap builds.
Scope: **research and prior recorded test/audit evidence only**. No code, build, local runtime, cache, staged installer, or binary was modified or executed. **No authorization to rebuild**.
Decision: **PREBUILT WHEEL TECHNICALLY VIABLE FOR DEVELOPMENT; NOT CLEARED FOR DISTRIBUTION UNDER THE EXISTING PL-0350 EVIDENCE GATE. OFFICIAL PRE-GENERATED SOURCE IS A PROMISING THIRD ROUTE REQUIRING SMALL-ASSET ATTESTATION.**

## Exact binary and prior test evidence

- PackLab `uv.lock`: `cadquery-ocp-novtk==7.9.3.1.1`, CPython 3.12 Windows x64 wheel, size **46,364,919** bytes, SHA-256 `5d22339cdaac64c396f0658de8728915acfac9b868406f0078e52f50a3c25c65`; depends on `cadquery-ocp-proxy==7.9.3.1.1`. Source: https://github.com/Sekiph82/PackLab/blob/main/uv.lock
- PyPI confirms release May 28, 2026, `cp312-cp312-win_amd64`, version 7.9.3.1.1, upstream describes no VTK support, and declares OCP binding Apache-2.0. PyPI wheel upload says **Trusted Publishing: No**, so hash pinning is essential but not a complete upstream build attestation. https://pypi.org/project/cadquery-ocp-novtk/7.9.3.1.1/
- Independent GitHub upstream release API https://api.github.com/repos/CadQuery/ocp-build-system/releases/tags/v7.9.3.1.1 lists the SAME filename, same size **46,364,919 bytes** and SAME SHA-256. This cross-check supports wheel byte identity across distribution channels but does not prove the precise origin/license of bundled native third-party DLLs.
- Existing PackLab R0 inventory confirms current/previous-good OWNER DEV runtime includes identical `OCP.cp312-win_amd64.pyd` **93,748,736 bytes** with installed digest `9B103790E366DC33509F7EE8958DFA40334076EADDC40DABA275BF18E6A50B20`; current OwnerDev smoke passed. Neither owner runtime is a provenance-verified source-build checkpoint. https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_R0_RECOVERY_INVENTORY.md
- Actual **hosted staged installer input on prebuilt wheel** previously passed no-network Qt GUI/QtPdf/OCP/CAD/Open3D smoke in PL-0350 V04 and V05. This establishes strong **technical packaging potential** and explains why rebuilding the Python wrapper is not necessary merely for functional CAD execution. No installer was cleared/published because **redistribution evidence failed**. https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V04.md and https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V05.md

## Exact prior distribution blocker (not a hypothetical risk)

V04/V05 hosted product staging: **511 files / about 531.6 MB**, five unresolved native owners (`cadquery-ocp-novtk`, `open3d`, `pyside6-addons`, `pyside6-essentials`, `shiboken6`), six unresolved items including corresponding-source evidence, **zero** missing notice sets and **zero** forbidden Qt components. The OCP wheel alone owned **79 staged file rows**: `OCP*.pyd`, many `TK*.dll`, and additional third-party native components (FreeImage/FreeType/OpenEXR/etc.). The Apache-2.0 binding license is not automatically the license for those DLLs.

V05's independent audit states the **actual root blocker**: the upstream OCP build recipe uses a broad `occt=7.9.3=all*` native binary selection and the delocated wheel's metadata does **not** provide an exact complete build/source/version map of its bundled third-party DLLs. We must not manufacture missing provenance by guessing versions from DLL filenames. Thus a previously rejected wheel is **NOT newly cleared** by noticing that PyPI distributes it. The frozen V07 source-built approach was a means to secure that traceability, not evidence that pip wheels are categorically illegal.

## License and redistribution boundaries

- CadQuery/OCP Python binding: **Apache-2.0**; preserve its license and required attributions/NOTICE when applicable. https://github.com/CadQuery/OCP/blob/d69b064a3a604ebf245b1f3b14fb54c835a3a571/LICENSE
- Underlying Open CASCADE / OCCT 7.9.3: **LGPL-2.1 with OCCT exception**, distinct from OCP binding's Apache license. Notices, access to corresponding source, license terms and applicable library-replacement/relinking rights matter even if using a ready-made wheel. https://github.com/Open-Cascade-SAS/OCCT/wiki/license ; https://github.com/Open-Cascade-SAS/OCCT
- Other wheel DLLs have **separate** third-party licenses and exact component attribution cannot be assumed; honor LGPL/Apache/BSD/MIT/etc. per actual file. A prebuilt wheel does not magically remove source-disclosure obligations.
- PackLab's Qt/PySide components (including QtPdf and third-party PDFium inventory) pose independent LGPL-3.0 obligations regarding corresponding Qt source, notices and replacement/relinking. Qt officially warns that simply linking to its own source-hosting site is insufficient for distributable source availability. For proprietary distribution, commercial licensing is an alternative but is not recorded. https://www.qt.io/development/open-source-lgpl-obligations ; https://www.qt.io/faq/qt-open-source-licensing . Do not redistribute GPL-only Qt modules such as VirtualKeyboard on the claimed LGPL route.
- Prior PackLab policy rightly distinguishes `CLEARED_FOR_PL0350_ENGINEERING_PACKAGING` (engineering artifacts audited) vs `legal_review_required=true` / `public_release_authorized=false`. Even a successful unsigned installer is not legal sign-off.

## IMPORTANT newly discovered third route: upstream pre-generated OCP bindings source

CadQuery's own OCP README says **building from released generated sources without pywrap regeneration is supported**, and its official build-system workflow uses `PYWRAP=false` to consume released binding sources:
- https://github.com/CadQuery/OCP
- https://github.com/CadQuery/ocp-build-system/blob/main/.github/workflows/build-ocp.yml
- https://github.com/CadQuery/ocp-build-system

Independent official **GitHub release API** https://api.github.com/repos/CadQuery/OCP/releases/tags/7.9.3.1.1 exposes EXACT-PINNED tag `7.9.3.1.1` pointing to source revision `d69b064...` matching PackLab's OCP lock and has asset:
- `OCP_src_stubs_Windows.zip`, 6,481,047 bytes, GitHub API digest **`sha256:290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`**, uploaded 2026-05-25.
- Source URL: https://github.com/CadQuery/OCP/releases/download/7.9.3.1.1/OCP_src_stubs_Windows.zip
- Upstream build workflow previously published matching `OCP-source_7.9.3.1.1-windows-2022` generated-source artifact (historical artifact now absent from the checked upstream Actions run API, not reusable as a run artifact). Release asset and its digest remain discoverable via the upstream **release** API, independent of PackLab's canceled runner. https://github.com/CadQuery/ocp-build-system/actions/runs/26501389469

**This is a potentially better resolution than either accepting opaque bundled native DLLs or repeating 5h of pywrap.** If the small release ZIP really contains all required exact generated `.cpp`/headers/CMake and its byte-level contents/provenance are validated, PackLab can potentially **skip pywrap regeneration** but **still build its own source-pinned OCCT and compile the OCP extension** under controlled Windows runners. This keeps the native third-party source-provenance gate, which the opaque wheel route failed.

**UNVERIFIED HARD LIMIT:** This research read GitHub release API *metadata*, not the ZIP's binary contents. The published digest and source revision do not alone certify CMake interoperability, no-VTK edits/compatibility, 319-equivalent module coverage, reproducible generated code, Windows SDK/compiler compatibility, OCP patch level or clean native runtime. The uninspected archive must NEVER be marked production-ready. Do not claim that generated code is automatically equivalent to the original locally generated pywrap bytes without testing/hashing.

## Recommended safe follow-up (NO NATIVE BUILD AUTHORIZED)

Priority 1: **read-only small-asset inspection** of official 6.48 MB `OCP_src_stubs_Windows.zip`: verify official release asset SHA-256, ZIP safety and filenames, generated project CMake/config/actual module inventory, exact source lock/revision, VTK/no-VTK compatibility, whether pywrap step can be removed, minimal OCCT SDK dependency, and build/test plan. Keep analysis under small bounded scratch, no native compilation, no user Desktop mutation. Report `PREGENERATED_SOURCE_COMPATIBLE`, `INCOMPATIBLE`, or `INSUFFICIENT_EVIDENCE` plus required owner decision. This is within user-approved feasibility research, not approval to invoke GitHub >hour builds.
Priority 2: if upstream asset is fully compatible, owner may explicitly approve a checkpointed OCCT + generated native C++ compile + final packaging route **without pywrap**, with all license/source and no-network CAD gates.
Fallback: if official generated code proves incompatible, owner can choose proven-but-opaque wheel re-provenancing (nontrivial 79 native file rows) or fully source-built OCCT + 319-module pywrap with durable per-stage checkpoints and explicit time estimate.

## Decision at completion of this review

- **PREBUILT_WHEEL_RUNNABLE_IN_EXISTING_STUDIO / REDISTRIBUTION_NOT_CLEARED**.
- **OFFICIAL_7.9.3.1.1_GENERATED_SOURCE_ASSET_FOUND / BYTE_CONTENT_NOT_YET_INSPECTED**.
- **NO_INSTALLER, NO_LEGAL_APPROVAL, NO_NATIVE_BUILD, NO CODE CHANGE**.
- PL-0350 remains OWNER_REQUIRED, PL-0351 blocked; preserve working OwnerDev. Read-only investigation may proceed; any binary-route substitution or native build remains a separate explicit owner decision.
