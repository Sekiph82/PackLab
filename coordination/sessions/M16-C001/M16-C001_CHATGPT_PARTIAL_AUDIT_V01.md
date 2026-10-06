# M16-C001 - ChatGPT Partial Audit V01

Date: 2026-10-06
Decision: **AUDITED_PARTIAL_CHANGES_REQUIRED**
Current frontier: **PL-0347 V01 blocker accepted**
PL-0348 through PL-0367: **NOT_STARTED**
PL-0368: **DEFERRED_POST_M17**

## Independent evidence inspected

- PL-0347 frozen prompt and audit criteria.
- Implementation commit `4431c7d7789789831c09ae6de77fcf239f74f00f`.
- Windows formatter correction `7cd7cc0c4b38078285a88a1aa62714a679818b1c`.
- PL-0347 builder log and M16 master log.
- Live workflow `.github/workflows/windows-python-quality.yml`.
- CI contract tests.
- Hosted Windows Actions run `37382974030` and decoded job log.
- Live Git diff from ChatGPT M16 baseline `4aca84e58bc8b82b56b1b25d960e93019481a6cf`.

## PL-0347 V01 implementation findings

The workflow implementation itself is correctly scoped and is retained.

It provides:

- `windows-latest`;
- Python 3.12;
- pinned uv 0.11.26;
- `uv lock --check`;
- `uv sync --locked --all-groups`;
- Ruff lint;
- changed-file Ruff format with Windows-safe line-ending handling;
- configured-source mypy;
- locked pytest;
- `contents: read` only;
- no secret injection;
- pinned full-SHA Actions;
- explicit timeout;
- separate preservation of the historical preview workflow.

The implementation/correction commits changed only the production workflow and its CI contract test. None of the 12 mypy-failing source files was modified by PL-0347 V01.

The hosted run proves:

- lock validation/install: PASS;
- Ruff lint: PASS;
- changed-file Ruff format: PASS after the V01 correction;
- pytest: `1972 passed, 10 skipped, 1 deselected`;
- mypy: FAIL, `46 errors in 12 files (checked 216 source files)`.

The builder correctly did **not** soften, skip or make mypy non-blocking.

## Mypy blocker classification

The blocker is real, but it is not evidence that the new CI workflow created a regression. It exposes pre-existing configured-source type debt.

The 46 errors are concentrated in these unchanged files:

1. `core/src/packlab_core/calibration/marker_detection.py`
2. `core/src/packlab_core/transfer_protocol.py`
3. `core/src/packlab_core/packscan/container.py`
4. `apps/windows-studio/src/packlab_studio/import_report.py`
5. `apps/windows-studio/src/packlab_studio/receiver.py`
6. `core/src/packlab_core/jerrycan_grip_indent.py`
7. `core/src/packlab_core/assembly_variant_swap.py`
8. `core/src/packlab_core/jerrycan_handle_void_candidates.py`
9. `core/src/packlab_core/assembly_clearance.py`
10. `apps/windows-studio/src/packlab_studio/engineering_export.py`
11. `apps/windows-studio/src/packlab_studio/packaging_library_audit.py`
12. `apps/windows-studio/src/packlab_studio/packaging_library_browser.py`

Independent source review shows these are predominantly:

- missing runtime-to-static narrowing after existing validation;
- JSON/object parsing helpers returning `object` without typed extraction;
- Optional authority IDs passed through contracts whose runtime invariant must be made explicit;
- one local variable type collision in engineering export;
- typed receiver/error-envelope narrowing.

This debt should be repaired at source. It should **not** be hidden behind a baseline file, mypy exclude, disabled error code, workflow narrowing or soft-fail.

## Frozen remediation ruling

PL-0347 V02 is authorized to repair exactly the configured-source mypy blocker while preserving runtime/domain behavior and authority.

Hard rules:

- keep `uv run --locked mypy core apps tools` unchanged as a hard CI gate;
- final mypy result must be zero errors;
- do not add `# type: ignore` to silence these errors;
- do not relax mypy configuration, exclude files, disable error codes or introduce a baseline/allowlist;
- do not use unchecked `Any`/casts as a substitute for validation;
- prefer explicit `isinstance`/shape checks and typed parsing helpers;
- preserve existing malformed-input/fail-closed behavior;
- preserve M09/M13/M14/M15 authority semantics, especially optional standalone/captured Design Model provenance;
- no `or ""` / placeholder identifier trick may convert missing authority into a fake valid authority;
- where Optional values are semantically legal, correct the receiving type/branch truthfully rather than forcing non-null;
- add/update characterization tests for any path whose runtime parsing/validation logic is touched.

## Verdict

`AUDITED_PARTIAL_CHANGES_REQUIRED`

PL-0347 V01 stop is independently accepted as a truthful quality-gate stop. PL-0347 is not yet `AUDITED_PASS`.

Resume at PL-0347 V02. PL-0348 through PL-0367 remain unauthorized until V02 is builder-green. PL-0368 remains `DEFERRED_POST_M17`.
