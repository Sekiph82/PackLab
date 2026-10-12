# PL-0350 R03 Builder Report

Date: 2026-10-13
Result: **BATCH_STOPPED_AT_PL-0350 / OCCT_SDK_INSTALL_LAYOUT_VALIDATION_MISMATCH**

## Implemented

- Preserved `USE_VTK=OFF` and configured the source-built OCCT SDK with `USE_OPENGL=ON`, versioned SDK metadata/cache identity, required OpenGL payload checks, and a full generated-source dependency audit before OCP compilation.
- Corrected the retained-artifact preflight after run [38304697335](https://github.com/Sekiph82/PackLab/actions/runs/38304697335) failed before native jobs. The corrected calculation keeps the 8 GiB two-run ceiling and reserves equal dynamic room for two authorized runs. Each artifact upload checks cumulative current-run usage.
- Product change pushed as `038d3c462ef176293cb37d778fc79676f3bbf0be`.

## Hosted result

The corrected exact-SHA dispatch [38305407910](https://github.com/Sekiph82/PackLab/actions/runs/38305407910) passed capacity preflight and started the one authorized source-built SDK run. The SDK build created and installed:

- `install/inc/OpenGl_Context.hxx`
- `install/win64/vc14/lib/TKOpenGl.lib`
- `install/win64/vc14/bin/TKOpenGl.dll`

The build then stopped at the SDK required-path check, which expected the import library and DLL directly under `lib/` and `bin/`. The files were present under OCCT's `win64/vc14/` subdirectory. The validation error was `OCCT install lacks the required OpenGL header, import library, or runtime DLL`.

No SDK manifest, sealed SDK artifact, or v3 cache entry was produced. The existing R02 SDK and source-evidence artifacts remain unchanged. OCP and Studio jobs were skipped, so there is no native OCP binary, packaged smoke, compliance clearance, installer, or warm cache-hit proof. This report does not claim PL-0350 acceptance.

## Validation

- 34 focused CI/dependency tests passed.
- Ruff, format check, targeted mypy, compileall, all 15 workflow Python imports, and `git diff --check` passed.
- GitHub parsed and ran the workflow dispatch. A local YAML parser/actionlint was unavailable.
- No native compilation ran on the owner's machine; observed local C: free space was 123,487,326,208 bytes.

## Boundary

R03 stops at its first hosted SDK manifest/layout failure. No retry or second native build was performed. Root `TASKS.md`, ChatGPT audits, owner files, and the old retained artifacts were preserved. No adjacent task, signing, public release, or installer claim was made. Awaiting independent audit and a separately issued follow-up prompt for any further implementation/build.
