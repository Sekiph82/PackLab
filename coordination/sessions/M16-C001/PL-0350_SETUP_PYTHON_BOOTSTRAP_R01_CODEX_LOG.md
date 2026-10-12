# PL-0350 setup-python Bootstrap R01 — Codex Implementation Log

Date: 2026-10-12
Status: **BATCH_STOPPED_AT_PL-0350 / AWAITING_INDEPENDENT_AUDIT**
Stop code: `OCCT_SOURCE_FETCH_FAILED_TO_IMPORT_TOOLS`

## Revision and synchronization

- Starting canonical revision: `da30586a0912a05d5122aeba81f42c3bb2c8d839`.
- Implementation revision: `fe87cd03ba5455eda6bf6d2851335e6eae93d47b`.
- Evidence log/report publication was committed separately from product implementation and pushed to canonical `main` after the cold-run stop.
- Clean managed worktree: `C:\Users\sekip\.codex\worktrees\pl0350-hosted-315-novtk\PackLab`.
- Fetched `origin/main`, confirmed the worktree had no local changes/divergence, and fast-forwarded it to the authorized start revision. After implementation publication and fetch, local `HEAD` and `origin/main` were both `fe87cd03ba5455eda6bf6d2851335e6eae93d47b`; trees matched and the worktree was clean.
- The owner Desktop checkout's pre-existing modified `geometry_adapter.py` and untracked `scan_design_heatmap.py` files were left untouched.
- Read the active R01 prompt, matching R01 audit criteria, root `TASKS.md` project status, parent PL-0350 prompt/audit references, and required source/build/license contracts. No conflict was found.

## Implementation files and changes

Product files changed in the implementation commit:

- `.github/workflows/windows-studio-build.yml`
- `tests/ci/test_windows_studio_build_workflow.py`

The three setup-python bootstrap pins for capacity preflight, OCCT SDK, and controlled OCP runtime now use `3.12.10`; the package job retains `3.12`. Native conda-forge Python and libpython remain locked to 3.12.15 and their existing SHA-256 values. The workflow asserts the setup-python identity for capacity reporting and the micromamba Python identity before native jobs. The native OCP CMake executable and prefix continue to come from the native interpreter. The optional `preflight_only` dispatch input defaults false and job-level guards explicitly skip OCCT, OCP, and Studio when it is true. Manual-only trigger and full revision/ref gates remain in place.

No lock, native contract, source archive, license/notice file, root `TASKS.md`, independent audit, owner decision, or user runtime file was changed.

## Local validation

Commands and outcomes on the implementation tree:

| Command | Result |
| --- | --- |
| `uv run --locked pytest tests/ci/test_windows_studio_build_workflow.py -q` | PASS, 4 passed |
| `uv run --locked ruff check core apps tools tests` | PASS |
| `uv run --locked ruff format --check tests/ci/test_windows_studio_build_workflow.py` | PASS |
| `uv run --locked mypy core apps tools` | PASS, 236 files |
| `uv run --locked python -m compileall -q core apps tools tests` | PASS |
| PyYAML workflow parse and job/pin inspection | PASS; three bootstrap jobs at 3.12.10, package job at 3.12, native jobs guarded |
| `git diff --check` and staged equivalent | PASS |

Tests cover the bootstrap/native version split, unchanged 3.12.15 conda lock, CMake Python provenance, `preflight_only` job skipping, exact ref and affirmative manual dispatch gates, and manual-only trigger restriction. The implementation did not modify native Python source; no full repository test suite or local native compile was run.

## GitHub publication and workflow evidence

- Implementation commit message: `Fix hosted Python bootstrap toolcache pin`.
- Ordinary `git push origin HEAD:main` failed twice with `remote: fatal error in commit_refs`; `origin/main` was confirmed unchanged. The prompt explicitly authorized publishing this implementation. The exact implementation tree was then published with the GitHub Git-data API using an `expected_sha` guard and non-force ref update from parent `da30586a...`.
- Published commit: `fe87cd03ba5455eda6bf6d2851335e6eae93d47b`, parent `da30586a0912a05d5122aeba81f42c3bb2c8d839`, tree identical to the locally reviewed implementation tree. A local commit object `3831fcc9a780f47b357dba20c9ce9e308d5e15e6` with that same tree/parent was created before the standard push failure; GitHub's API serialization yielded the published SHA above. No content discrepancy resulted.
- Exact-SHA Windows Python Quality run: https://github.com/Sekiph82/PackLab/actions/runs/38256982630 — SUCCESS, 3m26s; lock validation, Ruff, formatting, mypy, and unit/repository tests passed.
- Diagnostic preflight-only run: https://github.com/Sekiph82/PackLab/actions/runs/38257424866 — SUCCESS, 28s. Job `114839019830` succeeded; OCCT `114839158495`, OCP `114839159198`, and Studio `114839160229` were skipped. Logs show setup-python installed CPython 3.12.10 from `C:\hostedtoolcache\windows\Python\3.12.10\x64`. The generated-source check reported 319 input modules, 315 output modules, and archive SHA-256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`. The job step summary records free disk, existing artifact/cache usage, ZIP size, patched-tree size, and source inventory; the rendered numeric step-summary content was not available through the Actions log/API output inspected for this handoff.
- The native lock was rechecked: CPython 3.12.15 SHA-256 `9476db87d6af903245b160190de22448b07fced7f700b84744858f4df90b5b28`; libpython 3.12.15 SHA-256 `8a6489422d213c1ce80f156c7d4951b1276b82f09ae329f624969ef93833639c`.

## One authorized cold continuation — hard stop

Cold run: https://github.com/Sekiph82/PackLab/actions/runs/38257727675
Exact head SHA: `fe87cd03ba5455eda6bf6d2851335e6eae93d47b`
Run conclusion: **FAILURE**, 5m07s total.

| Job | Result | Evidence |
| --- | --- | --- |
| Capacity/source preflight `114840035571` | PASS, 23s | The same exact 319-to-315 source patch check passed. Its step summary recorded capacity/storage data. |
| OCCT SDK `114840209934` | FAIL, 4m41s | Micromamba installed the locked Python/libpython 3.12.15 packages; the explicit native Python 3.12.15 identity assertion passed. Exact SDK cache key `Windows-x64-occt-sdk-v2-2be7a8bdc7e5cf5fbe52770b19c7d6324a057900f7c64f1e5cd84ca7a53666e4` was not found. The next source-fetch step failed before archive download or source verification. |
| OCP native build `114842151906` | SKIPPED | Dependent stage did not run. |
| Studio package `114842152536` | SKIPPED | Dependent stage did not run. |

The failed step invoked `uv run --locked python tools/packaging/fetch_verify_windows_native_sources.py ...`. At `tools/packaging/fetch_verify_windows_native_sources.py:12`, importing `tools.packaging.validate_windows_native_source_lock` raised `ModuleNotFoundError: No module named 'tools'`. PowerShell then raised `A locked corresponding-source archive failed verification.` This is a source-fetch script import failure; no claim is made that an archive failed its hash check. The cache restore was a miss. Source fetch/verification, OCCT compilation, durable SDK artifact upload, OCP compilation, DLL manifest, installer, smoke/compliance evidence, and warm-cache run did not occur. No native output artifact or artifact SHA exists from this run.

Per the frozen R01 prompt, this first cold failure is the hard stop. No retry, warm run, worker/timeout change, alternate source route, or adjacent PL task was attempted. Existing cache contents were not produced or validated by this failed run.

## Safety and remaining evidence boundaries

- No local OCCT/OCP/pywrap/C++ compilation, owner Desktop executable update, OwnerDev refresh, signing, public release, private-data upload, or shared-cache deletion occurred.
- No installer, compiled OCP module, stage artifact, source verification evidence, or redistribution clearance was produced. `legal_review_required=true` and `public_release_authorized=false` remain; no legal approval is claimed.
- Secrets/privacy review: no secrets or private supplier/customer data were added to the changed files or published. The hosted jobs used repository workflow inputs and public source/archive material only.
- Root `TASKS.md`, ChatGPT audit criteria/verdict files, and owner decision files remain unchanged.
- The cold diagnostic demonstrates that the setup-python/native interpreter version split works through micromamba environment creation, but does not prove source/build/package acceptance.

## Handoff

`BATCH_STOPPED_AT_PL-0350 / OCCT_SOURCE_FETCH_FAILED_TO_IMPORT_TOOLS`

Await independent ChatGPT audit. Do not mark PL-0350 accepted or start PL-0351, PL-0368, or M17.
