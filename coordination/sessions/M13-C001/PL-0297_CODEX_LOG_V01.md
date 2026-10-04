# PL-0297 - Codex Implementation Log V01

Task: **Export Design Model/assembly to STEP with explicit millimetre units**

Cycle: M13-C001
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Re-read root `TASKS.md` project status: M13-C001 ordered PL-0289 through PL-0309 batch; `READY`; required actor `CODEX`; M12 is `AUDITED_PASS`; no M14 authorization.
- Re-read the M13 master, M12 audit, ADR-0005, M09 deferral, PL-0294 and PL-0295 prompts, and PL-0297 criteria.
- Starting synchronized local/origin SHA: `434b6c991b6f05d590e13a475fa577ed75972cda`.
- During implementation, origin advanced to `899f9b3db0eeacbc8dd96015dc249ebfae54bec6` with an owner calibration correction. Root `TASKS.md` retained M13 `READY` / `CODEX`; the changed tracker line concerned only the superseded M09 print-capture notice. The remote changes affected calibration artwork, tests and owner documentation, not PL-0297 source paths.
- Preserved the original implementation commit `60e9117e56c4e00c03548f76b29745743954a6d6` on its original local branch and cherry-picked it onto a fresh branch based on the fetched `origin/main`, without reset, rebase, stash or force push. The locked full suite was rerun against that combined state.
- Published implementation commit: `afc2a4d97ed902b9e774480f5bebecdaa09541c3`.

## Files changed

- `core/src/packlab_core/cad_step_export.py`
- `tests/core/test_cad_step_export.py`

No tracker, audit, prompt, criteria, dependency, lockfile, later-child, private evidence, credential, or generated binary files were changed.

## Implementation

- Added deterministic STEP export for one validated, exact-model-bound BREP solid. Export rejects RELATIVE / `reconstruction_units`, and accepts only `METRIC_UNVERIFIED` / `mm_unverified` while retaining `DEFERRED_OWNER_VALIDATION` and `mold_use_authorized=false`.
- Configures the selected OCCT writer explicitly for `MM`, writes the stable part name into the STEP product record, and derives the STEP file timestamp from the source Design Model's UTC creation time. The writer operates on a geometry copy. The export reopens the exact artifact and requires every reported STEP length unit to be `millimetre` before publishing the destination.
- Export metadata binds the exact Design Model, BREP, operation and parent-authority revisions; source geometry digest; CAD binding/kernel versions; artifact byte digest/size; reopened length units; and existing PL-0295 feature-reference diagnostics. Its deterministic identity includes the artifact digest and source/version/name/unit fields.
- Metadata explicitly states that millimetres encode unverified numerical design values, and denies physical-accuracy, mold/manufacturing, Scan Master, Design Model or BREP authority promotion.
- This exporter accepts one BREP solid. The current M13 BREP representation contract does not encode an assembly geometry payload; no assembly ancestry or component transforms were inferred. Feature references are preserved in export metadata, while unavailable face-level STEP names are not fabricated.
- Tests cover deterministic file bytes and export ID, part name in STEP product data, reopened millimetre units, relative-input rejection, stable feature mapping metadata, both captured and standalone parent modes, deferred/no-promotion metadata, source immutability, and refusal to overwrite an existing destination.

## Validation evidence

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest tests/core/test_cad_step_export.py tests/core/test_cad_brep.py tests/core/test_cad_validation.py tests/core/test_cad_feature_map.py tests/calibration/test_calibration_mats.py -q` | STEP and predecessor regressions pass; any failure blocks the child. | PASS: 32 passed. |
| `uv run --locked pytest -q` | Locked full suite passes on fetched origin plus implementation; any failure blocks the child. | PASS: 1,549 passed, 6 skipped, 1 deselected; two duplicate-ZIP-name warnings. |
| `uv run --locked ruff check core/src/packlab_core/cad_step_export.py tests/core/test_cad_step_export.py` | Changed-file lint passes. | PASS. |
| `uv run --locked ruff format --check core/src/packlab_core/cad_step_export.py tests/core/test_cad_step_export.py` | Changed files are formatted. | PASS. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/cad_step_export.py` | Changed module passes scoped typing. | PASS: no issues in 1 source file. |
| `uv run --locked mypy core/src/packlab_core/cad_step_export.py` | Report changed and imported typing issues. | No diagnostic in the changed module. Two existing errors remain in unmodified `calibration/marker_detection.py`. |
| `uv run --locked python -m compileall -q core/src/packlab_core/cad_step_export.py tests/core/test_cad_step_export.py` | Changed files compile. | PASS. |
| `uv lock --check` | Lock remains valid and unchanged. | PASS; no dependency or lockfile changes. |
| `git diff --check` and staged `git diff --cached --check` | No whitespace errors. | PASS. |
| Credential/privacy/scope scan | No secrets, private evidence, downloads, unrelated scope or generated binaries. | PASS for changed paths; credential-pattern scan returned no matches. No PL-0298+ or M14+ implementation was added. |
| Remote boundary | Fetch origin and verify SHA parity after implementation publication. | PASS after safe transplant: implementation push advanced origin from `899f9b3...` to `afc2a4d...`; `git ls-remote origin refs/heads/main` confirmed exact SHA parity. |

## Failures and fixes

- Initial STEP export checks found a malformed header timestamp expression; it was corrected and the complete STEP suite passed.
- Repeated STEP writes initially differed because OCCT adds a changing suffix to its generated product name. The writer output now normalizes the product label to the explicit stable part name and the source Design Model timestamp; repeated file-byte and export-ID checks pass.
- The first implementation push was rejected because `origin/main` advanced after preflight. The remote delta was inspected, M13 authorization rechecked, the local implementation commit preserved, then cherry-picked onto the new origin tip. All focused and full checks were rerun before the successful push.
- Git's inherited `core.autocrlf=true` marked Ruff-normalized LF working files dirty despite their normalized blobs matching the published commit. This managed worktree has `core.autocrlf=false` in its worktree-specific Git config; no tracked file or shared Desktop checkout was changed, and final status is clean.

## Limitations

- The current exporter accepts a single BREP solid. Assembly STEP remains unavailable because this source representation does not carry an assembly CAD payload and component transforms; no assembly geometry was synthesized.
- Stable feature references are retained as metadata diagnostics. This BREP lineage contract does not resolve subshape face names, so STEP face/component labels beyond the supported part product name are not claimed.
- STEP millimetre declarations and software round-trip do not validate physical dimensions. PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`. The PL-0289 HIGH native-library license/notice redistribution gate remains unresolved.

## Handoff

Implementation and this log are separate commits. This child has not been independently audited. The ordered M13 batch may continue only under the frozen master prompt and while green.

READY_FOR_INDEPENDENT_AUDIT
