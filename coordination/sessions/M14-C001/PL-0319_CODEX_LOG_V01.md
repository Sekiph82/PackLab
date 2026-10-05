# PL-0319 - Codex Implementation Log V01

Task: **Separate geometry material from product liquid/content appearance**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0319_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0319_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live root `TASKS.md` authorizes `M14-C001-R02`: PL-0313 V02 followed by PL-0314 through PL-0331; actor `CODEX`. The tracker was not edited.
- Read live `TASKS.md`, the exact PL-0318 predecessor prompt/criteria, M13 R02 final audit, M09 physical-validation deferral, ADR-0005, and this PL-0319 prompt/criteria before implementation.
- Starting synchronized SHA: `c84ddb37b5f3da36a379976a90b9443ca79fbb32`; worktree clean on `codex/m13-c001-pl0297`, push target `origin/main`. The Desktop owner checkout remains untouched.
- Implementation/evidence commit: `3866e11b1d89e7191d176b98e64033efb3fae6d4` (`Separate geometry and content visual assignments`), pushed to `origin/main`.

## Implementation

Added `core/src/packlab_core/component_visual_assignments.py` with separate immutable `GeometryMaterialAssignmentRevision` and `ContentAppearanceAssignmentRevision` contracts. Both bind to an exact Design Model revision and a stable component ID that must exist in that model. Geometry assignments pin the exact material-library revision and material ID. Content assignments carry only visual display name/color/opacity and source classification. The separate types do not contain or overwrite one another’s channel fields.

Replacement creates a deterministic successor within the same channel and exact model/component binding. Removal creates an immutable empty tombstone successor while leaving the prior assigned revision addressable. `ComponentVisualAssignmentState` combines optional active channel assignments only when their exact model/component provenance matches; changing one channel can be combined with the previous other-channel revision. Model geometry is not mutated.

Content and combined-state metadata explicitly set fill-volume and formulation inference to false. No fill volume or formulation field/value is produced. Material values remain `NON_CERTIFIED_VISUAL_REFERENCE` metadata.

Files changed:

- `core/src/packlab_core/component_visual_assignments.py`
- `tests/core/test_component_visual_assignments.py`

No dependency, lockfile, tracker, audit artifact, later child, or M15+ file was changed.

## Validation

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_component_visual_assignments.py tests/core/test_visual_material_library.py` | Independent channels, provenance binding, replacement/removal and visual-only limits pass; wrong component/model/library bindings reject. | PASS: 25 passed in 0.26s. Covers geometry-only, content-only, combined state, independent replacements/removals, exact component/model pinning, deterministic identity, no cross-channel overwrite, no model mutation, and no inferred fill/formulation property. |
| `uv run --locked pytest -q` | Locked repository suite passes; any failure blocks this child. | PASS: 1,742 passed, 6 skipped, 1 deselected in 176.91s. Two existing duplicate ZIP-name warnings in container-validation tests. |
| `uv run --locked ruff check core/src/packlab_core/component_visual_assignments.py tests/core/test_component_visual_assignments.py` | Changed files pass Ruff. | PASS: all checks passed. |
| `uv run --locked ruff format --check core/src/packlab_core/component_visual_assignments.py tests/core/test_component_visual_assignments.py` | Changed files are formatted. | PASS: both files formatted. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/component_visual_assignments.py` | Changed source passes targeted typing. | PASS: no issues in 1 source file. |
| `uv run --locked python -m compileall -q core/src/packlab_core/component_visual_assignments.py tests/core/test_component_visual_assignments.py` | Changed source and tests compile. | PASS. |
| `uv lock --check`; `git diff --exit-code -- TASKS.md pyproject.toml uv.lock` | No dependency/lockfile or tracker change. | PASS: 78 packages resolved; no diff. |
| `git diff --check`; changed-file security/scope review | No whitespace, network access, or scope leakage. | PASS. Only the two scoped files changed; no runtime network, subprocess, filesystem access, or out-of-scope file was added. |
| Push/parity check (`git fetch origin main`, `git rev-parse HEAD`, `git rev-parse origin/main`, `git ls-remote origin refs/heads/main`, status) | Published implementation matches canonical GitHub `main`. | PASS at implementation commit `3866e11b1d89e7191d176b98e64033efb3fae6d4`; local, fetched origin, and live ref equal; worktree clean. |

## Limitations

- Geometry material and content appearance assignments are visual/design metadata only; they do not imply physical material properties, volume, formulation, fill state, certification, or regulatory approval.
- Assignments pin supplied immutable Design Model revision and existing stable component IDs; they do not edit Design Model geometry or feature authority.
- Removed tombstones clear their channel references while retaining the prior assignment revision and predecessor link.

## Handoff

PL-0319 V01 implementation/evidence is builder-green and published. Its matching log is published separately and ends with the required marker. No independent audit verdict is claimed. Continue at PL-0320 only after this child log/index publication and remote parity verification.

READY_FOR_INDEPENDENT_AUDIT
