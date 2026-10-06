# PL-0350 - Codex Prompt V04

Task: **Close the exact 59-item Windows redistribution gate and produce the unsigned audit installer**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001-R05**

This V04 supersedes PL-0350 V03 after independent inspection of hosted artifact ID `11413813934`.

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V06.md

V03 audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V03.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V04.md

## Start rule

Synchronize the managed checkout non-destructively with latest `origin/main`. Preserve owner-local work.

Read:

- live root `TASKS.md`;
- M16 partial audit V06;
- PL-0350 V03 log + audit;
- exact current production spec/workflow;
- component registry/inventory tool;
- dependency/license register;
- OWNER DEV post-Codex refresh policy.

Do not edit root `TASKS.md`.

## Frozen baseline

The exact V03 hosted stage was:

- 557 files;
- 542,575,818 bytes;
- 167 unresolved file rows;
- 7 unresolved components;
- 59 unresolved items;
- status `BLOCKED`.

The 59 items are exactly:

### Explicit file gates
- 44 `api-ms-win-*.dll`;
- 2 root `VCRUNTIME140*.dll`;
- 1 `ucrtbase.dll`;
- 1 `base_library.zip`;
- 1 `libcrypto-3-x64.dll`;
- 1 `libssl-3-x64.dll`;
- `qt-staged-surface.json`;
- `windows-runtime-capabilities.json`.

### Component gates
- `cadquery-ocp-novtk==7.9.3.1.1`;
- `microsoft-windows-runtime`;
- `open3d==0.20.0`;
- `pyside6-addons==6.11.2`;
- `pyside6-essentials==6.11.2`;
- `shiboken6==6.11.2`;
- `unmapped-source-component`.

V04 must close this exact surface against a **fresh rebuilt stage**. Do not reuse V03 JSON as final evidence.

## Non-negotiable production capability contract

After every pruning or native-runtime change, the frozen executable must still PASS:

- Qt GUI;
- QtPdf technical drawing parse/render;
- OCP/CAD bounded operation;
- Open3D 0.20.0 bounded operation;
- no runtime network.

Do not remove a required production feature to reduce licensing work.

## Phase A - Close deterministic ownership gaps first

### PackLab-generated JSON

Map:

- `qt-staged-surface.json`;
- `windows-runtime-capabilities.json`

as PackLab-owned generated evidence bound to the exact build revision.

They must no longer appear as `unmapped-source-component`.

### CPython base library

Map PyInstaller `base_library.zip` to the exact CPython 3.12 runtime and PSF license evidence.

Do not treat the archive as an unknown third-party component.

### OpenSSL

Map:

- `libcrypto-3-x64.dll`;
- `libssl-3-x64.dll`

to the exact OpenSSL runtime shipped with the selected CPython environment.

Record:

- exact observed OpenSSL version from the same build environment;
- source provenance;
- file digests/PE metadata;
- exact OpenSSL license/notice evidence.

Do not flatten OpenSSL into the CPython license.

## Phase B - Windows runtime pruning / prerequisite model

The 44 API-set DLLs, root `ucrtbase.dll`, and root `VCRUNTIME140*.dll` are not PackLab application logic.

Prefer a supported external Windows/VC-runtime prerequisite model **only when the post-prune frozen app proves it works**.

### Root/system copies

After validating source/import identity, exclude from the final PackLab stage:

- `api-ms-win-*.dll`;
- root `ucrtbase.dll`;
- root `VCRUNTIME140*.dll`;
- other plain-name MSVC/UCRT files collected from the host only when proven replaceable by the supported Windows/VC runtime prerequisite.

Create a deterministic prerequisite manifest containing:

- supported Windows architecture;
- required VC runtime architecture;
- minimum accepted runtime version;
- detection method;
- official help/download reference;
- no automatic download.

The future Inno installer must fail clearly when that prerequisite is absent/outdated.

### Nested wheel runtime copies

Do **not** blindly remove wheel-private renamed runtime DLLs.

For files under PySide/Shiboken/OCP/Open3D such as:

- `MSVCP140*.dll`;
- `VCRUNTIME140*.dll`;
- `VCOMP140.dll`;
- delvewheel-renamed `msvcp140-<hash>.dll` / `vcomp140-<hash>.dll`;

inspect the native import table first.

If the wheel binary imports the renamed private DLL name, either:

1. retain it and map its exact Microsoft runtime redistribution evidence, or
2. perform a reviewed deterministic rebinding/pruning approach and prove fresh frozen capability smoke.

Do not delete a hashed private runtime merely because its basename resembles MSVC.

## Phase C - Qt / PySide / Shiboken exact module evidence

The accepted staged Qt runtime remains bounded by the PL-0349 module contract.

At minimum the final stage is expected to contain only the approved Qt modules/plugins actually required by PackLab.

### Required mapping

For every retained file owned by:

- PySide6 Essentials 6.11.2;
- PySide6 Addons 6.11.2;
- Shiboken6 6.11.2;

record exact:

- staged path + SHA;
- Python distribution owner;
- Qt module or plugin owner;
- license route;
- third-party notice set;
- corresponding source package;
- source archive SHA.

Expected source-family mapping, subject to exact verification:

- `pyside-setup` 6.11.2 for PySide/Shiboken bindings;
- `qtbase` 6.11.2 for Core/Gui/Widgets/Network/platform/image plugins;
- `qtsvg` 6.11.2 for QtSvg and SVG plugins;
- `qtpdf` 6.11.2 for QtPdf.

Use authoritative exact 6.11.2 source archives and hash them.

### QtPdf

Map the exact QtPdf/PDFium third-party notice surface required by the staged `Qt6Pdf.dll`.

Do not represent QtPdf as generic LGPL text only.

### Optional staged files

If `opengl32sw.dll` or another Qt native helper is not required by PackLab's real frozen runtime, remove it and prove the post-prune smoke.

If it is required, map its exact component/license/source evidence.

### Forbidden surface

Virtual Keyboard and other unapproved/GPL-only Qt module families remain forbidden under the current route.

## Phase D - OCP / OCCT / bundled native wheel closure

The exact `cadquery-ocp-novtk==7.9.3.1.1` wheel stage currently carries roughly 80 unresolved-owned rows.

Classify each staged wheel file into one of these exact buckets:

1. **OCP binding**
   - `OCP/OCP.cp312-win_amd64.pyd`;
   - OCP package metadata needed for version provenance;
   - Apache-2.0 binding evidence.

2. **OCCT 7.9.3**
   - `TKernel-*.dll`;
   - `TK*.dll`;
   - LGPL-2.1 + OCCT exception;
   - exact OCCT 7.9.3 source archive evidence.

3. **Third-party native libraries bundled by the wheel**
   Examples observed in the exact V03 stage include:
   - FreeImage;
   - FreeType;
   - OpenEXR/Iex/IlmThread/Imath;
   - jpeg;
   - lcms2;
   - Lerc;
   - liblzma;
   - libpng;
   - libwebp/libwebpmux/libsharpyuv;
   - openjp2/openjph;
   - raw;
   - tiff;
   - deflate/zlib/zstd;
   - any other exact wheel-native file.

For every such file:

- identify exact upstream component/version from wheel/delvewheel/import metadata and authoritative package build evidence;
- map license/notice text;
- record file digest;
- record source-availability evidence if applicable.

4. **Microsoft runtime copies**
   - handle separately under Phase B.

Do not label all files in `cadquery_ocp_novtk.libs` as OCCT.

Do not clear the OCP component until every retained native file is classified.

If the wheel contains native libraries irrelevant to PackLab and they can be removed without breaking the frozen OCP smoke/import graph, prefer deterministic reduction and prove it.

## Phase E - Open3D 0.20.0 closure

The exact V03 stage carries only these unresolved Open3D native rows:

- `open3d/Open3D.dll`;
- `open3d/pybind.cp312-win_amd64.pyd`;
- `open3d/tbb12.dll`.

Map them individually.

Required:

- exact locked Open3D 0.20.0 wheel provenance;
- Open3D MIT license;
- exact Open3D 0.20.0 third-party/native notice inventory relevant to the Windows wheel;
- TBB component/version/license mapping for `tbb12.dll`;
- static third-party contents represented in `Open3D.dll` via the exact upstream build/third-party manifest rather than calling the whole DLL simply MIT.

If an exact third-party component/source obligation cannot be supported, stop truthfully.

## Phase F - Inventory model upgrades

Update compliance output so each retained shipped file records:

- relative path;
- SHA-256;
- bytes;
- file category;
- exact component owner(s);
- component version;
- mapping evidence;
- PE metadata;
- license;
- notice refs;
- source-evidence refs where required;
- unresolved reason or null.

Separate **external prerequisites** from shipped files.

Final validation must include:

- `unresolved_shipped_file_count`;
- `unresolved_component_count`;
- `forbidden_qt_component_count`;
- `missing_notice_count`;
- `missing_source_package_count`;
- `external_prerequisite_count`;
- `engineering_packaging_status`;
- `legal_review_required=true`;
- `public_release_authorized=false`.

Clearance requires all unresolved/missing/forbidden counts = 0 and:

`engineering_packaging_status = CLEARED_FOR_PL0350_ENGINEERING_PACKAGING`

Do not claim legal certification.

## Phase G - Fresh hosted proof and installer

Run a fresh Windows hosted workflow from the published V04 implementation.

Required sequence:

1. build exact production stage;
2. staged Qt assertion;
3. post-prune frozen Qt/PDF/OCP/Open3D no-network smoke;
4. exact inventory;
5. pre-clearance text evidence;
6. enforce zero-unresolved engineering gate;
7. collect reviewed notices/licenses;
8. collect/hash required source archives;
9. re-inventory exact final installer input;
10. re-run frozen capability smoke;
11. build versioned unsigned Inno installer;
12. record installer SHA/bytes/tool version;
13. upload short-lived:
   - final compliance evidence;
   - required source archives;
   - unsigned installer.

No Git tag, GitHub Release, signing claim or V0.1 release.

## Validation

Run:

- `uv lock --check`;
- changed-file Ruff/format;
- `uv run --locked mypy core apps tools`;
- focused redistribution/pruning/source-map tests;
- workflow contract tests;
- locked full pytest;
- compile checks;
- `git diff --check`;
- secrets/privacy/scope review.

Do not fix unrelated preview formatting debt.

## Owner DEV standing delivery

After implementation/evidence commits are pushed and local HEAD/origin/GitHub main parity is confirmed, run:

`tools/dev/post_codex_owner_dev_refresh.ps1 -AllowPublishedCommit`

Record `OWNER_DEV_READY` or a truthful owner-local delivery failure in the child log.

## Stop conditions

Stop with exact evidence if any retained shipped native file/component remains unresolved.

Do not start PL-0351 unless:

- the hosted engineering gate is zero-unresolved;
- required source evidence is present;
- unsigned installer artifact exists.

## Handoff

Publish implementation/evidence commit(s), then publish:

`coordination/sessions/M16-C001/PL-0350_CODEX_LOG_V04.md`

as a distinct log-only commit.

Record:

- V03 59-item baseline;
- exact before/after unresolved counts;
- removed external Windows runtime files;
- retained nested runtime decisions;
- CPython/OpenSSL mappings;
- exact Qt/PySide/Shiboken source/notice set;
- OCP/OCCT/third-party wheel mapping;
- Open3D/TBB mapping;
- hosted run/artifact IDs;
- installer/source artifact facts if green;
- OWNER_DEV refresh result;
- final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
