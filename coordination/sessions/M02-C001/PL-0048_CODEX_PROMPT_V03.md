# PL-0048 — Codex Remediation Work Order V03

Task: **PL-0048 — Coherent right-handed PackScan pose convention**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_PROMPT_V03.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_LOG_V03.md

## Authorization gate

Read TASKS.md, AGENTS.md, MILESTONE_BATCH_PROTOCOL.md, PL-0048 V01/V02 history, the blocking V02 audit, this prompt and its criteria.

TASKS.md must authorize `M02-REMEDIATION-BATCH-002` / CODEX.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset, rebase, force-push, destructively clean, stash owner work, edit TASKS.md, start PL-0051, or start M03.

## Authorized files

- `schemas/packscan/pose.schema.json`
- `docs/packscan/pose.md`
- `tests/fixtures/packscan/pose-*.json`
- `tests/packscan/test_pose_contract.py`

Minimal adjacent files are allowed only if technically unavoidable and justified in the log.

## Required convention

Preserve a **right-handed** PackScan pose space without a single-axis reflection.

Freeze the PackScan camera/local convention as:
- +X right
- +Y up
- +Z points out of the camera/device screen side
- camera viewing direction is **-Z**
- matrices are row-major stored values but mathematically use column vectors on the right
- translation unit is metres

This is intentionally compatible with ARKit's right-handed camera convention. The mathematical basis conversion is identity. Converting `simd_float4x4` storage to row-major JSON is serialization/layout handling, not a geometric reflection or transpose of the mathematical transform.

## Mandatory requirements

1. Replace the false `packscan_right_handed_x_right_y_up_z_forward` convention with a truthful versioned identifier that states right-handed X-right/Y-up with camera forward -Z.
2. Remove the reflection basis `B = diag(1,1,-1,1)` and the `arkit_camera_neg_z_to_packscan_pos_z_reflection_v1` identifier.
3. Freeze mathematical conversion as identity between ARKit pose coordinates and PackScan pose coordinates, with only explicit matrix serialization from Apple's column-oriented storage access into PackScan row-major nested arrays.
4. Preserve translation units as metres.
5. Preserve quaternion `xyzw` ordering and use identity component mapping for the same right-handed basis unless a mathematically justified normalization/sign-equivalence rule is documented.
6. Require the coordinate-convention and basis-conversion identifiers on all pose records.
7. Enforce state pairs:
   - available -> normal
   - degraded -> limited
   - unavailable -> not_available and confidence null, with no transforms/quaternion.
8. Add a negative fixture for `status=unavailable` with `tracking_state=normal`.
9. Add sensitivity tests proving the destination basis is right-handed, for example `X cross Y = Z` / determinant +1, and that camera forward is -Z.
10. Add a mutation/negative test that the old +Z-forward/right-handed reflection convention cannot satisfy the current contract.
11. Preserve UTC timestamp/provenance/no-LiDAR boundaries and do not claim native ARKit/device execution.

## Validation

Run focused pose tests, actual Draft 2020-12 positive/negative validation, full relevant Python regression, Ruff, mypy, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must fail against the V02 handedness defect and the V02 unavailable/normal tracking gap.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_LOG_V03.md with synchronized start, implementation/evidence commit, exact files, mathematical convention mapping, negative/mutation evidence, full regressions, scope/privacy review, platform limitations and remote visibility.

End exactly `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
