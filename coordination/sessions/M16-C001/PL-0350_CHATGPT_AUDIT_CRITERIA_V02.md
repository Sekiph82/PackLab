# PL-0350 - ChatGPT Audit Criteria V02

Task: **Windows file-level redistribution inventory + versioned installer**

All criteria are mandatory.

1. Live TASKS authorization, M16 partial audit V02 and PL-0350 V01 blocker are read; root TASKS is not edited by Codex.
2. The exact current hosted PL-0349 staging tree is inventoried before runner teardown. No stale/local bundle is used as current evidence.
3. Every staged file has relative path, SHA-256, byte length, category, component/distribution mapping, mapping evidence and license/notice status; PE metadata is recorded where available.
4. Canonical compliance evidence contains no runner/workspace absolute path, username, credential or secret.
5. PyInstaller/CPython/PySide6/Shiboken6/actual Qt modules and plugins/OCP/OCCT/Open3D/native/NumPy/SciPy/other staged components are mapped based on actual shipped files, not the lockfile alone.
6. Distribution-provided license/notice files are collected by exact component/version and digest. Supplemental evidence is explicit, pinned and reviewed; no license is borrowed from another component.
7. OCP binding and OCCT licensing evidence remain separate. Exact staged OCCT/native files are mapped and required OCCT license/exception texts are included.
8. Qt/PySide uses only evidence-backed open-source route unless separate commercial-license authority actually exists. Actual staged Qt modules/plugins are inventoried; unresolved route/components fail closed.
9. Open3D staged native contents, if any, carry reviewed main and applicable third-party notice evidence; no blanket MIT simplification is accepted.
10. Compliance validator reports `unresolved_count = 0` before any installer/binary publication. Any unresolved file/component/notice blocks the child.
11. Before clearance, hosted artifact upload contains only text/JSON/license evidence, never EXE/DLL/PYD/application bundle/private data.
12. Any new artifact action/build tool is SHA/version pinned as applicable and recorded in the dependency/license register.
13. Final staging input includes THIRD_PARTY_NOTICES and required license/exception texts and is re-inventoried/revalidated after those files are added.
14. Versioned Inno Setup installer derives AppVersion from Studio semantic version, binds build revision in provenance/name, excludes private/project/checkpoint/external-engine/signing data and records SHA-256/size/tool version.
15. Binary artifact publication occurs only after the exact staged input has `CLEARED_FOR_PL0350_PACKAGING`; no Git tag/GitHub Release/V0.1/signing claim is made.
16. Fresh hosted Windows evidence proves build, no-network smoke, inventory, zero-unresolved compliance, installer generation and permitted artifact publication.
17. Ruff/format, mypy, focused/workflow tests, locked full pytest, compile, dependency/license/privacy/scope checks pass.
18. Scope remains PL-0350 plus accepted PL-0349 packaging seam; PL-0351+ and M17+ are not implemented.
19. Implementation/evidence and V02 log publication are distinct; V02 log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V02.md
