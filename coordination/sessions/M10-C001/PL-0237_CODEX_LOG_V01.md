# PL-0237 - Codex Implementation Log V01

Task: **Record reconstruction and Scan Master versions with explicit selection**
Cycle: **M10-C001**
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0237_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0237_CHATGPT_AUDIT_CRITERIA_V01.md

## Synchronization and authorization

- Live tracker: M10-C001 continuation PL-0235 through PL-0240, `READY`, `CODEX`; M11 remains unauthorized.
- Synchronized child starting SHA: `1284ee20dbba09ced3c8adff45705cf57d5cb183` (PL-0236 master-index publication). Fetch confirmed local/origin parity and a clean worktree before PL-0237 changes.
- M09 accepted frontier remains PL-0202 through PL-0219. PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`, not passed.
- Implementation commit was pushed as a fast-forward to `origin/main`; the matching child log is published separately.

## Inputs read

- Original M10 master work order and criteria; M10 continuation V02 work order and criteria.
- PL-0237 V01 child prompt and matching audit criteria.
- PL-0233 Scan Master authority spec and its mandatory OpenReality integration architecture pre-read.
- M09 accepted partial audit and owner physical-validation deferral decision.
- `coordination/MILESTONE_BATCH_PROTOCOL.md`, `coordination/README.md`, and `coordination/AUDIT_POLICY.md`.
- Existing Scan Master, reconstruction, mask revision, and project-adjacent metadata contracts.

## Files changed

- `core/src/packlab_core/project_revisions.py` (new)
- `tests/core/test_project_revisions.py` (new)

No task tracker, audit verdict, dependency/lockfile/license file, captured source artifact, private scan, generated binary, or later-child implementation was changed.

## Implementation

Added a frozen PackLab-owned project revision registry for `RECONSTRUCTION_OBSERVATION`, `OBJECT_CAPTURE_GEOMETRY`, `M10_CLEANUP`, and `SCAN_MASTER` entries. Records carry revision IDs, artifact digests, explicit parent IDs, authority class, generated flag, scale state and provenance, and physical/mold gates. Reconstruction entries pin immutable RAW_CAPTURE IDs and digests. Append validation requires parents to exist earlier in the history, validates the allowed parent-kind chain, rejects duplicate/missing parents and generated geometry, and requires every derived entry to inherit the parent's scale state and provenance. A Scan Master entry additionally requires `DEFERRED_OWNER_VALIDATION`, a scale provenance ID, and false mold authorization.

The immutable registry exposes append and active-selection operations with an expected-state revision token. Each append or actual selection change produces a new state; stale writers fail with a concurrency conflict. Active pointers can reference only an existing revision of the matching kind. Append-only selection events replay to the current active pointer, so switching an active revision does not rewrite any revision or downstream parent ID.

Canonical serialization includes the full revision and selection history plus a SHA-256 envelope digest. Deserialization verifies the digest, contract, duplicate JSON keys, parent graph, selection-event history and active pointers, preserving the registry across serialize/reopen. No project artifact bytes are mutated by this metadata contract.

## Validation evidence

| Command | Expected / failure condition | Actual |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_project_revisions.py tests/core/test_scan_master.py tests/core/test_repeat_scan_registration.py tests/core/test_mask_revisions.py tests/core/test_reconstruction_export.py tests/core/test_reconstruction_artifact_diagnostics_core.py tests/core/test_physical_accuracy_benchmark.py tests/calibration/test_scale_provenance.py` | Registry cases and Scan Master, registration, revision, reconstruction, and scale predecessors pass; any failure blocks this child. | Passed: `52 passed in 1.26s`. Covers append/reopen/switch, active pointer/event history, parent stability, duplicate/missing/wrong-kind revisions, immutable RAW_CAPTURE reference, inherited deferred scale, corruption detection and stale-writer conflicts. |
| `uv run --locked pytest -q` | Exact locked full repository suite exits 0; any failure blocks this child. | Passed: `1221 passed, 6 skipped, 1 deselected, 2 warnings in 19.16s`. The warnings are existing duplicate ZIP fixture names in PackScan and transfer validation tests. |
| `uv run --locked ruff check core/src/packlab_core/project_revisions.py tests/core/test_project_revisions.py` | Changed-file lint is clean. | Passed: `All checks passed!`. |
| `uv run --locked ruff format --check core/src/packlab_core/project_revisions.py tests/core/test_project_revisions.py` | Changed files are formatted. | Passed: `2 files already formatted`. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/project_revisions.py` | New registry type-checks. | Passed: `Success: no issues found in 1 source file`. |
| `uv run --locked python -m compileall -q core/src/packlab_core/project_revisions.py tests/core/test_project_revisions.py` | Changed Python files compile; nonzero exit blocks this child. | Passed, exit 0. |
| `git diff --check` and staged diff check | No whitespace errors. | Passed, exit 0. |
| Changed-path, credential/private-key, and later-scope scans | Only the two authorized PL-0237 paths; no credential/private-key pattern or M11/later-child implementation. | Passed: exactly two changed paths, scans clean. No dependency, license, tracker or audit path changed. |

## Failures and fixes

Initial static checks identified formatting and local type-narrowing issues in registry validation. These were corrected; Ruff, format check, mypy, compileall, focused/predecessor suite and exact full suite all passed on the final implementation.

## Limitations and authority boundaries

- The contract persists metadata as canonical serialized bytes for the owning project store to write and reopen. It does not write or mutate project geometry artifacts.
- Expected-state revision tokens provide optimistic concurrency checks at this core registry boundary; callers must apply returned state only against the same current project registry.
- No physical validation, metric verification, mold-use authorization, RAW_CAPTURE mutation, or M11 work was performed.

## Publication

- Implementation/evidence commit: `6aff6284043f13f706eee2c6c80a217f565f524c` (`Add append-only project revision registry`).
- `git push origin HEAD:main` succeeded. The child-log-only commit follows separately.
- Secrets/privacy review: changed code and tests contain synthetic identifiers/digests only; credential/private-key scan clean.
- Final child status: implementation checks green; awaiting independent ChatGPT audit. This is not acceptance.

READY_FOR_INDEPENDENT_AUDIT
