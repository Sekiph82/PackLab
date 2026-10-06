# PL-0350 - ChatGPT Independent Audit V02

Date: 2026-10-06
Decision: **AUDITED_CHANGES_REQUIRED**
Task: **Windows redistribution inventory and installer gate**

## Evidence inspected

- PL-0350 V02 prompt/criteria and implementation log.
- Implementation commits `5b933b18083763a8f281b49a420e6715dbc69bab` and `397786cac0cf276d1ebd5a27e0fc6c77e07619b9`.
- Hosted run 37431656815.
- Downloaded compliance artifact ID `11396764327`.
- `windows-redistribution-inventory.json`.
- `windows-component-summary.json`.
- `compliance-validation.json`.
- collected THIRD_PARTY_NOTICES and license evidence.
- current inventory tool, component registry, workflow and tests.

## Stop verdict

The V02 stop is **VALID**.

The hosted pipeline behaved correctly:

- production build: PASS;
- no-network startup smoke: PASS;
- exact hosted inventory generation: PASS;
- text-only pre-clearance artifact: PASS;
- installer/binary publication: correctly SKIPPED/BLOCKED.

The compliance validator records:

- staged files: 283;
- staged bytes: 141,367,765;
- mapped files: 283;
- component blockers: 7;
- files carrying unresolved status: 196;
- `unresolved_count=55`;
- final status: `BLOCKED`.

The value 55 is not simply 55 staged files. It is the validator's unresolved item set, including component-level blockers plus specific unmapped/runtime files. 196 staged files inherit an unresolved status because they map to one of those blocked components.

## Exact blocker breakdown

Unresolved components:

1. `microsoft-windows-runtime`;
2. `pyinstaller-hooks-contrib`;
3. `pyside6`;
4. `pyside6-addons`;
5. `pyside6-essentials`;
6. `shiboken6`;
7. `unmapped-source-component`.

The 46 files classified as `unmapped-source-component` are mechanically identifiable:

- 42 Windows API-set DLLs;
- 1 `ucrtbase.dll`;
- 1 CPython `base_library.zip`;
- 2 OpenSSL 3.5.5 DLLs (`libcrypto-3-x64.dll`, `libssl-3-x64.dll`).

Two additional root VCRUNTIME files are separately classified as unresolved Microsoft runtime.

The exact staged Qt/PySide set is also over-broad for the PackLab Studio source imports. The bundle includes, among other files, Qt QML/Quick/PDF/VirtualKeyboard modules and plugins. PackLab Studio source imports inspected by this audit use QtCore, QtGui and QtWidgets surfaces; no direct application import justifies the GPL-only Qt Virtual Keyboard module.

The current official Qt licensing documentation lists **Qt Virtual Keyboard as GPLv3-only for open-source users**, not LGPL. Because PackLab has no recorded commercial Qt license, that module must not be accidentally included in the open-source redistribution path.

## New production-completeness finding

The same artifact proves that OCP/OCCT and Open3D are not staged at all.

This is not a compliance success. These are locked direct runtime dependencies and PackLab loads them dynamically. Their absence means the current bundle is easier to inventory only because production CAD/geometry capabilities are missing.

PL-0349 is therefore reopened separately before PL-0350 can continue.

## Retained V02 implementation

The V02 compliance pipeline itself is useful and should be retained:

- path-free per-file SHA/size inventory;
- PyInstaller TOC + installed-distribution mapping;
- PE metadata;
- component summary;
- text-only pre-clearance artifact;
- fail-closed zero-unresolved gate;
- binary/installer steps gated behind clearance;
- checked-in supplemental license evidence with digest validation.

## Next remediation direction

After PL-0349 V02 produces a capability-complete stage, PL-0350 V03 must rerun inventory on that corrected bundle and close the actual shipped surface.

The remediation should reduce accidental redistribution rather than license-map unnecessary files:

- use only required PySide/Qt modules/plugins;
- remove GPL-only/unneeded Qt modules such as Virtual Keyboard from the open-source route;
- avoid redistributing Windows API-set/UCRT/MSVC runtime files when they can be truthful external OS/VC-runtime prerequisites;
- map CPython `base_library.zip` to CPython;
- map CPython's bundled OpenSSL files to exact OpenSSL evidence;
- distinguish PyInstaller hooks used only at build-analysis time from runtime hooks actually embedded;
- inventory the newly included OCP/OCCT and Open3D native surface completely.

No legal-compliance conclusion is implied by this audit. This is an engineering redistribution-evidence gate. Public release remains separately gated.

## Verdict

`AUDITED_CHANGES_REQUIRED`

PL-0350 V02 remains incomplete but its stop and evidence pipeline are independently accepted. Resume only after PL-0349 V02.
