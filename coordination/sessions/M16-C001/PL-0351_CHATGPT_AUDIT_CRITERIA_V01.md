# PL-0351 - ChatGPT Audit Criteria V01

Task: **Packaged Windows application clean-artifact portability smoke test**

> Amended before first execution on 2026-10-06 after owner-machine QtCore DLL-load evidence.

All criteria mandatory.

1. PL-0350 is builder-green first and the exact cleared unsigned installer artifact/provenance is the only application-under-test input.
2. Smoke runs in a separate fresh Windows job, not the producer job's staging workspace.
3. Installer artifact is downloaded with a pinned reviewed action and SHA-256/length verified against PL-0350 provenance.
4. The test launches the **installed** PackLabStudio.exe from an isolated install location, not a source/staging executable.
5. Runtime environment is sanitized so checkout/venv Python, Qt, Shiboken, OCP, Open3D, Poppler/ICU or developer-tool DLL paths cannot make the application pass accidentally.
6. Installed app proves embedded build/version provenance, clean startup/exit, QtCore/QApplication/StudioMainWindow functionality and no native loader/procedure/plugin/ICU/Shiboken error.
7. Real installed QtSvg/QtPdf PackLab PDF export + QPdfDocument parse/render smoke passes.
8. Real installed OCP/CAD and Open3D 0.20.0 PackLab capability smokes pass.
9. No runtime network/download or external engine is required.
10. Any Windows loader failure remains a hard failure and produces path-private diagnostic evidence; no retry/ignore/soft-fail hides it.
11. External VC runtime prerequisite behavior, if applicable, is verified truthfully without unauthorized auto-download/bundling.
12. Installer uninstall/cleanup runs in an always-cleanup path and leaves no intentional CI residue.
13. No private data, owner-local path identity, signing material or installed application tree is uploaded unintentionally.
14. Workflow/static tests, Ruff/format/mypy/compile as applicable, locked full pytest, privacy/secrets/scope checks pass.
15. Scope remains PL-0351 and accepted packaging seams; no PL-0352+, M17 or PL-0368 implementation.
16. Implementation/evidence and child-log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0351_CODEX_PROMPT_V01.md
