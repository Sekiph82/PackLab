# PL-0083 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `e83a7eb33dd5eee23e4a849114e2e7f303115d59`

## Independent findings

The child adds a clear tracking classifier that distinguishes:
- normal;
- limited with reason;
- unavailable;
- interrupted;
- recovering;

and correctly gates pose evidence eligibility without inventing a confidence score.

However the frozen task also requires user-visible warning behavior and stable recovery semantics.

### No user-visible warning integration

The implementation changes only `TrackingFoundation.swift` and tests. No SwiftUI/view-model/overlay path presents the classifier message to the user. Criterion 12 / Requirement C is therefore incomplete.

### No recovery stability/hysteresis

`TrackingQualityClassifier` is stateless. A single subsequent `.normal` classification immediately returns a ready/eligible snapshot. There is no policy requiring sustained normal tracking, frame count, or time threshold before clearing a degradation warning.

The provided “flapping” test simply calls normal → limited → recovering → normal and expects immediate eligibility. That is the opposite of the frozen requirement to clear only after stable recovery conditions.

### Diagnostics retention is not demonstrated

The classifier changes pose eligibility, but no inspected integration proves previously recorded diagnostics remain retained when degradation occurs. Criterion 13 is only partially supported.

## Criteria

- PASS: 1-11, 16-18
- FAIL: 12, 13, 14, 15, 19-20

## Required remediation

1. Bind tracking degradation/recovery state to a visible capture warning/instruction.
2. Add an explicit recovery-stability policy/hysteresis before returning to pose-eligible normal state.
3. Preserve degradation events/diagnostics across state changes.
4. Add deterministic tests for rapid flapping, sustained recovery threshold, warning visibility state and diagnostic retention.
5. Publish a complete task-specific log checkpoint.

PL-0083 remains unchecked.

Decision: **CHANGES_REQUIRED**
