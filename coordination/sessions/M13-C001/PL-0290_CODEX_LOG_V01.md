# PL-0290 - Codex Implementation Log V01

Task: **Implement CAD capability adapter and version diagnostics**  
Cycle: **M13-C001**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0290_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0290_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live `TASKS.md` and M13 master authorization were reread at `625d5b192a13b64ed618867dfad34f00c6d84d4f`; ordered batch remains PL-0289 through PL-0309 / READY / CODEX. M12 remains `AUDITED_PASS`; PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`; M14+ remains unauthorized.
- This isolated worktree began at `625d5b192a13b64ed618867dfad34f00c6d84d4f`, equal to `origin/main`. `git fetch origin main` before changes reported 0 ahead / 0 behind. Canonical Desktop owner-local files remain outside this worktree and were preserved.
- Read the master/child prompts and criteria, PL-0289 prompt and log, ADR-0005, M09 physical-validation deferral, M12 audit, dependency/license register, and batch protocol.

## Implementation

- Added a PackLab-owned CAD adapter in `core/src/packlab_core/cad_adapter.py`. Its public contracts use immutable PackLab dataclasses/enums, plain numeric/string values, and opaque shape handles; they expose no OCP classes.
- `profile_to_cad_input` and `cross_section_to_cad_input` deterministically preserve source identity, point order, scale state, and coordinate units. `RELATIVE` stays `reconstruction_units`; `METRIC_UNVERIFIED` stays `mm_unverified`.
- Shape handles bind to the exact Design Model revision and preserve either `CAPTURED_SCAN_MASTER` or `STANDALONE_DESIGN_GEOMETRY` parent authority. Physical validation stays `DEFERRED_OWNER_VALIDATION`; mold use remains unauthorized.
- `probe_cad_runtime` only inspects the installed PL-0289 binding. It reports the observed package and Windows kernel binary versions, platform/architecture, and independent states for BREP construction, revolve, loft, booleans, topology validation, tessellation, STEP read/write, and STL write. Import and individual capability failures are surfaced without package installation/download fallback.
- Added 12 focused tests for deterministic conversion, both scale states, both parent modes, opaque PackLab contracts, no binding-type leakage, unavailable import, per-capability error reporting, and actual selected binding/kernel versions and capability probes.

## Files changed

- `core/src/packlab_core/cad_adapter.py`
- `tests/core/test_cad_adapter.py`
- `coordination/sessions/M13-C001/PL-0290_CODEX_LOG_V01.md` (this log only)

Implementation commit: recorded below after publication.

## Validation commands and results

| Command/check | Expected result / failure condition | Actual result |
| --- | --- | --- |
| `uv run --locked pytest -q tests/core/test_cad_adapter.py` | Adapter-specific authority, conversion, import failure, leakage, and installed-runtime probes pass. | PASS: 12 passed. |
| `uv run --locked pytest -q` | Full locked suite passes; any unexpected failure is a regression. | PASS: 1,502 passed, 6 skipped, 1 deselected, 2 existing duplicate-ZIP-name warnings in 55.57s. |
| `uv run --locked ruff check core/src/packlab_core/cad_adapter.py tests/core/test_cad_adapter.py` | Changed Python files pass Ruff. | PASS. |
| `uv run --locked ruff format --check core/src/packlab_core/cad_adapter.py tests/core/test_cad_adapter.py` | Changed Python files are formatted. | PASS. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/cad_adapter.py` | Adapter types pass without treating imported legacy files as changed scope. | PASS: no issues in the adapter. |
| `uv run --locked mypy core/src/packlab_core/cad_adapter.py` | Report adapter/import typing issues for review. | Adapter is clean; command reports 2 pre-existing errors in `calibration/marker_detection.py` (lines 112 and 140), reached through imports. They are outside this child's scope. PL-0289 had already recorded 28 existing whole-tree mypy errors across 9 unrelated files. |
| `uv run --locked python -m compileall -q core/src/packlab_core/cad_adapter.py tests/core/test_cad_adapter.py` | Changed sources compile. | PASS. |
| `uv lock --check` | Existing locked dependency graph remains consistent. | PASS; PL-0290 changes no dependency or lockfile. |
| `git diff --check` | No whitespace errors. | PASS. |
| Source/scope/privacy scan of adapter and tests | No runtime package/network fallback, secrets, private inputs, generated binaries, protected tracker/audit changes, or later-child scope. | PASS. Search found only binding imports and capability declarations; no installer/download/network client. `TASKS.md`, audit files, dependencies, and M14+ files are unchanged. |
| Runtime diagnostics test | Observe binding/kernel version, platform, and all required capability states using the locked runtime. | PASS: `cadquery-ocp-novtk` 7.9.3.1.1; OCCT/TKernel 7.9.3; Windows AMD64; all nine required capability probes AVAILABLE. |

## Failures, fixes, limitations

- First focused test run exposed a test annotation assertion bug and an STL probe that had not tessellated its temporary box. Corrected the assertion and meshed the probe shape before STL writing; all 12 focused tests now pass.
- Initial targeted mypy identified adapter annotations that were too broad/narrow for private binding values and one imported pre-existing `marker_detection.py` typing issue. Corrected adapter typing; `mypy --follow-imports=silent` is clean. The unsilenced command continues to report only the two existing `marker_detection.py` errors documented above.
- Capability probing exercises representative local operations. It establishes installed runtime availability and file-format operation support only; it does not establish geometric accuracy, physical validity, mold readiness, manufacturability, or certification.
- PL-0289's HIGH native-library licensing/notice redistribution gate remains in force. PL-0290 does not modify that dependency decision or clear redistribution.

Implementation commit: `3d05ad4e44042ccf549eddaddd07bf2fef756289`

## Handoff

Implementation and this log are published in separate commits. This child has not been self-audited. The ordered batch may continue only under the frozen master protocol and only while green.

READY_FOR_INDEPENDENT_AUDIT
