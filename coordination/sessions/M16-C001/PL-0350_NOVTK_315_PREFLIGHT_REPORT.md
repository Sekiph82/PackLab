# PL-0350 — 315-Module no-VTK Prebuild Preflight Report

Date: 2026-10-12  
Status: **PREFLIGHT_STATIC_CONTRACT_PASS / NATIVE_BUILD_NOT_AUTHORIZED**  
Disposition: `AWAITING_INDEPENDENT_AUDIT / NATIVE_BUILD_OWNER_APPROVAL_REQUIRED`

## Authority and boundaries

The synchronized `origin/main` tracker authorized this non-compiling preflight for PL-0350. The owner decision accepts a 315-module no-VTK production binding, with exactly `IVtk`, `IVtkOCC`, `IVtkTools`, and `IVtkVTK` omitted from the official 319-module generated source. It does not authorize OCCT compilation, pywrap, OCP C++ compilation/linking, a hosted native workflow, an installer, or PL-0351.

All `.github/workflows/*.yml` and `.yaml` files and their push filters were inspected before edits. The only paths changed by this task are these two files under `coordination/sessions/M16-C001/`; none of the configured push filters matches them. `windows-studio-build.yml` would start the controlled native producer for `tools/packaging/**`, `tests/ci/**`, `.github/workflows/windows-studio-build.yml`, `apps/windows-studio/**`, `core/**`, `schemas/**`, `pyproject.toml`, `uv.lock`, or `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`. `windows-python-quality.yml` also matches broad `tools/**`, `tests/**`, app/core, workflow, and lock paths. Neither workflow can be triggered by this docs-only change. No workflow was dispatched.

The Desktop checkout and all other worktrees were left untouched. Work occurred in managed worktree `C:\Users\sekip\.codex\worktrees\m16-r08-v15\PackLab`. No product, source-lock, workflow, task tracker, audit, owner-decision, cache, runtime, or installer file was edited. No native build or compiled binary was produced.

## Exact source and 319-to-315 contract

Re-downloaded the official `OCP_src_stubs_Windows.zip` release asset only after confirming 173.60 GiB free on C: (the prompt's minimum is 40 GiB). The response was streamed in memory; no scratch file or extraction was created. Actual size was 6,481,047 bytes and SHA-256 was `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`, matching the owner decision and prior audit. The input release is OCP 7.9.3.1.1, upstream revision `d69b064a3a604ebf245b1f3b14fb54c835a3a571`.

The ZIP inspection confirmed:

- 319 distinct generated module IDs, each with exactly one `.cpp`, `_pre.cpp`, and `_tmpl.hxx` member;
- 638 matching `OCP.cpp` forward declarations and 638 matching registration calls: one enum and one module entry for each of the 319 IDs;
- the generated CMake file contains VTK discovery, a VTK version status line, and VTK link targets; `OCP.cpp` has the four VTK module declarations and registration calls;
- the deterministic output set is the input set minus exactly `IVtk`, `IVtkOCC`, `IVtkTools`, and `IVtkVTK`: 315 modules remain.

The static plan is bound by SHA-256 `8263b11294f99be6052272273fb84b518abe328d43dc3d7ce668f86962584248`. It is the SHA-256 of UTF-8 canonical JSON (`sort_keys=True`, separators `(',', ':')`) containing schema `packlab-ocp-novtk-static-plan-v1`, the exact input archive digest and byte size, sorted IDs read from the ZIP, the four-ID removal set, sorted output IDs, the required three source suffixes, and the paired `register_<id>_enums` / `register_<id>` rule. This digest identifies the proposed static patch plan; it is not a digest of patched C++ output because no production source patch was applied in this preflight.

An in-memory validation fixture accepted the real 319-ID inventory and produced 315 IDs with the exact four-item difference. Negative fixtures for a missing ID, an extra ID, and a duplicate ID all failed closed. Source triplets and registrations were inspected directly in the real archive. The no-VTK CMake and registration rewrite remains a proposed, reviewable next-stage patch; this preflight did not execute an upstream patch against production files. Before a future build, that patch must remove VTK CMake discovery/link references, the four module triplets, and only their declarations/calls, then verify no VTK CMake reference, no registration, and no missing non-VTK source remains.

`OCP.cpp` reports `OCP.__version__ = "7.9.3.1"`, while release/source-lock package identity is 7.9.3.1.1. A future manifest must preserve both values as distinct source/package and runtime-reported identities; it must not rewrite the generated runtime version to imply equality.

## PackLab import and feature-surface scan

Scanned `core/src` and `apps/windows-studio/src` Python sources for static OCP imports and literal `importlib.import_module` / `__import__` targets. Product source uses these 27 OCP submodules:

`OCP.BRep`, `OCP.BRepAdaptor`, `OCP.BRepAlgoAPI`, `OCP.BRepBndLib`, `OCP.BRepBuilderAPI`, `OCP.BRepCheck`, `OCP.BRepClass`, `OCP.BRepLProp`, `OCP.BRepMesh`, `OCP.BRepOffsetAPI`, `OCP.BRepPrimAPI`, `OCP.BRepTools`, `OCP.Bnd`, `OCP.GeomAbs`, `OCP.HLRAlgo`, `OCP.HLRBRep`, `OCP.IFSelect`, `OCP.Interface`, `OCP.STEPControl`, `OCP.StlAPI`, `OCP.TColStd`, `OCP.TopAbs`, `OCP.TopExp`, `OCP.TopLoc`, `OCP.TopTools`, `OCP.TopoDS`, and `OCP.gp`.

All 27 appear in the retained 315 IDs. The only additional dynamic OCP import is literal `importlib.import_module("OCP")`, the root package used for runtime identity/capability probing; no computed OCP submodule name was found. A broader source/test scan found no references to the four removed module IDs. This is textual import evidence, not compiled import or behavior proof.

PackLab STEP read/write uses literal OCP `STEPControl`, `IFSelect`, `Interface`, and topology/geometry imports, all retained. The DXF vector export is implemented in PackLab Python (`technical_drawing_export.py`) as the documented bounded R2000 ASCII subset and has no OCP import dependency. Measurement, BREP geometry, tessellation, label-surface, and STL paths use retained IDs from the list above. This inventory supports the 315 module contract at the source level; it does not prove native API compatibility, STEP behavior, or packaged operation. Dynamic Python features outside the literal import patterns and runtime plugins remain unproven.

## Locked inputs, provenance, and future CI phase design

Current PackLab source locks remain unchanged:

- OCP 7.9.3.1.1 source revision `d69b064a3a604ebf245b1f3b14fb54c835a3a571`, source archive SHA-256 `a5153cef9f4a3a3dbbb1d498a971206a6c35dc4d829e7e011f96e0539c22e616`;
- pywrap source revision `92519409a57f9ec3f2c005b8057006fdb4752c23`, SHA-256 `b88b0f2b9c7d2ae72a7399efc44951659fb1a28ea607d962ba1f507ce754ba48` (only required by the current pywrap route; the generated ZIP candidate avoids invoking pywrap, subject to later owner approval and build evidence);
- OCCT 7.9.3 revision `a016080bf6738d6aeae020badee4e888ad1540a5`, SHA-256 `c533f2667b59921bd6bd40ce82e7b9900b0289ccc731af5fdeeba097de80ef0f`;
- Windows x64, CPython 3.12.15, Windows SDK 10.0.26100.0, CMake 3.31.8 and MSVC 19.44.35229.0 remain the current controlled build contract; the locked conda environment includes pybind11 2.13.6 and fmt 12.1.0.

The generated ZIP is source only: it supplies no OCCT SDK, Python development files, pybind11/fmt dependency trees, compiled extension, or runtime DLLs. A future, separately owner-authorized design should use same-run immutable artifact transfer and distinct bounded jobs:

1. **OCCT SDK producer (target <=6 hours).** Verify the exact locked OCCT source and toolchain, build/install the existing `USE_VTK=OFF` configuration, and record exact stage timing. Prior evidence reports approximately 42m40s for OCCT; that historical builder measurement is not a guarantee for a clean current runner. Seal only required install headers, libraries, and runtime DLLs with a versioned schema, per-file SHA-256/size manifest, source/lock digests, toolchain identity, and relocatability check. Do not transfer CMake build trees or caches containing runner-absolute paths.
2. **315-module OCP producer (target <=6 hours).** Verify the 6.48 MB generated ZIP by digest, validate the 319 triplets and 638 registrations, apply a reviewed deterministic no-VTK patch, assert exactly 315 IDs/registration pairs and no residual VTK CMake link/discovery, then compile/link against the sealed OCCT stage and locked Python/pybind11/fmt/MSVC inputs. Seal the resulting runtime with a per-file inventory and an explicit 7.9.3.1 runtime-reported versus 7.9.3.1.1 source identity. Native C++ compile/link duration is unknown; pywrap's historical approximately 5h04m phase may be avoided, but that does not establish an OCP compile time or success.
3. **Packaged runtime/redistribution gate (separate later authorization).** Transfer only validated outputs from the same workflow run; verify stage manifests before use; run no-network packaged QtPdf, OCP/CAD, STEP, DXF, and Open3D smoke/notice checks before considering an unsigned installer. Do not infer licensing clearance from source locks alone.

For all future checkpoints, use schema-versioned manifests that bind source revision/archive digests, patch digest, lockfile digests, compiler/SDK identities, producer workflow/run, relative file paths, byte lengths, and SHA-256 values. Reject path traversal, duplicate/case-colliding paths, unlisted files, digest mismatches, stale absolute CMake paths, and a checkpoint whose producer identity differs from the consuming run. Use workflow artifacts for single-run stage transfer. Any reusable cache must be keyed by every source, patch, build script, compiler/toolchain and schema input, then treated as untrusted and fully revalidated. A cache hit and a cold build need separate proof. Record artifact bytes and runner disk consumption before approving limits; current evidence establishes generated-ZIP size (6,481,047 bytes; 62,426,401 uncompressed bytes), but does not establish the installed OCCT SDK or compiled 315-module runtime size. Those size budgets remain an open measurement gate.

The current native source lock records the source and licenses for OCCT, OCP, pywrap, Qt/PySide, QtPdf/PDFium, Open3D and oneTBB. The 79 OCP native-file provenance rows from the opaque wheel remain OPEN; this route does not close them. QtPdf/PDFium and Open3D notices/source obligations also remain separate redistribution gates. `OCP_specific.inc`/fmt and the cctbx-derived `pystreambuf.h` notice need to be included in later source/notice review. No license version or binary provenance is inferred from this preflight.

## Checks, limits, and handoff

- Exact release ZIP size/SHA and module/register inventory: PASS.
- In-memory exact-set transformation and missing/extra/duplicate rejection fixtures: PASS.
- Product OCP import inventory: all literal submodules are present in the retained set; removed-ID references: none; computed OCP submodule imports: none found; root `OCP` import is literal and accounted for.
- Workflow path safety: PASS for the two documentation paths only.
- Disk: 173.60 GiB free before and 173.61 GiB after; no scratch file or extraction was created; under the 200 MiB disposable-scratch ceiling.
- Native build, pywrap, C++ compile/link, Actions run, wheel substitution, installer, EXE change, full test suite, and packaged behavior were not performed.
- Known limits: no real patched 315-source tree was produced; no native API/ABI proof; source scanning cannot prove computed/plugin imports beyond the reviewed literal inventory; output SDK/runtime artifact sizes and native OCP compile duration are unknown; no new license clearance is claimed.

Source commands, results, starting/final revisions, and the publication handoff are recorded in `PL-0350_NOVTK_315_PREFLIGHT_CODEX_LOG.md`.

**AWAITING_INDEPENDENT_AUDIT / NATIVE_BUILD_OWNER_APPROVAL_REQUIRED**
