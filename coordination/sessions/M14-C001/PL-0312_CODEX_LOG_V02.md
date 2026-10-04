# PL-0312 - Codex Implementation Log V02

Task: **Implement curvature/slope analysis to suggest label-safe regions without inventing feature ownership**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0312_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0312_CHATGPT_AUDIT_CRITERIA_V02.md

## Authorization and synchronization

- Live root `TASKS.md` authorized M14-C001-R01: PL-0312 V02 then PL-0313 through PL-0331; status `CHANGES_REQUIRED`; actor `CODEX`. `TASKS.md` was not edited.
- Read the M14 partial audit V01, M13 final audit, M09 physical-validation deferral, ADR-0005, accepted PL-0310/PL-0311 audits and contracts, PL-0312 V01 blocker log, V02 prompt/criteria, R01 master prompt/criteria, and `cad_feature_map.py` authority contract.
- Starting synchronized SHA: `6f14388137f4442e87ea19b2b9e96a28a305de9a`; local, `origin/main`, and live GitHub main matched before implementation. Safe fast-forward included only the tracker and M14 audit/prompt/criteria package.
- Execution worktree: `C:\Users\sekip\.codex\worktrees\packlab-m13-c001\PackLab`. The dirty, 345-commit-behind Desktop owner checkout was preserved without sync or edits. Authorized push target: `origin/main`.
- Accepted PL-0310/PL-0311 source and evidence were not changed. M15+ was not started.

## Resolution and implementation

- PL-0312 V01's accepted authority stop is resolved by the V02 instruction to retain stable component provenance while allowing BREP-scoped derived analysis regions and explicit ambiguous/unresolved feature attribution.
- Implementation/evidence commit: `7576279cf4f8fd7e7c101e8a5e6a63ffcd8708c8`.
- Added `core/src/packlab_core/cad_label_surface_analysis.py` with immutable finite policy, candidate, feature-evidence and result records. It validates exact model/BREP/parent/unit and registered geometry digest, a valid single-solid topology, unique component provenance, and the accepted M13 mapping evidence.
- Analysis uses exact `BRepAdaptor_Surface` and `BRepLProp_SLProps` differential properties through `cad_adapter.py`, plus face point classification to conservatively mark trimmed/boundary regions. It does not use pixels, tessellation or mesh data.
- Explicit face/region/differential-sample limits bound work. Slope is the maximum sampled normal deviation from the requested target normal; curvature is maximum absolute principal curvature in the preserved source-unit inverse. Threshold comparison is inclusive at equality.
- Region IDs hash exact model/BREP revisions and digest, component, mapping/attribution evidence, policy and canonicalized geometric support samples. Returned regions are sorted by region ID; duplicate signatures fail closed. Face order and transient face identity are not returned or used as identity.
- Attribution is never promoted from whole-solid evidence to region ownership. The accepted cylinder revolve fixture reports `AMBIGUOUS`, includes both source feature IDs/status evidence, and keeps `resolved_feature_id=null`. A coarse or whole-solid mapping without a region selector reports `UNRESOLVED` at region level with its source mapping evidence retained.
- Trimmed/boundary, periodic-seam, unsupported-class, slope-threshold and curvature-threshold conditions are represented in region classification/reasons. Limitations disclose finite-grid sampling, possible between-sample geometry, trims/seams/discontinuities, and that suggestions are not face IDs or fit proof.
- Candidate records retain component, model/BREP/digest, parent revision/kind, physical-validation state, scale and units. They are advisory only, create no Label Zone, and imply no print-fit, physical accuracy, mold or manufacturing authority.
- Changed implementation/test paths: `core/src/packlab_core/cad_adapter.py`, `core/src/packlab_core/cad_label_surface_analysis.py`, `tests/core/test_cad_label_surface_analysis.py` only. No dependency or lockfile change.

## Validation evidence

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_cad_label_surface_analysis.py tests/core/test_label_zone_placement.py tests/core/test_label_zone.py tests/core/test_design_model.py tests/core/test_cad_brep.py tests/core/test_cad_feature_map.py` | CAD surface analysis and PL-0310/0311/M13 predecessor regressions pass. | PASS: 76 passed in 5.51s. Covers planar box, cylinder curvature/seam, sloped plane threshold, high-curvature sphere, accepted ambiguous revolve, ordering, collision, bounds, captured/standalone parents, units, source immutability and exact provenance. |
| `uv run --locked pytest -q` | Locked full repository suite passes; any failure blocks PL-0312. | PASS: 1,660 passed, 6 skipped, 1 deselected in 195.54s. Two existing duplicate-ZIP-name warnings arose in PackScan duplicate-name and unsafe-ZIP tests. |
| `uv run --locked ruff check core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_label_surface_analysis.py tests/core/test_cad_label_surface_analysis.py` | Changed files pass Ruff. | PASS: all checks passed. |
| `uv run --locked ruff format --check core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_label_surface_analysis.py tests/core/test_cad_label_surface_analysis.py` | Changed files are formatted. | PASS: all three files formatted. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_label_surface_analysis.py` | Changed source passes targeted typing. | PASS: no issues in 2 source files. |
| `uv run --locked python -m compileall -q core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_label_surface_analysis.py tests/core/test_cad_label_surface_analysis.py` | Changed source and tests compile. | PASS. |
| `uv lock --check`; `git diff -- pyproject.toml uv.lock` | Lock remains valid without dependency changes. | PASS: 78 packages resolved; no dependency/lockfile diff. |
| Changed-file privacy/security/scope scan | No secret, private path, network/process launch or unrelated task scope. | PASS: no matches; only the three listed implementation/test files were in the implementation commit. No private evidence, generated binary, tracker, prompt, criteria or accepted audit changed. |
| `git diff --check` | No whitespace errors. | PASS. |
| Implementation publication | Push authorized `origin/main`; local/origin/GitHub must match. | PASS: implementation commit pushed; local `HEAD`, `origin/main`, and GitHub `main` matched at `7576279cf4f8fd7e7c101e8a5e6a63ffcd8708c8`. |

## Limitations and authority boundaries

- `LABEL_SAFE_CANDIDATE` means only that the finite support samples met the selected slope/curvature policy and no sampled boundary/seam/unsupported condition fired. It is advisory; unsampled geometry, label footprint fit, printability and physical performance are not proven.
- The current accepted feature mapper has no stable region selector. Ambiguous/unresolved source feature ownership is preserved explicitly; a stable component ID and exact contributing feature evidence are retained.
- RELATIVE curvature stays inverse `reconstruction_units`; metric-unverified curvature stays inverse `mm_unverified`. Physical validation remains deferred, and mold/manufacturing use remains unauthorized.
- No M13 mapping behavior was changed, no new dependency/network/runtime download was introduced, and M15+ was not started.

## Handoff

- Implementation/evidence commit: `7576279cf4f8fd7e7c101e8a5e6a63ffcd8708c8`.
- This V02 child log is to be published in a separate log-only commit. Original M14 master row and R01 continuation index updates follow separately.
- PL-0312 V02 is builder-green and awaiting independent audit; the continuation prompt authorizes immediate PL-0313 execution.

READY_FOR_INDEPENDENT_AUDIT
