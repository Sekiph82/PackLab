# PL-0209 - Codex Implementation Log V01

Task: **Persist scale provenance, uncertainty and scale-state promotion rules**

Date: 2026-10-02

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0209_CODEX_PROMPT_V01.md

Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0209_CHATGPT_AUDIT_CRITERIA_V01.md

## Repository and authorization

- Repository root: `C:/Users/sekip/Desktop/PackLab`.
- Branch/remote: `main` / `https://github.com/Sekiph82/PackLab.git`.
- Live tracker rechecked: M09-C001 ordered `PL-0202` through `PL-0224`, `READY`, `CODEX`.
- Starting synchronized SHA: `324d34d46bd1cb54ee23cad1ce41181400466682`.
- Per-child sync: fetched `origin/main`; divergence `0 0`, clean before edits.
- Master prompt/protocol, repository coordination policies, accepted M08 audit, and this child prompt/criteria were read.
- Mandatory pre-reads read in full: `docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md`, `docs/calibration/pre-use-verification.md`, `docs/calibration/benchmarks/first-physical-benchmark.md`, and the linked `docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md`. Also inspected both owner-record templates and the scale-estimation/storage contracts.

## Implementation

Added `core/src/packlab_core/calibration/scale_provenance.py`. It snapshots camera-bound scale estimates with their used observation IDs, physical reference IDs/digests/values/units, residuals, rejected observation reasons, algorithm/outlier versions, reconstruction and camera parents, uncertainty representation, UTC creation time, and actor/process provenance. A rejected estimate remains `RELATIVE` with no factor; an estimate remains `METRIC_UNVERIFIED` until an explicit promotion call succeeds. Provenance identities are deterministic hashes of the serialized evidence and metadata.

Promotion requires a structurally complete `accepted_owner_physical` evidence record with `ACCEPTED_FOR_CAPTURE` status, owner measurement completion, UTC verification timestamp, operator/instrument references, and exact matching verified reference IDs, digests, marker IDs and measured dimensions. Synthetic fixture, nominal SVG, AI visual-reference, and incomplete evidence cannot promote. The `ai_visual_reference_measurement_authority` field remains false. `ProjectManager.persist_scale_provenance` appends immutable revisions to project authority state, updates the active provenance and scale state, checks the current reconstruction parent, and uses project optimistic revision checks.

The public repository contains no completed owner physical verification record. Tests use only synthetic fixture data and verify that it remains unverified or is rejected for promotion. No real `METRIC_VERIFIED` record was created; the successful owner-evidence promotion path remains unverified until owner evidence is supplied and independently inspected.

Changed files:

- `core/src/packlab_core/calibration/scale_provenance.py` (new)
- `core/src/packlab_core/calibration/__init__.py`
- `apps/windows-studio/src/packlab_studio/project.py`
- `tests/calibration/test_scale_provenance.py` (new)

No dependency, model, hosted service, private capture, owner measurement, generated geometry, or M10 work was added. `TASKS.md`, audit-owned files, RAW_CAPTURE, accepted M08 artifacts, and dependency manifests are unchanged. Credential-pattern scan returned no matches; staged changes contain only Python source and tests, with no binary or generated artifact.

## Validation evidence

| Command | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/calibration/test_scale_provenance.py tests/calibration/test_reconstruction_scale.py tests/core/test_normalization_transform.py tests/core/test_coordinate_frame.py tests/core/test_object_mask_lifting.py` | Scale state, provenance, persistence, deterministic factor application and predecessor authority contracts pass. | Passed: `45 passed`. |
| `uv run --locked pytest -q` | Exact locked full suite exits 0; any failed test blocks PL-0209. | Exit 0: `1053 passed, 7 skipped, 1 deselected, 2 warnings` in 18.43s. Existing duplicate ZIP-entry warnings remain in `tests/packscan/test_container.py` and `tests/transfer/test_validation_gate.py`. |
| `uv run --locked ruff check core/src/packlab_core/calibration/scale_provenance.py core/src/packlab_core/calibration/__init__.py apps/windows-studio/src/packlab_studio/project.py tests/calibration/test_scale_provenance.py` | No changed-file lint errors. | Passed: `All checks passed!`. |
| `uv run --locked ruff format --check core/src/packlab_core/calibration/scale_provenance.py core/src/packlab_core/calibration/__init__.py apps/windows-studio/src/packlab_studio/project.py tests/calibration/test_scale_provenance.py` | Changed Python files formatted. | Passed: all four files already formatted. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/calibration/scale_provenance.py apps/windows-studio/src/packlab_studio/project.py` | Changed scale provenance and persistence type-check. | Passed: `Success: no issues found in 2 source files`. |
| `uv run --locked python -m compileall -q core/src/packlab_core/calibration/scale_provenance.py core/src/packlab_core/calibration/__init__.py apps/windows-studio/src/packlab_studio/project.py tests/calibration/test_scale_provenance.py` | Changed Python files compile. | Passed, exit 0. |
| `git diff --check` and `git diff --cached --check` | No whitespace errors. | Passed. Git emitted only its CRLF conversion notice for two edited tracked Python files. |
| `git diff --cached --name-only`, protected-file/dependency guard, and credential-pattern scan | Only authorized files changed; trackers and dependencies untouched; no credential pattern. | Passed. Exactly four Python paths staged; protected-file/dependency guards had no diff; credential scan returned no matches. |

Coverage includes relative/unverified/verified unit mapping, rejected observations excluded from used scale factors but retained with reasons, synthetic/AI/incomplete promotion rejection, stale reconstruction invalidation, deterministic provenance serialization, append-only persistence/reopen, and project revision checks. Deterministic normalized transform application is covered by the PL-0208 predecessor regression. No printer, camera, detector, or measurement accuracy claim is made. No owner-controlled physical evidence was used or fabricated.

## Publication

- Implementation commit: `061282d37f1014481f19539dcf89fcb8820d4cab` (`calibration: persist scale provenance and promotion gates`).
- Pushed to `origin/main`; fetch confirmed local `HEAD` and `origin/main` both equal `061282d37f1014481f19539dcf89fcb8820d4cab` before the log-only commit.
- No owner work was overwritten. No audit verdict was created.

READY_FOR_INDEPENDENT_AUDIT
