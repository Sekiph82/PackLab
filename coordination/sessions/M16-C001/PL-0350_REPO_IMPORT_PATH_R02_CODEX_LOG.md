# PL-0350 repository import path R02 — Codex implementation log

Date: 2026-10-12
Status: **BATCH_STOPPED_AT_PL-0350 / AWAITING_INDEPENDENT_AUDIT**
Stop code: `OCP_COMPILE_FAILED_OPENGL_CONTEXT_HEADER_MISSING`

## Revision and synchronization

- Starting canonical revision: `1a3f8c715337ee368481c4c72aa407dcf580c16e`.
- Implementation revision: `4f064e2f44359a40298d13baece02dcb18fb01f7` (`Fix Windows workflow repository Python imports`).
- Implementation was pushed to canonical `main`; exact-SHA quality and diagnostic runs used that revision.
- Managed worktree: `C:\Users\sekip\.codex\worktrees\pl0350-hosted-315-novtk\PackLab`.
- The managed worktree was clean at implementation start and fast-forwarded from `origin/main` to the R02 authorized base. The owner Desktop checkout and its pre-existing local files/runtime were not used or modified.
- R02 prompt, matching independent audit criteria, root `TASKS.md` project status, and the parent R01 audit were read. No scope conflict was found.

## Implementation

Product files changed in implementation commit `4f064e2f44359a40298d13baece02dcb18fb01f7`:

- `.github/workflows/windows-studio-build.yml`
- `tests/ci/test_windows_studio_build_workflow.py`
- `tools/packaging/verify_windows_workflow_python_imports.py` (new)

All 21 repository-local CLI calls in the Windows Studio workflow now use `python -m tools.packaging.<module>` from the repository root, with the existing `uv`, setup-Python, or micromamba environment as appropriate. The capacity-preflight job runs the new import smoke before source ZIP download. The smoke checks repository-importing modules in isolated `python -S` subprocesses, reproduces the previous direct-path `ModuleNotFoundError`, verifies module-form `--help` entrypoints, and rejects direct script paths (including interpreter flags and `python.exe`). Regression tests exercise the real smoke and workflow rules.

The workflow remains `workflow_dispatch` only; `preflight_only` continues to skip all three native/package jobs. Python versions, source hashes, No-VTK 319-to-315 patch, worker cap, timeouts, source provenance, manifest, compliance gates, and unsigned installer contract were left intact. `TASKS.md`, audit files, owner decisions, native source locks, and owner-local files were not changed.

## Local implementation checks

All checks below passed on implementation SHA `4f064e2f44359a40298d13baece02dcb18fb01f7`:

| Command/check | Result |
| --- | --- |
| `uv run --locked pytest tests/ci/test_windows_studio_build_workflow.py -q` | PASS, 6 passed |
| `uv run --locked ruff check core apps tools tests` | PASS |
| `uv run --locked ruff format --check tools/packaging/verify_windows_workflow_python_imports.py tests/ci/test_windows_studio_build_workflow.py` | PASS |
| `uv run --locked mypy core apps tools` | PASS, 237 source files |
| `uv run --locked python -m compileall -q tools/packaging/verify_windows_workflow_python_imports.py tests/ci/test_windows_studio_build_workflow.py` | PASS |
| `python -S -m tools.packaging.verify_windows_workflow_python_imports` | PASS; old path reproducer failed as expected with `No module named 'tools'`; all 12 module probes passed |
| Workflow YAML parse and manual-only/preflight-skip inspection | PASS |
| `git diff --check` | PASS |

No full repository suite or local native compilation was run.

## GitHub implementation and diagnostic evidence

- Windows Python Quality: [run 38262833083](https://github.com/Sekiph82/PackLab/actions/runs/38262833083) — SUCCESS on exact implementation SHA.
- Hosted preflight-only diagnostic: [run 38262855024](https://github.com/Sekiph82/PackLab/actions/runs/38262855024) — SUCCESS. Capacity/import job `114857527800` passed; OCCT `114857768312`, OCP `114857767712`, and Studio `114857769191` were skipped. Setup Python 3.12.10 and all 12 module probes were verified. The official source check passed for 319 input modules to 315 output modules; archive SHA-256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`.

## One authorized cold continuation — first failure and stop

Cold run: [38263302823](https://github.com/Sekiph82/PackLab/actions/runs/38263302823)
Exact head: `4f064e2f44359a40298d13baece02dcb18fb01f7`
Conclusion: **FAILURE**, 2h 5m 47s total.

| Job | Result | Evidence |
| --- | --- | --- |
| Capacity/source preflight `114859078661` | PASS, 20s | Hosted source preparation and capacity stage completed. |
| OCCT SDK checkpoint `114859244116` | PASS, 50m 7s | Built, validated, and uploaded the exact same-run SDK checkpoint. |
| Official 315-module OCP runtime `114879875867` | FAIL, 2h 5m 47s | Native compile step ran from 15:24:33Z to 17:25:54Z and returned exit code 1. |
| Studio package `114928446599` | SKIPPED | OCP dependency failed; no packaging or installer stage ran. |

The first compiler errors in the failed OCP stage were:

```text
generated/OCP_src_stubs_Windows/OpenGl.cpp(41,10): error C1083:
Cannot open include file: 'OpenGl_Context.hxx': No such file or directory
generated/OCP_src_stubs_Windows/OpenGl_pre.cpp(40,10): error C1083:
Cannot open include file: 'OpenGl_Context.hxx': No such file or directory
```

The build command was `cmake --build ... --config Release --target OCP --parallel 4`; Python reported `subprocess.CalledProcessError`, exit status 1. The 270-minute compile budget was not reached. This records the compiler output only and does not infer why that header was absent. No repair or retry was attempted.

Retained run artifacts (both unexpired at inspection):

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `packlab-occt-sdk-38263302823-1` | 56,405,631 bytes | `1ad03b366958f0a81d98813fac313d85d0133e79db9e85f4844d783b0306d0ae` |
| `packlab-native-source-evidence-38263302823-1` | 1,398 bytes | `4b596da7de0616b58bcf21194dc0bc832e6f53464282b87c1199bc325bd35e9d` |

No OCP runtime artifact was sealed or uploaded. Studio packaging, CAD/PDF/Open3D packaged smokes, unsigned installer evidence, full cold acceptance, and warm-cache proof did not occur. No installer SHA, clearance, or native acceptance is claimed.

## Safety, limitations, and handoff

- One diagnostic and one cold continuation were run. No cold retry, warm-cache run, local native build, source substitution, worker/timeout adjustment, PL-0351, or M17 work was performed.
- The Desktop checkout, known-good PackLab executable, OwnerDev state, and owner data were not modified. No private supplier/customer data, credentials, or secrets were added or published.
- No legal or redistribution clearance, signing, public release, or owner-native acceptance is claimed. `TASKS.md` remains unchanged and PL-0350 remains open pending the independent audit.
- Evidence log and report are being published separately from the product implementation commit.

**Handoff:** `BATCH_STOPPED_AT_PL-0350 / OCP_COMPILE_FAILED_OPENGL_CONTEXT_HEADER_MISSING` — `AWAITING_INDEPENDENT_AUDIT`.
