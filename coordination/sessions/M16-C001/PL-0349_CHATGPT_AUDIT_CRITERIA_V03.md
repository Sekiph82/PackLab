# PL-0349 - ChatGPT Audit Criteria V03

Task: **Capability-complete frozen Windows Studio with required QtPdf Addons support**

All criteria are mandatory.

1. Live TASKS authorization and M16 partial audit V04 are read; root TASKS is not edited by Codex.
2. Accepted technical-drawing PDF capability is preserved; `PySide6.QtPdf.QPdfDocument` is not removed or stubbed.
3. Qt PDF 6.11.2 is treated as an allowed engineering module under its documented LGPLv3/GPLv2/commercial licensing options, while final redistribution obligations remain deferred to PL-0350.
4. Direct PySide dependencies are exact-pinned and minimize the meta/Addons surface where package graph permits.
5. Explicit Qt module contract covers QtCore/Gui/Widgets/Svg/Pdf and distinguishes direct imports, required transitive runtime files and forbidden/unjustified modules.
6. PyInstaller does not collect the entire Addons tree by package membership; retained Addons content is justified by QtPdf or another exact documented runtime edge.
7. Qt Virtual Keyboard and other unaccepted GPL-only/unjustified Qt module families are absent from the frozen stage.
8. Frozen executable Qt smoke proves Studio GUI and real technical-drawing PDF capability, including QPdfDocument parse/render behavior.
9. Frozen executable OCP/CAD smoke proves exact required CAD capability and bounded real operation.
10. Frozen executable Open3D smoke proves exact 0.20.0 geometry capability and bounded real operation.
11. Runtime completeness manifest records qt_studio_gui, qt_vector_pdf, ocp_cad and open3d_geometry as PASS and is path-free/build-bound.
12. Staged Qt module assertion enumerates actual frozen Qt modules/plugins and fails on forbidden/unapproved module families.
13. No runtime network/download, private data, checkpoints, Blender/COLMAP/OpenMVS bundle or feature removal for packaging convenience is introduced.
14. Lock, Ruff/format, mypy, focused tests, full pytest, compile, dependency/license/privacy/scope checks pass.
15. Fresh hosted Windows build proves the full frozen capability surface and records exact staged file count/bytes for PL-0350 V03.
16. Scope remains PL-0349; no PL-0350 installer/compliance completion, PL-0351+, M17 or PL-0368 implementation.
17. Implementation/evidence and V03 log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CODEX_PROMPT_V03.md
