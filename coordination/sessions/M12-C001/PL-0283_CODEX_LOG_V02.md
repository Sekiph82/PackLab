# PL-0283 - Codex Implementation Log V02

Task: **Define tube parametric family with explicit standalone Design Geometry root**
Cycle: **M12-C001-R02**
Status: **READY_FOR_INDEPENDENT_AUDIT**

Prompt: `PL-0283_CODEX_PROMPT_V02.md`
Criteria: `PL-0283_CHATGPT_AUDIT_CRITERIA_V02.md`

## Authorization and synchronization

- Live root `TASKS.md` authorized M12-C001-R02 and the ordered PL-0283 through PL-0288 V02 continuation; no tracker, prompt or criteria mismatch was found.
- Read the R02 master prompt and criteria, M12 partial audit V02, ADR-0005, M11 accepted audit, M09 physical-validation deferral, PL-0283 V02 prompt/criteria, and mandatory Design Model binding, serialization, history, validation, and model sources.
- Starting synchronized SHA: `975ed25b87d5c281c64841a0517c1be515f1a478`. The managed worktree was clean and detached at this SHA; `origin` was `https://github.com/Sekiph82/PackLab.git`. Desktop owner checkout was left untouched.
- Before publication, fetch and divergence check showed local implementation commit one ahead and zero behind `origin/main`; ordinary push advanced `main` from `975ed25` to `2d0d5c34e279ba9617a504c75cbc0e266a86df53`. Follow-up fetch confirmed local/origin parity `0 0`.

## Implementation

Implementation/evidence commit: `2d0d5c34e279ba9617a504c75cbc0e266a86df53`.

- Added immutable `StandaloneDesignGeometryRoot` and source-kind provenance with deterministic digest/revision ID, project scope, explicit scale/unit provenance, actor/reason/time, `captured_ancestry_exists=false`, deferred physical status and mold authorization false.
- Added explicit `CAPTURED_SCAN_MASTER` and `STANDALONE_DESIGN_GEOMETRY` parent discrimination. Standalone Design Model revisions serialize without scan, reconstruction, geometry-digest or captured-scale-provenance fields. Existing captured v1 identity and serialization paths remain intact.
- Extended generic revision editing/history, strict document serialization/deserialization, validation and disposable preview metadata to standalone roots. Captured-only deviation, assembly graph and assembly export services reject standalone models.
- Added tube dimensions with bounded relationship validation, stable body/shoulder/neck/cap/crimp feature IDs, unit-bearing parameter nodes, ordered backend-neutral loft inputs and deterministic preview proxies. Supports exact captured parent bindings and explicit standalone roots. No flexible-wall deformation, physical accuracy, manufacturing, mold or CAD/BREP/STEP authority is claimed.
- Extended cross-section creation with optional immutable section ancestry so separate stations with identical profile points retain unique deterministic IDs; default behavior and existing v1 section identity are unchanged.

## Validation evidence

Focused/predecessor command:

`uv run --project core --locked pytest -q tests/core/test_design_model.py tests/core/test_design_serialization.py tests/core/test_design_history.py tests/core/test_design_validation.py tests/core/test_design_preview.py tests/core/test_design_operations.py tests/core/test_design_model_binding.py tests/core/test_assembly_graph.py tests/core/test_assembly_export_preview.py tests/core/test_design_deviation_report.py tests/core/test_cross_section.py tests/core/test_standalone_design_geometry.py`

- Expected: captured/standalone authority, tube, serialization/history/preview, and protected assembly/deviation regressions pass; invalid parent modes or impossible dimensions fail closed.
- Actual: **70 passed**.
- An earlier 35-test run found a missing standalone root on the immutable revision-construction path; history creation was fixed to preserve the root and the rerun passed. Early tube checks also found duplicate deterministic IDs for equal body stations and a deviation entrypoint that checked the Scan Master before parent mode; immutable section ancestry and mode-first rejection fixed these cases.

Scan-bound compatibility evidence:

- Existing captured serialization regression now pins Design Model revision `design-model:073ffb34da80cf16b1569f5d7dbc0b69e8fddb68c164edeb374bb37f9c90dcd0` and serialized document SHA-256 `c90772fe0630c6c9fc6eb80b3cc563cdd710e2541fe03d67b83a0ef805e92f09`.
- Expected: both remain byte/identity stable under the new authority branch. Actual: the exact assertions passed in the focused and full suites.

Required shared-contract full-suite gate, at unchanged implementation SHA `2d0d5c34e279ba9617a504c75cbc0e266a86df53`:

1. `uv run --locked pytest -q` — **1,459 passed, 6 skipped, 1 deselected**, 2 existing `zipfile` duplicate-name fixture warnings; elapsed 52.26s.
2. Immediately consecutive `uv run --locked pytest -q` — **1,459 passed, 6 skipped, 1 deselected**, same 2 fixture warnings; elapsed 48.39s.

Other required checks:

- Changed-file Ruff: `uv run --project core --locked ruff check core/src/packlab_core/assembly_export_preview.py core/src/packlab_core/assembly_graph.py core/src/packlab_core/cross_section.py core/src/packlab_core/design_deviation_report.py core/src/packlab_core/design_model.py core/src/packlab_core/design_model_binding.py core/src/packlab_core/design_preview.py core/src/packlab_core/design_serialization.py core/src/packlab_core/design_validation.py core/src/packlab_core/tube_family.py tests/core/test_design_serialization.py tests/core/test_standalone_design_geometry.py` — **All checks passed**.
- Changed-file format: `uv run --project core --locked ruff format --check core/src/packlab_core/assembly_export_preview.py core/src/packlab_core/assembly_graph.py core/src/packlab_core/cross_section.py core/src/packlab_core/design_deviation_report.py core/src/packlab_core/design_model.py core/src/packlab_core/design_model_binding.py core/src/packlab_core/design_preview.py core/src/packlab_core/design_serialization.py core/src/packlab_core/design_validation.py core/src/packlab_core/tube_family.py tests/core/test_design_serialization.py tests/core/test_standalone_design_geometry.py` — **12 files already formatted**.
- Targeted mypy with imported legacy modules suppressed: `uv run --project core --locked mypy --follow-imports=silent core/src/packlab_core/design_model.py core/src/packlab_core/design_model_binding.py core/src/packlab_core/design_serialization.py core/src/packlab_core/design_history.py core/src/packlab_core/design_validation.py core/src/packlab_core/design_preview.py core/src/packlab_core/tube_family.py core/src/packlab_core/cross_section.py core/src/packlab_core/design_deviation_report.py core/src/packlab_core/assembly_export_preview.py core/src/packlab_core/assembly_graph.py` — **Success: no issues found in 11 source files**. A broader initial mypy invocation also reported two errors in untouched `core/src/packlab_core/calibration/marker_detection.py` (`len(Any | None)` and indexing `Any | None`); changed modules were corrected and the targeted check passed.
- `uv run --locked python -m compileall -q core/src/packlab_core` — exit 0.
- Implementation diff and cached diff checks — exit 0. Child-log whitespace was corrected and rechecked before its clean log-only commit.
- No dependency, license, private scan, supplier data, asset, binary, generated reconstruction, tracker, audit, or M13 files were added or changed. Manual changed-path and added-content review found no credentials or private data.

## Scope, limitations, and handoff

- Changed only the Design Model authority/tube implementation, its narrow section identity support, regression tests, and this authorized child log. Root `TASKS.md` and all ChatGPT audit files were not modified.
- The two full-suite runs satisfy the R02 shared-authority gate before PL-0284.
- `mm_unverified` remains nominal design-unit semantics; relative dimensions remain `reconstruction_units`. PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`. Scan Master bytes and history are not mutated.
- Implementation/evidence is published and remote-visible. This log is a separate log-only publication. Independent audit and root tracker lifecycle remain ChatGPT-owned.

READY_FOR_INDEPENDENT_AUDIT
