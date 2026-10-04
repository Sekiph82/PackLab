# PL-0295 - Codex Implementation Log V01

Task: **Preserve named feature references across CAD regeneration where practical**

Cycle: M13-C001
Prompt: `PL-0295_CODEX_PROMPT_V01.md`
Criteria: `PL-0295_CHATGPT_AUDIT_CRITERIA_V01.md`

## Authorization and synchronization

- Re-read root `TASKS.md` project status: M13-C001 ordered PL-0289 through PL-0309 batch; `READY`; required actor `CODEX`; M12 is `AUDITED_PASS`; no M14 authorization.
- Re-read the M13 master, M12 audit, ADR-0005, M09 deferral, PL-0291, PL-0292, PL-0293 prompts, and PL-0295 criteria.
- Starting local/origin SHA: `09a65ac59fc60fae20ba7a972fa9a01bd6018275`, synchronized and clean at child start.
- Implementation commit: `5bd49e17ffecdf413724ecf6c91e91a2df2d0827`.

## Files changed

- `core/src/packlab_core/cad_brep.py`
- `core/src/packlab_core/cad_boolean.py`
- `core/src/packlab_core/cad_feature_map.py`
- `tests/core/test_cad_feature_map.py`

No tracker, audit, prompt, criteria, dependency, lockfile, later-child, private evidence, credential, or generated binary files were changed.

## Implementation

- Added `source_feature_ids` to the BREP revision lineage and included it in revision identity and serialization. The BREP contract is now `packlab.cad-brep-revision.v2`. Revolve and loft representations retain their exact Design Operation parent feature IDs; boolean results retain the exact tool and body feature IDs.
- Added a PackLab-owned named feature mapping revision bound to one exact Design Model revision, BREP revision, source operation, parent authority and unit state.
- Named reference IDs derive from stable Design Model feature IDs and remain unchanged across ordinary parameter regeneration. Mapping revisions change with the exact source model/BREP revisions.
- A single lineage contributor may resolve to the whole output solid. A boolean modifier can map only coarsely to the boolean result solid. Multiple contributors sharing a solid are `AMBIGUOUS`; absent lineage and unsupported selectors are `UNRESOLVED`.
- Mapping records explicitly state that preview indices, native topology hashes and universal topological identity are not used or claimed.
- Added coverage for body, neck, cap and handle references; boolean-result lineage; ordinary parameter regeneration; changed contributor topology becoming ambiguous; unresolved references; and prohibited preview/native-hash authority.

## Validation evidence

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_cad_feature_map.py tests/core/test_cad_boolean.py tests/core/test_cad_brep.py tests/core/test_cad_loft.py` | Named mapping and predecessor regressions pass. | PASS: 27 passed. |
| `uv run --locked pytest -q` | Locked full suite passes; any failing test blocks a green child. | PASS: 1,534 passed, 6 skipped, 1 deselected, 2 existing duplicate-ZIP-name warnings. |
| `uv run --locked ruff check core/src/packlab_core/cad_brep.py core/src/packlab_core/cad_boolean.py core/src/packlab_core/cad_feature_map.py tests/core/test_cad_feature_map.py` | Changed-file lint passes. | PASS. |
| `uv run --locked ruff format --check core/src/packlab_core/cad_brep.py core/src/packlab_core/cad_boolean.py core/src/packlab_core/cad_feature_map.py tests/core/test_cad_feature_map.py` | Changed files are formatted. | PASS. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/cad_brep.py core/src/packlab_core/cad_boolean.py core/src/packlab_core/cad_feature_map.py` | Changed modules pass scoped typing. | PASS: no issues in 3 source files. |
| `uv run --locked mypy core/src/packlab_core/cad_brep.py core/src/packlab_core/cad_boolean.py core/src/packlab_core/cad_feature_map.py` | Report changed and imported typing issues. | No diagnostics in changed modules. Four errors remain in unmodified imported modules: two in `calibration/marker_detection.py`, one in `jerrycan_grip_indent.py`, and one in `jerrycan_handle_void_candidates.py`. |
| `uv run --locked python -m compileall -q core/src/packlab_core/cad_brep.py core/src/packlab_core/cad_boolean.py core/src/packlab_core/cad_feature_map.py tests/core/test_cad_feature_map.py` | Changed sources compile. | PASS. |
| `uv lock --check` | Lock remains valid and unchanged. | PASS; no dependency or lockfile changes. |
| `git diff --check` and staged `git diff --cached --check` | No whitespace errors. | PASS. |
| Credential/privacy/scope scan | No secrets, private evidence, downloads, unrelated scope or generated binaries. | PASS for changed paths; no credential-pattern matches. `TASKS.md`, audit files, dependency selection and M14+ paths remain unchanged. |
| Remote boundary | Fetch `origin/main`; verify relationship and SHA parity after publication. | PASS: fetched at `0 ahead / 0 behind` before implementation; final parity recorded after publication. |

## Limitations

- Whole-solid references are coarse. Joined body/neck/cap contributors are reported ambiguous rather than assigned to native faces. Boolean modifier references identify only the result solid, not a face-level void boundary.
- This mapping is best-effort lineage evidence; OCCT topology is not universally stable across regeneration.
- PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`. The PL-0289 HIGH native-library license/notice redistribution gate remains unresolved.

## Handoff

Implementation and this log are separate commits. This child has not been independently audited. The ordered M13 batch may continue only under the frozen master prompt and while green.

READY_FOR_INDEPENDENT_AUDIT
