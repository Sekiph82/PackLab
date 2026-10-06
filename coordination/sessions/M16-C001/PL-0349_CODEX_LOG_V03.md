# PL-0349 - Codex Implementation Log V03

Task: **Capability-complete Windows Studio bundle with required Qt PDF Addons support**

Cycle: **M16-C001-R04**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CODEX_PROMPT_V03.md
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CHATGPT_AUDIT_CRITERIA_V03.md

## Authorization and synchronized start

- Live `origin/main:TASKS.md` authorized M16-C001-R04, beginning with PL-0349 V03. Root `TASKS.md` was not edited.
- Managed execution checkout: `C:\Users\sekip\.codex\worktrees\packlab-m15-c001\PackLab`; owner Desktop checkout and unrelated worktrees were preserved.
- Synchronized starting SHA: `17f4f806fbe159c6c5d09dece4c8498453890407`; `HEAD` and `origin/main` were equal and the managed worktree was clean before implementation.
- Read the R04 master prompt/criteria, PL-0349 V03 prompt/criteria, partial audit V04, PL-0350 V03 prompt/criteria and prior evidence, dependency/license register, M16 governance, and production workflow/source seams.

## Implementation and evidence commits

- `e159654dc76f93043703ed54758bbd5aeac5f349` — pinned exact PySide6 Essentials/Addons 6.11.2 distributions, added a narrow Qt/PyInstaller staging contract, frozen PDF/CAD/Open3D capability probes, pre-import native DLL setup, staged Qt assertions and hosted workflow integration.
- `9dccd1c00d2122f894b007b39ad33aef25b1ce42` — removed the unsupported `--noupx` script-build flag when invoking a `.spec`; the spec itself sets `upx=False`.
- The first hosted attempt at `e159654d` failed before staging because PyInstaller rejects `--noupx` with a `.spec`. The corrected hosted attempt used `9dccd1c` and passed all PL-0349 build, stage, smoke and inventory steps.

## Runtime and staged surface

- Direct dependency pins: `PySide6-Essentials==6.11.2` and `PySide6-Addons==6.11.2`; the lock resolves the shared PySide/Shiboken runtime at 6.11.2.
- The contract keeps direct `QtCore`, `QtGui`, `QtWidgets`, `QtSvg` and required Addons `QtPdf`; `QtNetwork` is explicitly justified as a transitive runtime module. PyInstaller uses explicit OCP/Open3D import boundaries and excludes Open3D development/notebook payloads.
- The staged assertion and fresh hosted inventory report exactly these Python extensions: `PySide6.QtCore`, `QtGui`, `QtNetwork`, `QtPdf`, `QtSvg`, `QtWidgets`.
- Staged Qt DLLs: `Qt6Core.dll`, `Qt6Gui.dll`, `Qt6Network.dll`, `Qt6Pdf.dll`, `Qt6Svg.dll`, `Qt6Widgets.dll`.
- Staged Qt plugins: `iconengines/qsvgicon.dll`, `imageformats/qico.dll`, `imageformats/qjpeg.dll`, `imageformats/qsvg.dll`, `platforms/qoffscreen.dll`, `platforms/qwindows.dll`, `styles/qmodernwindowsstyle.dll`.
- The assertion rejects unapproved Qt modules/plugins, Virtual Keyboard, unrelated ICU runtime DLLs, and Open3D development/notebook content. The hosted stage passed with no forbidden module families.
- The screenshots' `QtCore` loader failure led to two local packaging fixes: register staged `shiboken6` and native DLL directories before importing Studio; exclude unrelated ICU DLLs collected from the local Poppler environment. The local frozen smoke then progressed through Qt and all four capability groups. CadQuery OCP distribution metadata is explicitly bundled so the frozen version probe reports the pinned 7.9.3.1.1 binding.
- Qt loaded using the Windows system ICU on the local and hosted Windows runners; no foreign ICU DLL is shipped. Windows system/runtime prerequisite mapping is left to PL-0350 V03.

## Validation

- Local lock check: `uv lock --check` — PASS.
- Local typing: `uv run --locked mypy core apps tools` — PASS, 222 source files.
- Local full tests: `uv run --locked pytest` — **1998 passed, 11 skipped, 1 deselected, 2 warnings**.
- Hosted Python quality run [37455141881](https://github.com/Sekiph82/PackLab/actions/runs/37455141881) — PASS: lock/install, Ruff lint/format, mypy (222 files), and **2001 passed, 10 skipped, 1 deselected, 2 warnings**.
- Focused packaging tests — PASS, 17 tests after adding the external-ICU guard; workflow-only correction tests — PASS, 2 tests.
- Changed-file Ruff lint/format — PASS. `compileall` over `core/src`, Studio, packaging tools and touched tests — PASS. `git diff --check` — PASS.
- Local PyInstaller one-directory build, staged Qt assertion and no-network frozen capability smoke — PASS. The local smoke manifest recorded `qt_studio_gui`, `qt_vector_pdf`, `ocp_cad` and `open3d_geometry` as PASS with network `NONE`; because that diagnostic build was run before committing the implementation, its embedded revision points to the starting SHA and is not claimed as exact-source provenance. The fresh hosted manifest is bound to the published implementation SHA below.

## Fresh hosted Windows evidence

- Studio Windows run [37455141899](https://github.com/Sekiph82/PackLab/actions/runs/37455141899), commit `9dccd1c00d2122f894b007b39ad33aef25b1ce42`: lock/install, one-directory build, Qt staged-surface assertion, no-network frozen Studio/PDF/OCP/Open3D smoke, and exact stage inventory all passed.
- Exact hosted stage: **557 files, 542,575,818 bytes**. The path-free runtime manifest observed PySide6 Essentials/Addons 6.11.2, OCP 7.9.3.1.1 (kernel 7.9.3), and Open3D 0.20.0; all four required capability groups passed.
- Text-only pre-clearance artifact: `packlab-windows-compliance-preclearance-9dccd1c00d2122f894b007b39ad33aef25b1ce42`, artifact ID `11408812753`. Its exact hosted validation is `BLOCKED` at the separate PL-0350 redistribution gate: `unresolved_count=64`, `unresolved_file_count=173`, `unresolved_component_count=12`. The workflow stopped before installer construction or binary upload. This does not change the PL-0349 capability result and is the active PL-0350 V03 work.
- No installer/release clearance, legal-compliance claim, signing, tag, GitHub Release, or V0.1 publication is claimed.

## Scope, privacy, and handoff

- Changes are limited to PL-0349 runtime completeness and its required packaging seam. No PL-0351+ child or M17 work was started; PL-0368 remains `DEFERRED_POST_M17`.
- No secrets, private scans, supplier files, signing material, or staged application binaries were committed. The uploaded pre-clearance artifact contains text/JSON/notice evidence only.
- Implementation commits and this child log are separate publications. Final local/origin parity is recorded by the separate R04 continuation-log commit. This is builder evidence, not an independent audit verdict or task-closure decision.

READY_FOR_INDEPENDENT_AUDIT
