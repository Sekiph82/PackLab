# PL-0349 - Codex Prompt V03

Task: **Build a capability-complete Windows Studio bundle with required Qt PDF Addons support**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001-R04**

This V03 supersedes PL-0349 V02 after independent review of the real QtPdf dependency and Qt PDF 6.11.2 licensing.

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V04.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CHATGPT_AUDIT_CRITERIA_V03.md

## Start rule

Synchronize the managed execution checkout non-destructively with latest `origin/main`. Preserve owner-local work. Verify live root `TASKS.md` authorizes M16-C001-R04 / PL-0349 V03.

Read before implementation:

- M16 partial audit V04;
- PL-0349 V01/V02 prompts, logs and audits;
- PL-0350 V02 artifact findings;
- `technical_drawing_pdf.py`;
- `cad_adapter.py`;
- `geometry_adapter.py`;
- current production build workflow;
- `pyproject.toml` and `uv.lock`;
- dependency/license register.

Do not edit root `TASKS.md`.

## Corrected Qt dependency ruling

PackLab **does require** one Addons module:

`PySide6.QtPdf.QPdfDocument`

for the accepted technical-drawing PDF capability.

Qt PDF 6.11.2 is officially available under LGPLv3 or GPLv2 in addition to commercial licensing. Do not remove this production feature simply to eliminate the Addons distribution.

Official engineering evidence:

- https://doc.qt.io/QT-6/qtpdf-licensing.html
- https://doc.qt.io/QT-6/qtpdf-index.html
- https://doc.qt.io/qt-6.11/licenses-used-in-qt.html

This is an engineering decision, not legal certification.

## Required Python dependency surface

Inspect the exact locked dependency graph.

If clean and compatible, replace the broad direct meta dependency:

`PySide6>=6.8,<7`

with exact pinned runtime packages:

- `PySide6-Essentials==6.11.2`;
- `PySide6-Addons==6.11.2`.

Preserve normal `PySide6.*` imports.

If exact direct pins cannot be represented safely because of the package dependency graph, retain the exact `PySide6==6.11.2` meta-package but do **not** use that as permission to freeze every installed Addons module.

Update lock and dependency/license register intentionally.

## Required Qt module contract

Create an explicit PackLab production Qt-module contract from repository-wide source/runtime evidence.

At minimum accepted direct application modules are:

- QtCore;
- QtGui;
- QtWidgets;
- QtSvg;
- QtPdf.

The contract must distinguish:

- direct PackLab imports;
- transitive runtime Qt libraries/plugins required by those direct modules;
- forbidden/unjustified Qt modules.

### Addons rule

`PySide6-Addons` may remain installed because `QtPdf` is required.

But the frozen production stage must include only Addons files/modules proven necessary for:

- `QtPdf`;
- exact transitive runtime dependencies of `QtPdf`;
- another separately proven PackLab production import, if discovered and documented.

Do not collect the whole Addons distribution by package membership alone.

### Forbidden/unjustified surface

Under the current community/open-source engineering route:

- Qt Virtual Keyboard must not be staged;
- other Qt modules identified by official Qt licensing as GPL-only must not be staged unless a separately accepted compatible authority exists;
- unused QML/Quick/PDFQuick/3D/Multimedia/etc. modules must not be staged merely because they exist in Addons.

If the frozen dependency graph proves an additional module is technically required, document that exact edge rather than silently broadening the package.

## Explicit PyInstaller collection

Use a deterministic PyInstaller spec/hook configuration that collects:

### Qt
- exact QtCore/Gui/Widgets/Svg/Pdf Python extension modules;
- exact Qt DLLs and plugins needed by the real PackLab Qt runtime tests;
- exact QtPdf native runtime resources/dependencies;
- no unrelated Addons tree.

### OCP
- exact OCP Python modules/extensions and native DLLs required by PackLab CAD capabilities.

### Open3D
- exact Open3D Python/native runtime needed by `Open3DGeometryAdapter`, excluding examples/Jupyter/development assets.

Do not rely on accidental static discovery for these dynamic imports.

## Frozen capability smoke

Extend the packaged build smoke so the frozen executable proves all accepted in-process production capabilities.

### Qt/Studio
- QApplication/offscreen startup;
- StudioMainWindow construct/show/process/close.

### Technical Drawing PDF
- `probe_vector_pdf_capability().available == True`;
- `QPdfDocument` parser availability;
- `QSvgRenderer` availability;
- a bounded generated technical-drawing PDF or dedicated minimal vector/PDF round-trip smoke succeeds through PackLab-owned API;
- resulting PDF parse/page/render smoke passes;
- no network.

Do not replace the accepted real PDF path with a stub merely to avoid QtPdf.

### OCP/CAD
- accepted PackLab CAD runtime probe AVAILABLE;
- exact locked binding version;
- one bounded real PackLab CAD operation;
- one bounded BREP/tessellation/bounds operation.

### Open3D
- PackLab Open3D probe AVAILABLE;
- observed version exactly 0.20.0;
- one bounded PackLab geometry conversion/operation.

## Runtime completeness manifest

Generate path-free `windows-runtime-capabilities.json` bound to exact build revision/version.

It must list required capability groups:

- `qt_studio_gui`;
- `qt_vector_pdf`;
- `ocp_cad`;
- `open3d_geometry`.

For each record:

- expected package/module/version;
- observed packaged package/module/version;
- smoke operation;
- status;
- no-network status.

Any required group not PASS fails the build.

Also record external architecture dependencies that are intentionally not bundled, such as Blender/COLMAP/OpenMVS, without probing/download.

## Qt staged-surface assertion

After PyInstaller build, before PL-0350:

- enumerate staged `PySide6` extension modules and Qt DLL/plugin/module files;
- compare them to the approved Qt module contract;
- fail on forbidden/unapproved module families;
- specifically fail if Virtual Keyboard is present;
- record the approved staged Qt module list in path-free evidence.

This is a packaging-completeness/minimization gate. PL-0350 owns final license/notice/source evidence.

## Validation

Run locally:

- `uv lock --check`;
- Ruff lint/format;
- `uv run --locked mypy core apps tools`;
- focused Qt/PDF/OCP/Open3D/packaging tests;
- full locked pytest;
- compile checks;
- dependency/license/scope/privacy checks.

Then launch a fresh real hosted Windows build.

Hosted PASS requires:

1. locked dependency install;
2. production frozen staging build;
3. no-network Studio Qt smoke;
4. technical-drawing QtPdf smoke PASS;
5. OCP/CAD smoke PASS;
6. Open3D smoke PASS;
7. runtime completeness manifest with all required groups PASS;
8. staged Qt module assertion PASS with no forbidden/unapproved modules;
9. no private data/checkpoints/external-engine bundles;
10. exact staged file count/bytes recorded for PL-0350 V03.

No installer/release claim yet.

## Handoff

Publish implementation/evidence commit(s), then:

`coordination/sessions/M16-C001/PL-0349_CODEX_LOG_V03.md`

as a distinct log-only commit.

Record:

- V02 Addons blocker resolution;
- exact final PySide package pins;
- Qt module contract;
- exact retained Addons modules;
- staged Qt modules/plugins summary;
- hosted run ID/URL;
- PDF/OCP/Open3D frozen capability results;
- runtime completeness manifest;
- full validation;
- final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
