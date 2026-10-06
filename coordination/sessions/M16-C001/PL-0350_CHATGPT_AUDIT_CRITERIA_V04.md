# PL-0350 - ChatGPT Audit Criteria V04

Task: **Exact 59-item redistribution closure + unsigned audit installer**

All criteria mandatory.

1. Live TASKS + partial audit V06 + V03 audit are read; Codex does not edit root TASKS.
2. V04 starts from the exact capability-complete PL-0349 V03 production surface, not a stale V02 bundle.
3. PackLab-generated JSON evidence files are mapped as PackLab-owned.
4. `base_library.zip` maps to exact CPython/PSF evidence.
5. `libcrypto` and `libssl` map to exact OpenSSL runtime/version/license evidence, not generic CPython ownership.
6. Root API-set/UCRT/MSVC files are removed when using the external prerequisite model and fresh frozen capability smoke passes afterward.
7. Nested/renamed wheel MSVC runtime files are never blindly deleted; import-table/provenance evidence supports keep/prune decisions.
8. Windows/VC runtime prerequisite detection is deterministic and performs no automatic download.
9. Every retained PySide6 Essentials/Addons/Shiboken file maps to exact Qt module/plugin, license/notice and hash-pinned corresponding source evidence.
10. QtPdf third-party/PDFium notice surface is explicit; no generic-LGPL-only shortcut is accepted.
11. Unapproved/GPL-only Qt module families remain absent.
12. Every retained OCP wheel file is classified as OCP binding, OCCT, exact third-party native dependency, Microsoft runtime, or reviewed metadata/resource.
13. OCCT files have exact 7.9.3 LGPL/exception/source evidence; non-OCCT wheel natives have their own component/license mappings.
14. Open3D.dll, pybind.pyd and tbb12.dll are mapped individually against exact Open3D 0.20.0 + third-party/TBB evidence.
15. Final shipped-file inventory contains zero unresolved retained files/components, zero missing notices/source packages and zero forbidden Qt modules.
16. Final status is engineering-only `CLEARED_FOR_PL0350_ENGINEERING_PACKAGING`, with legal review/public-release gates still explicit.
17. Final installer input is re-inventoried and frozen Qt/PDF/OCP/Open3D smoke passes after all pruning/compliance additions.
18. Versioned unsigned Inno installer is built only after clearance and has exact version/revision/hash/size/prerequisite provenance.
19. Hosted artifacts include final compliance evidence, required source evidence and unsigned installer only after clearance.
20. No tag/GitHub Release/V0.1/signing claim, PL-0351+, M17 or PL-0368 implementation occurs inside this child.
21. Lock/Ruff/format/mypy/focused/full pytest/compile/workflow/privacy checks pass without unrelated formatting cleanup.
22. After published parity, OWNER DEV post-Codex refresh is run and recorded.
23. Implementation/evidence and V04 log are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V04.md
