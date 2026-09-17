# PackLab Dependency and License Register

## Scope and review status

- **Evidence/review date:** 2026-09-17.
- **Document status:** governance and compliance register for implementation planning; it is **not legal advice**, a legal opinion, or final distribution approval.
- PackLab is currently a personal-use project, but its public repository and any future public source, installer, binary, bundled-engine, or service distribution require license discipline.
- License facts can change by version, component, build configuration, package format, and distribution method. The links below identify upstream evidence reviewed for this register; they do not substitute for version-specific evidence at release time.
- Transitive and optional third-party dependencies actually shipped must be inventoried and reviewed when versions/builds are pinned.
- **PL-0005 does not install, pin, vendor, bundle, link, modify, or distribute any dependency.** No dependency is claimed to be installed, operational, compatible, or cleared for redistribution by this document.
- Exact compatibility and version selection are later work. In particular, the Python OpenCascade binding is deliberately not selected here; PL-0289 owns that selection/compatibility decision.

## Register

The integration modes describe the intended PackLab boundary, not work completed in PL-0005.

| Dependency / capability | PackLab role | Planned integration mode | Current selection status | Primary license(s) | Version / pin status | Risk / attention |
| --- | --- | --- | --- | --- | --- | --- |
| [NextLevel](https://github.com/NextLevel/NextLevel) | iOS camera-control abstraction for Capture | Swift package behind PackLab-owned capture interfaces; NextLevel internals stay behind the camera-service boundary | Planned, not integrated; exact package version TBD | MIT, per upstream [LICENSE](https://github.com/NextLevel/NextLevel/blob/main/LICENSE) | Unpinned; later PL-0037 work | **LOW ATTENTION** |
| [COLMAP](https://github.com/colmap/colmap) | SfM, camera registration, and sparse reconstruction | External executable/engine behind a PackLab-owned SfM adapter and capability boundary | Planned, not installed or selected at a build/version | New BSD / 3-clause BSD for COLMAP itself, per the [official license page](https://colmap.github.io/license.html) | Unpinned; build configuration TBD | **MEDIUM ATTENTION** |
| [OpenMVS](https://github.com/cdcseacave/openMVS) | Dense point cloud, mesh reconstruction, refinement, and texturing | External engine behind a PackLab-owned dense-reconstruction adapter | Planned, not installed or selected at a build/version | GNU AGPL v3, per upstream [LICENSE](https://github.com/cdcseacave/openMVS/blob/master/LICENSE) and [COPYRIGHT.md](https://github.com/cdcseacave/openMVS/blob/master/COPYRIGHT.md) | Unpinned; build/configuration TBD | **HIGH LICENSE ATTENTION** |
| [Open3D](https://github.com/isl-org/Open3D) | Point-cloud/mesh analysis, cleanup, registration, measurement, and deviation support | Library use behind a PackLab-owned point-cloud/mesh analysis adapter | Planned, not installed or selected at a build/version | MIT, per upstream [LICENSE](https://github.com/isl-org/Open3D/blob/main/LICENSE) | Unpinned; build/package TBD | **LOW ATTENTION** |
| [OpenCV](https://github.com/opencv/opencv) | Computer vision for calibration, image analysis, masks, and capture/reconstruction support | Library use behind PackLab-owned analysis/calibration services and adapters | Planned, not installed or selected at a version | Version-sensitive: Apache License 2.0 for 4.5.0 and higher; 3-clause BSD for 4.4.0 and lower, per the [official licensing page](https://opencv.org/license/) | Unpinned; the later pinned version must drive the compliance record | **MEDIUM ATTENTION** |
| [PyTorch](https://github.com/pytorch/pytorch) | Optional/where-applicable ML analysis and segmentation capability | Python capability behind PackLab-owned analysis services; CPU/GPU build choice remains separate | Planned, not installed or selected at a package/build | Main project BSD-3-Clause, with package/build licensing represented separately by upstream [LICENSE](https://github.com/pytorch/pytorch/blob/main/LICENSE) and metadata | Unpinned; package, platform, and accelerator build TBD | **MEDIUM ATTENTION** |
| [Open CASCADE Technology (OCCT)](https://github.com/Open-Cascade-SAS/OCCT) | Engineering BREP/CAD operations and STEP capability | Native CAD kernel consumed through a PackLab-owned engineering/CAD adapter | Planned, not installed or selected at a version; binding is separate and TBD | LGPL 2.1 with the Open CASCADE special exception, per upstream [license](https://github.com/Open-Cascade-SAS/OCCT/blob/master/LICENSE_LGPL_21.txt) and [exception](https://github.com/Open-Cascade-SAS/OCCT/blob/master/OCCT_LGPL_EXCEPTION.txt); upstream also offers alternative commercial/contractual terms | Unpinned; exact OCCT version/build TBD | **MEDIUM ATTENTION** |
| Python OpenCascade binding layer | Python bridge to the OCCT engineering/CAD capability | Candidate Python binding behind the PackLab-owned CAD adapter; no binding API becomes a PackLab contract before selection | **TBD / NOT SELECTED**; PL-0289 owns selection and compatibility | TBD by the selected binding. A Python binding may have a license different from OCCT itself; OCCT’s license must not be assigned to every possible binding | No binding, package, or version is frozen | **TBD / NOT SELECTED** |
| [Blender](https://www.blender.org/about/license/) | Headless/external UV, material, and visual presentation/render automation; not dimensional truth | External/headless executable and controlled scripts at the Blender render boundary | Planned, not installed or selected at a version | GNU GPL family; Blender’s official guidance describes GPL-version/distribution nuances and separately discusses bundled components | Unpinned; executable and script/add-on scope TBD | **HIGH LICENSE ATTENTION** |
| [PySide6 / Qt for Python](https://doc.qt.io/qtforpython-6/) | Windows Studio desktop presentation and UI | Python UI library at the presentation boundary; UI does not own PackLab domain truth | Planned, not installed or selected at a version or licensing route | LGPLv3/GPLv3 and Qt commercial licensing routes, per [Qt for Python licensing](https://doc.qt.io/qtforpython-6/) and [Qt licensing](https://www.qt.io/development/qt-framework/qt-licensing) | Unpinned; modules, package, and route TBD | **MEDIUM ATTENTION** |

### Focused provenance and compliance notes

#### NextLevel

The canonical upstream project is `NextLevel/NextLevel`, and its upstream LICENSE identifies the library as MIT. PackLab intends to use it only as an iOS camera-control abstraction behind PackLab-owned capture interfaces. The exact Swift package version remains unpinned and is deferred to PL-0037 or later authorized iOS work. NextLevel’s own permissive license does not resolve the licenses of future Swift package dependencies or other contents selected by a pinned package/build; those contents require review.

#### COLMAP

COLMAP’s official license page says that COLMAP itself is under the new BSD license (the 3-clause BSD terms shown there). The same page explicitly says that third-party dependencies are separately licensed and that building COLMAP with those dependencies may affect the resulting COLMAP license. PackLab therefore records COLMAP as an external SfM/sparse-reconstruction engine behind an adapter, but does not treat the core BSD terms as automatic clearance for every COLMAP binary or build. The external-process boundary is an architectural integration record, not a legal conclusion.

#### OpenMVS

The canonical upstream is `cdcseacave/openMVS`; its repository identifies the project as AGPL-3.0 and links its LICENSE/COPYRIGHT evidence. PackLab records OpenMVS as the planned external dense-reconstruction boundary and classifies it **HIGH LICENSE ATTENTION**. Any future distribution, bundling, modification, linking, closed-source/commercial product plan, or network/service deployment involving OpenMVS requires explicit license and architecture review. This register does not conclude that a future PackLab model is automatically compliant or automatically impossible; the actual integration and distribution facts must be analyzed before release.

#### Open3D

Open3D’s canonical repository LICENSE identifies the project as MIT. The upstream repository also maintains a [third-party library inventory](https://github.com/isl-org/Open3D/blob/main/3rdparty/README.md), which demonstrates why a permissive primary license does not remove the need to review the libraries and build/package configuration actually used or shipped. PackLab keeps Open3D behind its point-cloud/mesh analysis boundary and leaves the exact version/build unpinned.

#### OpenCV

OpenCV’s official licensing page states that OpenCV 4.5.0 and higher use Apache License 2.0, while OpenCV 4.4.0 and lower use the 3-clause BSD license. PackLab has not selected a version, so this register intentionally preserves the distinction rather than flattening OpenCV to one license. The later pinned version, modules, build options, and shipped contents must drive the final compliance record. The canonical source repository and its [LICENSE](https://github.com/opencv/opencv/blob/4.x/LICENSE) remain useful version-specific evidence.

#### PyTorch

The main PyTorch project’s upstream LICENSE provides the BSD-3-Clause-style terms for the main project. PyTorch’s upstream packaging metadata also says that the installed package license expression can include Apache-2.0, Apache-2.0 with LLVM exception, BSD-2-Clause, BSD-3-Clause, BSL-1.0, and MIT, and its `license-files` configuration covers the project and third-party license files. PackLab therefore records the main project as BSD-3-Clause while separately requiring a package/build/NOTICE/transitive review. It must not describe a future shipped PyTorch graph as simply “BSD” without inspecting the pinned artifact and its included notices.

Authoritative evidence: [PyTorch LICENSE](https://github.com/pytorch/pytorch/blob/main/LICENSE), [package metadata in pyproject.toml](https://github.com/pytorch/pytorch/blob/main/pyproject.toml), and upstream [NOTICE](https://github.com/pytorch/pytorch/blob/main/NOTICE).

#### Open CASCADE Technology (OCCT)

OCCT’s canonical repository states that the open-source OCCT distribution is under LGPL version 2.1 with a special exception defined in `OCCT_LGPL_EXCEPTION.txt`, with the complete license in `LICENSE_LGPL_21.txt`. The same upstream README identifies commercial licensing or a contractual agreement as an alternative option; PL-0005 does not select or purchase that option. OCCT is recorded as the engineering BREP/CAD/STEP capability. Its license and exception are separate from the license of any Python binding and from licenses of other libraries in a packaged build.

Authoritative evidence: [OCCT README/license summary](https://github.com/Open-Cascade-SAS/OCCT), [LGPL-2.1 license text](https://github.com/Open-Cascade-SAS/OCCT/blob/master/LICENSE_LGPL_21.txt), and [OCCT special exception](https://github.com/Open-Cascade-SAS/OCCT/blob/master/OCCT_LGPL_EXCEPTION.txt).

#### Python OpenCascade binding layer

No Python binding is selected by PL-0005. **TBD / NOT SELECTED** is the current selection status, and PL-0289 remains the binding selection/compatibility task. A binding is its own project and may use a license different from OCCT; it does not inherit OCCT’s LGPL-2.1-plus-exception terms merely because it wraps OCCT. For provenance only, [pythonocc-core](https://github.com/tpaviot/pythonocc-core) is a candidate example, not a PackLab choice; its upstream page reports LGPL-3.0 and links its own [LICENSE](https://github.com/tpaviot/pythonocc-core/blob/master/LICENSE). Any candidate must be audited separately for its source, generated wrapper, native-library, wheel, and transitive contents before selection.

#### Blender

Blender’s official license page describes Blender software as GNU GPL, says source developed at blender.org is by default GNU GPL version 2 or later, and explains that the components together are compatible under GPLv3-or-later terms for Blender binary distribution. The same page identifies other component licenses, so a pinned distribution still needs component evidence. PackLab uses Blender headlessly for UV/material/render/presentation automation; Blender does not own Scan Master or Design Model dimensional truth. Blender’s guidance says published Python scripts/add-ons using its API must use a GPL-compatible license, so those scripts require review if distributed. Blender’s official page separately states that user-created artwork, images, movies, `.blend` files, and other output data are free for the creator to use; rendered output does not automatically become GPL merely because Blender created it.

#### PySide6 / Qt for Python

Official Qt for Python documentation says PySide6 and Shiboken6 are available under LGPLv3/GPLv3 and the Qt commercial license. Qt’s licensing page describes open-source and commercial routes and the obligations associated with choosing between them. PackLab records PySide6 as the Windows Studio presentation layer; it does not own domain truth. Qt modules, plugins, bundled components, and third-party contents can have additional or different licensing constraints. Final packaging must review the actual modules shipped, notices, and applicable LGPL/GPL or commercial-route obligations, including relocation/relinking requirements where applicable. PackLab has not purchased or selected a commercial Qt license, and proprietary distribution is not automatically cleared merely because LGPL is available.

## Risk / attention classification

These labels are project-governance triage, not legal opinions:

| Classification | Meaning |
| --- | --- |
| **LOW ATTENTION** | A permissive primary license is identified, but required notices and transitive/build review still apply. |
| **MEDIUM ATTENTION** | Version, build, module, package, or licensing-route choices materially affect obligations and must be reviewed before release. |
| **HIGH LICENSE ATTENTION** | Strong-copyleft or architecture/distribution choices require explicit review before distribution, bundling, modification, linking, or service deployment. |
| **TBD / NOT SELECTED** | The component choice itself is not frozen, so its license and compatibility cannot yet be finalized. |

## Architecture and ownership invariants

- External engines remain behind PackLab-owned adapters and capability boundaries. Recording an external executable or library boundary does not by itself prove a legal conclusion; the mode is recorded because it affects later compliance review.
- NextLevel remains behind PackLab-owned iOS capture interfaces.
- PySide6 is a presentation/UI dependency; PySide6 widgets do not own PackLab domain or project truth.
- Blender consumes approved geometry, artwork, and material data for visual presentation; it does not own dimensional or engineering truth.
- The license register does not change Scan Mesh, Scan Master, or Design Model ownership. A render, mesh, or CAD/export artifact remains distinct from the relevant PackLab source of truth.

## Distribution-scenario review matrix

The matrix identifies re-review triggers. It is not a legal determination that any scenario is permitted or prohibited.

| Scenario | What must be re-reviewed before proceeding |
| --- | --- |
| Personal/local use only | Record the exact local versions/builds and preserve notices for anything retained or shared; still review transitive components and local package terms. This scenario does not make future public distribution obligations disappear. |
| Public source repository | Review every source dependency and committed script/resource, preserve required copyright/license notices, check repository-facing licenses and candidate binding terms, and keep private scans, credentials, and confidential supplier assets out of Git. |
| Distributing a PackLab Windows installer/binary | Audit the exact packaged PySide6/Qt modules and notices, all bundled/runtime libraries, executable discovery/download behavior, and any Blender/COLMAP/OpenMVS/OCCT components. Confirm the selected licensing route and any applicable source, relinking, attribution, or offer obligations before release. |
| Bundling third-party binaries with PackLab | Inventory each binary and its build configuration, transitive/optional contents, license/NOTICE files, source-availability requirements where applicable, and whether bundling changes the integration analysis. OpenMVS/AGPL, OCCT, COLMAP dependencies, PyTorch, Qt, and Blender require explicit component-level review. |
| Modifying third-party source | Preserve upstream notices and change records, identify the exact source revision, review obligations for the modified component and its transitive contents, and confirm the distribution/source-availability path before publishing binaries or source. OpenMVS and Blender changes require particular attention. |
| Network/service deployment involving possible AGPL software | Reassess whether and how OpenMVS is used, whether the service interaction or modified/bundled code triggers additional obligations, what source/offer and notice path is needed, and whether the architecture should change. Obtain an explicit review before exposing such a service. |

## Future-release compliance checklist

Before any public source, installer, binary, bundled-engine, or service release, the owner/release process should:

- [ ] Pin the exact dependency version, commit, package, and build configuration actually used.
- [ ] Save upstream LICENSE/COPYRIGHT/NOTICE evidence for each pinned version/build.
- [ ] Inventory transitive and optional dependencies actually shipped, including package metadata and bundled native libraries.
- [ ] Record whether each dependency is linked, invoked as an external executable, bundled, modified, or downloaded separately.
- [ ] Preserve required copyright, license, attribution, and NOTICE files in the relevant source and binary distributions.
- [ ] Review source-offer/source-availability obligations for copyleft components where applicable.
- [ ] Inspect the PySide6/Qt modules, plugins, and third-party contents actually shipped and document the selected licensing route.
- [ ] Review any distributed Blender Python scripts/add-ons for GPL-compatible licensing under Blender’s guidance.
- [ ] Perform an explicit OpenMVS integration/distribution review, including AGPL implications for bundling, modification, linking, and network/service deployment.
- [ ] Review the chosen Python OpenCascade binding separately from OCCT; do not reuse OCCT’s license as the binding’s license.
- [ ] Confirm that private scans, confidential supplier files, credentials, signing material, and proprietary production artwork are excluded from the release.
- [ ] Treat this register as governance evidence, not legal counsel; obtain appropriate legal review for a real distribution decision.

## Limitations and deferred decisions

This register is a version-agnostic planning record. No dependency is installed, pinned, vendored, bundled, linked, modified, or distributed by PL-0005. Exact compatibility, package contents, platform builds, transitive inventories, and release notices remain unverified until the relevant later tasks select and validate them. The Python OpenCascade binding remains **TBD / NOT SELECTED** pending PL-0289.
