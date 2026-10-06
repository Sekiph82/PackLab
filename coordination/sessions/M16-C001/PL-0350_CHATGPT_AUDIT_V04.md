# PL-0350 - ChatGPT Independent Audit V04

Date: 2026-10-06
Decision: **AUDITED_CHANGES_REQUIRED**
Task: **Exact redistribution closure + unsigned audit installer**

## Evidence inspected

- PL-0350 V04 prompt and audit criteria.
- Implementation commit `234c212bb0fccf7fc9e22f97ef5a643cfde594b2`.
- Hosted-evidence commit `11c6b86c3b934d5f794894028873305d1c441ba1`.
- Child/master logs through `44f6eaa147f46851986ec61d9e155d495e608614`.
- Hosted Windows run `37481126993`.
- Pre-clearance artifact ID `11420659070`, downloaded and inspected independently.
- `compliance-validation.json`.
- `windows-component-summary.json`.
- `windows-redistribution-inventory.json`.
- collected notice/license evidence.

## Stop verdict

The V04 stop is **VALID**.

Hosted execution independently confirms success through:

- locked dependency installation;
- production staging build;
- approved Qt staged-surface assertion;
- real frozen no-network Qt GUI + QtPdf + OCP/CAD + Open3D smoke;
- exact hosted inventory;
- text-only pre-clearance artifact.

The workflow then fails closed at redistribution clearance. No installer, final compliance artifact, or source archive artifact is produced.

## Exact V04 artifact facts

- build revision: `234c212bb0fccf7fc9e22f97ef5a643cfde594b2`;
- Studio: `0.1.0`;
- staged files: **511**;
- staged bytes: **531,589,169**;
- unresolved shipped-file rows: **115**;
- unresolved components: **5**;
- total unresolved items: **6**;
- missing notice sets: **0**;
- missing source-package evidence: **5**;
- forbidden Qt components: **0**;
- external prerequisites: **1**;
- engineering status: `BLOCKED`;
- legal review required: `true`;
- public release authorized: `false`.

The six unresolved items are exactly:

1. `component:cadquery-ocp-novtk`;
2. `component:open3d`;
3. `component:pyside6-addons`;
4. `component:pyside6-essentials`;
5. `component:shiboken6`;
6. `evidence:missing-source-packages`.

## Exact unresolved staged rows

Independent artifact inspection confirms the 115 inherited unresolved rows break down as:

- `cadquery-ocp-novtk`: **79** rows;
- `pyside6-essentials`: **24** rows;
- `shiboken6`: **6** rows;
- `open3d`: **3** rows;
- `pyside6-addons`: **2** rows;
- composite `PackLabStudio.exe`: **1** row because its embedded component set still contains unresolved owners.

### OCP wheel surface

The 79 OCP-owned rows include:

- exact distribution metadata;
- `OCP/OCP.cp312-win_amd64.pyd`;
- OCCT `TKernel/TK*.dll`;
- bundled third-party natives including FreeImage, FreeType, OpenEXR/Iex/IlmThread/Imath, JPEG, LittleCMS, Lerc, LZMA, PNG, WebP, OpenJPEG/OpenJPH, RAW, TIFF, zlib/deflate/zstd;
- wheel-private MSVC runtime copies.

The current component-level Apache-2.0 row is correctly still unresolved because those native files cannot all inherit the OCP binding license.

### Open3D surface

The exact unresolved native rows are only:

- `open3d/Open3D.dll`;
- `open3d/pybind.cp312-win_amd64.pyd`;
- `open3d/tbb12.dll`.

Existing PL-0225 evidence already pins the exact Windows CPython 3.12 wheel:

- `open3d-0.20.0-cp312-cp312-win_amd64.whl`;
- SHA-256 `60010f21d44f13557ba007893bc13a69827faa4dc49eedd923d1397096c20d92`;
- wheel license MIT;
- TBB observed as 2021.12.0 / Apache-2.0;
- upstream third-party inventory exists.

The remaining gap is exact build/native composition and corresponding source evidence, not package identity.

### Qt / PySide / Shiboken surface

The unresolved staged rows are bounded to the already-approved Qt surface:

- Essentials: 24 rows;
- Addons: 2 rows, `Qt6Pdf.dll` + `QtPdf.pyd`;
- Shiboken: 6 rows.

No forbidden Qt module is staged.

The unresolved condition is now exact module/source/third-party attribution and corresponding source-package evidence, not discovery of which Qt features PackLab uses.

## V04 accepted remediation

Retain V04 changes:

- PackLab-generated evidence ownership is closed;
- CPython `base_library.zip` ownership is closed;
- OpenSSL 3.0.16 runtime/license/source reference is closed;
- root API-set/UCRT/VCRuntime copies are removed;
- external x64 VC runtime prerequisite is explicit/no-download;
- fresh packaged capability smoke remains green after pruning;
- no missing notice set and no forbidden Qt component remain.

## Required V05 direction

V05 must close the five unresolved native owners with **machine-readable exact mapping artifacts**, not by setting registry flags manually.

Required checked-in maps:

1. `windows_qt_native_component_map.json`;
2. `windows_ocp_native_component_map.json`;
3. `windows_open3d_native_component_map.json`.

The redistribution inventory must consume and validate these maps against the exact staged tree.

A component may become `EVIDENCE_PRESENT` only when every staged row owned by that component is accounted for by exact file-level evidence and all required corresponding-source evidence is hash-pinned.

## Public upstream facts independently verified for V05

- Qt publishes the exact PySide 6.11.2 source archive `pyside-setup-everywhere-src-6.11.2.zip`, size 23,134,400 bytes, SHA-256 `c0fdd62b91a1d36d5ee2e1fb71050a32fbc93fcdeef0fdcb41d29afaaf00d9b5`.
- Qt publishes 6.11.2 submodule source archives including `qtbase`, `qtsvg`, and the Qt PDF source module; V05 must retrieve their official hash metadata and pin it.
- Qt PDF 6.11.2 is LGPLv3/GPLv2 in addition to commercial licensing and includes PDFium plus documented third parties. The exact third-party notice/source set must be carried.
- Existing PackLab evidence already pins the Open3D 0.20.0 Windows wheel and upstream third-party inventory.

These facts are engineering inputs only. This audit is not legal advice or a legal-compliance certification.

## Owner DEV / downstream portability

OWNER DEV refresh at final R05 handoff reports `OWNER_DEV_READY` at `44f6eaa1`.

The owner-observed `QtCore` procedure-load failure remains deliberately open for the amended PL-0351 separate clean-install job. It cannot be marked fixed before a cleared installer exists.

## Verdict

`AUDITED_CHANGES_REQUIRED`

Resume at PL-0350 V05. Do not start PL-0351 until V05 reaches zero unresolved engineering items and produces the unsigned audit installer.
