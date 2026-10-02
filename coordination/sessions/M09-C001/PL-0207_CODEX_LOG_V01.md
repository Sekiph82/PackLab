# PL-0207 - Codex Implementation Log V01

Task: **Select and persist front direction**

Date: 2026-10-02

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0207_CODEX_PROMPT_V01.md

Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0207_CHATGPT_AUDIT_CRITERIA_V01.md

## Repository and authorization

- Repository root: `C:/Users/sekip/Desktop/PackLab`.
- Branch/remote: `main` / `https://github.com/Sekiph82/PackLab.git`.
- Live tracker rechecked: M09-C001 ordered `PL-0202` through `PL-0224`, `READY`, `CODEX`.
- Starting synchronized SHA: `8390e4009bcc018a3f914bb7603765720691b3d5`.
- Per-child sync: fetched `origin/main`; divergence `0 0`, clean before edits.
- Master prompt/protocol, repository coordination policies, accepted M08 audit, and this child prompt/criteria were read.
- Mandatory pre-read read in full: `docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md`.

## Implementation

Added `core/src/packlab_core/front_direction.py`. It accepts an explicitly supplied direction from either an operator selection or a bounded algorithmic candidate, validates a finite nonzero vector in canonical XY (within a strict horizontal tolerance), normalizes and deterministically serializes it, and hashes all selection and parent provenance into a versioned revision ID. Records carry actor/evidence IDs, base-plane and upright selections, geometry, reconstruction and camera revisions, and coordinate units. The record explicitly leaves `physical_front_verified=false`; this contract does not infer physical front or propose candidates itself.

Added `ProjectManager.persist_front_direction` to append records under `measurement_provenance.front_direction_revisions` in authoritative editable project state and set the active revision pointer. It validates the supplied current parent IDs, rejects duplicate/stale records, and uses the existing expected-project-revision check for optimistic concurrency. Prior serialized records remain in the append-only history and survive project reopen.

Changed files:

- `core/src/packlab_core/front_direction.py` (new)
- `apps/windows-studio/src/packlab_studio/project.py`
- `tests/core/test_front_direction.py` (new)
- `tests/studio/test_project_revision.py`

No dependency, model, hosted service, private capture, generated geometry, physical measurement, or M10 work was added. `TASKS.md`, audit-owned files, RAW_CAPTURE, and accepted M08 artifacts are unchanged. Credential-pattern scan returned no matches; changed files are source and tests only, with no binary or generated artifact.

## Validation evidence

| Command | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_front_direction.py tests/studio/test_project_revision.py tests/core/test_upright_alignment.py tests/core/test_coordinate_frame.py` | New behavior, project persistence, and predecessor front/axis contracts pass. | Passed: `35 passed`. |
| `uv run --locked pytest -q` | Exact locked full suite exits 0; any failed test blocks PL-0207. | Exit 0: `1037 passed, 7 skipped, 1 deselected, 2 warnings` in 17.69s. Existing duplicate ZIP-entry warnings remain in `tests/packscan/test_container.py` and `tests/transfer/test_validation_gate.py`. |
| `uv run --locked ruff check core/src/packlab_core/front_direction.py apps/windows-studio/src/packlab_studio/project.py tests/core/test_front_direction.py tests/studio/test_project_revision.py` | No changed-file lint errors. | Passed: `All checks passed!`. |
| `uv run --locked ruff format --check core/src/packlab_core/front_direction.py apps/windows-studio/src/packlab_studio/project.py tests/core/test_front_direction.py tests/studio/test_project_revision.py` | Changed Python files formatted. | Passed: all four files already formatted. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/front_direction.py apps/windows-studio/src/packlab_studio/project.py` | Changed implementation type-checks. | Passed: `Success: no issues found in 2 source files`. |
| `uv run --locked python -m compileall -q core/src/packlab_core/front_direction.py apps/windows-studio/src/packlab_studio/project.py tests/core/test_front_direction.py tests/studio/test_project_revision.py` | Changed Python files compile. | Passed, exit 0. |
| `git diff --check` and `git diff --cached --check` | No whitespace errors. | Passed. Git emitted only its CRLF conversion notice for two edited tracked Python files. |
| `git diff --cached --name-only`, protected-file/dependency guard, and credential-pattern scan | Only authorized files changed; trackers and dependency manifests untouched; no credential pattern. | Passed. Exactly four source/test paths staged; tracker/audit/dependency guards had no diff; credential scan returned no matches. |

Coverage includes cardinal and arbitrary horizontal vectors, normalization, vertical/zero/non-finite rejection, explicit operator actor/evidence provenance, deterministic metadata, stale parent rejection, append-only history, and persistence across project reopen. No physical front or metric-accuracy claim is made. An initial direct `python -m pytest` attempt could not import the workspace packages; rerunning through the repository's locked `uv` environment resolved collection. Ruff initially identified import-order/format issues, which were corrected and all changed-file checks rerun successfully.

## Publication

- Implementation commit: `4ea530ca1064746ce18640729666f3133787f8ff` (`measurement: persist versioned front direction`).
- Pushed to `origin/main`; fetch confirmed local `HEAD` and `origin/main` both equal `4ea530ca1064746ce18640729666f3133787f8ff` before the log-only commit.
- No owner work was overwritten. No audit verdict was created.

READY_FOR_INDEPENDENT_AUDIT
