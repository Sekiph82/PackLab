# PL-0350 - Codex Prompt V06

Task: **Replace opaque native provenance with a PackLab-controlled provenance-complete Windows runtime, close the final Qt/Open3D source-evidence gates, and produce the unsigned audit installer**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001-R07**

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V08.md

V05 independent audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_V05.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V06.md

## Start rule

Synchronize the managed checkout non-destructively with latest `origin/main`. Preserve owner-local work.

Read:

- live root `TASKS.md`;
- partial audit V08;
- PL-0350 V05 audit/log/evidence;
- current Windows build workflow/spec/inventory/registry;
- PL-0225 Open3D evidence;
- current Qt module contract;
- OWNER DEV native Desktop EXE policy.

Do not edit root `TASKS.md`.

The owner Desktop native `PackLab.exe` is already independently accepted. Preserve it and refresh it after every published implementation.

## Frozen hosted baseline

Latest exact hosted production run:

https://github.com/Sekiph82/PackLab/actions/runs/37744258521

Pre-clearance artifact:

https://github.com/Sekiph82/PackLab/actions/runs/37744258521/artifacts/11534574864

Baseline:

- staged files: 511;
- staged bytes: 531,590,047;
- unresolved shipped-file rows: 115;
- unresolved components: 5;
- unresolved items: 6;
- missing source-package evidence: 5;
- missing notices: 0;
- forbidden Qt modules: 0;
- external prerequisites: 1;
- engineering status: BLOCKED.

The unresolved components are:

- `cadquery-ocp-novtk==7.9.3.1.1`;
- `open3d==0.20.0`;
- `pyside6-addons==6.11.2`;
- `pyside6-essentials==6.11.2`;
- `shiboken6==6.11.2`.

## Core V06 decision

Do **not** continue trying to reverse-guess exact third-party provenance from the current opaque prebuilt `cadquery-ocp-novtk` wheel.

For production Windows packaging, replace that opaque native provenance boundary with a **PackLab-controlled provenance-complete OCP/OCCT runtime build**.

The existing wheel may remain available for ordinary development if needed, but the production installer path must no longer depend on unidentified bundled native DLL provenance.

## Phase A - Define a machine-readable Windows native source lock

Create a canonical checked-in source lock, for example:

`tools/packaging/windows_native_source_lock.json`

Each native source/package record must contain:

- source/package ID;
- component name;
- exact version;
- exact build/revision where applicable;
- authoritative URL;
- expected SHA-256;
- license identifier;
- license/notice source;
- source-availability role;
- production purpose.

No wildcard build selectors such as `all*` are allowed in the final production lock.

Add schema validation and negative tests for missing hashes, mutable URLs, wildcard build selectors, duplicate IDs and unreferenced required sources.

## Phase B - Build a provenance-complete OCP/OCCT runtime

Preferred route:

1. pin the OCP source revision used by PackLab;
2. pin OCCT exactly to 7.9.3 source;
3. use an exact transitive native dependency lock;
4. build the Windows OCP binding/runtime in GitHub Actions from those pinned inputs;
5. stage only the native files actually required by PackLab's tested OCP capability.

Two acceptable implementation routes:

### Route B1 - source-built native stack

Build required OCP/OCCT/native dependencies from exact source archives.

### Route B2 - exact binary-package build inputs

Use exact upstream/conda-forge binary package artifacts only when every package has:

- exact package filename/build string;
- immutable authoritative URL;
- SHA-256;
- package metadata/license;
- corresponding source reference.

Then build OCP against that exact locked environment.

Do not use a solver result with unresolved/wildcard build identity.

### OCP production artifact

Create a path-private CI artifact or wheel produced by the workflow from the exact lock.

Record:

- input lock digest;
- OCP source revision;
- OCCT source revision/version;
- compiler/toolchain;
- exact produced file hashes;
- exact staged native dependency map.

The production PyInstaller job must consume the newly built controlled runtime rather than the opaque original wheel's bundled DLL set.

Do not commit built binaries to Git.

## Phase C - Minimize OCP/OCCT surface

PackLab uses OCP for engineering/CAD operations, not for unrelated visualization/media features.

Configure/build/stage the smallest OCCT/native surface that passes the real PackLab OCP smoke.

Where technically valid, disable optional OCCT third-party features PackLab does not use.

Do not remove functionality required by:

- revolve/solid creation;
- precise bounds;
- tessellation used by PackLab;
- STEP/BREP/STL or current accepted engineering export paths;
- existing locked tests.

After minimization, every staged OCP/OCCT/native file must map to an exact source/package lock record.

## Phase D - OCP native file manifest

Create a checked-in/generated manifest contract such as:

`tools/packaging/windows_ocp_controlled_runtime_manifest.json`

or an equivalent generated evidence artifact.

Every staged OCP runtime file must record:

- relative staged path;
- SHA-256;
- owning component;
- exact source/package ID;
- version/build/revision;
- license/notice references;
- why PackLab needs it.

The validator must fail bidirectionally:

- a staged OCP-owned file missing from the manifest;
- a manifest file absent from the stage;
- a source/package ID not present in the exact lock;
- source/package hash mismatch.

## Phase E - Qt/PySide/Shiboken source evidence closure

The Qt runtime surface is already bounded and the frozen capability smoke is green.

Do not rebuild Qt unless necessary.

Close source evidence for the exact retained official PySide/Qt 6.11.2 binary distribution using official source archives.

At minimum verify and bind:

- PySide/Shiboken 6.11.2 source;
- Qt Base 6.11.2;
- Qt SVG 6.11.2;
- Qt PDF 6.11.2.

For each source archive:

- authoritative Qt URL;
- expected SHA-256;
- observed SHA-256;
- exact retained staged modules/files covered.

Map the exact QtPdf/PDFium third-party notice/source surface from the exact 6.11.2 source/SBOM evidence.

Official project-published PySide/Qt wheels may be treated as `PROJECT_OFFICIAL_BINARY` only when exact wheel version/hash + corresponding official source version/hash + required third-party notices are all bound.

Do not claim commercial Qt authority.

## Phase F - Open3D source evidence closure

Keep exact official wheel identity:

- `open3d==0.20.0`;
- Windows CPython 3.12 wheel;
- SHA-256 `60010f21d44f13557ba007893bc13a69827faa4dc49eedd923d1397096c20d92`.

Bind it to:

- official Open3D v0.20.0 source archive/hash;
- official v0.20.0 third-party inventory;
- exact oneTBB source/license evidence for staged `tbb12.dll`;
- applicable notices for the exact official wheel/native surface.

The official Open3D wheel may be treated as `PROJECT_OFFICIAL_BINARY` only when exact release artifact identity and corresponding official source/third-party inventory are verified.

Do not flatten separately licensed third-party content to MIT.

## Phase G - Evidence classes

Make the inventory explicit about provenance class.

Allowed production classes:

- `PACKLAB_CONTROLLED_BUILD`;
- `PROJECT_OFFICIAL_BINARY`;
- `EXTERNAL_SYSTEM_PREREQUISITE`;
- `PACKLAB_OWNED`.

The opaque OCP wheel's unidentified bundled third-party DLLs must not qualify as `PROJECT_OFFICIAL_BINARY` merely because the wheel has a package name.

Every shipped native file must resolve to one accepted provenance class.

## Phase H - Hosted proof

Run a fresh hosted Windows build from the published implementation.

Required sequence:

1. validate exact source lock;
2. fetch exact source/package inputs and verify SHA-256;
3. build/assemble controlled OCP runtime;
4. install/overlay controlled OCP runtime into the production build environment;
5. build PackLab Studio;
6. assert bounded Qt surface;
7. run no-network frozen Qt GUI + QtPdf + OCP/CAD + Open3D smoke;
8. inventory exact stage;
9. upload text-only pre-clearance evidence;
10. enforce zero unresolved/missing/forbidden engineering gate.

Clearance requires:

- unresolved shipped files = 0;
- unresolved components = 0;
- missing notice = 0;
- missing source package = 0;
- forbidden Qt component = 0;
- engineering status = `CLEARED_FOR_PL0350_ENGINEERING_PACKAGING`;
- `legal_review_required=true`;
- `public_release_authorized=false`.

## Phase I - Installer

Only after clearance:

1. add final reviewed compliance texts;
2. re-inventory exact installer input;
3. rerun frozen capability smoke;
4. build the versioned unsigned Inno installer;
5. record installer SHA-256, bytes and tool version;
6. upload:
   - unsigned installer;
   - final text compliance evidence;
   - required corresponding-source audit artifacts.

No Git tag, GitHub Release, signing claim or V0.1 release.

## Phase J - Validation

Run:

- `uv lock --check`;
- changed-file Ruff/format;
- `uv run --locked mypy core apps tools`;
- focused source-lock/native-runtime/inventory tests;
- negative provenance tests;
- workflow contract tests;
- locked full pytest;
- compile checks;
- `git diff --check`;
- privacy/secrets/scope checks.

## GitHub-link publication contract

This is mandatory.

Every implementation/evidence/log file must be pushed to `origin/main`.

The final Codex handoff to the owner must contain **clickable GitHub HTTPS links**, not local paths.

At minimum provide GitHub links for:

- each implementation commit;
- evidence commit;
- PL-0350 V06 Codex log;
- R07 master Codex log;
- GitHub Actions quality run;
- GitHub Actions Windows build run;
- every relevant Actions artifact;
- prompt and audit-criteria files.

Do not output `C:\Users\...` links as owner handoff references.

Inside the published Codex logs, use GitHub URLs for referenced repository files/runs/artifacts wherever a clickable reference is useful.

## OWNER DEV native EXE standing delivery

After every published implementation/evidence commit and confirmed parity, run the accepted native EXE refresh.

Record the resulting `OWNER_DEV_EXE_READY` state in the child/master logs.

Do not regress to Desktop `.lnk` or PowerShell launch.

## Stop rule

If the controlled OCP runtime cannot be built reproducibly from exact pinned provenance, stop truthfully with exact hosted evidence.

Do not invent source versions.

Do not start PL-0351 until PL-0350 V06 produces a cleared unsigned installer.

## Handoff

Publish implementation/evidence commit(s), then publish:

`coordination/sessions/M16-C001/PL-0350_CODEX_LOG_V06.md`

as a distinct log-only commit.

If blocked, end the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`

and stop the master at `AWAITING_MILESTONE_AUDIT`.

If green, continue to PL-0351 under the master continuation.
