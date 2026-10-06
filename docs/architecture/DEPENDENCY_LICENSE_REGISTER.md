# PackLab Dependency and License Register

## Scope and review status

- **Evidence/review date:** 2026-10-01.
- **Document status:** governance and compliance register for implementation planning; it is **not legal advice**, a legal opinion, or final distribution approval.
- PackLab is currently a personal-use project, but its public repository and any future public source, installer, binary, bundled-engine, or service distribution require license discipline.
- License facts can change by version, component, build configuration, package format, and distribution method. The links below identify upstream evidence reviewed for this register; they do not substitute for version-specific evidence at release time.
- Transitive and optional third-party dependencies actually shipped must be inventoried and reviewed when versions/builds are pinned.
- PL-0135 selects PySide6 `>=6.8,<7` for the Windows Studio presentation boundary. The exact lockfile resolution is the reproducibility record; this register does not constitute distribution approval.
- Exact compatibility and version selection are later work. In particular, the Python OpenCascade binding is deliberately not selected here; PL-0289 owns that selection/compatibility decision.

## Register

The integration modes describe the intended PackLab boundary, not work completed in PL-0005.

| Dependency / capability | PackLab role | Planned integration mode | Current selection status | Primary license(s) | Version / pin status | Risk / attention |
| --- | --- | --- | --- | --- | --- | --- |
| [NextLevel](https://github.com/NextLevel/NextLevel) | iOS camera-control abstraction for Capture | Swift package behind PackLab-owned capture interfaces; NextLevel internals stay behind the camera-service boundary | Planned, not integrated; exact package version TBD | MIT, per upstream [LICENSE](https://github.com/NextLevel/NextLevel/blob/main/LICENSE) | Unpinned; later PL-0037 work | **LOW ATTENTION** |
| [COLMAP](https://github.com/colmap/colmap) | SfM, camera registration, and sparse reconstruction | External executable/engine behind a PackLab-owned SfM adapter and capability boundary | Planned, not installed or selected at a build/version | New BSD / 3-clause BSD for COLMAP itself, per the [official license page](https://colmap.github.io/license.html) | Unpinned; build configuration TBD | **MEDIUM ATTENTION** |
| [OpenMVS](https://github.com/cdcseacave/openMVS) | Dense point cloud, mesh reconstruction, refinement, and texturing | External engine behind a PackLab-owned dense-reconstruction adapter | Planned, not installed or selected at a build/version | GNU AGPL v3, per upstream [LICENSE](https://github.com/cdcseacave/openMVS/blob/master/LICENSE) and [COPYRIGHT.md](https://github.com/cdcseacave/openMVS/blob/master/COPYRIGHT.md) | Unpinned; build/configuration TBD | **HIGH LICENSE ATTENTION** |
| [Open3D](https://github.com/isl-org/Open3D) | Point-cloud/mesh analysis, cleanup, registration, measurement, and deviation support | Python library behind the PackLab-owned `geometry_adapter` boundary; downstream contracts use PackLab-owned values | **SELECTED for PL-0225**: `open3d==0.20.0`, CPython 3.12 Windows x86-64 wheel; exact artifact evidence is linked below | MIT for Open3D; wheel also bundles oneTBB 2021.12.0 (Apache-2.0) and includes separately inventoried web-extension notices | Exact wheel SHA-256 and locked Python dependency closure recorded in `PL-0225_OPEN3D_WINDOWS_CP312_LICENSE_EVIDENCE_V01.md`; no runtime auto-download | **MEDIUM ATTENTION** |
| [OpenCV](https://github.com/opencv/opencv) | Computer vision for calibration, image analysis, masks, and capture/reconstruction support | Library use behind PackLab-owned analysis/calibration services and adapters | Planned, not installed or selected at a version | Version-sensitive: Apache License 2.0 for 4.5.0 and higher; 3-clause BSD for 4.4.0 and lower, per the [official licensing page](https://opencv.org/license/) | Unpinned; the later pinned version must drive the compliance record | **MEDIUM ATTENTION** |
| [PyTorch](https://github.com/pytorch/pytorch) | Optional/where-applicable ML analysis and segmentation capability | Python capability behind PackLab-owned analysis services; CPU/GPU build choice remains separate | Planned, not installed or selected at a package/build | Main project BSD-3-Clause, with package/build licensing represented separately by upstream [LICENSE](https://github.com/pytorch/pytorch/blob/main/LICENSE) and metadata | Unpinned; package, platform, and accelerator build TBD | **MEDIUM ATTENTION** |
| [SAM 2](https://github.com/facebookresearch/sam2) | V1 promptable image segmentation for M08 object masks | Local PyTorch model behind PackLab `SegmentationBackend`; no hosted API | **SELECTED for PL-0186**: SAM 2.1 Hiera Base+; upstream revision `2b90b9f5ceec907a1c18123530e92e794ad901a4`; checkpoint `sam2.1_hiera_base_plus.pt`; config `configs/sam2.1/sam2.1_hiera_b+.yaml` | Apache License 2.0 for reviewed repository source; checkpoint provenance is separately pinned by source/hash during PL-0186 | Checkpoint official source approved; SHA-256, exact PyTorch/torchvision/runtime artifacts must be recorded during PL-0186 before acceptance | **MEDIUM ATTENTION** |
| [Open CASCADE Technology (OCCT)](https://github.com/Open-Cascade-SAS/OCCT) | Engineering BREP/CAD operations and STEP capability | Native CAD kernel consumed through a PackLab-owned engineering/CAD adapter | **Selected for PL-0289:** OCCT 7.9.3 in `cadquery-ocp-novtk==7.9.3.1.1`, Windows x86-64 / CPython 3.12 wheel | LGPL 2.1 with the Open CASCADE special exception, per upstream [7.9.3 license](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_9_3/LICENSE_LGPL_21.txt) and [7.9.3 exception](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_9_3/OCCT_LGPL_EXCEPTION.txt); upstream also offers alternative commercial/contractual terms | Exact `TKernel` DLL `FileVersion` and `ProductVersion` observed as 7.9.3; `OCP.__version__` observed as 7.9.3.1. Wheel bundles native libraries and does not include the OCCT license/exception texts | **HIGH LICENSE ATTENTION** |
| Python OpenCascade binding layer | Python bridge to the OCCT engineering/CAD capability | Selected binding behind a PackLab-owned CAD adapter; callers must not take a dependency on binding-owned objects | **Selected for PL-0289:** `cadquery-ocp-novtk==7.9.3.1.1`; transitive `cadquery-ocp-proxy==7.9.3.1.1`; exact pin in `pyproject.toml` and `uv.lock` | Binding source project is [OCP](https://github.com/CadQuery/OCP), Apache-2.0; the wheel reports Apache-2.0 but omits a license file. This is separate from the bundled OCCT 7.9.3 LGPL-2.1-plus-exception and all other bundled native components | Windows x86-64 / CPython 3.12 wheel: 46,364,919 bytes, SHA-256 `5d22339cdaac64c396f0658de8728915acfac9b868406f0078e52f50a3c25c65`; PyPI checksum independently matched downloaded wheel. PyPI reports upload via twine 6.2.0 and no Trusted Publishing attestation. Wheel contains 70 DLLs totaling 64,872,176 bytes; native component license/notice inventory and redistribution packaging remain a release gate | **HIGH LICENSE / REDISTRIBUTION ATTENTION** |
| [Blender](https://www.blender.org/about/license/) | Headless/external UV, material, and visual presentation/render automation; not dimensional truth | External/headless executable and controlled scripts at the Blender render boundary | Planned, not installed or selected at a version | GNU GPL family; Blender’s official guidance describes GPL-version/distribution nuances and separately discusses bundled components | Unpinned; executable and script/add-on scope TBD | **HIGH LICENSE ATTENTION** |
| [PySide6 / Qt for Python](https://doc.qt.io/qtforpython-6/) | Windows Studio desktop presentation and UI | Python UI library at the presentation boundary; UI does not own PackLab domain truth | Selected for PL-0135; runtime range `>=6.8,<7` and exact resolution in `uv.lock` | LGPLv3/GPLv3 and Qt commercial licensing routes, per [Qt for Python licensing](https://doc.qt.io/qtforpython-6/) and [Qt licensing](https://www.qt.io/development/qt-framework/qt-licensing) | Declared and locked for Python 3.12 | **MEDIUM ATTENTION** |

| [OpenReality](https://github.com/reality-opened/openreality) | Reference architecture for object-centric reconstruction, mask-to-3D lifting, provenance and optional generated-object lanes | **Reference only**; PackLab does not take a runtime dependency by this record | Reviewed at public commit `4d93d5f5b75166a43f0fd64b7d44acc12a56907f`; no package/binary selected | BSD-2-Clause for the OpenReality repository itself; separately fetched models retain their own licenses | Reference commit pinned in `OPENREALITY_INTEGRATION_ARCHITECTURE.md`; no vendor lock-in permitted | **MEDIUM ATTENTION** |
| [VGGT](https://github.com/facebookresearch/vggt) | Candidate future neural reconstruction backend | Future M19 research only behind PackLab `ReconstructionBackend`; not a V1 dependency | **NOT INSTALLED / NOT SELECTED**. Original `VGGT-1B` checkpoint forbidden for commercial PackLab; `VGGT-1B-Commercial` or successor requires separate acceptance and hash/version pin | Custom VGGT License. Upstream states only the separately released commercial checkpoint permits commercial use; original checkpoint remains non-commercial | Exact checkpoint, license acceptance, restrictions, runtime and redistribution path must be recorded by PL-0436 before any use | **HIGH LICENSE ATTENTION** |
| [SAM 3D Objects](https://github.com/facebookresearch/sam-3d-objects) | Candidate future AI visual-reference completion | Future `AI_VISUAL_REFERENCE` only; must never become measurement or Scan Master authority | **NOT INSTALLED / NOT SELECTED** | Custom SAM License with trade-control/acceptable-use restrictions | PL-0435 must pin code/checkpoint/license and enforce generated-authority isolation | **HIGH LICENSE / AUTHORITY ATTENTION** |
| [TRELLIS](https://github.com/microsoft/TRELLIS) | Candidate future image-conditioned 3D visual-reference generation | Future `AI_VISUAL_REFERENCE` only | **NOT INSTALLED / NOT SELECTED** | MIT for TRELLIS models and majority of project code per upstream; some submodules carry separate licenses | PL-0435 must inventory enabled submodules/checkpoints and keep outputs non-authoritative | **MEDIUM ATTENTION** |

## CI workflow tooling

- Reviewed 2026-10-06: [`actions/cache` v6.1.0](https://github.com/actions/cache/tree/55cc8345863c7cc4c66a329aec7e433d2d1c52a9), pinned to commit `55cc8345863c7cc4c66a329aec7e433d2d1c52a9` in `.github/workflows/windows-python-quality.yml`. The upstream repository is MIT-licensed. It is used only to cache the uv package/download cache at `${{ runner.temp }}/uv-cache`, keyed by runner OS/architecture, Python 3.12, uv 0.11.26, and `uv.lock`. It does not cache `.venv`, project/library/reconstruction outputs, or credentials. Cache restore does not replace `uv lock --check` or `uv sync --locked`.
- This is CI tooling only; it is not a PackLab runtime dependency and is not included in Studio, Capture, or a distributable artifact. The Windows hosted runner must satisfy the upstream action runtime requirements.
- Reviewed 2026-10-06: PyInstaller `6.22.3` is pinned in the project `dev` dependency group and `uv.lock`; the upstream project documents GPL-2.0-or-later with an exception for generated applications, plus Apache-2.0 for specified files. Its locked `pyinstaller-hooks-contrib` dependency is `2026.8`; its upstream license distinguishes GPL-2.0-or-later standard hooks from Apache-2.0 runtime hooks. Exact locked dependency versions are in `uv.lock`. These are build-tool license facts only and do not clear any Python/native runtime files included in the PackLab Studio staging output; PL-0350 must inventory those files and notices before any redistribution decision.
- PyInstaller and its hooks are build tools, not PackLab runtime dependencies. The production build runs only on the declared Windows Actions runner. The staging output is not a release or redistribution approval.

### Focused provenance and compliance notes

#### NextLevel

The canonical upstream project is `NextLevel/NextLevel`, and its upstream LICENSE identifies the library as MIT. PackLab intends to use it only as an iOS camera-control abstraction behind PackLab-owned capture interfaces. The exact Swift package version remains unpinned and is deferred to PL-0037 or later authorized iOS work. NextLevel’s own permissive license does not resolve the licenses of future Swift package dependencies or other contents selected by a pinned package/build; those contents require review.

#### COLMAP

COLMAP’s official license page says that COLMAP itself is under the new BSD license (the 3-clause BSD terms shown there). The same page explicitly says that third-party dependencies are separately licensed and that building COLMAP with those dependencies may affect the resulting COLMAP license. PackLab therefore records COLMAP as an external SfM/sparse-reconstruction engine behind an adapter, but does not treat the core BSD terms as automatic clearance for every COLMAP binary or build. The external-process boundary is an architectural integration record, not a legal conclusion.

#### OpenMVS

The canonical upstream is `cdcseacave/openMVS`; its repository identifies the project as AGPL-3.0 and links its LICENSE/COPYRIGHT evidence. PackLab records OpenMVS as the planned external dense-reconstruction boundary and classifies it **HIGH LICENSE ATTENTION**. Any future distribution, bundling, modification, linking, closed-source/commercial product plan, or network/service deployment involving OpenMVS requires explicit license and architecture review. This register does not conclude that a future PackLab model is automatically compliant or automatically impossible; the actual integration and distribution facts must be analyzed before release.

#### Open3D

Open3D’s canonical repository LICENSE identifies the project as MIT. PL-0225 selected `open3d==0.20.0` after installing and importing the exact CPython 3.12 Windows x86-64 wheel in PackLab’s Windows environment and exercising point-cloud and triangle-mesh conversion. The selected wheel SHA-256, observed native files/build flags, embedded web-extension notices, and exact resolved Python dependency license metadata are recorded in [PL-0225 Open3D Windows/Python 3.12 artifact evidence](evidence/PL-0225_OPEN3D_WINDOWS_CP312_LICENSE_EVIDENCE_V01.md). The upstream [`v0.20.0` third-party inventory](https://github.com/isl-org/Open3D/blob/v0.20.0/3rdparty/README.md) remains part of package-level review; the exact binary's native dependency licensing must be reconsidered before redistribution. PackLab uses Open3D only behind its PackLab-owned geometry adapter, with no Open3D class in domain contracts and no runtime download behavior. Selecting this local analysis dependency is not distribution approval.

#### OpenCV

OpenCV’s official licensing page states that OpenCV 4.5.0 and higher use Apache License 2.0, while OpenCV 4.4.0 and lower use the 3-clause BSD license. PackLab has not selected a version, so this register intentionally preserves the distinction rather than flattening OpenCV to one license. The later pinned version, modules, build options, and shipped contents must drive the final compliance record. The canonical source repository and its [LICENSE](https://github.com/opencv/opencv/blob/4.x/LICENSE) remain useful version-specific evidence.

#### SAM 2 / SAM 2.1 Base+

Owner decision ADR-0004 selects SAM 2.1 Hiera Base+ for PackLab V1 segmentation behind the PackLab-owned `SegmentationBackend` contract. The reviewed upstream SAM 2 repository revision is `2b90b9f5ceec907a1c18123530e92e794ad901a4`; its repository LICENSE is Apache License 2.0. The official upstream README publishes `sam2.1_hiera_base_plus.pt` and config `configs/sam2.1/sam2.1_hiera_b+.yaml` for the Base+ model.

The production checkpoint may be obtained only from Meta's official public checkpoint source documented in ADR-0004. PL-0186 must compute and persist the local checkpoint SHA-256, exact byte size, runtime/device facts and exact PyTorch/torchvision/SAM 2 artifact versions before independent acceptance. The checkpoint binary must not be committed to Git and the application must not silently auto-download it. CUDA is optional and capability-probed; CPU is a functional fallback without a performance guarantee. Upstream recommends WSL for Windows, so native-Windows versus WSL execution must be treated as a probed runtime fact rather than assumed support.

PL-0186 V02 explicitly acquired the approved public checkpoint on 2026-10-01 for provenance verification: `sam2.1_hiera_base_plus.pt`, 323606802 bytes, SHA-256 `a2345aede8715ab1d5d31b4a509fb160c5a4af1970f199d9054ccfb746c004c5`. The artifact remains outside Git. The PackLab 3.12.10 locked environment did not contain PyTorch, torchvision, or SAM 2, so no native model execution claim is made; the adapter reports this capability truthfully and has no download fallback.

Authoritative project decision: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md

#### PyTorch

The main PyTorch project’s upstream LICENSE provides the BSD-3-Clause-style terms for the main project. PyTorch’s upstream packaging metadata also says that the installed package license expression can include Apache-2.0, Apache-2.0 with LLVM exception, BSD-2-Clause, BSD-3-Clause, BSL-1.0, and MIT, and its `license-files` configuration covers the project and third-party license files. PackLab therefore records the main project as BSD-3-Clause while separately requiring a package/build/NOTICE/transitive review. It must not describe a future shipped PyTorch graph as simply “BSD” without inspecting the pinned artifact and its included notices.

Authoritative evidence: [PyTorch LICENSE](https://github.com/pytorch/pytorch/blob/main/LICENSE), [package metadata in pyproject.toml](https://github.com/pytorch/pytorch/blob/main/pyproject.toml), and upstream [NOTICE](https://github.com/pytorch/pytorch/blob/main/NOTICE).

#### Open CASCADE Technology (OCCT)

OCCT’s canonical repository states that the open-source OCCT distribution is under LGPL version 2.1 with a special exception defined in `OCCT_LGPL_EXCEPTION.txt`, with the complete license in `LICENSE_LGPL_21.txt`. The same upstream README identifies commercial licensing or a contractual agreement as an alternative option; PL-0005 does not select or purchase that option. OCCT is recorded as the engineering BREP/CAD/STEP capability. Its license and exception are separate from the license of any Python binding and from licenses of other libraries in a packaged build.

Authoritative evidence: [OCCT README/license summary](https://github.com/Open-Cascade-SAS/OCCT), [LGPL-2.1 license text](https://github.com/Open-Cascade-SAS/OCCT/blob/master/LICENSE_LGPL_21.txt), and [OCCT special exception](https://github.com/Open-Cascade-SAS/OCCT/blob/master/OCCT_LGPL_EXCEPTION.txt).

#### Python OpenCascade binding layer

PL-0289 selected `cadquery-ocp-novtk==7.9.3.1.1` for Windows x86-64 / CPython 3.12. Its exact PyPI wheel is `cadquery_ocp_novtk-7.9.3.1.1-cp312-cp312-win_amd64.whl` (46,364,919 bytes; SHA-256 `5d22339cdaac64c396f0658de8728915acfac9b868406f0078e52f50a3c25c65`). The digest matches the PyPI JSON release digest. PyPI identifies the upload as twine 6.2.0 without Trusted Publishing; this is artifact checksum evidence, not an authenticated build attestation. The matching wheel was installed with uv 0.11.26 under CPython 3.12.10 and passed import, revolve, loft, boolean-cut, tessellation, STEP write/read smoke checks. `OCP.__version__` reported `7.9.3.1`, and the native `TKernel` DLL reported `FileVersion` and `ProductVersion` 7.9.3.

The binding source project [OCP](https://github.com/CadQuery/OCP) is Apache-2.0. The wheel metadata also says Apache-2.0, but the exact wheel omits the license file present in the upstream source project. The bundled OCCT shared libraries remain LGPL-2.1-plus-exception; these terms are separate from the OCP binding license. The wheel contains 70 DLLs totaling 64,872,176 bytes. `cadquery-ocp-proxy==7.9.3.1.1` is the only Python dependency of the no-VTK wheel. The exact per-DLL third-party component/license and notice inventory is incomplete, and the wheel itself omits license notices; therefore packaging/distribution is not cleared. Before any installer or binary redistribution, inventory every DLL, add required notices/source-offer or relinking materials, and confirm the applicable licenses. The no-VTK wheel avoids pulling the full wheel's VTK/Matplotlib stack, but still bundles a substantial native kernel and supporting libraries.

The upstream [pythonocc-core](https://github.com/tpaviot/pythonocc-core) README documents conda-forge installation for Python 3.12 and reports LGPL-3.0. It did not resolve from the configured PyPI/uv index (`pythonocc-core==7.9.3` has no matching distribution), and conda was not available in this Windows environment, so it was not a feasible candidate for PackLab's locked uv runtime.

#### Blender

Blender’s official license page describes Blender software as GNU GPL, says source developed at blender.org is by default GNU GPL version 2 or later, and explains that the components together are compatible under GPLv3-or-later terms for Blender binary distribution. The same page identifies other component licenses, so a pinned distribution still needs component evidence. PackLab uses Blender headlessly for UV/material/render/presentation automation; Blender does not own Scan Master or Design Model dimensional truth. Blender’s guidance says published Python scripts/add-ons using its API must use a GPL-compatible license, so those scripts require review if distributed. Blender’s official page separately states that user-created artwork, images, movies, `.blend` files, and other output data are free for the creator to use; rendered output does not automatically become GPL merely because Blender created it.

#### PySide6 / Qt for Python

Official Qt for Python documentation says PySide6 and Shiboken6 are available under LGPLv3/GPLv3 and the Qt commercial license. Qt’s licensing page describes open-source and commercial routes and the obligations associated with choosing between them. PackLab records PySide6 as the Windows Studio presentation layer; it does not own domain truth. Qt modules, plugins, bundled components, and third-party contents can have additional or different licensing constraints. Final packaging must review the actual modules shipped, notices, and applicable LGPL/GPL or commercial-route obligations, including relocation/relinking requirements where applicable. PackLab has not purchased or selected a commercial Qt license, and proprietary distribution is not automatically cleared merely because LGPL is available.


#### OpenReality / neural and generated-3D references

OpenReality is an architecture reference, not a blanket license for every model its self-host stack can fetch. PackLab must treat repository code, model code and model checkpoints as separate compliance units.

- Reference architecture: https://github.com/reality-opened/openreality
- PackLab integration contract: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md
- Official VGGT commercial-checkpoint distinction: https://github.com/facebookresearch/vggt/blob/main/README.md and https://github.com/facebookresearch/vggt/blob/main/LICENSE.txt
- SAM 3D Objects license: https://github.com/facebookresearch/sam-3d-objects/blob/main/LICENSE
- TRELLIS license and submodule caveat: https://github.com/microsoft/TRELLIS/blob/main/README.md and https://github.com/microsoft/TRELLIS/blob/main/LICENSE

No generated-3D model license review can substitute for PackLab's geometry-authority rules. Even a commercially usable model remains `AI_VISUAL_REFERENCE` unless a separate audited architecture explicitly changes that contract.

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

This register records planning and selection evidence, not a legal determination. PL-0289 selected and locked one Python OpenCascade binding after Windows/CPython/uv installation and capability checks. The exact transitive native component/license inventory and redistribution notices remain unresolved; do not treat the dependency selection as installer/binary redistribution clearance. Preserve this gate through later M13 work and before any release packaging.
