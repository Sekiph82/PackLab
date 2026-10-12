# PL-0350 Official Generated OCP Source ZIP — ChatGPT Independent Audit V01

Date: 2026-10-12
**NARROW VERDICT: AUDITED_PASS (READ-ONLY SOURCE INSPECTION ONLY)**
**PARENT PL-0350: OWNER_REQUIRED / NOT PASS**
Next owner gate: `NOVTK_315_MODULE_CONTRACT_DECISION_REQUIRED`; `NATIVE_BUILD_NOT_AUTHORIZED`.

## Evidence and direct cross-check

- Report: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_REPORT.md
- Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_CODEX_LOG.md
- Published log refinement: https://github.com/Sekiph82/PackLab/commit/19f9df681795506a7f62697804b1dbab5de8f9b2
- Read-only criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_AUDIT_CRITERIA.md
- Official release JSON: https://api.github.com/repos/CadQuery/OCP/releases/tags/7.9.3.1.1
- Official upstream source action pinned to workflow revision: https://github.com/CadQuery/ocp-build-system/blob/81d357f678704c9cd33b7a4e1adf1dfd71bcbe18/.github/actions/build-ocp-source/action.yml
- Official upstream native build action, VTK patch: https://github.com/CadQuery/ocp-build-system/blob/81d357f678704c9cd33b7a4e1adf1dfd71bcbe18/.github/actions/build-ocp/action.yml
- PackLab controlled builder: https://github.com/Sekiph82/PackLab/blob/main/tools/packaging/build_controlled_ocp_runtime.py

Independently fetched official release API and the upstream `build-ocp-source` and `build-ocp` action source. They show the exact Windows release archive's name/size/sha256 and the actual `PYWRAP=false` download/compile path. The upstream `novtk` step explicitly removes VTK discovery and libraries and deletes `OCP/IVtk*` with matching registration removal. The report's archived-file hashes, exact 1,613 ZIP-member names and installed owner Desktop state were reviewed as **builder-observed evidence**, not remeasured independently on the owner's Windows device. No new native binaries were produced.

## PASS within the scoped read-only research task

1. Authorized read-only task completed with full SHA-256 match, 6,481,047-byte official asset and locked OCP revision `d69b064...`; no build/cache modification, wheel substitution or owner Desktop change claimed.
2. ZIP inspection recorded 1,613 entries, 62,426,401 uncompressed bytes, no unsafe paths/symlinks, and 319 generated module triplets (`.cpp`, `_pre.cpp`, `_tmpl.hxx`) plus generated binding entry point and 638 registrations. The report captures per-file hash evidence, known build inputs and limitations.
3. Confirmed upstream does indeed skip the ~5h pywrap generation with `PYWRAP=false`, **but does not skip native compilation**, OCCT SDK build, runtime validation or installer redistribution clearance.
4. Confirmed current PackLab builder explicitly selects `USE_VTK=OFF` and the official generated CMake initially expects VTK. The real upstream no-VTK recipe removes four specifically VTK-bound modules (`IVtk`, `IVtkOCC`, `IVtkTools`, `IVtkVTK`), leaving **315 non-VTK modules**.
5. Correctly kept all prior opaque-wheel provenance blockers (79 OCP native rows), Qt/PySide/Open3D notices/license obligations, no installer and PL-0351 gate OPEN. No runtime tests claimed from an inspection-only task.

## Key interpretation — incompatibility is with an internal contract, NOT established functional incompatibility

The report's `INCOMPATIBLE` label is **correct narrowly for the frozen numeric "all 319" requirement combined with `novtk`**. It is NOT proof that 315 modules lack required PackLab CAD features. The four excluded modules are precisely VTK-specific, and the pinned PackLab product is `cadquery-ocp-novtk`. Previous audit requiring all 319 for this no-VTK build likely conflated source generator progress with required shipped API surface. This artificial clash can be corrected **only with explicit owner approval of a documented contract change**, plus regression evidence that no required product feature imports the four modules.

The ZIP's internal `OCP.__version__ = 7.9.3.1` versus release/package `7.9.3.1.1` is also a version-identity mapping issue to document, not evidence the artifact was tampered. OCP must not be silently claimed byte-equivalent to the pywrap output PackLab previously generated.

## Recommendation / owner ruling requested

**Recommend a narrowly scoped change: permit exactly the upstream-proven 315-module `novtk` binding surface** (319 minus four VTK-only), retaining all PackLab-used CAD/STEP/DXF/mathematics modules, locked OCCT/OCP source+asset digest, strict no-VTK no-wheel requirements, source/licenses and shipped smoke gates.

If owner approves, first do lightweight import-dependency scan and deterministic small fixture tests for module coverage/patch correctness; if green, design independent hosted phases (OCCT ~43min, generated sources verified ~6.5 MB, native C++ compile of unknown duration, packaging/clearance) with bounded outputs and cache checkpoints. **Do not start an hours-long hosted build without separate explicit owner approval after preflight feasibility**. No work on owner C: except bounded scratch, no existing Desktop runtime change.

If owner does not approve removing four VTK modules, current generated-source path remains blocked by numeric contract; retain the source-build/pywrap route or propose an audited technical alternative. Do not re-run old six-hour monolith.

## Disposition

- Read-only official ZIP inspection: `AUDITED_PASS` **for inspection only**.
- Generated-source build compatibility with current unmodified frozen 319/no-VTK contract: `INCOMPATIBLE`.
- Potential 315-module no-VTK controlled build: `CANDIDATE_AWAITING_OWNER_CONTRACT_RULING_AND_LATER_BUILD_TESTS`.
- Parent PL-0350: `OWNER_REQUIRED`, no sealed artifact or unsigned installer, no packaging clearance. PL-0351 and M17 not started; PL-0368 deferred.
