# PL-0323 - Codex Implementation Log V01

Task: **Persist material assignments per component**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0323_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0323_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live root `TASKS.md` authorizes `M14-C001-R02`: PL-0313 V02 followed by PL-0314 through PL-0331; actor `CODEX`. The tracker was not edited. The PL-0324 Blender capability gate remains in force; M15+ remains unauthorized.
- Read the live `TASKS.md`, M14 R02 continuation prompt and criteria, M14 partial audit V02, M13 R02 final audit, M09 physical-validation deferral, ADR-0005, the PL-0322 predecessor prompt/criteria, and this PL-0323 prompt/criteria before implementation.
- Starting synchronized SHA: `1e05ff5979263b12ca6133f63e97d359fa905024`; worktree clean on `codex/m13-c001-pl0297`, push target `origin/main`. The protected Desktop checkout remains untouched.
- Implementation/evidence commit: `b5412210f2a5e4cf29905cbde742467cffa58925` (`Persist per-component visual material state`), pushed to `origin/main`.

## Implementation

Added `core/src/packlab_core/component_material_project.py`, a versioned canonical JSON project snapshot for per-component geometry-material assignment, optional product-content appearance, optional PCR declarations, and PCR appearance variants. Entries are normalized by stable component ID; the project revision and envelope SHA-256 are deterministic. Serialization is bounded to 8 MiB, rejects duplicate JSON keys/non-finite numbers, requires the explicit schema version, and rejects unknown versions instead of silently migrating.

Loading requires the exact active `DesignModelRevision` and `VisualMaterialLibraryRevision`. The loader verifies project digest and revision, assignment record identities, material-library references, PCR declaration/material binding, exact model/component provenance, and component existence. Missing/deleted components, duplicate component entries, stale model/library/material references, mismatched PCR declarations, malformed authority flags, and unsupported versions fail closed. Component IDs are the stable semantic IDs already represented by the Design Model; tessellation/native face identities are not used.

Replacement and removal helpers create new immutable snapshots. Existing per-channel assignment revisions retain their predecessor IDs; callers can remove one channel while preserving the other or remove a component entry. The persisted project data does not include geometry and serializes `mutates_design_model`, physical/regulatory claims, and PCR certification/environmental claims as false. PCR values remain user-supplied/design metadata; an external authority pointer is not independently checked.

Files changed:

- `core/src/packlab_core/component_material_project.py`
- `tests/core/test_component_material_project.py`

No dependency, lockfile, tracker, audit artifact, later-child, Blender, or M15+ file was changed.

## Validation

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run pytest tests/core/test_component_material_project.py tests/core/test_component_visual_assignments.py tests/core/test_pcr_material_declarations.py tests/core/test_pbr_visual_parameters.py tests/core/test_visual_material_library.py -q` | Round-trip, multiple components, replacement/removal, stale/ambiguous references, deterministic storage, exact revision binding, version handling, privacy, source-geometry immutability, and predecessor assignment/PCR/PBR contracts pass. | PASS: 83 passed in 0.36s. |
| `uv run --locked pytest -q` | Locked repository suite passes; any failure blocks this child. | PASS on final source: 1,805 passed, 6 skipped, 1 deselected in 167.82s. Two existing duplicate ZIP-name warnings in container-validation tests. |
| `uv run ruff check core/src/packlab_core/component_material_project.py tests/core/test_component_material_project.py` | Changed files pass Ruff. | PASS: all checks passed. |
| `uv run ruff format --check core/src/packlab_core/component_material_project.py tests/core/test_component_material_project.py` | Changed files are formatted. | PASS: both files already formatted. |
| `uv run mypy --follow-imports=silent core/src/packlab_core/component_material_project.py` | Changed source passes targeted typing without expanding known unrelated imports. | PASS: no issues in 1 source file. |
| `uv run python -m compileall -q core/src/packlab_core/component_material_project.py tests/core/test_component_material_project.py` | Changed source and tests compile. | PASS. |
| `uv lock --check`; `git diff -- TASKS.md pyproject.toml uv.lock` | No dependency/lockfile or tracker change. | PASS: 78 packages resolved; no protected-file diff. |
| `git diff --check`; changed-file privacy/security/scope review | No whitespace, network/runtime access, path leakage, private evidence, or scope leakage. | PASS. Changed files contain no network, subprocess, path-writing, or external-file access. Canonical data contains IDs and bounded visual values; the test confirms the current workspace path is not serialized. |
| `git fetch origin main`; `git rev-list --left-right --count HEAD...origin/main`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git ls-remote origin refs/heads/main` | Starting source synchronized and published implementation matches canonical GitHub `main`. | PASS at implementation SHA `b5412210f2a5e4cf29905cbde742467cffa58925`; divergence before implementation was `0 0`; pushed `HEAD:main`; local HEAD, fetched `origin/main`, and live GitHub ref equal. |

## Limitations

- This core boundary provides canonical bytes for a project-owned persistence caller; it does not add a GUI workflow or mutate the existing project state file.
- The snapshot stores assignment metadata and stable Design Model/component references only; it does not store or change geometry.
- Schema version 1 is supported. Unknown future versions are rejected; no implicit migration is attempted.
- PCR data remains non-certified user-supplied/design metadata; no physical, environmental, manufacturing, or regulatory performance is established.

## Handoff

PL-0323 V01 implementation/evidence is builder-green and published. Its matching log is published separately and ends with the required marker. No independent audit verdict is claimed. Continue at PL-0324 only after this child log/index publication and remote parity verification; PL-0324 remains a real Blender capability gate.

READY_FOR_INDEPENDENT_AUDIT
