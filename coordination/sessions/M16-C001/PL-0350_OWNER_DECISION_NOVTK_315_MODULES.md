# PL-0350 — Owner Decision: Official Generated OCP No-VTK 315-Module Contract

Decision date: 2026-10-12
Decision: **OWNER_ACCEPTED_NOVTK_315_MODULE_CONTRACT**
Scope: Narrow *module-surface and source-generation architecture* change only, **not a build/run authorization**.

## Owner ruling

The owner explicitly approves PackLab's Windows source-built OCP `novtk` binding target as **315 modules**, i.e. the exact 319 generated IDs in CadQuery/OCP official Windows source release 7.9.3.1.1, less exactly four VTK-specific modules:

- `IVtk`
- `IVtkOCC`
- `IVtkTools`
- `IVtkVTK`

The former unqualified `319-module` shipping/acceptance condition is **superseded ONLY for the no-VTK production binding**. The pinned generated-source ZIP must itself contain all 319 unmodified source modules and each source triplet before the reviewed, deterministic upstream-style removal of the four VTK-specific modules/registrations. The final no-VTK code surface must preserve all remaining 315 generated module registrations and the actual PackLab CAD/STEP/DXF/measurement/engineering API import surface. No feature may be lost by quietly removing any other module.

Official immutable inputs:
- https://github.com/CadQuery/OCP/releases/tag/7.9.3.1.1
- `OCP_src_stubs_Windows.zip`, **6,481,047 bytes**, SHA-256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`.
- Upstream OCP revision `d69b064a3a604ebf245b1f3b14fb54c835a3a571`.
- Existing PackLab locked OCCT 7.9.3, CPython 3.12.15, Windows 2022 x64, MSVC/Windows SDK/CMake toolchain contract remains unchanged unless independently proposed and separately authorized.
- Official `PYWRAP=false` + upstream `novtk` patch is a permitted **design candidate**, NOT an automatically proven compiled result.
- This ruling **does not permit swapping in opaque prebuilt cadquery-ocp-novtk wheels** or pretending their 79 native-file provenance rows are closed.

## Immediate authorization and STOP rule

Approved now: a short, bounded, **non-compiling preflight**: static PackLab import scan; exact 319→315/4 module and registration contract; safely review/implement a deterministic no-VTK *patch validation plan*; corresponding source/license/third-party evidence mapping review; CI graph and artifact-size/time budget design. Use small fixtures/scripts/docs only. Preserve all original product features and strict fail-closed checks.

**Not authorized**: native OCCT compilation, pywrap regeneration, OCP C++ compile/link, cold or warm native hosted Actions, any multi-hour workflow dispatch, changing the active Desktop PackLab.exe/OwnerDev runtime, wheel substitution, destructive cache/AppData cleanup, an installer release, or proceeding to PL-0351. Obtain **separate explicit owner approval** before real native build, after independent audit of the preflight.

**CI push trap:** `.github/workflows/windows-studio-build.yml` currently auto-triggers on `push: main` changes to `tools/packaging/**`, `tests/ci/**`, `apps/windows-studio/**`, `core/**`, `schemas/**`, `pyproject.toml`, `uv.lock`, or the workflow itself. Therefore the non-build preflight must NOT push to any path that triggers the long controlled-OCP job. Publishing task documentation and small analysis-only files in non-trigger paths is permitted after verifying **all** workflows. Do not rely on a `skip ci` message, job cancellation, a 480-minute YAML timeout, or surprise runtime charges to mitigate this.

This owner approval does not confer independent audit PASS for installer or distribution. The earlier official ZIP inspection is narrowly `AUDITED_PASS`, PL-0350 remains unchecked, PL-0351 blocked, PL-0368 deferred and M17 not started.

References:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_CHATGPT_AUDIT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_REPORT.md
