# PL-0350 Official Generated Source ZIP — Read-Only Inspection Report

Date: 2026-10-12
Classification: **INCOMPATIBLE** with the current frozen PackLab `novtk` + 319-module build contract. The archive is a credible route to skip pywrap generation only if the module-count contract is reconciled and the native build is later authorized and validated.

## Authority and provenance

- Live authority at synchronized `origin/main`: root `TASKS.md` names this exact read-only check as the next action and says no native build or wheel substitution is authorized.
- Official release: [CadQuery/OCP 7.9.3.1.1](https://github.com/CadQuery/OCP/releases/tag/7.9.3.1.1), API metadata: [release JSON](https://api.github.com/repos/CadQuery/OCP/releases/tags/7.9.3.1.1).
- Release tag commit: `d69b064a3a604ebf245b1f3b14fb54c835a3a571`; `git ls-remote` resolved the exact tag to the same commit.
- PackLab `tools/packaging/windows_native_source_lock.json` pins OCP 7.9.3.1.1 to that same revision and pins the source archive separately. This release asset is an additional Windows generated-source artifact, not a replacement for that source-lock record without a future authorized change.
- Asset: `OCP_src_stubs_Windows.zip`, 6,481,047 bytes; GitHub release digest and independently measured SHA-256: `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`.
- ZIP central-directory inventory: 1,613 entries, 62,426,401 uncompressed bytes, all entries rooted at `OCP_src_stubs_Windows/`. The inspection found no absolute/traversal paths or Unix symlink entries. Inspection streamed ZIP members without extraction; the disposable scratch contained only the ZIP and a small inventory file and was removed afterward.
- SHA-256 of the sorted archive file manifest (`<member path> SP <member SHA-256>`, UTF-8 lines joined by LF): `33bd4ce107d3828f57c561741c4a97cbcb2db9416f0a673a2778aa3ace0d2277`.

## Archive inventory and generated module coverage

The archive contains:

- 319 module `.cpp` sources plus the `OCP.cpp` extension entry point (320 non-`_pre` `.cpp` files total);
- 319 companion `_pre.cpp` files;
- 319 `*_tmpl.hxx` headers;
- 324 nested `OCP-stubs/<module>/__init__.pyi` files and one root `OCP-stubs/__init__.pyi` index;
- `CMakeLists.txt`, `OCP_specific.inc`, `pystreambuf.h`, and `vtk_pybind.h`.

The 319 module IDs have one `.cpp`, one `_pre.cpp`, and one `*_tmpl.hxx` each. `OCP.cpp` has 638 registration calls: one enum registration and one module registration per ID. This verifies a 319-module generated-source inventory in the ZIP. It does not prove byte or semantic equivalence to PackLab's locally generated pywrap output.

The four VTK-specific module IDs present in that inventory are `IVtk`, `IVtkOCC`, `IVtkTools`, and `IVtkVTK`. The remaining module IDs are the other 315 of the 319 IDs recorded by the archive manifest. `OCP.cpp` assigns `OCP.__version__ = "7.9.3.1"`; the release/tag and package-lock version is `7.9.3.1.1`. This difference must be treated explicitly in any later runtime identity check.

Selected exact member sizes and SHA-256 values:

| ZIP member | Bytes | SHA-256 |
|---|---:|---|
| `OCP_src_stubs_Windows/CMakeLists.txt` | 2,483 | `c13d8d57ec3e91596e845de67308cf991abbdc0042edf2a9d8ada8f1afa9217b` |
| `OCP_src_stubs_Windows/OCP.cpp` | 44,975 | `7ea32f48b96d131b2581168a487afab67aab4da719ad785179a03fd32364aaf2` |
| `OCP_src_stubs_Windows/Adaptor2d.cpp` | 35,440 | `58a4d7ab3cbe7a907c4b0b7f0ef62fc48a754164876c179208bdbc0e5c6a2556` |
| `OCP_src_stubs_Windows/Adaptor2d_pre.cpp` | 3,107 | `5cbcbfdb4d228b5f1077d0b1bdd0bff2e2b711595e60f01497db8e52ffa3949d` |
| `OCP_src_stubs_Windows/Adaptor2d_tmpl.hxx` | 909 | `255a4e5142220b95c2ce6805a418c1b089b903b88aa9a8e407c8188cc43bc3fa` |
| `OCP_src_stubs_Windows/OCP_specific.inc` | 2,040 | `758421a6f0488c034924fee083e38126d00dfb8f6a98fdc9c005ab41674b4efe` |
| `OCP_src_stubs_Windows/pystreambuf.h` | 4,958 | `35c5bdf5577b1398d5cf9e8c0ee5e83fc4825b39495449cbf2b6199c1a64cf9f` |
| `OCP_src_stubs_Windows/vtk_pybind.h` | 3,355 | `341cf4d231c1fe10e2fdc4e2f3671cb529b0cf1918bd769d32cf3d8d6163ffb7` |
| `OCP_src_stubs_Windows/OCP-stubs/__init__.pyi` | 4,517 | `194b0ae9c3db890ba6f74ea2dc993438b85de8475f4fc1b59849c30a5473733d` |
| `OCP_src_stubs_Windows/OCP-stubs/Adaptor2d/__init__.pyi` | 17,789 | `0b6f01625d3ed32e91a4be80137417e910ae9bf6def272c4d0687b447daee77e` |
| `OCP_src_stubs_Windows/IVtk.cpp` | 27,041 | `a928ecf2d7499d2fb2ecd3facfdd64b9a1328b7bbac1df18e34ae9348a072b8e` |
| `OCP_src_stubs_Windows/IVtkOCC.cpp` | 20,550 | `57e9104bd344c013e3a016902b54cc5bfaa92fa297ef8f2473449b5586af3af8` |
| `OCP_src_stubs_Windows/IVtkTools.cpp` | 29,360 | `7b9dbdfb6ba337b960570f0444a9e5920167e5b6596646335f59192d321c2a54` |
| `OCP_src_stubs_Windows/IVtkVTK.cpp` | 13,174 | `92dd20aeed352902f153c2baa0f66006c79be7bb9cc2aea73b7e7240f14cf3e0` |

## Build-recipe finding

The official [upstream build workflow run](https://github.com/CadQuery/ocp-build-system/actions/runs/26501389469) used workflow revision `81d357f678704c9cd33b7a4e1adf1dfd71bcbe18`, whose environment sets `PYWRAP: "false"`. In its [`build-ocp-source` action](https://github.com/CadQuery/ocp-build-system/blob/81d357f678704c9cd33b7a4e1adf1dfd71bcbe18/.github/actions/build-ocp-source/action.yml), that branch downloads the official Windows generated-source ZIP, unpacks it, and prepares the stubs; it does not clone OCP for pywrap generation or invoke pywrap. A separate [`build-ocp` action](https://github.com/CadQuery/ocp-build-system/blob/81d357f678704c9cd33b7a4e1adf1dfd71bcbe18/.github/actions/build-ocp/action.yml) compiles and links the generated C++ against OCCT and Python.

The upstream no-VTK recipe does not consume this ZIP unchanged. It patches `CMakeLists.txt` to remove VTK discovery/link targets, deletes the four `IVtk*` generated modules, and removes their registrations from `OCP.cpp`. The ZIP's CMake file itself requires VTK (`WrappingPythonCore`, RenderingCore, RenderingOpenGL2, CommonDataModel, CommonExecutionModel, and freetype), globs all `.cpp` files, and links VTK. Therefore:

1. `PYWRAP=false` genuinely bypasses the expensive source-generation step and leaves a native compile/link stage.
2. Applying the published no-VTK patch to this exact 319-module inventory removes four modules, leaving 315. That fails PackLab's frozen requirement to keep all 319 pywrap modules. Building all 319 as-is also contradicts the `novtk` runtime policy and the current controlled OCCT build configured with `USE_VTK=OFF`.
3. This ZIP is therefore **INCOMPATIBLE with the current frozen PackLab build contract as written**, despite being a promising pywrap bypass. Reconcile the 319-module requirement and `novtk` policy first. Any changed contract or build route needs the required owner decision; this read-only report does not grant it.

## PackLab integration and remaining inputs

The current [`build_controlled_ocp_runtime.py`](https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/build_controlled_ocp_runtime.py) expects tar-extracted OCP and pywrap source trees, runs the pywrap generation phase, then configures and compiles the generated project. The ZIP would need an authorized alternate source path, secure ZIP handling, the no-VTK patch, explicit module-count validation, and a revised provenance manifest. Its direct CMake project also needs externally supplied OCCT headers/libraries, Python 3.12 headers/runtime, pybind11, fmt, and the selected Windows compiler/SDK. The existing PackLab contract pins Windows 2022, CPython 3.12.15, Windows SDK 10.0.26100.0, CMake 3.31.8, and MSVC 19.44.35229.0; no compile was run to establish compatibility with those exact pins.

PackLab's current CAD adapter imports modules such as `OCP.gp`, `OCP.BRepBuilderAPI`, `OCP.BRepPrimAPI`, `OCP.BRepCheck`, `OCP.TopExp`, `OCP.TopAbs`, `OCP.BRepAlgoAPI`, `OCP.Bnd`, and `OCP.BRepBndLib`. Those names appear in the ZIP's generated inventory, but only a native build and the existing packaged CAD smoke could establish import/behavior compatibility. The generated-source archive contains no OCCT SDK, pybind11/fmt dependency trees, compiled extension, or runtime DLLs.

The no-VTK patch is a build-system patch, not generated C++ source. Other non-C++ build inputs remain necessary: exact source-locked OCCT, Python development files, pybind11, fmt, and Windows SDK/OpenGL headers. `OCP_specific.inc` includes fmt and defines OCP exception/holder helpers. `pystreambuf.h` carries separate cctbx-derived licensing text and would need to remain within source/notice review.

## Time, blockers, and limits

- Prior PL-0350 evidence estimates pywrap generation at about 5h04m and OCCT native build at about 42m40s. With an approved compatible generated-source route, the pywrap generation portion may be avoided. The remaining C++ compile/link duration is unknown; no native compile, package build, or installer run occurred in this inspection.
- The current V05 opaque-wheel blocker remains open: 79 OCP native redistribution rows lack exact third-party source/build provenance. This source ZIP does not prove third-party DLL provenance, package notices, Qt/PySide6 or Open3D clearance, or licensing acceptance.
- Not proven here: equivalence to PackLab's pywrap output, compilation/linking, ABI/runtime behavior, full native OCP import/CAD behavior, reproducibility, artifact portability, complete downstream redistribution evidence, or an unsigned installer.
- No tests, native builds, pywrap generation, CI runs, wheel substitution, product/runtime refresh, source-lock change, owner Desktop change, private data, or credentials were used or changed.

## Handoff

The narrow source feasibility result is **INCOMPATIBLE** with the current exact module-count + no-VTK contract. It establishes that upstream can skip pywrap in a different configuration, while the published no-VTK path drops four modules. PL-0350 remains open and owner-gated; PL-0351 remains blocked. Any native build or change to the 319-module contract requires explicit owner authorization after independent audit.

**AWAITING_INDEPENDENT_AUDIT / OWNER_BUILD_APPROVAL_REQUIRED**

## Complete generated module ID list

Adaptor2d, Adaptor3d, AdvApp2Var, AdvApprox, AIS, APIHeaderSection, AppBlend, AppCont, AppDef, AppParCurves, Approx, AppStd, AppStdL, Aspect, BinDrivers, BinLDrivers, BinMDataStd, BinMDataXtd, BinMDF, BinMDocStd, BinMFunction, BinMNaming, BinObjMgt, BinTObjDrivers, BinTools, BinXCAFDrivers, Bisector, BiTgte, Blend, BlendFunc, Bnd, BndLib, BOPAlgo, BOPDS, BOPTools, BRep, BRepAdaptor, BRepAlgo, BRepAlgoAPI, BRepApprox, BRepBlend, BRepBndLib, BRepBuilderAPI, BRepCheck, BRepClass, BRepClass3d, BRepExtrema, BRepFeat, BRepFill, BRepFilletAPI, BRepGProp, BRepIntCurveSurface, BRepLib, BRepLProp, BRepMAT2d, BRepMesh, BRepOffset, BRepOffsetAPI, BRepPrim, BRepPrimAPI, BRepProj, BRepSweep, BRepToIGES, BRepToIGESBRep, BRepTools, BRepTopAdaptor, BSplCLib, BSplSLib, BVH, CDF, CDM, ChFi2d, ChFi3d, ChFiDS, Contap, Convert, CPnts, CSLib, DE, Draft, DsgPrs, ElCLib, ElSLib, Expr, ExprIntrp, Extrema, FairCurve, FEmTool, FilletSurf, Font, FSD, GC, GccAna, GccEnt, GccInt, gce, GCE2d, GCPnts, Geom, Geom2d, Geom2dAdaptor, Geom2dAPI, Geom2dConvert, Geom2dEvaluator, Geom2dGcc, Geom2dHatch, Geom2dInt, Geom2dLProp, Geom2dToIGES, GeomAbs, GeomAdaptor, GeomAPI, GeomConvert, GeomEvaluator, GeomFill, GeomInt, GeomLib, GeomLProp, GeomPlate, GeomProjLib, GeomToIGES, GeomTools, GeomToStep, gp, GProp, Graphic3d, Hatch, HatchGen, Hermit, HLRAlgo, HLRAppli, HLRBRep, HLRTopoBRep, IFGraph, IFSelect, IGESAppli, IGESBasic, IGESCAFControl, IGESControl, IGESConvGeom, IGESData, IGESDefs, IGESDimen, IGESDraw, IGESFile, IGESGeom, IGESGraph, IGESSelect, IGESSolid, IGESToBRep, Image, IMeshData, IMeshTools, IntAna, IntAna2d, IntCurve, IntCurvesFace, IntCurveSurface, Interface, InterfaceGraphic, Intf, IntImp, IntImpParGen, IntPatch, IntPolyh, IntRes2d, Intrv, IntStart, IntSurf, IntTools, IVtk, IVtkOCC, IVtkTools, IVtkVTK, Law, LDOM, LocalAnalysis, LocOpe, LProp, LProp3d, MAT, MAT2d, math, MeshVS, Message, NCollection, NIS, NLPlate, OpenGl, OSD, PCDM, Plate, PLib, Plugin, Poly, Precision, ProjLib, Prs3d, PrsMgr, Quantity, Resource, RWGltf, RWMesh, RWStepAP203, RWStepAP214, RWStepAP242, RWStepBasic, RWStepDimTol, RWStepElement, RWStepFEA, RWStepGeom, RWStepRepr, RWStepShape, RWStepVisual, RWStl, Select3D, SelectBasics, SelectMgr, ShapeAlgo, ShapeAnalysis, ShapeBuild, ShapeConstruct, ShapeCustom, ShapeExtend, ShapeFix, ShapeProcess, ShapeProcessAPI, ShapeUpgrade, Standard, StdDrivers, StdFail, StdLDrivers, StdLPersistent, StdObject, StdObjMgt, StdPersistent, StdPrs, StdSelect, StdStorage, StepAP203, StepAP209, StepAP214, StepAP242, StepBasic, STEPCAFControl, STEPConstruct, STEPControl, StepData, StepDimTol, STEPEdit, StepElement, StepFEA, StepGeom, StepRepr, STEPSelections, StepShape, StepToGeom, StepToTopoDS, StepVisual, StlAPI, Storage, Sweep, TColGeom, TColGeom2d, TColgp, TCollection, TColStd, TDataStd, TDataXtd, TDF, TDocStd, TFunction, TNaming, TObj, TopAbs, TopBas, TopClass, TopCnx, TopExp, TopLoc, TopoDS, TopoDSToStep, TopOpeBRep, TopOpeBRepBuild, TopOpeBRepDS, TopOpeBRepTool, TopTools, TopTrans, TPrsStd, Transfer, TShort, Units, UnitsAPI, UnitsMethods, UTL, V3d, Voxel, Vrml, VrmlAPI, WNT, XBRepMesh, XCAFApp, XCAFDimTolObjects, XCAFDoc, XCAFNoteObjects, XCAFPrs, XCAFView, XmlDrivers, XmlLDrivers, XmlMDataStd, XmlMDataXtd, XmlMDF, XmlMDocStd, XmlMFunction, XmlMNaming, XmlObjMgt, XmlTObjDrivers, XmlXCAFDrivers, XSControl
