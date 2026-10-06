# PL-0347 - Codex Prompt V02

Task: **Close configured-source mypy debt and make Windows Python quality gate genuinely green**
Milestone: **M16 - CI/CD, Signing & Distribution**
Cycle: **M16-C001-R01**

This V02 supersedes PL-0347 V01 after the independently accepted quality-gate stop.

Partial audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/M16-C001_CHATGPT_PARTIAL_AUDIT_V01.md

Audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0347_CHATGPT_AUDIT_CRITERIA_V02.md

## Start rule

Synchronize the execution checkout non-destructively with latest `origin/main`. Preserve owner-local work. Verify live root `TASKS.md` authorizes M16-C001-R01 / PL-0347 V02.

Read before editing:

- M16 partial audit V01;
- PL-0347 V01 prompt/criteria/log;
- current Windows quality workflow and CI contract test;
- M15 final audit;
- M13/M14 authority audits relevant to Design Model provenance;
- exact tests for each touched source seam.

Do not edit root `TASKS.md`.

## Frozen goal

Keep the existing Windows quality command exactly:

`uv run --locked mypy core apps tools`

as a hard gate.

V02 succeeds only when:

- hosted Windows mypy reports zero errors;
- Ruff lint passes;
- changed-file Ruff format passes;
- locked full pytest passes;
- no authority/runtime behavior is weakened.

Do not solve this task by:

- `# type: ignore`;
- mypy `exclude`;
- disabling error codes;
- per-module ignore sections;
- baseline/allowlist files;
- `continue-on-error`;
- narrowing mypy scope;
- workflow soft-fail;
- unchecked `cast(Any, ...)`;
- replacing missing IDs with empty/fake strings;
- broad signature weakening to `Any` or `object`.

A typed helper/cast is allowed only after an explicit runtime validation proves the narrower type and preserves the existing contract.

## Authorized source scope

Remediate the 46 errors in exactly these current files, plus directly corresponding tests/helpers when genuinely required:

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

Do not opportunistically perform unrelated refactors.

## Required remediation behavior

### A. Dynamic/OpenCV values

For marker detection, make image shape / detector outputs statically truthful through explicit guards or small validated helpers. Existing supported/unsupported image behavior must remain unchanged.

### B. Protocol and JSON numeric/boolean parsing

For transfer protocol and PackScan/import-report parsing, replace direct operations on `object` with explicit typed extraction/validation helpers.

Preserve current accepted/rejected wire-format behavior exactly unless the current implementation is demonstrably unsafe. If a behavioral tightening is necessary, add explicit characterization tests and document why it is fail-closed rather than a contract change.

### C. Optional authority/provenance identifiers

For jerrycan/assembly paths, inspect the actual domain semantics before fixing Optional errors.

- Do not convert `None` to empty/fabricated authority IDs.
- If the downstream record legitimately permits standalone/non-captured authority, make that receiving contract truthful.
- If non-null is an invariant for this path, prove it with an explicit branch/guard and preserve the existing fail-closed error semantics.
- Do not weaken captured-vs-standalone Design Model authority.

### D. Engineering export

Fix the local source-type collision by using separate variables/narrowed branches for Scan Master versus Design Model export sources. Preserve existing source selection, format availability and authority labels.

Accept `Mapping[str, object]` versus `dict[str, object]` truthfully where the helper is read-only, or normalize explicitly without changing manifest contents.

### E. Packaging Library JSON parsing

Replace untyped dict access with bounded typed parse helpers that validate exact fields before constructing domain links.

Malformed canonical/library state must fail closed; do not merely cast values to the requested types.

## Validation requirements

Run locally before publication:

- `uv lock --check`
- `uv run --locked ruff check core apps tools tests`
- Ruff format check for all changed Python files
- `uv run --locked mypy core apps tools` => **zero errors**
- focused tests for every touched source seam
- `uv run --locked pytest -q`
- targeted `python -m compileall`
- `git diff --check`
- dependency/lockfile/scope/privacy review

Then publish and obtain a **fresh real hosted Windows run** of `.github/workflows/windows-python-quality.yml`.

The hosted run must pass every required step, including:

- lock validation/install;
- Ruff lint;
- changed-file Ruff format;
- mypy;
- pytest.

Record run ID/URL, Python/uv facts and exact final test count.

Do not claim hosted PASS from a local run.

## Publication

Publish implementation/evidence commit(s), then publish:

`coordination/sessions/M16-C001/PL-0347_CODEX_LOG_V02.md`

in a distinct log-only commit.

The log must include:

- original 46-error baseline;
- per-file remediation summary;
- proof that no ignore/baseline/config weakening was introduced;
- local mypy zero-error result;
- fresh hosted Windows run result;
- full suite result;
- exact changed files/commits;
- final local/origin/GitHub parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
