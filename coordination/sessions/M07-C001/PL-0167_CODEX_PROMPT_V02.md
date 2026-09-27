# PL-0167 - Codex Remediation Work Order V02

Task: **PackScan camera intrinsics and pose-prior consumption**

Repository:
https://github.com/Sekiph82/PackLab

Prior audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CHATGPT_AUDIT_V01.md

Prior prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CODEX_PROMPT_V01.md

Prior criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CHATGPT_AUDIT_CRITERIA_V01.md

Prior log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CODEX_LOG_V01.md

New criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CHATGPT_AUDIT_CRITERIA_V02.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CODEX_LOG_V02.md

## Authorization gate

Before material work, read the live `TASKS.md`. It must authorize M07-C001 / `CHANGES_REQUIRED` / `CODEX` for the PL-0167 remediation and point to this V02 prompt and criteria. PL-0158 through PL-0166 remain accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0168 and later tasks remain unauthorized. If the live tracker does not match, stop with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the V01 prompt/criteria/log/audit, the PL-0163 contract, the PackScan schemas/authority, and the accepted PL-0166 workspace authority before editing. Preserve the existing PackLab-owned authority chain and all valid V01 behavior.

## Frozen remediation scope

Correct only the two V01 audit findings:

1. In the reusable camera-prior assessment boundary, require every non-rejected prior accepted for a `ReconstructionInputSet` to carry the exact source-package digest and working-set revision and to carry a valid source image identity. Missing binding fields must reject the prior explicitly with a warning/reason; mismatched fields must continue to reject it. Preserve valid importer-created priors and all existing explicit use modes.
2. In the PackScan metadata candidate discovery, make duplicate `(kind, photo_id)` payloads permanently ambiguous for that import. Once a key has more than one candidate, no candidate for that key may be selected, including when there are three or more candidates. Preserve valid unique payload selection and explicit warnings.
3. Add behavior-sensitive production-boundary tests for both findings: an otherwise-valid unbound prior crossing `assess_camera_priors`, and at least three uniquely named same-image intrinsics payloads proving that no candidate is accepted. Retain regression coverage for valid mapping, dimensions, lens/convention/units, every use mode, revision/digest mismatch, malformed/missing metadata, and RAW_CAPTURE/working-set immutability.

Do not redesign the prior contract, create a second authority, or change PackScan schemas. Do not implement feature extraction, matching, sparse/dense reconstruction, camera solving, segmentation, mask lifting, UI workflow, engine installation/execution, neural/generative models, metric calibration, or PL-0168+ work.

## Allowed files

- `core/src/packlab_core/reconstruction.py`
- `apps/windows-studio/src/packlab_studio/reconstruction_workspace.py`
- `tests/core/test_reconstruction.py` if needed for the generic boundary regression
- `tests/studio/test_camera_priors.py`
- `coordination/sessions/M07-C001/PL-0167_CODEX_LOG_V02.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, V01 evidence, prior prompts/criteria/logs/audits, dependency/lock files, schemas, generated artifacts, binaries, secrets, private scans, signing material, or PL-0168+ code.

## Validation and publication

Run and record every required check with exact command, expected result,
failure condition, actual result, and exit status:

- focused V02 tests and the relevant PackScan/reconstruction/workspace boundary tests;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff on every changed Python implementation/test path;
- targeted mypy on every changed Python implementation path, reporting unchanged repository debt without adding errors in changed modules;
- `python -m compileall -q` on every changed Python implementation path;
- `git diff --check` and protected-file/scope/privacy/secrets/generated/binary checks.

Review the actual changed-file set. Use separate implementation/evidence and log-only commits, push only `origin main`, verify remote visibility, create exactly `PL-0167_CODEX_LOG_V02.md`, and end it exactly with:

`READY_FOR_INDEPENDENT_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit artifacts, assign `AUDITED_PASS`, or start PL-0168.
