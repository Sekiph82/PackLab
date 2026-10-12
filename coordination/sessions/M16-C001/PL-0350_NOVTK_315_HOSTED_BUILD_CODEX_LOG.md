# PL-0350 Hosted 315-Module No-VTK Build — Codex Implementation Log

Date: 2026-10-12
Disposition: **BATCH_STOPPED_AT_PL-0350 / AWAITING_INDEPENDENT_AUDIT**
Stop code: `CAPACITY_PREFLIGHT_SETUP_PYTHON_VERSION_UNAVAILABLE`

## Authority and exact revisions

- Active prompt: `PL-0350_NOVTK_315_HOSTED_BUILD_CODEX_PROMPT.md` (SHA-256 `6ea608af59d91483cc2194ef69ad62f5fb8238632caaf24f7773014f17f93aa6`).
- Matching criteria: `PL-0350_NOVTK_315_HOSTED_BUILD_CHATGPT_AUDIT_CRITERIA.md`.
- Owner approval: `PL-0350_OWNER_APPROVAL_HOSTED_BUILD_315_NOVTK.md`.
- Initial GitHub `main` / synchronized starting revision: `43a3f9fbed20fac614b3775c5b8929a9b828d4c3`.
- Safety-only commit disabling automatic native-build triggers: `ef2b43bedcec9862653895c630fa23730a83f2d2`.
- Product implementation commit, pushed to `main`: `ca167dda2fe5c11de3f45e0285fe80b573194c48`.
- Matching GitHub Python Quality run: [38240270762](https://github.com/Sekiph82/PackLab/actions/runs/38240270762), conclusion `success`, exact head SHA `ca167dda2fe5c11de3f45e0285fe80b573194c48`.
- Single authorized cold dispatch: [38240655846](https://github.com/Sekiph82/PackLab/actions/runs/38240655846), conclusion `failure`, exact head SHA `ca167dda2fe5c11de3f45e0285fe80b573194c48`.

GitHub `origin/main` matched the implementation SHA before evidence authoring. The managed worktree was clean after the implementation commit. The separate owner checkout was observed before and after with the same preexisting state: modified `core/src/packlab_core/geometry_adapter.py`, untracked `core/src/packlab_core/scan_design_heatmap.py`, and untracked `tests/core/test_scan_design_heatmap.py`. No owner checkout files were edited. OwnerDev/current and previous-good runtime were not refreshed or modified.

## Change summary

The implementation changes only the gated Windows native workflow, controlled OCCT SDK build/seal and validator, official OCP generated-source patcher, native OCP C++ builder, controlled runtime bundle/contract, packaged runtime smoke, and corresponding tests. The workflow is manual-dispatch-only, requires an affirmative `run_native_build` input, exact `main` ref and exact build revision, and creates a capacity/source preflight followed by separate OCCT SDK, OCP runtime, and Studio package jobs. Each job has a 330-minute timeout. Cache restore uses exact keys; checkpoint size checks precede cache saves; same-run artifacts carry stage outputs. The installer path is unsigned and fail-closed on engineering redistribution clearance. No signing, public release, deployment, or tracker/audit mutation was added.

Source preparation uses the official OCP 7.9.3.1.1 generated Windows archive and deterministic No-VTK patcher. The real official archive was locally verified and patched in the task's bounded temporary preflight output before dispatch. The patcher recorded per-file hashes and byte lengths and verified actual source changes. The exact archive was 6,481,047 bytes, SHA-256 `290941ef2d34e7b10b7b6bde4577c5d5d0e703342f934c29a55660caaed8dd5b`, upstream revision `d69b064a3a604ebf245b1f3b14fb54c835a3a571`. The inventory was 319 module triplets and 638 declarations/calls before patching; exactly `IVtk`, `IVtkOCC`, `IVtkTools`, and `IVtkVTK` were removed, leaving 315 complete module triplets and 630 retained registrations. No pywrap invocation or opaque OCP wheel substitution occurred.

Real-archive patch output evidence from the bounded local dry-run:

- patched `OCP.cpp`: SHA-256 `28c88f6fa3c8e366a26add8fb145f7177f1e376c1b068857b247ab2fac349faf`;
- patched generated CMake input: SHA-256 `50ad079ba6686afc220b7b278ffd13a8e65dadb69a4bcf548eb50752c922ed19`;
- patch manifest: SHA-256 `113913a65a2ea8a1af94e1e12b4cbe32e13f7ac82e8defcb603339687977780e`;
- prepatch/postpatch file counts: 1,287 / 1,275.

Locked inputs: `windows_native_source_lock.json` SHA-256 `c6a32326c1463dce53a70366200e9739d853893030f0553739188d878b1bf277`; `controlled_ocp_runtime_contract.json` at implementation SHA SHA-256 `45573da96fd6f0bb8b6066521c9cdebaad4bd3f808eb8a7dc328e603bd1b44df`.

## Validation evidence

Exact monitored local command: `& .\tools\dev\run_packlab_tests.ps1 -q`. Result: **2,061 passed, 11 skipped, 1 deselected, 2 warnings in 253.34s**. Warnings were duplicate-name ZIP fixture warnings from `tests/packscan/test_container.py::test_exact_and_casefold_duplicate_names_are_rejected` and `tests/transfer/test_validation_gate.py::test_future_version_checksum_and_unsafe_zip_never_publish_extraction`. The wrapper ended `DISK_HYGIENE_PASS`; pytest peak 58,950,304 bytes, fixture peak 33,554,433 bytes, disposable peak 58,965,762 bytes, and disposable PackLab footprint after cleanup 15,312 bytes. C: free before test was 186,934,845,440 bytes; after cleanup it was 186,902,413,312 bytes (the wrapper observed 186,841,804,800 bytes before reclaiming its task-owned pytest directory).

Additional exact validations:

- `uv run --locked ruff check core apps tools tests` — passed.
- `uv run --locked ruff format --check` on all 10 changed Python files — passed.
- `uv run --locked mypy core apps tools` — passed, 236 source files.
- `uv run --locked python -m compileall -q core apps tools tests` — passed.
- Workflow parsed with PyYAML; jobs were `capacity-preflight`, `occt-sdk`, `controlled-ocp-runtime`, `build-studio`.
- `git diff --check` and `git diff --cached --check` — passed.
- GitHub Windows Python Quality run 38240270762 — passed in 3m23s, including lock validation, Ruff, formatting, mypy, and unit/repository tests.

The first safety-only push caused only ordinary Python Quality run 38236191450; that run failed because an existing workflow test expected the old 480-minute limit. The implementation test was updated for the authorized 330-minute ceiling. The exact implementation SHA quality run then passed. No native Studio build was automatically triggered by either push.

## Cold dispatch and earliest blocker

The only native workflow dispatch used `main`, `run_native_build=true`, and `build_revision=ca167dda2fe5c11de3f45e0285fe80b573194c48`. Run URL: [https://github.com/Sekiph82/PackLab/actions/runs/38240655846](https://github.com/Sekiph82/PackLab/actions/runs/38240655846).

The capacity-preflight job failed in its `Set up Python 3.12` step before disk/storage measurement, archive download, patch dry-run, or native build. Exact hosted-runner error: `The version '3.12.15' with architecture 'x64' was not found for Windows 2022.` The following preflight step was skipped. The OCCT SDK, OCP runtime, and Studio package jobs were skipped. No stage checkpoint/artifact, cache entry, OCP binary, native smoke result, compliance inventory, or installer was produced by this run. There is no cache-hit/warm run. No hosted-runner capacity result can be claimed from this dispatch.

The frozen prompt says to stop on a preflight blocker and not retry blindly. Accordingly, no retry, alternate interpreter, cache warm run, or additional native dispatch was attempted. This handoff records the exact blocker and requires independent audit/owner-directed next authorization; it does not claim PL-0350 acceptance.

## Privacy, safety, and release boundary

Only public source inputs were used. No owner-specific files/cache, credentials, private scans, supplier documents, or owner runtime were uploaded or included in artifacts. The failed workflow step exposed no token value (GitHub masked its token); the subsequent source/archive and build steps never ran. The task introduced no signing, public release, GitHub Release, tag, or production deployment. `legal_review_required=true` and `public_release_authorized=false` remain the boundary; no legal or redistribution clearance is claimed. Root `TASKS.md`, all `CHATGPT_AUDIT_*` files, and owner decision files were not edited.

## Handoff

`BATCH_STOPPED_AT_PL-0350 / AWAITING_INDEPENDENT_AUDIT`
Exact blocker code: `CAPACITY_PREFLIGHT_SETUP_PYTHON_VERSION_UNAVAILABLE`.

The exact implementation commit is `ca167dda2fe5c11de3f45e0285fe80b573194c48`. The SHA-256 of this implementation log is recorded in the matching report and master handoff after publication. No adjacent task was started.
