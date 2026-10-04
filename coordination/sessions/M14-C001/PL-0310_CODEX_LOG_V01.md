# PL-0310 - Codex Implementation Log V01

Task: **Define Label Zone entity independent of artwork image**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0310_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0310_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live root `TASKS.md` authorized M14-C001 / PL-0310 through PL-0331 / READY / CODEX. The tracker was not edited.
- Read the M14 master prompt and audit criteria, PL-0310 prompt and criteria, M13-C001 final audit, M09 physical-validation deferral, ADR-0005, the milestone-batch protocol, and PL-0309 predecessor prompt/criteria.
- Starting synchronized local/origin/GitHub SHA: `5c5e267591d875a2368d1f392320aec8e11ba5f0`; 0 ahead / 0 behind. Branch `codex/m13-c001-pl0297`, publishing only to authorized `origin/main`.
- Execution worktree: `C:\Users\sekip\.codex\worktrees\packlab-m13-c001\PackLab`. Owner Desktop checkout was not used or modified.
- M15+ is unauthorized and was not started.

## Implementation

- Implementation/evidence commit: `5f2f6216168516c9205d6fdfba719ba1a46fff28`.
- Added `core/src/packlab_core/label_zone.py` with frozen `LabelZone` and `LabelZoneBoundary` value types and `front`, `back`, and `wrap` zone kinds.
- The creation API requires the exact current `DesignModelRevision` and `CadBrepRepresentationRevision`, pins the source model and BREP revision/digest, parent-authority revision, scale state and unit, and resolves the stable component/feature ID against both the model and BREP feature lineage. Stale, deleted, cross-component, out-of-lineage, or mismatched model/BREP inputs fail closed.
- Placement is a finite, non-empty rectangle in normalized feature-local UV coordinates bounded to [0, 1]. These placement coordinates are explicitly unitless; source Design Model units remain separately pinned and are never promoted from `reconstruction_units` or `mm_unverified`.
- Zone identity is a canonical SHA-256 over zone kind, exact model/CAD/parent provenance, scale/unit, stable component/feature IDs, and boundary values. Artwork is not accepted by the API, serialized as a payload, or included in identity. Serialization explicitly states artwork bytes are absent and that physical fit/manufacturing suitability are not inferred.
- Added tests for all zone kinds, provenance, deterministic/stable identity, boundary and stale-feature failures, component and model/BREP mismatch, relative/mm_unverified preservation, immutability, and artwork independence.
- Changed files: `core/src/packlab_core/label_zone.py`, `tests/core/test_label_zone.py` only.

## Validation evidence

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_label_zone.py tests/core/test_design_model.py tests/core/test_cad_brep.py tests/core/test_cad_feature_map.py` | Label Zone and exact source-authority predecessor tests pass; any failure blocks PL-0310. | PASS: 50 passed in 2.89s. An earlier assertion mistakenly matched the explicit `artwork_bytes_included: false` metadata key; corrected it to check for asset payload/digest fields, then the final focused run passed. |
| `uv run --locked pytest -q` | Locked full repository suite passes; any failure blocks the child. | PASS: 1,634 passed, 6 skipped, 1 deselected in 147.62s. Two existing duplicate-ZIP-name warnings arose from PackScan duplicate-name and unsafe-ZIP tests. |
| `uv run --locked ruff check core/src/packlab_core/label_zone.py tests/core/test_label_zone.py` | Changed files pass Ruff. | PASS: all checks passed. |
| `uv run --locked ruff format --check core/src/packlab_core/label_zone.py tests/core/test_label_zone.py` | Changed files are formatted. | PASS: both files already formatted after `ruff format` correction. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/label_zone.py` | Changed source passes targeted typing. | PASS: no issues in 1 source file. Initial dict invariance finding was corrected with an explicit `dict[str, object]` annotation. |
| `uv run --locked python -m compileall -q core/src/packlab_core/label_zone.py tests/core/test_label_zone.py` | Changed Python files compile. | PASS. |
| `uv lock --check` and `git diff -- pyproject.toml uv.lock` | Dependency resolution is stable; no dependency or lockfile change. | PASS: 78 packages resolved; `pyproject.toml` and `uv.lock` diff empty. |
| `git diff --check` and `git diff --cached --check` | No whitespace errors in changed/staged files. | PASS. |
| Credential/privacy scan: `rg -n -i 'AKIA[0-9A-Z]{16}|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{20,}|C:\\\\Users\\\\sekip|/Users/sekip' core/src/packlab_core/label_zone.py tests/core/test_label_zone.py` | No secrets, credentials, or ambient local path identity. | PASS: no matches. |
| Scope/generated/binary/license review | Only authorized source and test changes; no generated/binary/private evidence, dependency, tracker, prompt, criteria, or audit change. | PASS: exactly the two listed files changed; no new license/dependency concerns introduced. |
| Implementation publication | Push only to `origin/main`; local/origin/GitHub must agree. | PASS: implementation commit pushed; local `HEAD`, `origin/main`, and `git ls-remote origin refs/heads/main` matched at `5f2f6216168516c9205d6fdfba719ba1a46fff28`. |

## Limitations and authority boundaries

- Normalized UV placement is design intent, not a claim that the zone physically fits a surface, label, print, mold, or manufactured package.
- `RELATIVE` remains `reconstruction_units`; `mm_unverified` remains physically unverified. Physical validation deferrals and OCP/OCCT redistribution license gates remain in force.
- No artwork import, byte storage, rendering, network fetch, dependency, or M15 work is included.

## Handoff

- Implementation/evidence commit: `5f2f6216168516c9205d6fdfba719ba1a46fff28`.
- This PL-0310 log is published in a distinct log-only commit; master index update follows separately.
- Implementer evidence only; independent PL-0310 audit remains pending.

READY_FOR_INDEPENDENT_AUDIT