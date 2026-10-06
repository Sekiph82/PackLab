# PL-0349 - Codex Prompt V02

Task: **Make the frozen Windows Studio production bundle runtime-capability complete**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001-R03**

This V02 supersedes the previously accepted PL-0349 V01 after exact PL-0350 staging evidence proved required dynamic runtime dependencies were absent.

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V03.md

Superseding PL-0349 audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CHATGPT_AUDIT_V02.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0349_CHATGPT_AUDIT_CRITERIA_V02.md

## Start rule

Synchronize the managed execution checkout non-destructively with latest `origin/main`. Preserve owner-local work. Verify live root `TASKS.md` authorizes M16-C001-R03 / PL-0349 V02.

Read:

- M16 partial audit V03;
- PL-0349 V01 prompt/criteria/log and superseding audit V02;
- PL-0350 V02 audit/artifact findings;
- current PyInstaller workflow/spec seam;
- `pyproject.toml`, `uv.lock`;
- `cad_adapter.py`, `geometry_adapter.py`;
- exact dependency/license register.

Do not edit root `TASKS.md`.

## Frozen finding

The current staged production build does not contain:

- `cadquery-ocp-novtk==7.9.3.1.1` / `OCP`;
- `open3d==0.20.0`.

They are direct runtime dependencies but are loaded through dynamic `importlib.import_module` calls, so the startup smoke did not detect the omission.

A production build that starts the GUI but loses PackLab CAD/geometry capabilities is not acceptable.

## Required runtime dependency contract

The frozen build must include all direct in-process production dependencies declared by PackLab unless an explicit architecture contract says a dependency is external/optional.

For the current project this includes at minimum:

- PackLab core + Studio packages;
- PySide/Qt runtime required by actual Studio imports;
- cadquery-ocp-novtk / OCP;
- Open3D 0.20.0.

Blender, COLMAP and OpenMVS remain external executables/capabilities and must not be bundled.

SAM/PyTorch/checkpoints remain outside this build unless separately authorized; no checkpoint/runtime download is introduced.

## PySide dependency narrowing

The current project source inspected by ChatGPT uses PySide QtCore, QtGui and QtWidgets surfaces and does not justify the broad PySide6 Addons meta-surface.

If repository-wide source/test inspection confirms that no PackLab production import requires Addons-only modules:

- replace the broad `PySide6>=6.8,<7` direct dependency with an exact locked minimal community package set, preferably `PySide6-Essentials==6.11.2`;
- preserve `PySide6` Python import compatibility;
- remove orphaned Addons/meta dependencies from the lock when safe;
- add a static contract test listing allowed direct PackLab Qt module imports.

Do not remove a Qt module merely for licensing convenience if a PackLab feature actually requires it. If a required production import proves Addons is needed, stop and record exact module/use instead.

## PyInstaller collection

Create an explicit, reviewable production packaging configuration/spec rather than relying on accidental static discovery.

### OCP

Collect the exact OCP Python extension/modules and native DLLs required for the accepted PackLab CAD capability. Do not include tests/examples/docs unrelated to runtime.

### Open3D

Collect the exact Open3D Python modules/native libraries/data required by `Open3DGeometryAdapter` and its accepted operations. Avoid Jupyter/examples/development assets when not needed.

### Qt

Collect only runtime modules/plugins/resources proven necessary by PackLab's source and packaged smoke tests. Do not collect the entire Qt distribution by default.

## Frozen packaged capability smoke

Extend the production executable with a **build-only noninteractive capability smoke** available only by explicit CLI argument/environment seam.

It must run from the frozen executable environment and return nonzero on failure.

At minimum it must prove:

### Qt
- QApplication/offscreen startup;
- StudioMainWindow construct/show/process/close.

### OCP/CAD
- PackLab CAD runtime diagnostics report AVAILABLE;
- exact binding version matches the locked selected binding;
- a bounded primitive/revolve/shape creation or equivalent accepted CAD probe succeeds through PackLab-owned APIs;
- one bounded tessellation or BREP-bound operation succeeds;
- no network/download.

### Open3D
- PackLab Open3D probe reports AVAILABLE;
- exact observed version is 0.20.0;
- a bounded PackLab-owned point-cloud/triangle-mesh conversion or simple geometry operation succeeds;
- no network/download.

Smoke output must be path-private and contain only component/version/capability facts.

Do not weaken PackLab probes to make frozen packaging pass.

## Runtime completeness manifest

Generate a path-free `windows-runtime-capabilities.json` bound to:

- PackLab build revision;
- Studio version;
- Python version;
- required production capability IDs;
- expected distribution/version;
- observed packaged status/version;
- smoke operation result;
- external/not-bundled dependencies with explicit architecture reason.

The manifest must fail the hosted build if any required in-process capability is absent.

## Validation

Run locally:

- `uv lock --check`;
- Ruff lint/format;
- `uv run --locked mypy core apps tools`;
- focused dependency/import/packaging tests;
- full locked pytest;
- compile checks;
- dependency/license/scope/privacy review.

Then run fresh hosted Windows build evidence.

Hosted PASS requires:

1. exact locked environment;
2. production PyInstaller staging build;
3. no-network GUI smoke;
4. frozen OCP/CAD capability smoke PASS;
5. frozen Open3D capability smoke PASS;
6. runtime completeness manifest with zero missing required in-process capabilities;
7. no private data/checkpoints/external engines;
8. no installer/release claim yet.

Record exact staged file count/bytes after the capability-complete build so PL-0350 V03 can inventory the correct bundle.

## Scope

This V02 may modify:

- production packaging workflow/spec/tooling;
- direct runtime dependency declarations/lock where required for truthful minimal Qt packaging;
- build-only smoke/provenance seams;
- focused packaging tests;
- dependency/license register for exact dependency changes.

Do not implement PL-0350 compliance closure, installer, PL-0351+, M17 or PL-0368 in this child.

## Handoff

Publish implementation/evidence commit(s), then:

`coordination/sessions/M16-C001/PL-0349_CODEX_LOG_V02.md`

in a distinct log-only commit.

Record:

- prior missing OCP/Open3D evidence;
- dependency changes;
- exact PySide/Qt direct dependency decision;
- packaging collection strategy;
- hosted run ID/URL;
- frozen capability smoke facts;
- runtime completeness manifest facts;
- full test/type/lint results;
- final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
