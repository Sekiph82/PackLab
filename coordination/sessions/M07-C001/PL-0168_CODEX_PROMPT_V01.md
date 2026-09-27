# PL-0168 — Codex Work Order V01

Task: **Feature-extraction configuration optimized first for packaged consumer goods**

Repository:
https://github.com/Sekiph82/PackLab

Previous child audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CHATGPT_AUDIT_V02.md

Mandatory architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

Mandatory pre-read:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0163_RECONSTRUCTION_BACKEND_CONTRACT.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0168_CODEX_LOG_V01.md

## Authorization gate

Before material work, read live `TASKS.md`. It must authorize M07-C001 / `READY` / `CODEX` for PL-0168. PL-0158 through PL-0167 must remain accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0169 and later tasks remain unauthorized. If the live tracker does not match, stop with `TASK_STATE_MISMATCH`.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination policies, the OpenReality architecture, the PL-0163 contract, the accepted M07 reconstruction authorities, the engine baseline/configuration boundaries, and the matching audit criteria before editing. Preserve the existing backend-neutral `ReconstructionJobSpec`/configuration digest boundary and the accepted PL-0167 camera-prior and PL-0166 working-set behavior.

## Frozen scope

Implement only a PackLab-owned, backend-neutral feature-extraction configuration boundary for the first packaged-consumer-goods preset:

1. Add an immutable typed configuration/preset representation for the initial COLMAP-compatible feature-extraction settings. The preset must make its intended consumer-packaging tradeoffs explicit, including image-size limit, feature-count limit, scale-space/octave settings, contrast/peak threshold, edge threshold, and orientation policy, with deterministic named defaults and validated bounds.
2. Provide deterministic serialization and a configuration digest suitable for reconstruction provenance. Reject unknown/unsafe values, non-finite numbers, invalid ranges, absolute paths, and silently unsupported backend options. Preserve explicit overrides without mutating the preset or input objects.
3. Provide a narrow mapping from the normalized PackLab configuration to the selected COLMAP 3.12.6 feature-extraction parameter names/values, while keeping engine syntax at the adapter boundary. Do not invoke COLMAP or install/download any engine.
4. Keep the configuration backend-neutral at the PackLab contract boundary. Do not put feature-extraction state in UI widgets, project trackers, `TASKS.md`, PackScan schemas, RAW_CAPTURE, or camera-prior objects. Do not claim the initial preset is physically benchmarked or universally optimal; label it as an explicit first preset and retain known limitations in provenance or documentation where the existing contract permits.
5. Add deterministic tests for default values and preset identity, valid overrides, digest stability/order independence, invalid/non-finite/out-of-range values, unsupported options, adapter mapping, and non-mutation/no-private-path behavior. Tests must exercise the PackLab-owned boundary rather than only a constant or string helper.

Do not implement feature extraction execution, image processing, matching, sparse mapping, camera solving, dense reconstruction, segmentation, mask lifting, UI workflow, engine installation/execution, neural/generative models, metric calibration, schema changes, dependency/lock changes, physical/native-device acceptance, or PL-0169+ work.

## Allowed files

- `core/src/packlab_core/feature_extraction.py`
- `tests/core/test_feature_extraction.py`
- `coordination/sessions/M07-C001/PL-0168_CODEX_LOG_V01.md`

Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, prior prompts/criteria/logs/audits, schemas, dependency/lock files, generated artifacts, binaries, secrets, private scans, signing material, UI code, engine executables, or PL-0169+ code. Do not modify accepted PL-0167/PL-0166 product code for convenience.

## Validation and publication

Run and record every required check with exact command, expected result, failure condition, actual result, and exit status:

- focused PL-0168 tests and relevant reconstruction-contract/engine-configuration boundaries;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff on every changed Python implementation/test path;
- targeted mypy on the changed Python implementation path, reporting unchanged repository debt without adding errors;
- `python -m compileall -q` on every changed Python implementation path;
- `git diff --check` and protected-file/scope/privacy/secrets/generated/binary checks.

Review the actual changed-file set. Use separate implementation/evidence and log-only commits, push only `origin main`, verify remote visibility, create exactly `PL-0168_CODEX_LOG_V01.md`, and end it exactly with:

`READY_FOR_INDEPENDENT_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, create/edit ChatGPT audit artifacts, assign `AUDITED_PASS`, or start PL-0169.
