# PL-0350 - ChatGPT Audit Criteria V03

Task: **Capability-complete Windows redistribution evidence + audit-only installer**

All criteria are mandatory.

1. PL-0349 V02 is builder-green first and proves frozen Qt/OCP/Open3D runtime completeness.
2. V03 inventories the exact capability-complete hosted stage; no stale V02 stage is substituted.
3. Qt/PySide shipped surface is minimized to modules/plugins actually required by PackLab and justified by import/runtime tests.
4. No GPL-only Qt module, including Qt Virtual Keyboard, is staged under the current community/open-source route without separately accepted authority.
5. Retained Qt/PySide/Shiboken files have exact component/module/license/third-party notice mappings and remain dynamically replaceable.
6. Exact corresponding source archives for retained LGPL-covered Qt/PySide/Shiboken components are provenance-pinned, hash-verified and published as companion short-lived CI audit source artifacts; missing required source blocks packaging.
7. Windows API-set/UCRT/MSVC runtime DLLs are not redistributed when defined as external prerequisites; pruning is exact/name/source based and fresh packaged capability smoke passes afterward.
8. Installer prerequisite contract checks supported Windows/architecture and required Microsoft VC++ runtime without auto-download.
9. CPython base_library.zip is mapped to CPython; bundled OpenSSL DLLs are mapped to exact OpenSSL version/build and exact license/notice evidence.
10. PyInstaller standard hooks are treated as build-time only unless actually embedded; exact runtime hooks are identified and licensed as shipped content.
11. OCP binding and OCCT kernel remain separate license/source units; every staged OCP/OCCT native file is mapped and required license/exception/source evidence is present.
12. Every staged Open3D/native file maps to the locked 0.20.0 wheel and actual third-party inventory; separate third-party obligations are not flattened to MIT.
13. Final inventory has zero unresolved shipped files/components, zero forbidden Qt modules, zero missing notices and zero missing required source packages.
14. Final status is engineering-only `CLEARED_FOR_PL0350_ENGINEERING_PACKAGING`; evidence retains `legal_review_required=true` and `public_release_authorized=false`.
15. Exact final installer input is re-inventoried and frozen Qt/OCP/Open3D capability smoke passes after pruning/compliance additions.
16. Versioned unsigned Inno installer is built only after clearance, has correct Studio version/build revision/prerequisite logic and records SHA-256/size/tool version.
17. Hosted artifact publication contains final compliance evidence, required source artifacts and cleared unsigned installer only after gate success; no tag/GitHub Release/V0.1 release.
18. Ruff/format, mypy, focused/workflow tests, full pytest, compile, dependency/license/privacy/scope checks pass.
19. Scope remains PL-0350 plus accepted PL-0349 packaging seam; PL-0351+, M17 and PL-0368 are not implemented.
20. Implementation/evidence and V03 log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V03.md
