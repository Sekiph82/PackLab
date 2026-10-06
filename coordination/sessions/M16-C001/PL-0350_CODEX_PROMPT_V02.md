# PL-0350 - Codex Prompt V02

Task: **Close Windows redistribution evidence gate and produce a versioned compliant installer artifact**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001-R02**

This V02 supersedes PL-0350 V01 after the independently accepted hard-stop.

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V02.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V02.md

## Start rule

Synchronize the managed execution checkout non-destructively with latest `origin/main`, preserve owner-local work, and verify live root `TASKS.md` authorizes M16-C001-R02 / PL-0350 V02.

Read before implementation:

- M16 partial audit V02;
- PL-0350 V01 prompt/criteria/blocker log;
- accepted PL-0347 V02, PL-0348 and PL-0349 audits/contracts;
- current `.github/workflows/windows-studio-build.yml`;
- `DEPENDENCY_LICENSE_REGISTER.md`;
- versioning/secrets policies;
- `pyproject.toml` and `uv.lock`.

Do not edit root `TASKS.md`.

## Frozen compliance rule

Do not upload or publish the current Windows application bundle merely to inspect it.

The exact hosted staging tree must be inspected **inside the Windows runner before teardown**.

Binary redistribution is allowed only after the new compliance validator reports exactly:

`unresolved_count = 0`

Until then:

- no PackLabStudio.exe upload;
- no DLL/PYD bundle upload;
- no installer upload;
- no release-ready claim.

## Required compliance inventory implementation

Add a deterministic PackLab-owned Windows redistribution inventory tool under the existing packaging tooling area.

It must inspect the exact PL-0349 staging tree and produce path-free canonical evidence.

### Required inventory input evidence

Use:

- exact staging tree;
- PyInstaller build metadata/TOC from the same build;
- exact locked Python environment;
- `importlib.metadata` distribution file metadata;
- PE/version metadata available on the runner;
- exact PackLab build revision and Studio semantic version;
- an explicit reviewed supplemental component/license registry only where installed distribution metadata is insufficient.

Do not infer component ownership from filename alone when exact source/TOC/distribution evidence exists.

### Required per-file inventory fields

For **every file** in the staged PackLabStudio directory record at minimum:

- safe relative POSIX path;
- SHA-256;
- byte length;
- file category;
- owning component/distribution or explicit composite component set;
- component version where available;
- mapping method/evidence type;
- PE FileVersion/ProductVersion/OriginalFilename/CompanyName when available for EXE/DLL/PYD;
- license identifier/status;
- required notice/license evidence references;
- unresolved reason if not fully mapped.

Canonical evidence must contain no runner/workspace absolute path, username, token or secret.

### Required component classes

At minimum classify/review actual shipped contents for:

- PackLab-owned code/resources;
- PyInstaller bootloader/runtime contribution;
- CPython runtime/stdlib;
- PySide6;
- PySide6-Essentials;
- PySide6-Addons if actually staged;
- Shiboken6;
- Qt DLLs/plugins actually staged;
- cadquery-ocp-novtk;
- cadquery-ocp-proxy;
- OCP binding files;
- OCCT DLLs actually staged;
- Open3D and its native contents if actually staged;
- NumPy/SciPy/other Python/native distributions actually staged;
- Microsoft/system runtime files if copied into the bundle;
- every other staged third-party file.

Do not assume all locked dependencies are shipped. The inventory is driven by the actual current staging tree.

## License/notice evidence

For each shipped component:

1. Prefer exact license/notice files delivered by the installed distribution:
   - dist-info `licenses/**`;
   - declared `License-File` entries;
   - `LICENSE*`, `LICENCE*`, `COPYING*`, `NOTICE*` files.
2. Record their exact component/version and SHA-256.
3. If the selected wheel/package omits required evidence, use a checked-in supplemental registry only with:
   - exact component/version;
   - authoritative upstream source/reference;
   - checked-in exact license/exception text;
   - SHA-256;
   - explicit reason supplemental evidence is required.
4. Never substitute one component's license for another.

### Qt/PySide rule

The repository currently contains no evidence of a commercial Qt license. Do not invent one.

The only currently evidence-backed route is the open-source Qt/PySide route documented by the exact installed packages/upstream evidence.

Inventory the actual Qt modules/plugins staged and include all required open-source license/notice evidence available for those exact components.

If the staged contents include a component whose redistribution route cannot be supported by reviewed evidence, leave it unresolved and stop.

Do not make a legal-compliance claim beyond the project engineering gate.

### OCP / OCCT rule

Keep the OCP binding license separate from OCCT.

For every staged OCP/OCCT DLL or native file:

- map it to exact installed distribution/build evidence;
- record version/file metadata and digest;
- package OCP binding license evidence;
- package exact OCCT LGPL-2.1 text and OCCT special-exception text from reviewed pinned evidence;
- record any additional staged native component separately.

If any staged native DLL cannot be mapped to reviewed component/license evidence, stop.

### Open3D/native rule

If Open3D files are staged:

- map exact staged files to the locked Open3D distribution;
- include Open3D's main license;
- collect/review packaged license files and exact upstream third-party inventory needed for the actually staged native artifact;
- do not describe the whole native binary as simply MIT when its bundled third-party notices require additional evidence.

If this mapping cannot be closed truthfully, stop.

## Compliance outputs

Generate, at minimum:

- `windows-redistribution-inventory.json`;
- `windows-component-summary.json`;
- `compliance-validation.json`;
- `THIRD_PARTY_NOTICES.txt`;
- `THIRD_PARTY_LICENSES/**`.

`compliance-validation.json` must include:

- schema version;
- PackLab build revision;
- Studio version;
- total staged file count/bytes;
- mapped file count;
- unresolved file/component count;
- required notice count;
- collected notice count;
- final status `CLEARED_FOR_PL0350_PACKAGING` or `BLOCKED`.

The validator must fail nonzero if any required file/component/notice is unresolved.

## Text-only hosted evidence artifact before binary publication

Add a SHA-pinned reviewed `actions/upload-artifact` action only if needed to make compliance evidence independently retrievable.

Before clearance, upload **only**:

- JSON/text compliance outputs;
- license/notice text files.

Do not include EXE, DLL, PYD, ZIP/PYZ application payloads, schemas, private data or installer binaries.

Use:

- `if-no-files-found: error`;
- explicit artifact name including build revision;
- temporary bounded retention, preferably 1 day until PL-0352 defines the general policy.

Record the action version/license in the dependency/license register.

## Installer generation

Only after the same hosted run validates `unresolved_count = 0`:

1. copy `THIRD_PARTY_NOTICES.txt` and `THIRD_PARTY_LICENSES/**` into the distributable staging tree;
2. re-run inventory/validation so the final installer input tree is itself accounted for;
3. build a deterministic Inno Setup installer using an explicitly selected/versioned build tool;
4. set installer `AppVersion` from canonical Studio semantic version;
5. include build revision in the output filename/provenance;
6. install only the production staged application and compliance texts;
7. exclude private scans, supplier files, PackLab project/library state, checkpoints, Blender/COLMAP/OpenMVS binaries and signing material;
8. record installer SHA-256/byte length/tool version.

No Git tag, GitHub Release, V0.1 release or signing claim is authorized.

### Binary artifact publication after clearance

After the compliance validator is green, the hosted workflow may upload the versioned installer and/or production staged bundle as a CI artifact for independent audit.

This is allowed only in the same or later run whose exact input tree has `CLEARED_FOR_PL0350_PACKAGING`.

Use explicit short retention until PL-0352 normalizes artifact policy.

Never upload an uncleared binary tree.

## Required validation

Run locally where applicable:

- `uv lock --check`;
- Ruff lint/format on changed Python;
- `uv run --locked mypy core apps tools`;
- focused inventory/compliance tests;
- workflow contract tests;
- locked full pytest;
- compile checks;
- `git diff --check`;
- dependency/license/scope/privacy review.

Then run a fresh hosted Windows production build.

The hosted run must prove:

1. exact production staging build;
2. no-network packaged smoke;
3. complete staging inventory generation;
4. zero unresolved files/components/notices;
5. compliance text-only evidence artifact publication;
6. versioned installer build;
7. final input-tree revalidation;
8. installer hash/size;
9. binary artifact upload only after clearance.

If any required redistribution item remains unresolved, stop truthfully and do not build/upload the installer.

## Handoff

Publish implementation/evidence commit(s), then publish:

`coordination/sessions/M16-C001/PL-0350_CODEX_LOG_V02.md`

as a distinct log-only commit.

Record:

- V01 blocker resolution;
- inventory tool and mapping method;
- exact component/version/license summary;
- any supplemental evidence;
- hosted run ID/URL;
- compliance evidence artifact name/ID;
- `unresolved_count`;
- installer name/version/hash/size if produced;
- binary artifact name/ID if publication is authorized;
- validation results;
- final local/origin/GitHub parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
