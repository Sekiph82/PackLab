# PL-0350 repository import path R02 — evidence and blocker report

Date: 2026-10-12
Status: **BATCH_STOPPED_AT_PL-0350 / AWAITING_INDEPENDENT_AUDIT**
First stop: `OCP_COMPILE_FAILED_OPENGL_CONTEXT_HEADER_MISSING`

## Outcome

R02 repaired repository-local Python CLI invocation throughout the Windows hosted workflow. All workflow script calls now use package module entrypoints. Focused regression tests verify the actual module smoke, reproduce the old direct-path import failure, and reject direct script paths. The exact-SHA Windows Python Quality run and a hosted preflight-only diagnostic both passed. The preflight diagnostic confirmed all 12 imports and skipped OCCT, OCP, and Studio.

The single authorized cold continuation passed hosted capacity/source preflight and produced a sealed OCCT SDK checkpoint. The subsequent official 315-module OCP compile failed when generated `OpenGl.cpp` and `OpenGl_pre.cpp` could not include `OpenGl_Context.hxx` (MSVC C1083). The compile returned exit code 1 after about 2 hours, before its 270-minute limit. Studio packaging was skipped. No cold retry or warm run was made. R02 does not meet PL-0350 acceptance.

## Revisions and run evidence

| Evidence | Revision/result |
| --- | --- |
| Authorized starting revision | `1a3f8c715337ee368481c4c72aa407dcf580c16e` |
| Published implementation | `4f064e2f44359a40298d13baece02dcb18fb01f7` |
| Windows Python Quality | [38262833083](https://github.com/Sekiph82/PackLab/actions/runs/38262833083), success |
| Hosted preflight-only diagnostic | [38262855024](https://github.com/Sekiph82/PackLab/actions/runs/38262855024), success |
| Authorized cold continuation | [38263302823](https://github.com/Sekiph82/PackLab/actions/runs/38263302823), failure, exact implementation SHA |
| Capacity/source preflight | [job 114859078661](https://github.com/Sekiph82/PackLab/actions/runs/38263302823/job/114859078661), success |
| OCCT SDK checkpoint | [job 114859244116](https://github.com/Sekiph82/PackLab/actions/runs/38263302823/job/114859244116), success |
| Official OCP runtime compile | [job 114879875867](https://github.com/Sekiph82/PackLab/actions/runs/38263302823/job/114879875867), failure |
| Studio package | [job 114928446599](https://github.com/Sekiph82/PackLab/actions/runs/38263302823/job/114928446599), skipped |

## Implementation checks

The implementation commit changed the Windows Studio workflow and its workflow regression tests, and added `tools/packaging/verify_windows_workflow_python_imports.py`. All 21 repository script invocations were converted to module entrypoints. A quick import smoke runs during hosted preflight before large source download and compilation. The manual-only trigger, `preflight_only` skip gates, 3.12.10 bootstrap, native Python 3.12.15 lock, 319-to-315 No-VTK patch, source hashes, 4-worker cap, timeout, manifests, compliance gates, and unsigned installer contract remain intact.

Local checks passed: focused workflow tests (6 passed), Ruff, format check, mypy (237 files), compileall on the changed Python files, isolated import smoke (12 module probes and expected direct-path failure), workflow YAML/rule inspection, and `git diff --check`. No full suite or local native compilation was run. Exact implementation checks and limitations are recorded in the [Codex log](PL-0350_REPO_IMPORT_PATH_R02_CODEX_LOG.md).

## First hard stop and retained artifacts

The cold compile step ran from `2026-10-12T15:24:33Z` to `2026-10-12T17:25:54Z`. Its first reported native compiler errors were:

```text
OpenGl.cpp(41,10): error C1083: Cannot open include file: 'OpenGl_Context.hxx'
OpenGl_pre.cpp(40,10): error C1083: Cannot open include file: 'OpenGl_Context.hxx'
```

The command `cmake --build ... --config Release --target OCP --parallel 4` returned exit status 1. This report does not speculate about the cause of the missing header. The OCP job ended in failure, and dependent Studio packaging was skipped. No OCP runtime artifact, package smokes, installer, installer digest, clearance, or warm-cache evidence was produced.

The run retained these two unexpired artifacts:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `packlab-occt-sdk-38263302823-1` | 56,405,631 bytes | `1ad03b366958f0a81d98813fac313d85d0133e79db9e85f4844d783b0306d0ae` |
| `packlab-native-source-evidence-38263302823-1` | 1,398 bytes | `4b596da7de0616b58bcf21194dc0bc832e6f53464282b87c1199bc325bd35e9d` |

The source-preparation evidence reported 319 input modules, 315 output modules, and archive SHA-256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`. This and the retained OCCT artifact do not establish a working OCP runtime or installer.

## Safety and disposition

The owner Desktop checkout, known-good executable, OwnerDev state, `TASKS.md`, audit files, and owner decisions were not changed. No local native compilation, data upload, secret publication, signing, or public release occurred. No adjacent task was started.

**Disposition:** `BATCH_STOPPED_AT_PL-0350 / OCP_COMPILE_FAILED_OPENGL_CONTEXT_HEADER_MISSING` — `AWAITING_INDEPENDENT_AUDIT`. PL-0350 remains open; no acceptance or redistribution clearance is claimed.
