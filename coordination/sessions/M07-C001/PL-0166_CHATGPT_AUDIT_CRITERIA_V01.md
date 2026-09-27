# PL-0166 — ChatGPT Audit Criteria V01

Task: **Reconstruction-safe photo preprocessing and working-set materialization**

Parent:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Mandatory architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

Related authority:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0003-object-centric-reconstruction-authority.md

Criteria:

1. Root `TASKS.md` authorizes M07-C001 / READY / CODEX for PL-0166 before material work; PL-0158 through PL-0165 remain accepted, PL-0068 remains `OWNER_REQUIRED`, and PL-0167+ is not authorized.
2. The parent master criteria, OpenReality-derived architecture, ADR-0003, accepted M06/M07 project/raw/workspace/provenance authorities, and the backend-neutral reconstruction contract remain intact.
3. A PackLab-owned deterministic input-preparation seam validates/reads finalized PackScan RAW_CAPTURE and materializes a revision-scoped reconstruction working set through existing ProjectManager/ProjectLayout/ReconstructionWorkspaceManager/PackScan authorities; no competing raw or project authority is introduced.
4. Every source image remains available as full-image evidence for camera solving. V01 preserves source image bytes and SHA-256 values; it does not silently crop, resize, recompress, erase backgrounds, strip metadata, or delete pixels through masks. Any explicit derived transform must retain the original and record a deterministic version/policy.
5. A machine-readable working-set manifest binds the source package/input digest, source and working image IDs, per-image SHA-256 values, deterministic order, and preprocessing policy/version, and integrates the working image IDs with the existing `ReconstructionInputSet` contract.
6. Invalid, corrupt, checksum-invalid, schema-invalid, digest-mismatched, missing-image, unsafe-path, destination-collision, and partial-write cases fail closed without publishing a partial working set or mutating RAW_CAPTURE, an existing revision, or a previously published working set.
7. Focused tests are sensitive to source immutability, byte/digest preservation, full-image availability, deterministic manifest/order, failure atomicity, path safety, and revision isolation; they do not merely mirror the implementation.
8. No camera-prior policy, feature extraction, matching, sparse mapping, dense reconstruction, segmentation, mask-to-3D lifting, UI workflow, external engine execution, model/checkpoint installation, or PL-0167+ implementation is included.
9. Focused tests and `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q -rs` exit `0`.
10. Ruff, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/privacy/secrets/signing, and generated/binary reviews pass truthfully; unchanged repository-wide mypy debt is disclosed and no changed module adds an error.
11. The child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0166_CODEX_LOG_V01.md, uses full GitHub URLs, records exact commands/results/SHAs/limitations, and ends exactly `READY_FOR_INDEPENDENT_AUDIT`.
12. Codex does not edit `TASKS.md`, create/edit ChatGPT audit artifacts, self-audit, assign `AUDITED_PASS`, or start PL-0167; implementation and log publication boundaries are separately reviewable.

Closure requires a fresh independent ChatGPT audit of the actual GitHub diff, source, tests, and handoff.
