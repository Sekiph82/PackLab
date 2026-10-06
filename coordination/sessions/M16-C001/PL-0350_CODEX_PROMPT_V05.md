# PL-0350 - Codex Prompt V05

Task: **Close the final five native-component redistribution gates and produce the unsigned audit installer**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001-R06**

This V05 supersedes PL-0350 V04 after independent inspection of hosted artifact `11420659070`.

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V07.md

V04 audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V04.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V05.md

## Start rule

Synchronize the managed Codex checkout non-destructively with latest `origin/main`. Preserve owner-local work and unrelated worktrees.

Read before implementation:

- live root `TASKS.md`;
- M16 partial audit V07;
- PL-0350 V04 prompt, log, evidence and audit;
- current PyInstaller spec/workflow;
- current redistribution inventory;
- current component registry;
- existing PL-0225 Open3D evidence;
- current dependency/license register;
- OWNER DEV post-Codex refresh policy.

Do not edit root `TASKS.md`.

## Frozen V04 baseline

The exact hosted V04 stage is:

- 511 staged files;
- 531,589,169 bytes;
- 115 unresolved shipped-file rows;
- 5 unresolved components;
- 6 unresolved items;
- 5 missing source-package evidence requirements;
- 0 missing notice sets;
- 0 forbidden Qt components;
- 1 external prerequisite;
- engineering status `BLOCKED`.

The only unresolved components are:

- `cadquery-ocp-novtk==7.9.3.1.1`;
- `open3d==0.20.0`;
- `pyside6-addons==6.11.2`;
- `pyside6-essentials==6.11.2`;
- `shiboken6==6.11.2`.

The aggregate sixth unresolved item is:

`evidence:missing-source-packages`.

All other V04 closures are accepted and must be preserved.

## Core V05 rule

Do not clear a component by manually flipping a registry field.

V05 must introduce three checked-in machine-readable exact native maps consumed by the redistribution validator:

- `tools/packaging/windows_qt_native_component_map.json`;
- `tools/packaging/windows_ocp_native_component_map.json`;
- `tools/packaging/windows_open3d_native_component_map.json`.

The validator must compare those maps to the **actual freshly staged files**.

A component can become `EVIDENCE_PRESENT` only when:

1. every staged file owned by that component is matched by the appropriate exact map;
2. no mapped file points to a missing staged file;
3. no staged owned file is absent from the map;
4. each mapped row has license/notice/source evidence;
5. every required source archive has authoritative URL, expected SHA-256 and observed SHA-256;
6. all expected and observed hashes match;
7. the fresh packaged capability smoke still passes.

No wildcard-only or package-level blanket mapping may satisfy a native file row.

## Phase A - Structured source-evidence model

Upgrade the registry/inventory model from opaque `source_evidence` truthiness to a structured validated schema.

Each required source package record must contain at minimum:

- `source_id`;
- exact component/version;
- authoritative URL;
- expected SHA-256;
- observed SHA-256;
- byte length;
- evidence purpose;
- mapped staged components/files;
- license/source role;
- verification status.

The validator must fail if:

- URL is missing;
- expected hash missing;
- observed hash missing;
- hashes differ;
- source archive was not actually downloaded/verified in the hosted run;
- one source record claims to cover files/modules it cannot justify.

Pre-clearance may record metadata, but final clearance requires verified source artifacts.

## Phase B - Qt / PySide / Shiboken closure

The approved staged Qt surface remains frozen from PL-0349/V04:

### PySide6 Essentials
Current unresolved rows: **24**

Includes:

- `PySide6/QtCore.pyd`;
- `QtGui.pyd`;
- `QtWidgets.pyd`;
- `QtSvg.pyd`;
- `QtNetwork.pyd`;
- corresponding Qt6 DLLs;
- approved platform/image/icon/style plugins;
- `pyside6.abi3.dll`;
- retained wheel-private MSVC runtime copies;
- `opengl32sw.dll` only if still proven required.

### PySide6 Addons
Current unresolved rows: **2**

- `PySide6/Qt6Pdf.dll`;
- `PySide6/QtPdf.pyd`.

### Shiboken6
Current unresolved rows: **6**

Includes:

- `Shiboken.pyd`;
- `shiboken6.abi3.dll`;
- retained wheel-private MSVC runtime copies.

### Required Qt native map

`windows_qt_native_component_map.json` must map every retained unresolved Qt/PySide/Shiboken row to:

- exact staged path;
- SHA-256;
- owning Python distribution;
- Qt module/plugin identity;
- license route;
- required notice IDs;
- corresponding source package IDs;
- wheel-private Microsoft runtime classification where applicable;
- reason retained.

### Corresponding source packages

The exact PySide source archive is independently known and must be re-verified in the hosted run:

- `pyside-setup-everywhere-src-6.11.2.zip`;
- size 23,134,400 bytes;
- SHA-256 `c0fdd62b91a1d36d5ee2e1fb71050a32fbc93fcdeef0fdcb41d29afaaf00d9b5`;
- official Qt download source.

Also obtain and hash-pin the official Qt 6.11.2 source archives actually needed for the retained modules:

- `qtbase` for Core/Gui/Widgets/Network and relevant plugins;
- `qtsvg` for QtSvg and SVG plugin surface;
- `qtpdf` for QtPdf.

Do not use the 1.5 GB all-in-one Qt source archive if the exact submodule archives are sufficient.

### QtPdf / PDFium notices

The Qt PDF module embeds PDFium and documented third-party code.

At minimum inspect exact Qt 6.11.2 qtpdf source licensing/SBOM evidence for:

- Abseil;
- FreeType;
- PDFium;
- Chromium;
- fast_float;
- ICU;
- libjpeg-turbo;
- libpng;
- zlib;
- any additional 6.11.2-specific component documented by the exact source tree/SBOM.

Collect exact license/notice texts required by the retained QtPdf binary.

Do not satisfy QtPdf with LGPL text alone.

### MSVC runtime copies under Qt/Shiboken

Retained nested wheel runtime DLLs must either:

- be mapped to exact Microsoft redistribution evidence, or
- be removed only after native import-table analysis proves they are unnecessary and a fresh frozen capability smoke passes.

Do not remove them by basename alone.

## Phase C - OCP / OCCT exact native closure

Current unresolved OCP-owned rows: **79**.

The exact map:

`windows_ocp_native_component_map.json`

must account for every one.

### Required classifications

Each staged row must be one of:

1. `OCP_BINDING`
2. `OCCT_7_9_3`
3. `THIRD_PARTY_NATIVE`
4. `MICROSOFT_RUNTIME_PRIVATE`
5. `PACKAGE_METADATA`

### OCP binding

Map:

- `OCP/OCP.cp312-win_amd64.pyd`;
- OCP distribution metadata.

Use exact OCP upstream commit/release evidence and Apache-2.0 binding license.

### OCCT

Map every `TKernel-*.dll` and `TK*.dll` retained from the wheel to:

- OCCT 7.9.3;
- LGPL-2.1 + OCCT exception;
- exact OCCT 7.9.3 source archive;
- source archive SHA;
- exact staged digest.

### Third-party wheel natives

The V04 artifact includes third-party DLLs such as:

- deflate;
- FreeImage;
- FreeType;
- Iex;
- IlmThread;
- Imath;
- jpeg8;
- lcms2;
- Lerc;
- liblzma;
- libpng16;
- libsharpyuv;
- libwebp;
- libwebpmux;
- OpenEXR;
- OpenEXRCore;
- openjp2;
- openjph;
- raw;
- tiff;
- zlib;
- zstd;
- any additional retained non-OCCT DLL.

For each:

- derive identity from exact wheel `DELVEWHEEL` metadata, PE metadata, imported-library relationships and OCP build provenance;
- determine exact upstream component/version;
- record license;
- record notice/source archive;
- hash-pin source evidence.

Do not guess a version from filename when the authoritative wheel/build evidence does not prove it.

If exact version cannot be proven, the gate remains blocked.

### OCP source package set

At minimum V05 is expected to need exact verified source evidence for:

- OCP binding source;
- OCCT 7.9.3;
- every separately distributed third-party native retained in the wheel.

If several retained DLLs are proven to originate from one exact source package, one source package may cover them, but the map must list every covered staged file explicitly.

### Microsoft private wheel runtime

The hashed `msvcp140-*.dll` and `vcomp140-*.dll` files must be classified from wheel/import evidence.

Do not fold them into OCP or OCCT licensing.

## Phase D - Open3D exact native closure

Current unresolved Open3D rows: **3**:

- `open3d/Open3D.dll`;
- `open3d/pybind.cp312-win_amd64.pyd`;
- `open3d/tbb12.dll`.

The map:

`windows_open3d_native_component_map.json`

must include all three.

### Frozen artifact identity

Preserve existing PackLab evidence:

- `open3d==0.20.0`;
- wheel `open3d-0.20.0-cp312-cp312-win_amd64.whl`;
- wheel SHA-256 `60010f21d44f13557ba007893bc13a69827faa4dc49eedd923d1397096c20d92`.

### Source evidence

Verify and pin:

- exact Open3D v0.20.0 source archive;
- exact upstream third-party inventory for v0.20.0;
- oneTBB source/license evidence for the staged `tbb12.dll` version;
- any additional source package required by the actual Windows wheel build.

### Static native composition

For `Open3D.dll` and `pybind.pyd`:

- inspect Open3D v0.20.0 build scripts, CMake config, third-party manifest and observed wheel build flags;
- record which third-party components are statically linked or otherwise incorporated into those binaries when upstream evidence supports the claim;
- associate applicable notices/source records.

Do not mark the whole native binary simply MIT if the upstream build includes separately licensed third-party code.

If upstream evidence cannot prove exact static composition sufficiently for the engineering gate, stop truthfully. Do not fabricate certainty.

## Phase E - Map validation tests

Add negative tests proving the validator fails when:

- one staged Qt file is removed from the map;
- one OCP third-party DLL is missing from the map;
- an OCP DLL is falsely classified as OCCT;
- one Open3D native row lacks source evidence;
- expected and observed source hashes differ;
- a source package claims coverage of a staged file not listed in its map;
- a staged component is set to `EVIDENCE_PRESENT` while any owned row remains unresolved.

Add positive tests using compact fixtures for complete maps.

## Phase F - Final hosted source verification

The hosted Windows run must download source archives from authoritative URLs only.

For every required source package:

1. download to a temporary compliance workspace;
2. verify byte length where pinned;
3. verify SHA-256;
4. record observed SHA;
5. fail immediately on mismatch;
6. do not execute source archives.

Before engineering clearance, upload only text/JSON/license evidence.

After all five component maps are complete and validated:

- source archives required for LGPL/source availability may be uploaded as short-lived audit artifacts;
- other source archives needed only as evidence may be represented by exact authoritative URL/hash metadata unless the frozen criterion explicitly requires artifact publication.

For Qt LGPL source availability, publish the verified required Qt/PySide source archives as short-lived audit artifacts.

## Phase G - Clearance and installer

Clearance requires all of:

- unresolved shipped-file count = 0;
- unresolved component count = 0;
- missing notice count = 0;
- missing source-package count = 0;
- forbidden Qt component count = 0;
- fresh frozen Qt GUI smoke PASS;
- QtPdf smoke PASS;
- OCP/CAD smoke PASS;
- Open3D smoke PASS;
- no runtime network.

Engineering status must be:

`CLEARED_FOR_PL0350_ENGINEERING_PACKAGING`

while preserving:

- `legal_review_required=true`;
- `public_release_authorized=false`.

Only then:

1. add final compliance texts;
2. re-inventory exact installer input;
3. rerun frozen capability smoke;
4. build versioned unsigned Inno installer;
5. record installer SHA/bytes/tool version;
6. upload:
   - final compliance evidence;
   - required Qt/PySide source archives;
   - unsigned installer.

No signing claim, Git tag, GitHub Release or V0.1 publication.

## Validation

Run:

- `uv lock --check`;
- changed-file Ruff/format;
- `uv run --locked mypy core apps tools`;
- focused native-map/source-evidence tests;
- workflow contract tests;
- locked full pytest;
- compile checks;
- `git diff --check`;
- privacy/secrets/scope checks.

Do not repair unrelated preview formatting debt.

## OWNER DEV standing delivery

After implementation/evidence publication and confirmed local/origin/GitHub parity, run:

`tools/dev/post_codex_owner_dev_refresh.ps1 -AllowPublishedCommit`

Record the result.

## Stop conditions

Stop truthfully if:

- any of the five component gates remains unresolved;
- exact source archive hash cannot be verified;
- native identity/version cannot be proven;
- fresh packaged capability smoke regresses;
- required Qt source artifact cannot be produced;
- installer cannot be built after clearance.

Do not start PL-0351 while PL-0350 remains blocked.

## Handoff

Publish implementation/evidence commit(s), then:

`coordination/sessions/M16-C001/PL-0350_CODEX_LOG_V05.md`

as a distinct log-only commit.

Record:

- V04 six-item baseline;
- exact map file counts;
- source package IDs/URLs/hashes;
- before/after unresolved counts;
- hosted run/artifact IDs;
- Qt source artifacts;
- installer facts if green;
- OWNER_DEV refresh result;
- final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
