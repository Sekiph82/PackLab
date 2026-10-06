# PL-0350 - ChatGPT Audit Criteria V05

Task: **Final five native-component redistribution gates + unsigned audit installer**

All criteria are mandatory.

1. Live TASKS, partial audit V07 and V04 audit are read; Codex does not edit root TASKS.
2. V05 preserves all accepted V04 ownership/pruning/VC-runtime/OpenSSL closures and capability behavior.
3. Three checked-in exact maps exist for Qt/PySide/Shiboken, OCP/OCCT/native-wheel and Open3D native files.
4. Inventory validates maps against the actual fresh staged tree bidirectionally: no unmapped owned staged files and no map rows for missing files.
5. No component becomes EVIDENCE_PRESENT through a manual registry flag while any owned file row remains unresolved.
6. Structured source-evidence records require authoritative URL, expected SHA, observed SHA, component/version, coverage and verification status.
7. Hosted source downloads are hash-verified and never executed.
8. Exact PySide 6.11.2 source archive is verified against SHA-256 `c0fdd62b91a1d36d5ee2e1fb71050a32fbc93fcdeef0fdcb41d29afaaf00d9b5`.
9. Exact Qt 6.11.2 qtbase/qtsvg/qtpdf source archives needed by the staged surface are independently hash-pinned and verified.
10. QtPdf/PDFium and exact 6.11.2 third-party notices are mapped; LGPL text alone is insufficient.
11. Every retained PySide6 Essentials/Addons/Shiboken row maps to exact module/plugin, notice and source evidence.
12. Every OCP-owned staged row is explicitly classified as binding, OCCT, third-party native, Microsoft private runtime or package metadata.
13. OCP binding license remains separate from OCCT LGPL/exception and from third-party native licenses.
14. Every retained OCCT `TK*.dll` maps to exact OCCT 7.9.3 source/license evidence.
15. Every retained OCP third-party DLL has proven upstream component/version/license/source evidence. Guessing from filename is forbidden.
16. Open3D.dll, pybind.pyd and tbb12.dll are individually mapped to exact Open3D 0.20.0/TBB/native evidence.
17. Open3D static third-party composition is not flattened to MIT when upstream build evidence identifies separate licenses.
18. Negative tests prove missing/misclassified map rows and source hash mismatch fail closed.
19. Final hosted gate reports zero unresolved shipped files/components, zero missing notices/source packages and zero forbidden Qt modules.
20. Fresh frozen Qt GUI/QtPdf/OCP/Open3D no-network smoke passes after all mapping/pruning changes.
21. Final engineering status is `CLEARED_FOR_PL0350_ENGINEERING_PACKAGING` with `legal_review_required=true` and `public_release_authorized=false`.
22. Versioned unsigned installer is built only after clearance and exact final input revalidation.
23. Required Qt/PySide source archives and final compliance evidence accompany the unsigned installer as short-lived audit artifacts.
24. No tag/GitHub Release/V0.1/signing claim, PL-0351+, M17 or PL-0368 implementation occurs inside this child.
25. Lock/Ruff/format/mypy/focused/full pytest/compile/workflow/privacy checks pass without unrelated cleanup.
26. OWNER DEV post-Codex refresh runs after published parity and is recorded.
27. Implementation/evidence and V05 log are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V05.md
