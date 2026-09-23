# PL-0082 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `48bd9631931382b1b046129b25a85cc977be3ee9`

## Independent result

The remediation closes important mathematical defects:
- invalid shape/non-finite multiplication no longer returns a valid-looking identity;
- throwing validated multiplication exists;
- a general 4×4 inverse is implemented;
- translation and X/Y/Z rotation constructors exist;
- a nontrivial composition/inverse round-trip is tested.

Two frozen remediation requirements remain incomplete.

### 1. X/Y/Z rotation tests are not golden mathematical tests

The new test only asserts:

- `CoordinateTransform.rotationX(...).values.count == 16`
- same for Y and Z.

This proves shape only. It does not verify the expected transformed basis vectors/matrix values/sign convention for any axis.

A wrong-handed or sign-flipped rotation implementation could pass the current tests.

Criterion 12 explicitly requires golden tests for X/Y/Z rotations, not merely constructor output length.

### 2. PackScan basis-conversion contract is missing

The authoritative M02 pose schema requires:

`basis_conversion = "arkit_to_packscan_identity_shared_right_handed_basis_v1"`

`PackScanCoordinateContract` currently defines only:
- `convention`;
- `units`.

There is no `basisConversion` constant and no automated comparison/validation against the authoritative pose schema.

Therefore remediation criterion 13 is not fully satisfied.

## Criteria

- PASS: 1-11, 15-18
- FAIL: 12, 13, 14, 19

## Required remediation

1. Add true golden X/Y/Z rotation tests using known vectors/matrices and verify the intended right-handed sign convention.
2. Add the authoritative PackScan basis-conversion constant and validate convention + basis conversion + metre unit against the M02 pose contract.
3. Add singular-matrix and invalid-conversion boundary tests where useful.

PL-0082 remains unchecked.

Decision: **CHANGES_REQUIRED**
