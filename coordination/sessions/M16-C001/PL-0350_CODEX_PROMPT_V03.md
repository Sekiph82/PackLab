# PL-0350 - Codex Prompt V03

Task: **Close redistribution evidence for the capability-complete Windows bundle and build an audit-only versioned installer**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001-R03**

This V03 supersedes PL-0350 V02 after exact hosted artifact analysis and must run only after PL-0349 V02 is builder-green.

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V03.md

PL-0350 V02 audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V02.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V03.md

## Start rule

Do not start this child unless:

- PL-0349 V02 has a published child log ending `READY_FOR_INDEPENDENT_AUDIT`;
- its fresh hosted Windows runtime-completeness smoke proves Qt + OCP/CAD + Open3D from the frozen application environment.

Synchronize safely with latest `origin/main`, preserve owner-local work, verify live root `TASKS.md` authorization, and do not edit root `TASKS.md`.

Read:

- M16 partial audit V03;
- PL-0349 V02 prompt/criteria/log;
- PL-0350 V02 prompt/criteria/log/audit;
- exact V02 hosted compliance artifact facts;
- dependency/license register;
- versioning/secrets policies.

## V02 diagnostic baseline

The corrected V02 hosted stage had:

- 283 files;
- 141,367,765 bytes;
- `unresolved_count=55`;
- 196 files carrying unresolved status;
- 7 unresolved component classes.

The 46 `unmapped-source-component` files were:

- 42 Windows API-set DLLs;
- 1 `ucrtbase.dll`;
- 1 `base_library.zip`;
- 2 OpenSSL 3.5.5 DLLs.

The same stage accidentally contained broad Qt/PySide content including Qt Virtual Keyboard, while omitting OCP/Open3D entirely.

V03 must inventory the **new capability-complete PL-0349 V02 stage**, not reuse these numbers as expected final contents.

## Engineering-gate semantics

This task is an engineering redistribution-evidence and packaging gate.

Do not write `legally_compliant=true` or equivalent.

The final validation must distinguish:

- `engineering_packaging_status`;
- `legal_review_required=true`;
- `public_release_authorized=false`.

A green PL-0350 V03 authorizes only short-lived unsigned CI artifacts for independent M16 audit. It does **not** authorize a Git tag, GitHub Release or public V0.1 release.

## A. Minimize the actual shipped Qt surface

Use the PL-0349 V02 exact dependency/import decision.

The final production stage must contain only Qt modules/plugins/resources required by PackLab's tested runtime features.

### Forbidden accidental Qt surface

Under the currently evidenced community/open-source route:

- fail if Qt Virtual Keyboard is staged;
- fail if any other Qt component that official Qt licensing identifies as GPL-only for open-source use is staged without separately accepted authority;
- fail if PySide6 Addons remains solely because the broad meta-package pulled it in and PackLab does not use it.

Official evidence starting points:

- https://doc.qt.io/qt-6/licensing.html
- https://www.qt.io/development/open-source-lgpl-obligations
- https://doc.qt.io/qtforpython-6/

Do not invent a commercial Qt license.

### Required retained Qt evidence

For every retained Qt/PySide/Shiboken module/plugin:

- exact staged file digest/version;
- exact owning module;
- applicable Qt/PySide license route;
- exact third-party attributions/notices relevant to that module/plugin;
- dynamic-library/replacement status.

Keep Qt DLLs dynamically replaceable.

Do not collapse all Qt files into one generic `LGPL` row.

## B. Qt/PySide corresponding source route for CI artifact

For this audit-only CI binary artifact, use a **source-copy route**, not a future promise invented on the owner's behalf.

For every retained LGPL-covered Qt/PySide/Shiboken component:

1. identify the exact corresponding official source package(s) for version 6.11.2;
2. use authoritative Qt source locations;
3. verify source archive SHA-256 against a pinned reviewed value;
4. record which retained binary modules each source archive covers;
5. upload the verified source archive(s) as a separate short-lived `packlab-windows-lgpl-source-<sha>` CI artifact only after the component mapping is complete.

At minimum this is expected to cover the exact retained Qt base/PySide/Shiboken source packages; include additional module source archives only if those modules are actually staged.

If exact official source archive provenance cannot be pinned and verified, stop.

The source artifact is audit evidence only. PL-0366/PL-0368 must later require durable source-availability handling for any real distribution.

## C. Remove Windows system/runtime redistribution from PackLab bundle

Do not redistribute Microsoft system/runtime DLLs just because PyInstaller collected them.

The final staged application should rely on an explicit supported Windows + Microsoft Visual C++ runtime prerequisite when technically valid.

### Remove from staged redistribution surface

After exact source/path validation and before final inventory, exclude bundled copies of:

- Windows API-set DLLs;
- `ucrtbase.dll`;
- `VCRUNTIME140*.dll`;
- `MSVCP140*.dll`;
- other MSVC/UCRT runtime files proven to be external runtime prerequisites rather than PackLab-owned dependencies.

Do not remove arbitrary Microsoft DLLs by CompanyName alone.

### Required prerequisite contract

Create a deterministic Windows prerequisite record and installer preflight:

- supported OS/architecture;
- required Microsoft Visual C++ Redistributable architecture;
- minimum runtime version derived from actual packaged native dependency requirements;
- official Microsoft download/help URL;
- no automatic download/install by PackLab CI/app/installer.

The Inno installer must fail with a clear prerequisite message when the required runtime is absent/outdated.

Fresh hosted frozen capability smoke must pass **after** pruning these bundled runtime files.

Authoritative evidence starting points:

- https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist/
- https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files
- https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution

Because PackLab will not redistribute those Microsoft binaries, do not mark them as shipped components in the final inventory.

## D. CPython base library and OpenSSL mapping

Fix the V02 unmapped classifications:

### base_library.zip

Map PyInstaller's `base_library.zip` to the exact CPython runtime and PSF license evidence.

### libcrypto/libssl

Map `libcrypto-3-x64.dll` and `libssl-3-x64.dll` to the exact CPython/OpenSSL binary provenance actually used.

Record:

- exact PE/OpenSSL version;
- source mapping from the installed Python runtime;
- Apache-2.0 license evidence for OpenSSL 3.x;
- any required OpenSSL notice/attribution evidence for the exact version.

Authoritative starting point:

- https://docs.python.org/3.12/license.html

Do not label OpenSSL as generic CPython-owned code.

## E. PyInstaller hooks-contrib shipped-vs-build distinction

Correct the V02 component model.

The `pyinstaller-hooks-contrib` package contains:

- standard hooks: GPL-2.0-or-later build-analysis code;
- runtime hooks: Apache-2.0 code that may be bundled with frozen applications.

Authoritative upstream evidence:

- https://github.com/pyinstaller/pyinstaller-hooks-contrib
- exact installed `pyinstaller_hooks_contrib-2026.8.dist-info/licenses/LICENSE`.

Do not mark the entire hooks-contrib distribution as shipped merely because standard hooks influenced Analysis.

Use PyInstaller Analysis/PKG/PYZ evidence to identify:

- build-only standard hooks: record as build tooling, not shipped component;
- exact runtime hook files actually embedded: map individually as shipped Apache-2.0 content.

If a standard GPL hook source itself is embedded in the application unexpectedly, treat it as an explicit blocker until correctly classified.

## F. Capability-complete OCP/OCCT mapping

The corrected PL-0349 V02 stage must now contain OCP/OCCT.

For every staged OCP/OCCT Python/native file:

- map exact source distribution/path;
- record file digest/version/PE metadata;
- separate OCP binding license from OCCT kernel license;
- include OCP Apache-2.0 evidence;
- include OCCT LGPL-2.1 text + OCCT special exception;
- identify any additional non-OCCT native library separately.

Do not infer that every DLL in the OCP wheel is OCCT solely from directory membership. Use exact names/version metadata and the already-recorded wheel evidence.

If any staged native file remains unmapped, stop.

For any LGPL source-availability obligation that applies to the distributed OCCT binary set, create verified exact corresponding source archive evidence as a companion CI source artifact or stop.

## G. Capability-complete Open3D mapping

The corrected PL-0349 V02 stage must now contain Open3D 0.20.0.

For the exact Windows wheel/staged native surface:

- map every staged Open3D/native file to the locked wheel;
- include Open3D main MIT license;
- use the existing PL-0225 exact wheel evidence;
- map actual bundled third-party/native contents against the exact Open3D 0.20.0 third-party inventory;
- collect required notices/license texts only for components actually present;
- identify any copyleft/source-availability requirement separately.

Do not call the whole native wheel simply `MIT` when staged third-party content has separate licenses.

If exact third-party mapping remains incomplete, stop.

## H. Final inventory schema

Upgrade compliance evidence so each staged file has:

- relative path;
- SHA-256;
- byte length;
- file category;
- owning component(s);
- component version;
- mapping evidence;
- PE metadata where applicable;
- license identifier/status;
- notice evidence refs;
- source-availability evidence/status where required;
- unresolved reason.

Add explicit external prerequisites separately; do not count them as shipped files.

The final validator must report at minimum:

- staged file count/bytes;
- mapped shipped file count;
- unresolved shipped file count;
- unresolved component count;
- forbidden Qt component count;
- external prerequisite count;
- required/collected notice counts;
- required/verified source-package counts;
- `engineering_packaging_status`;
- `legal_review_required=true`;
- `public_release_authorized=false`.

Installer generation requires:

- unresolved shipped files = 0;
- unresolved components = 0;
- forbidden Qt components = 0;
- missing notice = 0;
- missing required source package = 0;
- engineering status = `CLEARED_FOR_PL0350_ENGINEERING_PACKAGING`.

## I. Installer and artifacts

Only after the exact capability-complete final stage reaches the engineering clearance above:

1. add THIRD_PARTY_NOTICES and required license texts;
2. re-inventory exact installer input;
3. run frozen Qt/OCP/Open3D capability smoke again after all pruning/compliance additions;
4. build versioned unsigned Inno Setup installer;
5. verify prerequisite logic;
6. record installer hash/size/tool version;
7. upload short-lived audit artifacts:
   - unsigned installer;
   - final text compliance evidence;
   - required LGPL/source archive artifact(s).

Do not upload the raw application staging tree unless required for independent audit and separately authorized; the installer plus source/evidence artifacts are sufficient.

No Git tag/GitHub Release/V0.1 publication.

## Validation

Run:

- lock validation;
- Ruff/format;
- mypy;
- focused inventory/packaging/prerequisite tests;
- full locked pytest;
- compile checks;
- workflow contract tests;
- privacy/secrets/scope review.

Fresh hosted Windows run must prove:

- capability-complete PL-0349 V02 stage;
- post-prune Qt/OCP/Open3D capability smoke;
- zero unresolved/forbidden/missing-source engineering gate;
- text/source evidence artifacts;
- installer build;
- installer metadata/digest;
- no unauthorized release.

If any required mapping/source/notice remains unresolved, stop truthfully at PL-0350 V03.

## Handoff

Publish implementation/evidence commit(s), then:

`coordination/sessions/M16-C001/PL-0350_CODEX_LOG_V03.md`

as a distinct log-only commit.

Record exact before/after unresolved counts, retained Qt modules/plugins, removed system-runtime files, external prerequisite facts, OCP/Open3D inventory summary, source artifacts, hosted run/artifact IDs, installer facts if produced, full validation and final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
