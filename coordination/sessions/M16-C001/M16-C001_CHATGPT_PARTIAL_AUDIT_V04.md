# M16-C001 - ChatGPT Partial Audit V04

Date: 2026-10-06
Decision: **AUDITED_PARTIAL_CHANGES_REQUIRED**

Independently accepted frontier: **PL-0347 V02 through PL-0348**
Current child: **PL-0349 V03**
Next child after closure: **PL-0350 V03**
PL-0351 through PL-0367: **NOT_STARTED**
PL-0368: **DEFERRED_POST_M17**

## PL-0349 V02 blocker verdict

The builder stop is **VALID**.

PL-0349 V02 explicitly required Codex to stop if repository-wide source inspection proved that a real production feature required PySide6 Addons. Codex correctly found:

- `technical_drawing_pdf.py` uses `PySide6.QtPdf.QPdfDocument`;
- `QtPdf.pyd` is owned by the installed `PySide6-Addons==6.11.2` distribution;
- removing Addons would remove an accepted production PDF capability.

No product implementation was published and no hosted build was falsely claimed.

## Independent licensing resolution

The stop condition itself was too coarse.

Official Qt 6.11.2 documentation states that **Qt PDF is available under the GNU LGPL version 3 or GNU GPL version 2, in addition to commercial licensing**.

Official references:

- https://doc.qt.io/QT-6/qtpdf-licensing.html
- https://doc.qt.io/QT-6/qtpdf-index.html
- https://doc.qt.io/qt-6.11/licenses-used-in-qt.html

Therefore:

`PySide6 Addons required`

does **not** imply:

`feature must be removed or commercial Qt license required`.

The engineering rule must instead operate at **module/file level**, not at Python distribution-name level.

Qt PDF also carries third-party licensing/attribution requirements for PDFium and its bundled dependencies, including Abseil, FreeType, Chromium/PDFium, ICU, libjpeg-turbo, libpng and zlib. Those obligations belong to PL-0350's exact shipped-file/module compliance inventory.

This audit is not legal advice and does not certify distribution compliance. It resolves the PackLab engineering gate sufficiently to continue evidence collection.

## Frozen PL-0349 V03 direction

Preserve the production PDF capability.

The selected Python dependency surface may use exact pinned:

- `PySide6-Essentials==6.11.2`;
- `PySide6-Addons==6.11.2`;

instead of relying on the broad `PySide6` meta-package, if the locked dependency graph supports this cleanly.

At packaging time:

- include `QtPdf` because PackLab requires it;
- include `QtSvg`, QtCore, QtGui, QtWidgets and exact transitive Qt runtime libraries/plugins required by tested PackLab features;
- include only Addons modules/resources proven necessary by PackLab's source/runtime dependency graph;
- do not collect the entire Addons distribution indiscriminately;
- do not stage Qt Virtual Keyboard or other GPL-only/unjustified Qt modules under the current community route;
- preserve dynamic Qt libraries and later LGPL/source-availability evidence gates.

The previous PL-0349 V02 requirement to stop merely because Addons is needed is superseded.

## Runtime completeness remains mandatory

PL-0349 V03 must still prove from inside the frozen executable:

- Qt GUI startup;
- technical-drawing PDF capability, including real `QPdfDocument` parsing/render smoke;
- OCP/CAD capability and bounded operation;
- Open3D 0.20.0 capability and bounded operation;
- no runtime download.

No accepted feature may be removed to make packaging or licensing easier.

## PL-0350 remains downstream

After PL-0349 V03 is builder-green, PL-0350 V03 must inventory the exact resulting stage.

Its Qt/PySide compliance work must include:

- Qt PDF LGPLv3/GPLv2 module evidence;
- exact Qt PDF third-party notices;
- exact retained Essentials/Addons module mapping;
- zero accidental GPL-only/unrequired Qt modules;
- exact source-availability evidence required by the selected LGPL route.

## Verdict

`AUDITED_PARTIAL_CHANGES_REQUIRED`

PL-0349 V02 stop is accepted as truthful execution of the prior prompt. Resume at PL-0349 V03 under the corrected module-level Addons rule, then continue to PL-0350 V03.
