# PL-0349 - ChatGPT Independent Audit V03

Date: 2026-10-06
Decision: **AUDITED_PASS**
Task: **Capability-complete frozen Windows Studio with required QtPdf Addons support**

## Evidence inspected

- PL-0349 V03 prompt and audit criteria.
- Implementation commits:
  - `e159654dc76f93043703ed54758bbd5aeac5f349`
  - `9dccd1c00d2122f894b007b39ad33aef25b1ce42`
- PL-0349 V03 builder log.
- Exact diff from R04 baseline `17f4f806fbe159c6c5d09dece4c8498453890407`.
- Hosted Windows Studio run `37455141899`, job `112240797730`.
- Hosted Python quality run `37455141881`.
- Current production spec, Qt module contract, staged Qt assertion, frozen runtime bootstrap and capability smoke.

## Independent findings

### 1. Required QtPdf capability is preserved

PASS.

The build retains exact pinned:

- `PySide6-Essentials==6.11.2`;
- `PySide6-Addons==6.11.2`.

The staged direct/approved Qt surface is bounded to:

- QtCore;
- QtGui;
- QtWidgets;
- QtSvg;
- QtPdf;
- justified transitive QtNetwork.

The hosted staged-surface assertion reports exactly those extension/native modules plus the explicit approved plugin set. Virtual Keyboard and other forbidden/unapproved module families are absent.

### 2. Owner-observed QtCore loader failure was acted on

PASS for the V03 packaged-build seam.

The owner supplied Windows screenshots showing:

`ImportError: DLL load failed while importing QtCore: The specified procedure could not be found.`

The V03 implementation responded by:

- introducing a pre-import frozen-runtime DLL directory registration seam;
- registering staged PySide/Shiboken/Open3D/NumPy/OCP native directories before importing `packlab_studio.app`;
- excluding unrelated ICU DLLs that PyInstaller could collect from the build environment;
- keeping those fixes in the production entry/spec path.

This was not merely documented: the corrected hosted build at `9dccd1c` successfully passed Qt import/application startup after the fix.

### 3. Real packaged capability smoke

PASS.

Hosted run `37455141899` has these PL-0349 steps independently confirmed as SUCCESS:

- production one-directory staging build;
- staged Qt module assertion;
- packaged Studio no-network smoke;
- exact staging inventory.

The overall job later ends FAILURE only at the separate PL-0350 redistribution-clearance step.

The frozen smoke requires and verifies these groups:

- `qt_studio_gui`;
- `qt_vector_pdf`;
- `ocp_cad`;
- `open3d_geometry`.

Source inspection confirms those are real PackLab operations, not import-only placeholders:

- Studio QApplication + StudioMainWindow lifecycle;
- SVG → PDF export plus QPdfDocument parse/render;
- OCP revolve + precise bounds + tessellation;
- Open3D point-cloud round trip.

All are required to be PASS with network `NONE`.

### 4. OCP/Open3D packaging completeness

PASS.

Unlike the earlier incomplete V01 bundle, V03 explicitly collects dynamic OCP/Open3D runtime seams. Hosted evidence records:

- OCP binding `7.9.3.1.1`;
- OCCT kernel `7.9.3`;
- Open3D `0.20.0`.

The exact hosted stage is 557 files / 542,575,818 bytes and is now the correct input for PL-0350 V03.

### 5. Dependency and source scope

PASS.

The implementation changes are confined to the production packaging/runtime-completeness seam, tests, exact direct dependency pins and dependency-license register update. No PL-0351+, M17 or PL-0368 implementation is present.

### 6. User-machine portability caveat

RETAINED AS DOWNSTREAM GATE, not a PL-0349 failure.

The owner-observed QtCore screenshots cannot be cryptographically tied to the exact `9dccd1c` hosted stage because PL-0349 correctly did not upload the uncleared binary bundle. Therefore this audit cannot assert that the owner's failing executable was the same binary that passed hosted smoke.

A same-runner frozen smoke is necessary but not sufficient for final distributable portability.

Accordingly, PL-0351 is strengthened before its first execution to require a **separate clean Windows job** that downloads the exact cleared PL-0350 installer artifact, installs it into an isolated location and launches the installed application with a sanitized runtime environment. That downstream gate must catch QtCore/ICU/Shiboken procedure-resolution failures on artifact transfer/install.

## Validation evidence

Builder evidence records:

- local full suite: `1998 passed, 11 skipped, 1 deselected`;
- hosted quality: `2001 passed, 10 skipped, 1 deselected`;
- mypy: PASS;
- Ruff/format: PASS;
- hosted Qt/PDF/OCP/Open3D packaged smoke: PASS.

## Verdict

`AUDITED_PASS`

PL-0349 V03 is independently accepted. M16 may continue at PL-0350 V03. Final cross-host/install portability remains explicitly gated by the amended PL-0351 contract.
