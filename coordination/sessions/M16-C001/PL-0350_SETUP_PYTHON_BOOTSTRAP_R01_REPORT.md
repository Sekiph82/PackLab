# PL-0350 setup-python Bootstrap R01 — Evidence and Blocker Report

Date: 2026-10-12
Status: **BATCH_STOPPED_AT_PL-0350 / AWAITING_INDEPENDENT_AUDIT**
Blocker: `OCCT_SOURCE_FETCH_FAILED_TO_IMPORT_TOOLS`

## Outcome

The three hosted Windows bootstrap interpreters were changed to CPython 3.12.10 while the SHA-pinned native conda-forge Python/libpython 3.12.15 lock remained unchanged. The exact-SHA quality workflow and the `preflight_only=true` diagnostic passed. The diagnostic confirmed the 3.12.10 toolcache and 319-to-315 official source patch and skipped all three native/package jobs.

The single authorized cold continuation then failed in Stage A before downloading/verifying corresponding source archives or building OCCT. The failure was `ModuleNotFoundError: No module named 'tools'` when `fetch_verify_windows_native_sources.py` imported the repository module. The OCCT SDK cache lookup missed; subsequent SDK checkpoint steps and the OCP and Studio jobs were skipped. No native artifact, installer, compliance clearance, or warm-cache evidence was produced. R01 does not meet PL-0350 acceptance.

## Revisions and run evidence

| Evidence | Revision / result |
| --- | --- |
| Canonical starting revision | `da30586a0912a05d5122aeba81f42c3bb2c8d839` |
| Published implementation | `fe87cd03ba5455eda6bf6d2851335e6eae93d47b` |
| Exact-SHA Windows Python Quality | [38256982630](https://github.com/Sekiph82/PackLab/actions/runs/38256982630), success, 3m26s |
| Preflight-only diagnostic | [38257424866](https://github.com/Sekiph82/PackLab/actions/runs/38257424866), success, 28s |
| Authorized cold continuation | [38257727675](https://github.com/Sekiph82/PackLab/actions/runs/38257727675), failure, exact implementation SHA |
| Failed OCCT/source-fetch job | [114840209934](https://github.com/Sekiph82/PackLab/actions/runs/38257727675/job/114840209934), failure |
| Cold capacity/source job | [114840035571](https://github.com/Sekiph82/PackLab/actions/runs/38257727675/job/114840035571), success |
| OCP job | [114842151906](https://github.com/Sekiph82/PackLab/actions/runs/38257727675/job/114842151906), skipped |
| Studio job | [114842152536](https://github.com/Sekiph82/PackLab/actions/runs/38257727675/job/114842152536), skipped |

## Bootstrap and native Python evidence

Both preflight runs report setup-python CPython `3.12.10` installed from `C:\hostedtoolcache\windows\Python\3.12.10\x64`. In the cold OCCT job, micromamba successfully created the environment with the locked CPython `3.12.15` and libpython `3.12.15` packages; the explicit native Python 3.12.15 assertion passed. The lock hashes remain:

- Python 3.12.15: `9476db87d6af903245b160190de22448b07fced7f700b84744858f4df90b5b28`
- libpython 3.12.15: `8a6489422d213c1ce80f156c7d4951b1276b82f09ae329f624969ef93833639c`

The native interpreter identity was reached and verified, but no native compiler ran. The OCP CMake `Python_EXECUTABLE` wiring is source/test evidence only; no compiler invocation proves it end-to-end in this run.

## Source patch and capacity evidence

The preflight-only job and cold capacity/source job each emitted `OCP_GENERATED_SOURCE_PATCH_PASS`: 319 input modules to 315 output modules, 630 retained registrations, source archive SHA-256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`. The official ZIP verification/patch diagnostic passed. This is source-preparation evidence, not a built native runtime.

Each capacity job wrote a GitHub Actions step summary containing bootstrap identity, free disk bytes, existing artifact/cache usage, ZIP bytes and SHA, patched-tree bytes, module inventory, timing budget, and license/source paths. The run/job REST and text-log outputs inspected here confirmed the summary-writing step and source patch result, but did not expose the rendered numeric summary values; this report therefore does not invent free-space or storage figures.

## First hard stop and artifact inventory

The cold source-fetch step ran `uv run --locked python tools/packaging/fetch_verify_windows_native_sources.py --download-dir ... --evidence ...`. Python failed at line 12 importing `tools.packaging.validate_windows_native_source_lock` with `ModuleNotFoundError: No module named 'tools'`. The PowerShell wrapper converted the nonzero exit into `A locked corresponding-source archive failed verification.` The exception occurred before archive download/hash verification; it must not be described as a source archive hash mismatch.

The exact OCCT SDK cache lookup key was `Windows-x64-occt-sdk-v2-2be7a8bdc7e5cf5fbe52770b19c7d6324a057900f7c64f1e5cd84ca7a53666e4`, and Actions logged `Cache not found`. No cache save or validated checkpoint occurred. No run artifact was uploaded. The OCP, packaging, and warm runs did not occur. There is no compiled OCP DLL manifest, installer hash, native smoke result, license/notice clearance, or native artifact ID to report.

## Local and hosted validation

- Focused workflow tests: `uv run --locked pytest tests/ci/test_windows_studio_build_workflow.py -q` — 4 passed.
- Ruff, Ruff format, mypy (236 files), compileall, PyYAML workflow parse, and `git diff --check` — pass; exact commands/results are recorded in the Codex log.
- Hosted Python Quality run passed all reported checks on the implementation SHA.
- The full repository suite was not rerun; no native code was changed.
- No local native build was run.

## Safety and required disposition

The managed worktree was clean at start and synchronized to live `origin/main`; final implementation SHA matched `origin/main`. The dirty owner Desktop checkout was preserved. No owner runtime, root tracker, independent audit, secret, or private data was changed or published. No signing or public release occurred. Engineering redistribution clearance remains unproven; `legal_review_required=true`, `public_release_authorized=false`.

Required state: **`BATCH_STOPPED_AT_PL-0350 / OCCT_SOURCE_FETCH_FAILED_TO_IMPORT_TOOLS`**. This report does not authorize another cold run, a warm run, alternate toolchain/source, adjacent task, or acceptance. Await independent audit.
