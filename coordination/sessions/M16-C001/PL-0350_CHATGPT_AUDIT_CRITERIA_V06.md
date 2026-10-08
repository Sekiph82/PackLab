# PL-0350 - ChatGPT Audit Criteria V06

Task: **Provenance-complete controlled native runtime + unsigned installer closure**

All criteria mandatory.

1. Codex reads live TASKS, partial audit V08 and V05 audit; root TASKS is not edited.
2. The accepted owner Desktop native PackLab.exe is preserved and refreshed after published changes.
3. Production packaging no longer depends on unidentified third-party DLL provenance from the opaque prebuilt OCP wheel.
4. A machine-readable exact Windows native source/package lock exists; final production records contain no wildcard build selectors.
5. Every source/package input has immutable identity, authoritative URL and SHA-256.
6. OCP production runtime is built/assembled from PackLab-controlled exact inputs and is not committed as a binary to Git.
7. OCP source revision and OCCT 7.9.3 source identity are exact and reproducible.
8. Any binary-package native build inputs have exact package filename/build string, URL, SHA-256, license and source reference.
9. OCP/OCCT staged surface is minimized without removing accepted PackLab CAD/export capability.
10. Every staged OCP-controlled native file maps bidirectionally to exact source/package evidence.
11. Qt/PySide/Shiboken retained 6.11.2 modules map to exact official binary identity, official corresponding source archives and required notices.
12. QtPdf/PDFium third-party evidence is explicit and exact to the retained Qt 6.11.2 surface.
13. Open3D 0.20.0 official wheel identity remains exact and maps to official source/third-party inventory plus TBB evidence.
14. Inventory provenance classes are explicit and restricted to PACKLAB_CONTROLLED_BUILD, PROJECT_OFFICIAL_BINARY, EXTERNAL_SYSTEM_PREREQUISITE or PACKLAB_OWNED.
15. PROJECT_OFFICIAL_BINARY requires exact binary artifact identity + exact corresponding official source identity + notices.
16. Fresh hosted build verifies all source/package hashes before use.
17. Fresh frozen Qt GUI/QtPdf/OCP/Open3D no-network smoke passes with the controlled OCP runtime.
18. Final engineering gate has zero unresolved shipped files/components, zero missing notices/source packages and zero forbidden Qt modules.
19. Engineering status is CLEARED_FOR_PL0350_ENGINEERING_PACKAGING while legal_review_required remains true and public_release_authorized false.
20. Installer is built only after clearance and exact final input revalidation/smoke.
21. Unsigned installer and required compliance/source artifacts are published as short-lived GitHub Actions artifacts only after clearance.
22. Lock/Ruff/format/mypy/focused/full pytest/compile/workflow/privacy checks pass.
23. No tag/GitHub Release/V0.1/signing claim, PL-0351+, M17 or PL-0368 is implemented inside this child.
24. OWNER DEV native EXE refresh remains green and does not regress to Desktop LNK/PowerShell.
25. Implementation/evidence and child log publication are distinct.
26. Final owner handoff uses clickable GitHub HTTPS links for commits, logs, runs, artifacts, prompt and criteria; no local C:\ paths are used as handoff links.
27. Published logs themselves use GitHub URLs for referenced repository files/runs/artifacts where applicable.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V06.md
