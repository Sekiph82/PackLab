# PL-0166 — Codex Work Order V01

Task: **Reconstruction-safe photo preprocessing and working-set materialization**

Repository:
https://github.com/Sekiph82/PackLab

Parent master:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0166_CHATGPT_AUDIT_CRITERIA_V01.md

Mandatory architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

Related authority:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0003-object-centric-reconstruction-authority.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0166_CODEX_LOG_V01.md

## Authorization gate

Before material work, read the live `TASKS.md`. It must authorize M07-C001 / READY / CODEX for PL-0166. PL-0158 through PL-0165 must remain accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0167 and later tasks are not authorized.

Read `AGENTS.md`, `CLAUDE.md`, `README.md`, the coordination protocol/policy files, the parent master prompt/criteria, the mandatory architecture and ADR above, and the accepted authorities before editing. In particular, preserve the existing PackScan validator/container, RawEvidenceStore, ProjectManager, ProjectLayout, ReconstructionWorkspaceManager, ProvenanceManager, and backend-neutral reconstruction contract. Do not create a competing raw/project/workspace authority.

## Frozen scope

Implement only the PackLab-owned input-preparation seam needed for PL-0166:

1. Validate/read a finalized PackScan RAW_CAPTURE through the accepted PackScan authority and materialize a revision-scoped reconstruction working set through the accepted project/workspace authority.
2. Preserve every source image as full-image evidence for camera solving. The default V01 path must be byte-preserving and deterministic: no silent crop, resize, recompression, background erasure, metadata stripping, or mask-based deletion. If a preprocessing transform is genuinely required by the implementation, it must be explicit, deterministic, versioned in the working-set manifest, and retain the original full-image evidence alongside the derived file.
3. Record a machine-readable working-set manifest that binds the source PackScan/package digest, each source image asset ID and SHA-256, each working asset ID and SHA-256, deterministic ordering, and the preprocessing policy/version. Integrate the resulting image IDs with the existing `ReconstructionInputSet` contract without promoting working data to RAW_CAPTURE authority.
4. Fail closed before publishing a working set when the source package is missing, corrupt, checksum-invalid, schema-invalid, digest-mismatched, missing a declared image, or contains an unsafe/colliding destination. Do not overwrite RAW_CAPTURE, an existing reconstruction revision, or a previously published working set. Use the existing atomic/safe path boundaries and clean up partial output on failure.
5. Keep the full source-image set available to the backend input contract. Do not implement camera-prior policy, feature extraction, matching, sparse mapping, dense reconstruction, segmentation, mask-to-3D lifting, or UI workflow in this task; those belong to PL-0167+, M08, or later scopes.
6. Add deterministic focused tests that would fail if source bytes, source digests, full-image availability, failure atomicity, path safety, or revision isolation regressed. Preserve all accepted M06/M07 behavior and do not alter dependency or lock files.

No external engine execution, download, model/checkpoint installation, network access, private scan, generated reconstruction output, or physical/native-device acceptance is authorized.

## Validation and publication

Run and record every required check with the exact command, expected result, failure condition, actual result, and exit status:

- focused PL-0166 tests, including the existing reconstruction workspace/PackScan boundary tests;
- `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs`;
- Ruff on every changed Python implementation/test path;
- targeted mypy on every changed Python implementation path, reporting unchanged repository debt without adding errors in changed modules;
- `python -m compileall -q` on every changed Python implementation path;
- `git diff --check` and protected-file/scope checks.

Review the actual changed-file set. Do not edit `TASKS.md`, any `CHATGPT_AUDIT_*` artifact, prior prompts/criteria/logs/audits, dependency/lock files, generated artifacts, binaries, secrets, private scans, signing material, or PL-0167+ code. Use a separate implementation/evidence commit and log-only commit, push `origin main`, and verify remote visibility without self-auditing.

Create exactly the required log at the URL above using full GitHub URLs. End the log exactly with:

`READY_FOR_INDEPENDENT_AUDIT`

Stop after the handoff. Do not edit `TASKS.md`, assign `AUDITED_PASS`, or start PL-0167.
