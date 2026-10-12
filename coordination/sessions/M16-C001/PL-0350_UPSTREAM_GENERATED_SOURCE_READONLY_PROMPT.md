# PL-0350 — Official 7.9.3.1.1 Generated Binding Source: READ-ONLY CONTENT CHECK

Executor: CODEX. This is a small bounded feasibility follow-up within existing PL-0350, **not** permission for native builds, wheel substitution, installation or another long Actions job.

Prior independent research:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_PREBUILT_WHEEL_AND_UPSTREAM_SOURCE_RESEARCH_V01.md

Live state: read origin/main TASKS.md and any newer explicit owner decision; preserve all owner-local work. Codex must never edit root TASKS.md or ChatGPT audit files.

## Read-only task

1. Verify official source release metadata of https://api.github.com/repos/CadQuery/OCP/releases/tags/7.9.3.1.1 and pinpoint asset `OCP_src_stubs_Windows.zip` (6,481,047 bytes; expected SHA-256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`). Exact release OCP revision should match PackLab source lock `d69b064a3a604ebf245b1f3b14fb54c835a3a571`. Provenance and digest validation fail closed.
2. Download/read ONLY this ~6.5 MB public upstream source ZIP to a new **bounded disposable** scratch location; no downloads from unofficial mirrors, no PyPI wheel copies, no owner Desktop runtime alteration. For inspection prefer ZIP central-directory/file-stream reads rather than extract; if extraction is essential, prevent zip-slip, symlinks, oversized uncompressed expansion and unsafe paths and enforce <=200 MiB scratch. No full source repo clone, pywrap generation, native compilation, CMake build, Python product runtime refresh, bulk fixtures, or long CI dispatch. Abort if bounds exceeded.
3. Inspect exact archive inventory and source files: generated OCP `.cpp`, accompanying header/stubs, `CMakeLists.txt`, module registration, required 319-class complete module coverage, upstream generated-source version/OCCT 7.9.3 identity and pinned native build inputs. Check compatibility with `tools/packaging/build_controlled_ocp_runtime.py`, Windows 2022, locked CPython 3.12/SDK/MSVC, `novtk` policy and current OCP import/CAD contract. Do NOT assume upstream's downloaded Windows source is intrinsically equal to PackLab's own pywrap output; list what cannot be proven without compilation.
4. Confirm whether upstream official recipe `PYWRAP=false` truly builds the released generated sources and whether one controlled OCCT SDK + OCP compile/link could replace the five-hour pywrap stage. Determine any required non-C++ extra inputs or patches. Do not execute any of it.
5. Keep current V05 opaque-wheel blocker explicit: 79 OCP native redistribution rows and exact third-party DLL provenance unknown; official generated C++ does not resolve other Qt/Open3D or legal-notice gates automatically.
6. Publish `coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_REPORT.md` and a matching Codex log `coordination/sessions/M16-C001/PL-0350_UPSTREAM_GENERATED_SOURCE_READONLY_CODEX_LOG.md` with exact asset/file digests, size/paths/module inventory, validity findings, GitHub evidence, best estimated downstream stages, and statuses `COMPATIBLE_CANDIDATE`, `INCOMPATIBLE`, or `INSUFFICIENT_EVIDENCE`. The report may recommend a build route but does NOT authorize one.
7. Commit log/evidence only, preserve origin/main parity, return GitHub log link. End `AWAITING_INDEPENDENT_AUDIT / OWNER_BUILD_APPROVAL_REQUIRED`. Do not edit root TASKS.md.

Do not claim clean-install proof, license clearance, verified generated-binary equivalence or an unsigned installer from this read-only check.
