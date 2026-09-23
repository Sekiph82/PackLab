# PL-0084 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `c660e53f6fa8b8fe2629891debaa8e44c63f94b8`

## Independent findings

The child adds a useful epoch model:
- explicit reset reasons;
- relocalizing/recovered/failed states;
- monotonically increasing localization epochs;
- pose acceptance constrained to the current recovered epoch;
- deterministic proof that old epochs are rejected after reset.

However the frozen task requires actual capture-session reset/relocalization behavior.

### No ARSession reset execution

`SessionEpochCoordinator.reset(reason:)` only mutates the pure model. The implementation does not call the one ARSession owner with appropriate `ARSession.RunOptions` such as reset/relocalization options when required. Therefore criterion 11 / Requirement B is not implemented.

### No real user/system reset path

No SwiftUI/view-model/system-event path invokes a coordinated AR reset. The pure coordinator is not connected to the AR tracking controller, camera capture orchestration, interruption recovery, or degraded-tracking flow. Criterion 10 is incomplete.

### Diagnostics and orchestration coverage are incomplete

`lastReason` retains the most recent reason, but no diagnostic event/evidence record is persisted. Tests do not exercise reset during actual idle/active/degraded orchestration or repeated requests against the AR session owner; they only mutate the coordinator struct.

## Criteria

- PASS: 1-9, 12, 16-18
- FAIL: 10, 11, 13, 14, 15, 19-20

## Required remediation

1. Wire reset/relocalization through the single ARSession owner and use explicit ARSession run options only when required.
2. Connect user-requested, interruption and tracking-degradation reset triggers to that orchestration path.
3. Preserve immutable accepted captures while invalidating pose continuity across epochs.
4. Persist reset reason/epoch diagnostics and expose relocalizing/recovered/failed state.
5. Add deterministic orchestration tests for idle, active, degraded/interrupted and repeated reset requests.
6. Publish a complete task-specific log checkpoint.

PL-0084 remains unchecked.

Decision: **CHANGES_REQUIRED**
