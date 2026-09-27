# PL-0167 — Codex Work Order V01

Task: **PackScan camera intrinsics and pose-prior consumption**

Repository:
https://github.com/Sekiph82/PackLab

Parent architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

Architecture decision:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0003-object-centric-reconstruction-authority.md

Mandatory pre-read:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0163_RECONSTRUCTION_BACKEND_CONTRACT.md

Previous child audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0166_CHATGPT_AUDIT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0167_CODEX_LOG_V01.md

## Authorization gate

Before material work, read the live `TASKS.md`. It must authorize M07-C001 / READY / CODEX for PL-0167. PL-0158 through PL-0166 must remain accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0168 and later tasks are not authorized.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination protocol/policy files, the OpenReality architecture, ADR-0003, the PL-0163 contract, the PackScan schemas/validator, and the accepted M06/M07 project/workspace/provenance authorities before editing. Preserve the PL-0166 byte-preserving working-set seam and the existing backend-neutral `ReconstructionInputSet`/`CameraPrior` contract. Do not create a competing PackScan, project, calibration, pose, or reconstruction authority.

## Frozen scope

Implement only the PackLab-owned seam needed for PL-0167:

1. Read valid per-image camera intrinsics and available capture pose observations from the finalized PackScan through the accepted PackScan authority and associate them with the PL-0166 working image asset IDs.
2. Normalize each accepted prior to the explicit PackLab camera convention and record the source, dimensions/coordinate assumptions, units, and policy/version needed to interpret it. Reject malformed, incomplete, mismatched, inconsistent, or convention-ambiguous priors fail-closed or as explicit `REJECTED` priors according to the existing `CameraPrior` contract; never silently reinterpret data.
3. Support explicit prior-use modes already defined by the contract: fixed, initialization-only, refined, ignored, and rejected. The seam must not force a prior into the solver or treat ARKit/CoreMotion pose as metrology-grade truth. Preserve downstream authority for actual camera solving and M09 metric scale.
4. Bind priors to the exact working image IDs and revision-scoped working-set/source digest. A changed source package, working-set revision, image identity, image dimensions, lens identity, or camera convention must invalidate or reject the affected prior rather than silently reusing it.
5. Add deterministic focused tests for valid intrinsics/pose mapping, missing and malformed metadata, inconsistent dimensions/lens/convention/units, each prior-use mode, image/revision binding, rejection behavior, and preservation of RAW_CAPTURE/PL-0166 working-set immutability. Tests must exercise the production boundary rather than only mirror helper implementation.
6. Keep this task limited to prior ingestion/validation/normalization. Do not implement feature extraction, matching, sparse/dense reconstruction, camera solving, segmentation, mask lifting, UI workflow, engine installation/execution, neural/generative models, metric calibration, or PL-0168+ work.

No external engine execution, model/checkpoint download, network access, private scan, generated reconstruction output, physical/native-device acceptance, or dependency/lock-file change is authorized.

## Validation and publication

Run and record every required check with the exact command, expected result, failure condition, actual result, and exit status:

- focused PL-0167 tests and the relevant PackScan/reconstruction/workspace boundary tests;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff on every changed Python implementation/test path;
- targeted mypy on every changed Python implementation path, reporting unchanged repository debt without adding errors in changed modules;
- `python -m compileall -q` on every changed Python implementation path;
- `git diff --check` and protected-file/scope/privacy/secrets/generated/binary checks.

Review the actual changed-file set. Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, prior prompts/criteria/logs/audits, dependency/lock files, generated artifacts, binaries, secrets, private scans, signing material, or PL-0168+ code. Use separate implementation/evidence and log-only commits, push `origin main`, verify remote visibility, create exactly the required log, end it exactly with:

`READY_FOR_INDEPENDENT_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, assign `AUDITED_PASS`, or start PL-0168.
