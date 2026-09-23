# PL-0082 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `21bfbf9ea24da1ce7331a09b07fa4dbc46f69052`

## Independent findings

The child correctly freezes several important semantics:
- right-handed basis;
- X right, Y up, camera forward -Z;
- AR session origin;
- metre translation unit;
- explicit 4×4 representation;
- image-pixel coordinates excluded;
- coordinate convention string exactly matches the accepted M02 pose schema:
  `packscan_right_handed_x_right_y_up_z_out_of_screen_camera_forward_neg_z_v3`;
- identity basis conversion is consistent with the M02 schema's `arkit_to_packscan_identity_shared_right_handed_basis_v1`.

However the mandatory mathematical validation is incomplete.

### Required golden cases are missing

Criterion 13 / Requirement D explicitly requires tests for:
- identity;
- translation;
- axis rotations;
- composition;
- invertibility / round-trip within tolerance.

The inspected test covers only identity, identity composition, finiteness, and units. There is no translation case, X/Y/Z rotation case, inverse implementation, or round-trip test.

### Invalid matrix behavior is unsafe

`CoordinateTransform.multiplied(by:)` returns `.identity` whenever either matrix does not contain exactly 16 values. Invalid geometry therefore silently becomes a valid-looking identity transform rather than failing closed. That weakens boundary behavior and criterion 15.

## Criteria

- PASS: 1-12, 14, 16-18
- FAIL: 13, 15, 19-20

## Required remediation

1. Add explicit transform validation and fail-closed behavior for wrong-size/non-finite matrices.
2. Add inverse/round-trip support or an equivalent tested conversion round-trip.
3. Add golden tests for translation, rotations around all relevant axes, nontrivial composition, inverse and round-trip tolerance.
4. Demonstrate encoded PackScan coordinate/basis/unit constants remain aligned with the M02 pose schema.
5. Publish a complete task-specific log checkpoint.

PL-0082 remains unchecked.

Decision: **CHANGES_REQUIRED**
