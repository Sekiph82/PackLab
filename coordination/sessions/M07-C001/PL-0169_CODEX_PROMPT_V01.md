# PL-0169 - Codex Implementation Work Order V01

Task: **Matcher selection for ordered orbit datasets**

Repository:
https://github.com/Sekiph82/PackLab

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CHATGPT_AUDIT_V02.md

Matching criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0169_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0169_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 /
`READY` / `CODEX` for PL-0169 and point to this prompt and criteria.
PL-0158 through PL-0168 must remain accepted, PL-0068 must remain
`OWNER_REQUIRED`, and PL-0170 and later must remain unauthorized. If the live
tracker does not match, stop with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the
accepted OpenReality architecture, the PL-0163 reconstruction contract, the
M07 engine baseline, and the accepted feature-extraction boundary before
editing. Preserve backend neutrality, immutable PackScan source evidence, and
the distinction between guided-orbit and turntable capture.

## Frozen scope

Implement only a PackLab-owned, deterministic matcher-selection boundary for
ordered guided-orbit image datasets:

1. Accept an immutable ordered sequence of repository-relative image asset IDs
   plus an explicit capture mode and matcher-selection configuration.
2. Select the ordered/sequential strategy for guided-orbit input with an
   explicit, validated overlap/window policy. Preserve source order; do not
   silently sort, deduplicate, or reinterpret the sequence.
3. Reject empty, duplicate, absolute, traversal, or otherwise unsafe asset
   IDs; reject malformed or unsupported capture modes and invalid overlap
   values with actionable PackLab-owned errors.
4. Treat turntable input as a distinct mode and fail closed unless the
   contract explicitly represents its object-transform-aware adapter. Do not
   feed rotating-object data into a static-world ordered-orbit strategy.
5. Expose deterministic backend-neutral values and a provenance-safe
   serialization/digest if configuration identity is represented. Map to
   COLMAP matcher parameter names only in an adapter function; the adapter
   must not discover, install, launch, or execute COLMAP.
6. Add behavior-sensitive public-boundary tests for valid ordered input,
   order preservation, overlap boundaries, empty/duplicate/unsafe input,
   invalid modes and values, turntable separation, deterministic
   serialization/digest, and non-mutation.

Do not implement feature matching, image processing, pair computation against
image pixels, sparse mapping, camera solving, dense reconstruction,
segmentation, mask lifting, UI workflow, engine installation/execution,
neural/generative models, metric calibration, schema changes,
dependency/lock changes, physical/native-device acceptance, or PL-0170+ work.

## Allowed files

- `core/src/packlab_core/matching.py`
- `tests/core/test_matching.py`
- `coordination/sessions/M07-C001/PL-0169_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, prior prompt,
criteria, log, or audit, schemas, dependency/lock files, generated artifacts,
binaries, secrets, private scans, signing material, UI code, engine
executables, or PL-0170+ code.

## Validation and publication

Run and record every required check with the exact command, expected result,
failure condition, actual result, and exit status:

- focused PL-0169 tests and the relevant reconstruction/engine-contract
  boundaries;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff on every changed Python implementation/test path;
- targeted mypy on changed Python implementation paths, reporting unchanged
  repository debt without adding errors;
- `python -m compileall -q` on every changed Python implementation path;
- `git diff --check` and protected-file/scope/privacy/secrets/generated/
  binary checks.

Review the actual changed-file set. Use separate implementation/evidence and
log-only commits, push only `origin main`, verify remote visibility, create
exactly `PL-0169_CODEX_LOG_V01.md`, and end it exactly with:

`READY_FOR_INDEPENDENT_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit
artifacts, assign `AUDITED_PASS`, or start PL-0170.
