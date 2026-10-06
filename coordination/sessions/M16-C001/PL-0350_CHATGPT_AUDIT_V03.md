# PL-0350 - ChatGPT Independent Audit V03

Date: 2026-10-06
Decision: **AUDITED_CHANGES_REQUIRED**
Task: **Capability-complete Windows redistribution evidence + audit-only installer**

## Evidence inspected

- PL-0350 V03 prompt and criteria.
- Implementation commit `14a8e83e05e48cc70d141c65b82978c68bf2b19c`.
- V03 builder log.
- Hosted Windows run `37465015550`, job `112273752832`.
- Exact hosted pre-clearance artifact ID `11413813934`.
- `windows-redistribution-inventory.json`.
- `windows-component-summary.json`.
- `compliance-validation.json`.
- `license-evidence-manifest.json`.
- Current component registry and inventory implementation.

## Stop verdict

The V03 stop is **VALID**.

The hosted job independently confirms success through:

1. locked dependency install;
2. production one-directory build;
3. approved staged Qt surface;
4. real frozen Qt GUI + QtPdf + OCP/CAD + Open3D no-network smoke;
5. exact stage inventory;
6. text-only pre-clearance artifact upload.

The job then fails exactly at redistribution clearance. Installer/final binary/source publication steps are skipped.

That is correct behavior.

## Exact V03 artifact facts

- build revision: `14a8e83e05e48cc70d141c65b82978c68bf2b19c`;
- Studio: `0.1.0`;
- staged files: **557**;
- staged bytes: **542,575,818**;
- mapped files: **555**;
- unresolved file rows: **167**;
- unresolved components: **7**;
- unresolved items: **59**;
- status: `BLOCKED`.

The 59 unresolved items consist of **7 component gates + 52 explicit file gates**.

### Seven unresolved components

- `cadquery-ocp-novtk 7.9.3.1.1`;
- `microsoft-windows-runtime`;
- `open3d 0.20.0`;
- `pyside6-addons 6.11.2`;
- `pyside6-essentials 6.11.2`;
- `shiboken6 6.11.2`;
- `unmapped-source-component`.

### Fifty-two explicit unresolved files

- **44** `api-ms-win-*.dll` files;
- **2** root `VCRUNTIME140*.dll` files;
- **1** `ucrtbase.dll`;
- **1** `base_library.zip`;
- **1** `libcrypto-3-x64.dll`;
- **1** `libssl-3-x64.dll`;
- **2** PackLab-generated evidence JSON files:
  - `qt-staged-surface.json`;
  - `windows-runtime-capabilities.json`.

These counts are taken from the exact downloaded hosted artifact, not from the builder narrative.

## What V03 successfully closed

Retain the V03 implementation.

It correctly closed several earlier ambiguities:

- PyInstaller standard analysis hooks are not treated as shipped merely because they ran;
- exact embedded runtime hooks are separated and mapped;
- Blinker, Colorama, ItsDangerous and Jinja2 metadata-only license gaps are normalized against exact staged license evidence;
- pre-clearance remains text-only;
- frozen production capability surface remains intact.

V03 improved the previous exact stage from `64 / 173 / 12` to `59 / 167 / 7`, but did not satisfy the zero-unresolved gate.

## Required V04 direction

The next remediation must stop treating all remaining work as one generic license problem. Close it by exact class:

1. **ownership/pruning** for Windows runtime, CPython/OpenSSL and PackLab-generated JSON;
2. **Qt/PySide/Shiboken module/source evidence** for the exact six Qt modules + approved plugins;
3. **OCP/OCCT + bundled wheel native dependencies** at file/component level;
4. **Open3D 0.20.0 native/third-party composition** for the exact staged native files.

The existing capability-complete PL-0349 V03 behavior must not regress.

## Owner-machine QtCore evidence

The owner-observed `QtCore` missing-procedure error remains a downstream portability concern. It does not invalidate the exact hosted PL-0349 capability smoke, but it is not considered closed for distributable installation.

The amended PL-0351 clean-artifact job remains mandatory after PL-0350 reaches engineering clearance.

## Verdict

`AUDITED_CHANGES_REQUIRED`

Resume with PL-0350 V04. Do not start PL-0351 until the exact hosted compliance gate is zero-unresolved and an unsigned audit installer exists.
