# PL-0085 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `6961d5cb4a3c4f5426f4b68948b3024e3f483313`

## Independent findings

The child correctly adds:
- a toggleable SwiftUI debug overlay;
- a lightweight formatting model;
- explicit unavailable labeling;
- no second sensor pipeline;
- no hit-testing interference with capture controls.

However the actual overlay is not driven by live/existing tracking state.

### Overlay data is hard-coded

In `ContentView`, the overlay is built with:

- `TrackingSnapshot(quality: .unavailable, poseEvidenceEligible: false)`;
- `epoch: 0`;
- `pose: nil`.

Therefore the displayed tracking state, epoch and pose are always placeholders. The overlay is not connected to the real AR/motion state models from prior M03 tasks. Criterion 11 / Requirement B fails, and criterion 10 is incomplete because it does not actually display current state.

### Orientation information is absent

The frozen requirement asks for concise pose/orientation/epoch information. `PoseOverlayModel` shows only tracking, epoch and pose timestamp. It does not display any pose transform/orientation or motion attitude.

### Test coverage does not match the log claim

The implementation test covers unavailable and disabled states only. There is no inspected formatting test for normal and degraded inputs as required by criterion 14, despite the log stating normal/unavailable/disabled tests were added.

## Criteria

- PASS: 1-9, 12-13, 16-18
- FAIL: 10, 11, 14, 15, 19-20

## Required remediation

1. Bind the overlay to the real shared AR tracking/pose/motion state, not hard-coded unavailable values.
2. Display concise live pose/orientation and current localization epoch when available.
3. Preserve explicit simulator/unavailable labels and never synthesize data.
4. Add deterministic formatting/view-model tests for normal, degraded, recovering and unavailable states.
5. Publish a complete task-specific log checkpoint.

PL-0085 remains unchecked.

Decision: **CHANGES_REQUIRED**
